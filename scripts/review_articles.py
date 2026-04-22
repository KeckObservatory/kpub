"""
One-off backfill for articles inserted from an external source that lack the
derived fields normally set by the ingestion pipeline.

Filters Mongo by {year, from_broad_query: true} and, for each matching article,
computes snippits from the local full-text file and derives instruments,
archive, affiliation, has_acknowledgement, reason. Only empty/missing fields
are written; existing non-empty values are left alone.

Full-text path comes from the KPUB_FULL_TEXT_DIR env var (set in .env).
Layout expected: {KPUB_FULL_TEXT_DIR}/{year}/{bibcode}.txt
"""

import argparse
import datetime
import logging
import os
import re
import sys

import yaml

from kpub.kpub import (
    PublicationDB,
    get_word_match_counts_from_text,
    get_word_match_counts_by_pdf,
)

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
log = logging.getLogger('review_articles')

PACKAGEDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LAST_MODIFIER = 'review_articles'


def load_env_file(path):
    """Minimal .env parser: KEY=VALUE lines, '#' comments, ignores blank lines."""
    if not os.path.isfile(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, val = line.partition('=')
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            os.environ.setdefault(key, val)


def is_empty(value):
    """Treat None, '', [], {} as missing."""
    if value is None:
        return True
    if isinstance(value, (str, list, dict)) and len(value) == 0:
        return True
    return False


def load_full_text(full_text_dir, year, bibcode):
    path = os.path.join(full_text_dir, str(year), f'{bibcode}.txt')
    if not os.path.isfile(path):
        return None
    with open(path, encoding='utf-8', errors='replace') as f:
        text = f.read()
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', ' ', text)
    return text


def build_review_fields(pubdb, article, snippits, missions):
    """Derive the same fields the ingestion pipeline sets from snippits."""
    instruments = [k for k in snippits.keys() if k not in missions]
    archive = pubdb.get_archive_acknowledgement(snippits)
    affiliation, has_ack, reason = pubdb.get_affiliation(snippits, article.get('mission', ''))
    return {
        'snippits': snippits,
        'instruments': instruments,
        'archive': archive,
        'affiliation': affiliation,
        'has_acknowledgement': has_ack,
        'reason': reason,
    }


def pick_missing(article, derived):
    """Return subset of derived to write: field is empty AND new value differs."""
    return {k: v for k, v in derived.items() if is_empty(article.get(k)) and article.get(k) != v}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--year', type=int, required=True, help='Year to review (e.g. 2025)')
    parser.add_argument('--from-broad-query', dest='from_broad_query',
                        action=argparse.BooleanOptionalAction, default=True,
                        help='Filter by from_broad_query=True (default: true)')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of records processed')
    parser.add_argument('--dry-run', action='store_true', help='Print changes without writing')
    parser.add_argument('--disable-ads-fallback', action='store_true',
                        help='Skip the ADS PDF fallback when local full text is missing')
    args = parser.parse_args()

    load_env_file(os.path.join(REPO_ROOT, '.env'))
    full_text_dir = os.environ.get('KPUB_FULL_TEXT_DIR')
    if not full_text_dir:
        log.error('KPUB_FULL_TEXT_DIR is not set (check .env)')
        sys.exit(1)

    config = yaml.load(open(f'{PACKAGEDIR}/config/config.live.yaml'), Loader=yaml.FullLoader)
    pubdb = PublicationDB(config)

    missions = config.get('missions', [])
    instruments_cfg = config.get('instruments', [])
    acknowledgement = config.get('acknowledgement', [])
    archive_cfg = config.get('archive', []) or []
    blacklist = config.get('blacklist', []) or []
    words = list(missions) + list(instruments_cfg) + list(acknowledgement) + list(archive_cfg)
    if not words:
        log.error('No words configured (missions/instruments/acknowledgement/archive all empty)')
        sys.exit(1)

    query = {'year': args.year}
    if args.from_broad_query:
        query['from_broad_query'] = True

    ads_api_key = config.get('ADS_API_KEY')

    cursor = pubdb.collection.find(query)
    if args.limit:
        cursor = cursor.limit(args.limit)

    scanned = updated = no_changes = 0
    local_used = pdf_used = pdf_failed = pdf_skipped = 0

    for article in cursor:
        scanned += 1
        bibcode = article.get('bibcode') or article.get('_id')

        text = load_full_text(full_text_dir, args.year, bibcode)
        if text is not None:
            snippits = get_word_match_counts_from_text(text, words, blacklist)
            local_used += 1
        elif args.disable_ads_fallback:
            pdf_skipped += 1
            log.info(f'[{bibcode}] no local text, ADS fallback disabled, skipping')
            continue
        else:
            log.info(f'[{bibcode}] no local text, trying PDF fallback')
            try:
                snippits = get_word_match_counts_by_pdf(bibcode, words, ads_api_key, blacklist)
                pdf_used += 1
            except Exception as err:
                pdf_failed += 1
                log.warning(f'[{bibcode}] PDF fallback failed: {err}')
                continue

        derived = build_review_fields(pubdb, article, snippits, missions)
        fields = pick_missing(article, derived)

        if not fields:
            no_changes += 1
            continue

        fields['last_modifier'] = LAST_MODIFIER
        fields['date_modified'] = datetime.datetime.now()

        if args.dry_run:
            preview = {k: (f'<{len(v)} keys>' if k == 'snippits' else v) for k, v in fields.items()}
            log.info(f'[{bibcode}] would set: {preview}')
        else:
            pubdb.collection.update_one({'_id': article['_id']}, {'$set': fields})
            log.info(f'[{bibcode}] updated fields: {sorted(fields.keys())}')
        updated += 1

    pdf_attempts = pdf_used + pdf_failed
    local_rate = (local_used / scanned * 100) if scanned else 0
    pdf_rate = (pdf_used / pdf_attempts * 100) if pdf_attempts else 0
    log.info('--- Summary ---')
    log.info(f'Scanned: {scanned}  Updated: {updated}  No-change: {no_changes}  Dry-run: {args.dry_run}')
    log.info(f'Local full-text: {local_used}/{scanned} ({local_rate:.1f}%)')
    log.info(f'PDF fallback:    {pdf_used}/{pdf_attempts} ({pdf_rate:.1f}%)  failed: {pdf_failed}  skipped: {pdf_skipped}')


if __name__ == '__main__':
    main()
