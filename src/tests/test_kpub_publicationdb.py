"""Unit tests for kpub.PublicationDB methods.

The MongoDB client/collection are mocked (see conftest.py); no test here
ever opens a real network connection. Methods that PublicationDB inherits
from MongoDBConnector (query, add_row, article_exists, update_row_affiliation,
get_articles_by_mission_years, get_articles_by_years_instrument,
get_count_cumulative) are treated as the database boundary and are mocked
directly where a test's target method depends on them, so that each test
exercises only the logic that actually lives in kpub.py.
"""
import datetime
from unittest.mock import MagicMock

import pymongo
import pytest

import kpub as kpub_module


# ---------------------------------------------------------------------------
# get_affiliation
# ---------------------------------------------------------------------------

def test_get_affiliation_acknowledgement_found(db):
    snippits = {'W. M. Keck Foundation': {'count': 1, 'snippets': []}}
    affiliation, has_ack, reason = db.get_affiliation(snippits, mission='pipeline')
    assert affiliation == 'keck'
    assert has_ack is True
    assert reason == 'Acknowledgement found in snippets.'


def test_get_affiliation_instruments_found(db):
    snippits = {'HIRES': {'count': 1, 'snippets': []}}
    affiliation, has_ack, reason = db.get_affiliation(snippits, mission='keck')
    assert affiliation == 'keck'
    assert has_ack is False
    assert reason == 'Instrument names found in snippets.'


def test_get_affiliation_nothing_found_non_keck_mission(db):
    affiliation, has_ack, reason = db.get_affiliation({}, mission='unrelated')
    assert affiliation == 'unknown'
    assert has_ack is False
    assert reason == 'No instrument names found in snippets.'


def test_get_affiliation_nothing_found_keck_mission(db):
    affiliation, has_ack, reason = db.get_affiliation({}, mission='keck')
    assert affiliation == 'unknown'
    assert has_ack is False
    assert reason == 'Neither instr nor ack found.'


# ---------------------------------------------------------------------------
# get_archive_acknowledgement
# ---------------------------------------------------------------------------

def test_get_archive_acknowledgement_found(db):
    assert db.get_archive_acknowledgement({'KOA': {}}) is True


def test_get_archive_acknowledgement_not_found(db):
    assert db.get_archive_acknowledgement({'HIRES': {}}) is False


def test_get_archive_acknowledgement_not_configured(config):
    config = dict(config)
    config['archive'] = []
    db = kpub_module.PublicationDB(config=config, collection='articles')
    assert db.get_archive_acknowledgement({'anything': {}}) == ''


# ---------------------------------------------------------------------------
# get_aff_type
# ---------------------------------------------------------------------------

def test_get_aff_type_blank_string_returns_none(db):
    assert db.get_aff_type('-', db.config['aff_defs']) is None
    assert db.get_aff_type('', db.config['aff_defs']) is None


def test_get_aff_type_matches_keck(db):
    result = db.get_aff_type('Keck Observatory, Hawaii', db.config['aff_defs'])
    assert result == 'keck'


def test_get_aff_type_matches_usa_case_sensitive(db):
    result = db.get_aff_type('NASA Ames Research Center', db.config['aff_defs'])
    assert result == 'usa'


def test_get_aff_type_falls_back_to_default(db):
    result = db.get_aff_type('University of Tokyo, Japan', db.config['aff_defs'])
    assert result == 'intl'


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------

def test_add_inserts_row_with_expected_fields(db):
    article = {'bibcode': '2020ApJ...1A', 'pubdate': '2020-05-00', 'title': ['A title']}

    db.add(article, mission='keck', snippits={'HIRES': {'count': 1, 'snippets': []}},
           instruments='HIRES', archive=False, affiliation='keck',
           reason='Instrument names found in snippets.', hasAcknowledgement=False)

    db.collection.insert_one.assert_called_once()
    inserted = db.collection.insert_one.call_args[0][0]
    assert inserted['_id'] == '2020ApJ...1A'
    assert inserted['month'] == 5
    assert inserted['year'] == 2020
    assert inserted['mission'] == 'keck'
    assert inserted['instruments'] == ['HIRES']
    assert inserted['affiliation'] == 'keck'
    assert inserted['last_modifier'] == 'kpub'
    assert isinstance(inserted['date_modified'], datetime.datetime)


def test_add_swallows_duplicate_key_error(db, caplog):
    article = {'bibcode': '2020ApJ...1A', 'pubdate': '2020-05-00'}
    db.collection.insert_one.side_effect = pymongo.errors.DuplicateKeyError('dup')

    with caplog.at_level('WARNING', logger='KPUB'):
        db.add(article, mission='keck', snippits={}, instruments='',
               archive=False, affiliation='keck', reason='r', hasAcknowledgement=False)

    assert any('already been ingested' in r.message or 'already ingested' in r.message
               for r in caplog.records)


# ---------------------------------------------------------------------------
# add_article
# ---------------------------------------------------------------------------

def test_add_article_skips_existing_article(db):
    db.collection.count_documents.return_value = 1
    article = {'id': '123', 'bibcode': '2020ApJ...1A'}

    result = db.add_article(article)

    assert result == 0


def test_add_article_adds_new_article_with_snippets(db, monkeypatch):
    db.collection.count_documents.return_value = 0
    article = {'id': '123', 'bibcode': '2020ApJ...1A'}
    monkeypatch.setattr(db, 'find_all_snippets',
                         MagicMock(return_value={'HIRES': {'count': 1, 'snippets': ['abc']}}))
    monkeypatch.setattr(db, 'add', MagicMock(return_value=1))

    result = db.add_article(article, interactive=False)

    assert result == 1
    db.add.assert_called_once()
    _, kwargs = db.add.call_args
    assert kwargs['mission'] == 'keck'
    assert kwargs['instruments'] == 'HIRES'
    assert kwargs['affiliation'] == 'keck'


def test_add_article_marks_unrelated_when_no_snippets(db, monkeypatch):
    db.collection.count_documents.return_value = 0
    article = {'id': '123', 'bibcode': '2020ApJ...1A'}
    monkeypatch.setattr(db, 'find_all_snippets', MagicMock(return_value={}))
    monkeypatch.setattr(db, 'add', MagicMock(return_value=1))

    db.add_article(article, interactive=False)

    _, kwargs = db.add.call_args
    assert kwargs['mission'] == 'unknown'
    assert kwargs['instruments'] == ''


# ---------------------------------------------------------------------------
# find_all_snippets
# ---------------------------------------------------------------------------

def test_find_all_snippets_uses_pdf_method_and_saves_fulltext(db, monkeypatch):
    counts = {'HIRES': {'count': 1, 'snippets': ['abc']}}
    monkeypatch.setattr(kpub_module, 'get_word_match_counts_by_pdf',
                         MagicMock(return_value=(counts, 'the full text')))
    monkeypatch.setattr(kpub_module, 'get_word_match_counts_by_query', MagicMock())
    monkeypatch.setattr(db, 'save_fulltext', MagicMock())

    result = db.find_all_snippets('2020ApJ...1A')

    assert result == counts
    db.save_fulltext.assert_called_once_with('2020ApJ...1A', 'the full text')
    kpub_module.get_word_match_counts_by_query.assert_not_called()


def test_find_all_snippets_falls_back_to_query_method_on_pdf_failure(db, monkeypatch):
    counts = {'HIRES': {'count': 2, 'snippets': ['xyz']}}
    monkeypatch.setattr(kpub_module, 'get_word_match_counts_by_pdf',
                         MagicMock(side_effect=Exception('no pdf')))
    monkeypatch.setattr(kpub_module, 'get_word_match_counts_by_query',
                         MagicMock(return_value=(counts, 'query-sourced text')))
    monkeypatch.setattr(db, 'save_fulltext', MagicMock())

    result = db.find_all_snippets('2020ApJ...1A')

    assert result == counts
    db.save_fulltext.assert_called_once_with('2020ApJ...1A', 'query-sourced text')


def test_find_all_snippets_returns_empty_list_when_no_configured_words(config, monkeypatch):
    config = dict(config)
    config.update({'missions': [], 'instruments': [], 'acknowledgement': [], 'archive': []})
    db = kpub_module.PublicationDB(config=config, collection='articles')
    mock_pdf = MagicMock()
    monkeypatch.setattr(kpub_module, 'get_word_match_counts_by_pdf', mock_pdf)

    result = db.find_all_snippets('2020ApJ...1A')

    assert result == []
    mock_pdf.assert_not_called()


def test_find_all_snippets_does_not_save_when_no_fulltext(db, monkeypatch):
    monkeypatch.setattr(kpub_module, 'get_word_match_counts_by_pdf',
                         MagicMock(return_value=({}, '')))
    monkeypatch.setattr(db, 'save_fulltext', MagicMock())

    db.find_all_snippets('2020ApJ...1A')

    db.save_fulltext.assert_not_called()


# ---------------------------------------------------------------------------
# save_fulltext
# ---------------------------------------------------------------------------

def test_save_fulltext_delegates_to_upsert_fulltext(db, monkeypatch):
    monkeypatch.setattr(db, 'upsert_fulltext', MagicMock())

    db.save_fulltext('2020ApJ...1A', 'the plaintext')

    db.upsert_fulltext.assert_called_once_with('2020ApJ...1A', 'the plaintext')


# ---------------------------------------------------------------------------
# set_affiliation
# ---------------------------------------------------------------------------

def test_set_affiliation_updates_fields_and_returns_updated_articles(db):
    article = {'_id': '2020ApJ...1A', 'bibcode': '2020ApJ...1A'}

    result = db.set_affiliation([article], last_modifier='tester', affiliation='keck',
                                 koa_affiliation=True, instruments=['HIRES'], note='a note')

    assert len(result) == 1
    updated = result[0]
    assert updated['affiliation'] == 'keck'
    assert updated['archive'] is True
    assert updated['instruments'] == ['HIRES']
    assert updated['note'] == 'a note'
    assert updated['last_modifier'] == 'tester'
    db.collection.update_one.assert_called_once()
    filter_arg = db.collection.update_one.call_args[0][0]
    assert filter_arg == {'_id': '2020ApJ...1A'}


# ---------------------------------------------------------------------------
# add_by_bibcode
# ---------------------------------------------------------------------------

def test_add_by_bibcode_adds_matching_article(db, monkeypatch):
    monkeypatch.setattr(db, 'query_ads', MagicMock(return_value={
        'response': {'docs': [{'bibcode': '2020ApJ...1A', 'property': ['REFEREED']}]}
    }))
    monkeypatch.setattr(db, 'add_article', MagicMock())

    db.add_by_bibcode('2020ApJ...1A', interactive=False)

    db.query_ads.assert_called_once_with('identifier:2020ApJ...1A')
    db.add_article.assert_called_once_with(
        {'bibcode': '2020ApJ...1A', 'property': ['REFEREED']}, interactive=False)


def test_add_by_bibcode_logs_error_when_no_articles_found(db, monkeypatch, caplog):
    monkeypatch.setattr(db, 'query_ads', MagicMock(return_value={'response': {'docs': []}}))
    monkeypatch.setattr(db, 'add_article', MagicMock())

    with caplog.at_level('ERROR', logger='KPUB'):
        db.add_by_bibcode('2020ApJ...1A')

    assert any('No ADS record found' in r.message for r in caplog.records)
    db.add_article.assert_not_called()


def test_add_by_bibcode_skips_nonarticle_when_interactive(db, monkeypatch):
    monkeypatch.setattr(db, 'query_ads', MagicMock(return_value={
        'response': {'docs': [{'bibcode': '2020ApJ...1A', 'property': ['NONARTICLE']}]}
    }))
    monkeypatch.setattr(db, 'add_article', MagicMock())

    db.add_by_bibcode('2020ApJ...1A', interactive=True)

    db.add_article.assert_not_called()


# ---------------------------------------------------------------------------
# to_markdown / save_markdown
# ---------------------------------------------------------------------------

def test_to_markdown_renders_articles_grouped_by_year(db):
    rows = [{
        'year': 2020, 'title': ['a great paper'], 'bibcode': '2020ApJ...1A',
        'author': ['Smith, J.', 'Doe, A.'], 'pub': 'ApJ', 'property': ['REFEREED'],
    }]
    db.collection.find.return_value.sort.return_value = rows

    markdown = db.to_markdown(title='Test Publications')

    assert 'A GREAT PAPER' in markdown
    assert '2020ApJ...1A' in markdown
    assert 'Smith, J.' in markdown


def test_to_markdown_handles_none_property(db):
    rows = [{
        'year': 2020, 'title': ['t'], 'bibcode': '2020ApJ...1A',
        'author': ['Smith, J.'], 'pub': 'ApJ', 'property': None,
    }]
    db.collection.find.return_value.sort.return_value = rows

    markdown = db.to_markdown()

    assert '2020ApJ...1A' in markdown


def test_save_markdown_writes_file(db, monkeypatch, tmp_path):
    monkeypatch.setattr(db, 'to_markdown', MagicMock(return_value='MARKDOWN CONTENT'))
    output_fn = str(tmp_path / 'out.md')

    db.save_markdown(output_fn)

    assert (tmp_path / 'out.md').read_text() == 'MARKDOWN CONTENT'
    db.to_markdown.assert_called_once()
    assert db.to_markdown.call_args.kwargs['save_as'] == str(tmp_path / 'out.html')


# ---------------------------------------------------------------------------
# get_plot_data / get_plot
# ---------------------------------------------------------------------------

def test_get_plot_data_by_year(db, monkeypatch):
    mock_fn = MagicMock(return_value={'x': [1], 'y': [2]})
    monkeypatch.setattr(kpub_module.plot, 'get_plot_by_year_data', mock_fn)

    result = db.get_plot_data('plot_by_year')

    assert result == {'x': [1], 'y': [2]}
    mock_fn.assert_called_once_with(db, year_begin=2009, extrapolate=True)


def test_get_plot_data_author_count(db, monkeypatch):
    mock_fn = MagicMock(return_value={'authors': 3})
    monkeypatch.setattr(kpub_module.plot, 'get_plot_author_count_data', mock_fn)

    result = db.get_plot_data('plot_author_count', year_begin=2015)

    assert result == {'authors': 3}
    mock_fn.assert_called_once_with(db, year_begin=2015)


def test_get_plot_data_by_instrument_uses_config_instruments_by_default(db, monkeypatch):
    mock_fn = MagicMock(return_value=({'HIRES': 5}, 'ignored'))
    monkeypatch.setattr(kpub_module.plot, 'get_plot_instruments_data', mock_fn)

    result = db.get_plot_data('plot_by_instrument')

    assert result == {'HIRES': 5}
    _, kwargs = mock_fn.call_args
    assert kwargs['instruments'] == ['HIRES', 'LRIS']


def test_get_plot_data_unknown_plotname_raises(db):
    with pytest.raises(ValueError):
        db.get_plot_data('not_a_real_plot')


def test_get_plot_calls_all_plot_functions(db, monkeypatch):
    mocks = {
        'plot_by_year': MagicMock(),
        'plot_author_count': MagicMock(),
        'plot_instruments': MagicMock(),
        'plot_affiliations': MagicMock(),
    }
    for name, mock in mocks.items():
        monkeypatch.setattr(kpub_module.plot, name, mock)

    db.get_plot()

    assert mocks['plot_by_year'].call_count == 4  # 2 extensions x 2 variants
    assert mocks['plot_author_count'].call_count == 2  # 2 extensions
    mocks['plot_instruments'].assert_called_once()
    mocks['plot_affiliations'].assert_called_once()


# ---------------------------------------------------------------------------
# get_metrics
# ---------------------------------------------------------------------------

def test_get_metrics_computes_expected_statistics(db, monkeypatch):
    articles = [
        {'mission': 'keck', 'bibcode': '2020ApJ...1A', 'author_norm': ['Smith, J.', 'Doe, A.'],
         'first_author_norm': 'Smith, J.', 'property': ['REFEREED'], 'citation_count': 5},
        {'mission': 'keck', 'bibcode': '2020PhDT....1A', 'author_norm': ['Lee, K.'],
         'first_author_norm': 'Lee, K.', 'property': ['NOT REFEREED'], 'citation_count': 2},
        {'mission': 'unrelated', 'bibcode': '2020ApJ...3C', 'author_norm': ['Doe, A.'],
         'first_author_norm': 'Doe, A.', 'property': None},
    ]
    monkeypatch.setattr(db, 'query', MagicMock(return_value=articles))

    metrics = db.get_metrics()

    assert metrics['publication_count'] == 3
    assert metrics['keck_count'] == 2
    assert metrics['unrelated_count'] == 1
    assert metrics['phd_count'] == 1
    assert metrics['keck_phd_count'] == 1
    assert metrics['refereed_count'] == 1
    assert metrics['citation_count'] == 7
    assert metrics['author_count'] == 3
    assert metrics['first_author_count'] == 3
    assert metrics['keck_fraction'] == pytest.approx(2 / 3)


# ---------------------------------------------------------------------------
# get_all / get_most_cited / get_most_read / get_most_active_first_authors / get_all_authors
# ---------------------------------------------------------------------------

def test_get_all_delegates_to_query(db, monkeypatch):
    monkeypatch.setattr(db, 'query', MagicMock(return_value=['article1']))

    result = db.get_all(mission='keck')

    assert result == ['article1']
    db.query.assert_called_once_with(mission='keck')


def test_get_most_cited_orders_by_citation_count_desc(db, monkeypatch):
    articles = [
        {'bibcode': 'A', 'citation_count': 5},
        {'bibcode': 'B', 'citation_count': None},
        {'bibcode': 'C', 'citation_count': 10},
    ]
    monkeypatch.setattr(db, 'query', MagicMock(return_value=articles))

    top = db.get_most_cited(top=2)

    assert [a['bibcode'] for a in top] == ['C', 'A']


def test_get_most_read_orders_by_read_count_desc(db, monkeypatch):
    articles = [
        {'bibcode': 'A', 'read_count': 5},
        {'bibcode': 'B', 'read_count': 20},
        {'bibcode': 'C', 'read_count': 1},
    ]
    monkeypatch.setattr(db, 'query', MagicMock(return_value=articles))

    top = db.get_most_read(top=2)

    assert [a['bibcode'] for a in top] == ['B', 'A']


def test_get_most_active_first_authors_filters_by_min_papers(db, monkeypatch):
    articles = (
        [{'first_author_norm': 'Smith, J.'}] * 3
        + [{'first_author_norm': 'Doe, A.'}] * 1
    )
    monkeypatch.setattr(db, 'query', MagicMock(return_value=articles))

    result = dict(db.get_most_active_first_authors(min_papers=2))

    assert result == {'Smith, J.': 3}


def test_get_all_authors_counts_co_authors(db, monkeypatch):
    articles = [
        {'author_norm': ['Smith, J.', 'Doe, A.']},
        {'author_norm': ['Smith, J.']},
    ]
    monkeypatch.setattr(db, 'query', MagicMock(return_value=articles))

    names, counts = db.get_all_authors(top=5)

    name_to_count = dict(zip(names, counts))
    assert name_to_count['Smith, J.'] == 2
    assert name_to_count['Doe, A.'] == 1


# ---------------------------------------------------------------------------
# get_affiliation_counts
# ---------------------------------------------------------------------------

def test_get_affiliation_counts_first_author_and_top3(db, monkeypatch):
    monkeypatch.setattr(db, 'get_articles_by_mission_years', MagicMock(return_value=[
        {'year': 2020, 'aff': ['Keck Observatory', 'NASA Ames', 'Somewhere Else']},
    ]))

    counts = db.get_affiliation_counts(2020, 2020, 'keck')

    assert counts['first author keck'][2020] == 1
    assert counts['top3 authors keck'][2020] == 0


def test_get_affiliation_counts_top3_all_same_type(db, monkeypatch):
    monkeypatch.setattr(db, 'get_articles_by_mission_years', MagicMock(return_value=[
        {'year': 2020, 'aff': ['Keck A', 'Keck B', 'Keck C']},
    ]))

    counts = db.get_affiliation_counts(2020, 2020, 'keck')

    assert counts['top3 authors keck'][2020] == 1


# ---------------------------------------------------------------------------
# get_annual_publication_count / get_annual_publication_count_cumulative
# ---------------------------------------------------------------------------

def test_get_annual_publication_count_delegates(db, monkeypatch):
    mock_fn = MagicMock(return_value={2010: 0, 2011: 5})
    monkeypatch.setattr(db, 'get_articles_by_years_instrument', mock_fn)

    result = db.get_annual_publication_count(year_begin=2010, year_end=2011, instrument='HIRES')

    assert result == {2010: 0, 2011: 5}
    mock_fn.assert_called_once_with(2010, 2011, 'HIRES')


def test_get_annual_publication_count_cumulative_sums_per_year(db, monkeypatch):
    monkeypatch.setattr(db, 'get_count_cumulative', MagicMock(side_effect=lambda y: int(y) - 2008))

    result = db.get_annual_publication_count_cumulative(year_begin=2009, year_end=2011)

    assert result == {2009: 1, 2010: 2, 2011: 3}


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

def test_update_skips_articles_without_abstract_or_matching_bibcode_patterns(db, monkeypatch):
    monkeypatch.setattr(db, 'query_ads', MagicMock(return_value={'response': {'docs': [
        {'bibcode': '2020ApJ...1A'},  # no abstract -> skipped
        {'bibcode': '2020A&A..prop..1B', 'abstract': 'x'},  # .prop. -> skipped
        {'bibcode': '2020cosp..1234C', 'abstract': 'x'},  # cosp.. -> skipped
        {'bibcode': '2020ApJ.tmp.1D', 'abstract': 'x'},  # .tmp -> skipped
        {'bibcode': '2020ApJ...2E', 'abstract': 'A real abstract'},  # kept
    ]}}))
    monkeypatch.setattr(db, 'add_article', MagicMock(return_value=1))

    success, num_added = db.update(month='2020-05')

    assert success is True
    assert num_added == 1
    db.add_article.assert_called_once()
    called_article = db.add_article.call_args[0][0]
    assert called_article['bibcode'] == '2020ApJ...2E'
    db.query_ads.assert_called_once_with(db.config['ads_queries'][0]['query'], '2020-05')


def test_update_defaults_to_current_month(db, monkeypatch):
    monkeypatch.setattr(db, 'query_ads', MagicMock(return_value={'response': {'docs': []}}))

    db.update()

    args = db.query_ads.call_args[0]
    assert len(args) == 2
    import re as _re
    assert _re.match(r'^\d{4}-\d{2}$', args[1])


# ---------------------------------------------------------------------------
# open_pdf
# ---------------------------------------------------------------------------

def test_open_pdf_opens_browser_when_file_exists(db, monkeypatch):
    monkeypatch.setattr(kpub_module, 'get_pdf_file', MagicMock(return_value='/tmp/fake.pdf'))
    monkeypatch.setattr(kpub_module.os.path, 'isfile', MagicMock(return_value=True))
    monkeypatch.setattr(kpub_module.webbrowser, 'open', MagicMock())

    db.open_pdf('2020ApJ...1A')

    kpub_module.webbrowser.open.assert_called_once()
    assert 'fake.pdf' in kpub_module.webbrowser.open.call_args[0][0]


def test_open_pdf_does_nothing_when_file_missing(db, monkeypatch):
    monkeypatch.setattr(kpub_module, 'get_pdf_file', MagicMock(return_value=False))
    monkeypatch.setattr(kpub_module.os.path, 'isfile', MagicMock(return_value=False))
    monkeypatch.setattr(kpub_module.webbrowser, 'open', MagicMock())

    db.open_pdf('2020ApJ...1A')

    kpub_module.webbrowser.open.assert_not_called()


# ---------------------------------------------------------------------------
# query_ads
# ---------------------------------------------------------------------------

def test_query_ads_builds_expected_url_and_returns_data(db, monkeypatch):
    mock_request = MagicMock(return_value={'response': {'docs': []}})
    monkeypatch.setattr(kpub_module, 'request_ads_api', mock_request)

    result = db.query_ads('ack:"keck observatory"', pubdate='2020-05')

    assert result == {'response': {'docs': []}}
    called_url, called_key = mock_request.call_args[0]
    assert called_key == 'FAKE-ADS-API-KEY'
    assert 'ack:%22keck+observatory%22' in called_url
    assert 'pubdate:2020-05' in called_url
