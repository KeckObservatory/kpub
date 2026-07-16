"""Unit tests for the module-level helper functions in kpub.py.

None of these hit the network or a real database; external calls
(requests, textract, readline) are mocked.
"""
import datetime
from unittest.mock import MagicMock, call

import pytest

import kpub as kpub_module
from kpub import (
    add_prompt_valmaps,
    get_citation_fields,
    get_pdf_file,
    get_pdf_text,
    get_word_match_counts_by_pdf,
    get_word_match_counts_by_query,
    get_word_match_counts_from_text,
    highlight_text,
    input_with_prefill,
    kpub_update_citations,
    prompt_grouping,
    request_ads_api,
    update_citations,
)


# ---------------------------------------------------------------------------
# highlight_text
# ---------------------------------------------------------------------------

def test_highlight_text_wraps_matches_with_color_codes():
    colors = {'KECK': 'GREEN'}
    result = highlight_text('The KECK Observatory', colors)
    assert kpub_module.HIGHLIGHTS['GREEN'] in result
    assert kpub_module.HIGHLIGHTS['END'] in result
    assert 'KECK' in result


def test_highlight_text_is_case_insensitive():
    colors = {'keck': 'RED'}
    result = highlight_text('KECK observatory', colors)
    assert kpub_module.HIGHLIGHTS['RED'] in result


def test_highlight_text_no_match_returns_original_text():
    colors = {'NIRSPEC': 'CYAN'}
    result = highlight_text('nothing relevant here', colors)
    assert result == 'nothing relevant here'


def test_highlight_text_coerces_non_string_input():
    colors = {'123': 'RED'}
    result = highlight_text(12345, colors)
    assert kpub_module.HIGHLIGHTS['RED'] in result
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# get_word_match_counts_from_text
# ---------------------------------------------------------------------------

def test_get_word_match_counts_from_text_counts_matches():
    text = "We used the HIRES spectrograph and later the HIRES data again."
    counts = get_word_match_counts_from_text(text, ['HIRES'])
    assert counts['HIRES']['count'] == 2
    assert len(counts['HIRES']['snippets']) == 2


def test_get_word_match_counts_from_text_excludes_words_with_zero_matches():
    text = "Nothing relevant is mentioned here."
    counts = get_word_match_counts_from_text(text, ['HIRES', 'LRIS'])
    assert counts == {}


def test_get_word_match_counts_from_text_respects_blacklist():
    # "-ESING" contains "-ESI" so it would match the ESI instrument via the
    # '-' separator; the blacklist should suppress that specific snippet.
    text = "This is not about ESI, it's about proc-ESING results."
    counts = get_word_match_counts_from_text(text, ['ESI'], blacklist=['ESING'])
    # The genuine ", ESI" match should still be counted, but not the ESING one.
    assert counts['ESI']['count'] == 1


def test_get_word_match_counts_from_text_matches_multiple_separators():
    text = "keck/HIRES keck-HIRES (HIRES keck:HIRES"
    counts = get_word_match_counts_from_text(text, ['HIRES'])
    assert counts['HIRES']['count'] == 4


def test_get_word_match_counts_from_text_match_near_start_gives_correct_snippet():
    # Regression test: match.start() - 80 (and - 5) used to go negative for
    # matches near the start of the text, which Python silently wraps around
    # to slice from the end of the string instead of clamping to index 0.
    text = "Observations with (ESI) confirmed the result." + ("x" * 200)
    counts = get_word_match_counts_from_text(text, ['ESI'])
    assert counts['ESI']['count'] == 1
    snippet = counts['ESI']['snippets'][0]
    # A correctly-clamped snippet starts at index 0 of the text; the old,
    # unclamped negative-index slice instead started ~80 chars before the
    # end of the string, deep inside the trailing run of "x"s.
    assert snippet.startswith("Observations with (ESI)")


# ---------------------------------------------------------------------------
# request_ads_api
# ---------------------------------------------------------------------------

def _fake_response(json_data=None, status_ok=True, remaining='100', reset=None, content=b''):
    resp = MagicMock()
    resp.headers = {'X-RateLimit-Remaining': remaining}
    if reset is not None:
        resp.headers['X-RateLimit-Reset'] = reset
    resp.content = content
    if status_ok:
        resp.raise_for_status.return_value = None
    else:
        import requests
        resp.raise_for_status.side_effect = requests.HTTPError('boom')
    resp.json.return_value = json_data if json_data is not None else {}
    return resp


def test_request_ads_api_returns_json_by_default(monkeypatch):
    resp = _fake_response(json_data={'response': {'docs': []}})
    mock_get = MagicMock(return_value=resp)
    monkeypatch.setattr(kpub_module.requests, 'get', mock_get)

    data = request_ads_api('http://example.test/query', 'MYKEY')

    assert data == {'response': {'docs': []}}
    called_headers = mock_get.call_args.kwargs['headers']
    assert called_headers['Authorization'] == 'Bearer MYKEY'
    assert 'Mozilla' in called_headers['User-Agent']


def test_request_ads_api_returns_response_object_when_requested(monkeypatch):
    resp = _fake_response(json_data={'ok': True})
    monkeypatch.setattr(kpub_module.requests, 'get', MagicMock(return_value=resp))

    result = request_ads_api('http://example.test/query', 'MYKEY', returnResp=True)

    assert result is resp
    resp.json.assert_not_called()


def test_request_ads_api_warns_on_low_rate_limit(monkeypatch, caplog):
    epoch = int(datetime.datetime.now().timestamp())
    resp = _fake_response(json_data={}, remaining='5', reset=str(epoch))
    monkeypatch.setattr(kpub_module.requests, 'get', MagicMock(return_value=resp))

    with caplog.at_level('WARNING', logger='KPUB'):
        request_ads_api('http://example.test/query', 'MYKEY')

    assert any('Rate limit remaining' in rec.message for rec in caplog.records)


def test_request_ads_api_raises_on_http_error(monkeypatch):
    resp = _fake_response(json_data={}, status_ok=False)
    monkeypatch.setattr(kpub_module.requests, 'get', MagicMock(return_value=resp))

    import requests
    with pytest.raises(requests.HTTPError):
        request_ads_api('http://example.test/query', 'MYKEY')


# ---------------------------------------------------------------------------
# get_word_match_counts_by_query
# ---------------------------------------------------------------------------

def test_get_word_match_counts_by_query_concatenates_fields(monkeypatch):
    fake_data = {
        'response': {
            'docs': [{
                'title': ['A great HIRES paper'],
                'abstract': 'We observed with HIRES.',
                'ack': ['Thanks to Keck'],
                'body': 'The HIRES spectrograph was used throughout the body.',
            }]
        }
    }
    monkeypatch.setattr(kpub_module, 'request_ads_api', MagicMock(return_value=fake_data))

    counts, fulltext = get_word_match_counts_by_query('2020ApJ...1A', ['HIRES'], 'KEY')

    assert 'A great HIRES paper' in fulltext
    assert 'We observed with HIRES.' in fulltext
    assert 'Thanks to Keck' in fulltext
    assert 'The HIRES spectrograph' in fulltext
    assert counts['HIRES']['count'] >= 3


def test_get_word_match_counts_by_query_no_docs_returns_empty(monkeypatch):
    monkeypatch.setattr(kpub_module, 'request_ads_api',
                         MagicMock(return_value={'response': {'docs': []}}))

    counts, fulltext = get_word_match_counts_by_query('2020ApJ...1A', ['HIRES'], 'KEY')

    assert counts == {}
    assert fulltext == ''


def test_get_word_match_counts_by_query_escapes_ampersand_bibcode(monkeypatch):
    mock_request = MagicMock(return_value={'response': {'docs': []}})
    monkeypatch.setattr(kpub_module, 'request_ads_api', mock_request)

    get_word_match_counts_by_query('2020A&A...1A', [], 'KEY')

    called_url = mock_request.call_args[0][0]
    assert '2020A%26A...1A' in called_url
    assert '&' not in called_url.split('q=bibcode:%22')[1].split('%22')[0]


# ---------------------------------------------------------------------------
# get_word_match_counts_by_pdf / get_pdf_text
# ---------------------------------------------------------------------------

def test_get_word_match_counts_by_pdf_cleans_and_counts_text(monkeypatch):
    monkeypatch.setattr(kpub_module, 'get_pdf_file', MagicMock(return_value='/tmp/fake.pdf'))
    monkeypatch.setattr(kpub_module, 'get_pdf_text',
                         MagicMock(return_value="Line one HIRES\nLine two\r\x00 HIRES again"))

    counts, text = get_word_match_counts_by_pdf('2020ApJ...1A', ['HIRES'], 'KEY')

    assert '\n' not in text
    assert '\r' not in text
    assert counts['HIRES']['count'] == 2


def test_get_word_match_counts_by_pdf_raises_when_no_file(monkeypatch):
    monkeypatch.setattr(kpub_module, 'get_pdf_file', MagicMock(return_value=False))

    with pytest.raises(Exception, match='Could not download fulltext'):
        get_word_match_counts_by_pdf('2020ApJ...1A', ['HIRES'], 'KEY')


def test_get_word_match_counts_by_pdf_raises_when_no_text_extracted(monkeypatch):
    # Regression test: a downloaded file that yields no extractable text (e.g. a
    # bot-block/CAPTCHA page served instead of the real article) used to be
    # silently treated as a successful "zero matches" result instead of a
    # failure, which meant find_all_snippets never fell back to the
    # ADS-metadata query method.
    monkeypatch.setattr(kpub_module, 'get_pdf_file', MagicMock(return_value='/tmp/fake.html'))
    monkeypatch.setattr(kpub_module, 'get_pdf_text', MagicMock(return_value=''))

    with pytest.raises(Exception, match='No text could be extracted'):
        get_word_match_counts_by_pdf('2020ApJ...1A', ['HIRES'], 'KEY')


def test_get_pdf_text_html_uses_textract_bs4_parser(monkeypatch):
    fake_textract = MagicMock()
    fake_textract.process.return_value = b'hello html text'
    monkeypatch.setattr(kpub_module, 'textract', fake_textract)

    text = get_pdf_text('/tmp/2020ApJ...1A.html')

    assert text == 'hello html text'
    fake_textract.process.assert_called_once_with('/tmp/2020ApJ...1A.html')


def test_get_pdf_text_pdf_falls_back_to_second_method(monkeypatch):
    fake_textract = MagicMock()
    fake_textract.process.side_effect = [Exception('pdftotext failed'), b'extracted via pdfminer']
    monkeypatch.setattr(kpub_module, 'textract', fake_textract)

    text = get_pdf_text('/tmp/2020ApJ...1A.pdf')

    assert text == 'extracted via pdfminer'
    assert fake_textract.process.call_count == 2


def test_get_pdf_text_raises_when_all_methods_fail(monkeypatch):
    fake_textract = MagicMock()
    fake_textract.process.side_effect = Exception('boom')
    monkeypatch.setattr(kpub_module, 'textract', fake_textract)

    with pytest.raises(Exception, match='Could not extract PDF text'):
        get_pdf_text('/tmp/2020ApJ...1A.pdf')


# ---------------------------------------------------------------------------
# get_pdf_file
# ---------------------------------------------------------------------------

def test_get_pdf_file_succeeds_on_first_esource(monkeypatch):
    monkeypatch.setattr(kpub_module.os.path, 'isfile', MagicMock(return_value=False))
    resp = MagicMock(status_code=200, content=b'x' * 2000, headers={'Content-Type': 'application/pdf'})
    monkeypatch.setattr(kpub_module, 'request_ads_api', MagicMock(return_value=resp))
    m_open = MagicMock()
    monkeypatch.setattr('builtins.open', m_open)

    outfile = get_pdf_file('2020ApJ...1A', 'KEY')

    assert outfile == '/tmp/2020ApJ...1A.pdf'
    m_open.assert_called_once_with('/tmp/2020ApJ...1A.pdf', 'wb')


def test_get_pdf_file_uses_cached_file_if_present(monkeypatch):
    monkeypatch.setattr(kpub_module.os.path, 'isfile', MagicMock(return_value=True))
    mock_request = MagicMock()
    monkeypatch.setattr(kpub_module, 'request_ads_api', mock_request)

    outfile = get_pdf_file('2020ApJ...1A', 'KEY')

    assert outfile == '/tmp/2020ApJ...1A.pdf'
    mock_request.assert_not_called()


def test_get_pdf_file_falls_back_through_esources(monkeypatch):
    monkeypatch.setattr(kpub_module.os.path, 'isfile', MagicMock(return_value=False))
    bad_resp = MagicMock(status_code=200, content=b'x' * 2000,
                          headers={'Content-Type': 'text/html'})  # wrong type for a *_PDF esource
    good_resp = MagicMock(status_code=200, content=b'x' * 2000,
                           headers={'Content-Type': 'text/html'})  # right type for EPRINT_HTML
    mock_request = MagicMock(side_effect=[Exception('network error'), bad_resp, good_resp])
    monkeypatch.setattr(kpub_module, 'request_ads_api', mock_request)
    monkeypatch.setattr('builtins.open', MagicMock())

    outfile = get_pdf_file('2020ApJ...1A', 'KEY')

    # 3rd esource in FULLTEXT_ESOURCES is EPRINT_HTML -> .html extension
    assert outfile == '/tmp/2020ApJ...1A.html'
    assert mock_request.call_count == 3


def test_get_pdf_file_returns_false_when_all_esources_fail(monkeypatch):
    monkeypatch.setattr(kpub_module.os.path, 'isfile', MagicMock(return_value=False))
    monkeypatch.setattr(kpub_module, 'request_ads_api', MagicMock(side_effect=Exception('nope')))

    outfile = get_pdf_file('2020ApJ...1A', 'KEY')

    assert outfile is False


def test_get_pdf_file_rejects_short_content(monkeypatch):
    monkeypatch.setattr(kpub_module.os.path, 'isfile', MagicMock(return_value=False))
    short_resp = MagicMock(status_code=200, content=b'tiny', headers={'Content-Type': 'application/pdf'})
    monkeypatch.setattr(kpub_module, 'request_ads_api', MagicMock(return_value=short_resp))

    outfile = get_pdf_file('2020ApJ...1A', 'KEY')

    assert outfile is False


# ---------------------------------------------------------------------------
# get_citation_fields / update_citations / kpub_update_citations
# ---------------------------------------------------------------------------

def test_get_citation_fields_returns_first_doc(monkeypatch):
    fake_data = {'response': {'docs': [{'citation_count': 42}]}}
    monkeypatch.setattr(kpub_module, 'request_ads_api', MagicMock(return_value=fake_data))

    fields = get_citation_fields('2020ApJ...1A', 'KEY')

    assert fields == {'citation_count': 42}


def test_get_citation_fields_returns_false_when_missing(monkeypatch):
    monkeypatch.setattr(kpub_module, 'request_ads_api',
                         MagicMock(return_value={'response': {'docs': []}}))

    assert get_citation_fields('2020ApJ...1A', 'KEY') is False


def test_update_citations_updates_only_keck_articles(monkeypatch, config):
    monkeypatch.setattr(kpub_module, 'yaml',
                         MagicMock(load=MagicMock(return_value=config), FullLoader=None))
    monkeypatch.setattr('builtins.open', MagicMock())

    fake_pubdb = MagicMock()
    fake_pubdb.query.return_value = [
        {'bibcode': '2020ApJ...1A', 'affiliation': 'keck'},
        {'bibcode': '2020ApJ...2B', 'affiliation': 'unrelated'},
    ]
    monkeypatch.setattr(kpub_module, 'PublicationDB', MagicMock(return_value=fake_pubdb))
    monkeypatch.setattr(kpub_module, 'get_citation_fields',
                         MagicMock(return_value={'citation_count': 7}))

    update_citations('2020')

    fake_pubdb.update_citation_fields.assert_called_once_with('2020ApJ...1A', {'citation_count': 7})


def test_update_citations_skips_when_citation_fields_missing(monkeypatch, config):
    monkeypatch.setattr(kpub_module, 'yaml',
                         MagicMock(load=MagicMock(return_value=config), FullLoader=None))
    monkeypatch.setattr('builtins.open', MagicMock())

    fake_pubdb = MagicMock()
    fake_pubdb.query.return_value = [{'bibcode': '2020ApJ...1A', 'affiliation': 'keck'}]
    monkeypatch.setattr(kpub_module, 'PublicationDB', MagicMock(return_value=fake_pubdb))
    monkeypatch.setattr(kpub_module, 'get_citation_fields', MagicMock(return_value=False))

    update_citations('2020')

    fake_pubdb.update_citation_fields.assert_not_called()


def test_kpub_update_citations_delegates_to_update_citations(monkeypatch):
    mock_update = MagicMock()
    monkeypatch.setattr(kpub_module, 'update_citations', mock_update)

    kpub_update_citations('2021')

    mock_update.assert_called_once_with('2021')


# ---------------------------------------------------------------------------
# prompt helpers
# ---------------------------------------------------------------------------

def test_add_prompt_valmaps_appends_1_indexed_keys():
    valmap = {'0': 'unrelated'}
    result = add_prompt_valmaps(dict(valmap), ['keck', 'other'])
    assert result == {'0': 'unrelated', '1': 'keck', '2': 'other'}


def test_prompt_grouping_returns_user_input(monkeypatch):
    monkeypatch.setattr('builtins.input', MagicMock(return_value='1'))
    result = prompt_grouping({'1': 'keck'}, 'Mission')
    assert result == '1'


def test_input_with_prefill_uses_readline_hook(monkeypatch):
    monkeypatch.setattr(kpub_module.readline, 'set_pre_input_hook', MagicMock())
    monkeypatch.setattr('builtins.input', MagicMock(return_value='typed value'))

    result = input_with_prefill('prompt> ', 'prefill text')

    assert result == 'typed value'
    assert kpub_module.readline.set_pre_input_hook.call_count == 2
