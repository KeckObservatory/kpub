"""Unit tests for kpub's top-level CLI wrapper functions and helpers.

Each kpub_* function here reads the real config.live.yaml (a local repo
file -- no network/credentials are ever used) and then constructs a
PublicationDB. To guarantee no test touches a real MongoDB instance, every
test in this file replaces kpub.PublicationDB itself with a MagicMock
class, so the constructor never runs and every DB call is a mock we can
assert against.
"""
import datetime
import json
from unittest.mock import MagicMock

import pytest

import kpub as kpub_module
from kpub import (
    kpub_add,
    kpub_delete,
    kpub_export,
    kpub_export_fulltext,
    kpub_import,
    kpub_plot,
    kpub_plot_data,
    kpub_set_affiliation,
    kpub_spreadsheet,
    kpub_stats,
    kpub_update,
    make_parser,
    serialize_datetime,
)


@pytest.fixture(autouse=True)
def mock_publication_db(monkeypatch):
    """Replace PublicationDB with a MagicMock class for every test in this file."""
    mock_cls = MagicMock(name='PublicationDB_class')
    monkeypatch.setattr(kpub_module, 'PublicationDB', mock_cls)
    return mock_cls


# ---------------------------------------------------------------------------
# serialize_datetime
# ---------------------------------------------------------------------------

def test_serialize_datetime_returns_isoformat():
    dt = datetime.datetime(2020, 5, 1, 12, 30)
    assert serialize_datetime(dt) == dt.isoformat()


def test_serialize_datetime_raises_for_non_datetime():
    with pytest.raises(TypeError):
        serialize_datetime('not a date')


# ---------------------------------------------------------------------------
# kpub_stats
# ---------------------------------------------------------------------------

def test_kpub_stats_writes_overview_and_saves_markdown_twice(mock_publication_db, monkeypatch, tmp_path):
    monkeypatch.setattr(kpub_module, 'MDDIR', str(tmp_path))
    pubdb = mock_publication_db.return_value
    pubdb.get_metrics.return_value = {
        'publication_count': 10, 'refereed_count': 8, 'citation_count': 100, 'author_count': 5,
    }
    pubdb.get_most_cited.return_value = []
    pubdb.get_most_active_first_authors.return_value = []

    kpub_stats()

    assert pubdb.save_markdown.call_count == 2
    overview = tmp_path / 'publications-overview.md'
    assert overview.exists()
    content = overview.read_text()
    assert '10 publications' in content
    assert '8 are peer-reviewed' in content


# ---------------------------------------------------------------------------
# kpub_plot_data / kpub_plot
# ---------------------------------------------------------------------------

def test_kpub_plot_data_delegates_to_db(mock_publication_db):
    pubdb = mock_publication_db.return_value
    pubdb.get_plot_data.return_value = {'x': [1, 2, 3]}

    result = kpub_plot_data('plot_by_year', instruments='HIRES', year_begin=2015, extrapolate=True)

    assert result == {'x': [1, 2, 3]}
    pubdb.get_plot_data.assert_called_once_with(
        plotname='plot_by_year', instruments='HIRES', extrapolate=True, year_begin=2015)


def test_kpub_plot_calls_get_plot(mock_publication_db):
    pubdb = mock_publication_db.return_value

    kpub_plot()

    pubdb.get_plot.assert_called_once()


# ---------------------------------------------------------------------------
# kpub_update
# ---------------------------------------------------------------------------

def test_kpub_update_returns_db_update_result(mock_publication_db):
    pubdb = mock_publication_db.return_value
    pubdb.update.return_value = (True, 7)

    result = kpub_update('2020-05')

    assert result == (True, 7)
    pubdb.update.assert_called_once_with(month='2020-05')


# ---------------------------------------------------------------------------
# kpub_add / kpub_delete
# ---------------------------------------------------------------------------

def test_kpub_add_adds_each_bibcode(mock_publication_db):
    pubdb = mock_publication_db.return_value

    kpub_add(['2020ApJ...1A', '2020ApJ...2B'], interactive=True)

    assert pubdb.add_by_bibcode.call_count == 2
    pubdb.add_by_bibcode.assert_any_call('2020ApJ...1A', interactive=True)
    pubdb.add_by_bibcode.assert_any_call('2020ApJ...2B', interactive=True)


def test_kpub_delete_deletes_each_bibcode(mock_publication_db):
    pubdb = mock_publication_db.return_value

    kpub_delete(['2020ApJ...1A', '2020ApJ...2B'])

    assert pubdb.delete_by_bibcode.call_count == 2
    pubdb.delete_by_bibcode.assert_any_call('2020ApJ...1A')
    pubdb.delete_by_bibcode.assert_any_call('2020ApJ...2B')


# ---------------------------------------------------------------------------
# kpub_import
# ---------------------------------------------------------------------------

def test_kpub_import_adds_each_row_by_bibcode(mock_publication_db, tmp_path):
    pubdb = mock_publication_db.return_value
    jsonfile = tmp_path / 'rows.json'
    jsonfile.write_text(json.dumps([
        {'bibcode': '2020ApJ...1A', 'mission': 'keck'},
        {'bibcode': '2020ApJ...2B', 'mission': 'keck'},
    ]))

    kpub_import(str(jsonfile))

    assert pubdb.add_by_bibcode.call_count == 2
    pubdb.add_by_bibcode.assert_any_call('2020ApJ...1A', interactive=False)
    pubdb.add_by_bibcode.assert_any_call('2020ApJ...2B', interactive=False)


def test_kpub_import_logs_and_continues_on_row_error(mock_publication_db, tmp_path, caplog):
    pubdb = mock_publication_db.return_value
    pubdb.add_by_bibcode.side_effect = [Exception('ADS lookup failed'), None]
    jsonfile = tmp_path / 'rows.json'
    jsonfile.write_text(json.dumps([
        {'bibcode': '2020ApJ...1A'},
        {'bibcode': '2020ApJ...2B'},
    ]))

    with caplog.at_level('WARNING', logger='KPUB'):
        kpub_import(str(jsonfile))

    assert pubdb.add_by_bibcode.call_count == 2
    assert any('Could not import' in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# kpub_set_affiliation
# ---------------------------------------------------------------------------

def test_kpub_set_affiliation_delegates_to_db(mock_publication_db):
    pubdb = mock_publication_db.return_value
    pubdb.set_affiliation.return_value = [{'bibcode': '2020ApJ...1A', 'affiliation': 'keck'}]

    result = kpub_set_affiliation(
        [{'bibcode': '2020ApJ...1A'}], 'tester', affiliation='keck',
        koa_affiliation=True, instruments=['HIRES'], note='a note')

    assert result == [{'bibcode': '2020ApJ...1A', 'affiliation': 'keck'}]
    pubdb.set_affiliation.assert_called_once_with(
        [{'bibcode': '2020ApJ...1A'}], 'tester', affiliation='keck',
        koa_affiliation=True, instruments=['HIRES'], note='a note')


# ---------------------------------------------------------------------------
# kpub_export_fulltext
# ---------------------------------------------------------------------------

def test_kpub_export_fulltext_uses_fulltext_collection(mock_publication_db):
    pubdb = mock_publication_db.return_value
    pubdb.get_fulltext.return_value = [{'bibcode': '2020ApJ...1A', 'fulltext': 'text'}]

    result = kpub_export_fulltext(['2020ApJ...1A'])

    assert result == [{'bibcode': '2020ApJ...1A', 'fulltext': 'text'}]
    assert mock_publication_db.call_args.kwargs['collection'] == 'fulltext'
    pubdb.get_fulltext.assert_called_once_with(['2020ApJ...1A'])


# ---------------------------------------------------------------------------
# kpub_export
# ---------------------------------------------------------------------------

def test_kpub_export_all_ignores_month_filters(mock_publication_db):
    pubdb = mock_publication_db.return_value
    pubdb.get_articles.return_value = [{'bibcode': '2020ApJ...1A'}]

    result = kpub_export('2020-05', affiliation='keck', export_all=True)

    assert result == [{'bibcode': '2020ApJ...1A'}]
    pubdb.get_articles.assert_called_once_with(affiliation='keck')


def test_kpub_export_returns_empty_list_when_no_articles(mock_publication_db):
    pubdb = mock_publication_db.return_value
    pubdb.get_articles.return_value = []

    result = kpub_export('2020-05')

    assert result == []


def test_kpub_export_writes_json_file_with_datetime_serialization(mock_publication_db, tmp_path):
    pubdb = mock_publication_db.return_value
    pubdb.get_articles.return_value = [
        {'bibcode': '2020ApJ...1A', 'date_modified': datetime.datetime(2020, 1, 1, 12, 0, 0)}
    ]
    out_file = tmp_path / 'export.json'

    kpub_export('2020-05', filename=str(out_file))

    written = json.loads(out_file.read_text())
    assert written[0]['bibcode'] == '2020ApJ...1A'
    assert written[0]['date_modified'] == datetime.datetime(2020, 1, 1, 12, 0, 0).isoformat()


def test_kpub_export_writes_csv_file(mock_publication_db, tmp_path):
    pubdb = mock_publication_db.return_value
    pubdb.get_articles.return_value = [{'bibcode': '2020ApJ...1A', 'year': 2020}]
    out_file = tmp_path / 'export.csv'

    kpub_export('2020-05', filename=str(out_file), csv=True)

    content = out_file.read_text()
    assert 'bibcode' in content
    assert '2020ApJ...1A' in content


def test_kpub_export_parses_monthyear_and_begin_year(mock_publication_db):
    pubdb = mock_publication_db.return_value
    pubdb.get_articles.return_value = [{'bibcode': 'A'}]

    kpub_export('2020-05', begin_year='2018', affiliation=None)

    pubdb.get_articles.assert_called_once_with(
        begin_year=2018, end_year=2020, month=5, affiliation=None)


# ---------------------------------------------------------------------------
# kpub_spreadsheet
# ---------------------------------------------------------------------------

class _FakeWorksheet:
    def __init__(self):
        self.rows = []

    def append(self, values):
        self.rows.append(list(values))

    def __getitem__(self, key):
        return []


class _FakeWorkbook:
    def __init__(self):
        self.active = _FakeWorksheet()
        self.saved_to = None

    def save(self, filename):
        self.saved_to = filename


def test_kpub_spreadsheet_computes_refereed_label_and_citations_per_year(
        mock_publication_db, monkeypatch):
    fake_wb = _FakeWorkbook()
    monkeypatch.setattr('openpyxl.Workbook', MagicMock(return_value=fake_wb))

    pubdb = mock_publication_db.return_value
    old_date = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-00')
    pubdb.select_for_spreadsheet.return_value = [
        {
            'bibcode': '2020ApJ...1A', 'year': 2020, 'date': old_date, 'mission': 'keck',
            'date_modified': datetime.datetime(2020, 1, 1), 'last_modifier': 'kpub',
            'property': ['REFEREED'], 'citation_count': 10, 'read_count': 100,
            'first_author_norm': 'Smith, J.', 'title': ['A great paper'],
            'keyword_norm': None, 'keyword': None, 'abstract': 'abstract text',
            'author_norm': ['Smith, J.'], 'instruments': ['HIRES'], 'archive': False,
            'affiliation': 'keck', 'aff': ['Keck Observatory'],
        },
        {
            'bibcode': '2020ApJ...2B', 'year': 2020, 'date': old_date, 'mission': 'keck',
            'date_modified': datetime.datetime(2020, 1, 1), 'last_modifier': 'kpub',
            'property': ['NOT REFEREED'], 'citation_count': None, 'read_count': 5,
            'first_author_norm': 'Doe, A.', 'title': ['Another paper'],
            'keyword_norm': None, 'keyword': None, 'abstract': 'abstract text 2',
            'author_norm': ['Doe, A.'], 'instruments': [], 'archive': False,
            'affiliation': 'keck', 'aff': ['Keck Observatory'],
        },
    ]

    kpub_spreadsheet('my-export.xlsx')

    # PublicationDB must be constructed with just the config dict (not the filename)
    mock_publication_db.assert_called_once()
    call_args = mock_publication_db.call_args[0]
    assert len(call_args) == 1
    assert isinstance(call_args[0], dict)
    # and the workbook must be saved to the requested filename, not a hardcoded one
    assert fake_wb.saved_to == 'my-export.xlsx'

    header, row1, row2 = fake_wb.active.rows
    assert header[0] == 'bibcode'
    refereed_idx = header.index('refereed')
    citations_per_year_idx = header.index('citations_per_year')
    assert row1[refereed_idx] == 'REFEREED'
    assert row1[citations_per_year_idx] == pytest.approx(10 / 1, rel=0.05)
    assert row2[refereed_idx] == 'NOT REFEREED'
    assert row2[citations_per_year_idx] == 0  # citation_count None -> TypeError -> falls back to 0


# ---------------------------------------------------------------------------
# make_parser
# ---------------------------------------------------------------------------

def test_make_parser_update_subcommand():
    parser = make_parser()
    args = parser.parse_args(['update', '2020-05'])
    assert args.command == 'update'
    assert args.month == '2020-05'


def test_make_parser_update_subcommand_month_optional():
    parser = make_parser()
    args = parser.parse_args(['update'])
    assert args.month is None


def test_make_parser_add_subcommand_with_interactive_flag():
    parser = make_parser()
    args = parser.parse_args(['add', '2020ApJ...1A', '2020ApJ...2B', '-interactive'])
    assert args.bibcode == ['2020ApJ...1A', '2020ApJ...2B']
    assert args.interactive is True


def test_make_parser_delete_subcommand():
    parser = make_parser()
    args = parser.parse_args(['delete', '2020ApJ...1A'])
    assert args.bibcode == ['2020ApJ...1A']


def test_make_parser_export_subcommand_defaults():
    parser = make_parser()
    args = parser.parse_args(['export'])
    assert args.command == 'export'
    assert args.csv is False
    assert args.all is False


def test_make_parser_export_subcommand_with_all_flag():
    parser = make_parser()
    args = parser.parse_args(['export', '2020-05', '-csv', '--all'])
    assert args.csv is True
    assert args.all is True


def test_make_parser_stats_and_plot_subcommands():
    parser = make_parser()
    assert parser.parse_args(['stats']).command == 'stats'
    assert parser.parse_args(['plot']).command == 'plot'


def test_make_parser_update_citations_subcommand():
    parser = make_parser()
    args = parser.parse_args(['update_citations', '2020'])
    assert args.year == 2020


def test_make_parser_spreadsheet_subcommand_requires_filename():
    parser = make_parser()
    args = parser.parse_args(['spreadsheet', 'out.xlsx'])
    assert args.filename == 'out.xlsx'


def test_make_parser_requires_a_command():
    parser = make_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])
