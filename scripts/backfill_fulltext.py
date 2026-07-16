"""
Backfill the 'fulltext' collection for Keck-affiliation articles.

For each Keck article missing a real fulltext entry (or where the stored
fulltext is empty / no more than abstract-length), tries to (re-)download and
extract the fulltext via ADS's link_gateway (EPRINT_PDF/PUB_PDF/EPRINT_HTML/
PUB_HTML) or, failing that, an ADS metadata query. Only saves the result when
it's meaningfully longer than the article's abstract; otherwise leaves the
bibcode as missing/short so it can be retried later (e.g. once better access
to a given publisher becomes available). Safe to rerun.

Usage:
    python scripts/backfill_fulltext.py [--limit N] [--sample N] [--dry-run]
"""
import argparse
import collections
import logging
import os
import random
import sys

import yaml

PACKAGEDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, PACKAGEDIR)

from kpub import (
    PublicationDB,
    get_word_match_counts_by_pdf,
    get_word_match_counts_by_query,
)

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
log = logging.getLogger('backfill_fulltext')


def needs_fulltext(abstract, existing_fulltext):
    """A bibcode needs (re-)fetching if it has no fulltext doc, or the stored
    fulltext is empty, or no more than abstract-length (i.e. likely just a
    title+abstract restatement rather than real fulltext)."""
    if existing_fulltext is None:
        return True
    stripped = existing_fulltext.strip()
    if len(stripped) == 0:
        return True
    if len(stripped) <= len(abstract or '') + 300:
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit', type=int, default=None, help='Max number of articles to process')
    parser.add_argument('--sample', type=int, default=None, help='Randomly sample N articles instead of taking the first N')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for --sample')
    parser.add_argument('--dry-run', action='store_true', help='Do not write to the fulltext collection')
    args = parser.parse_args()

    config = yaml.load(open(f'{PACKAGEDIR}/config/config.live.yaml'), Loader=yaml.FullLoader)
    ads_api_key = config.get('ADS_API_KEY')

    db = PublicationDB(config, collection='articles')

    keck_articles = list(db.collection.find(
        {'affiliation': 'keck'}, {'bibcode': 1, 'abstract': 1, '_id': 0}))
    bibcodes = [a['bibcode'] for a in keck_articles]

    fulltext_collection = db.client['kpub']['fulltext']
    fulltext_docs = list(fulltext_collection.find(
        {'bibcode': {'$in': bibcodes}}, {'bibcode': 1, 'fulltext': 1, '_id': 0}))
    ft_map = {d['bibcode']: d.get('fulltext', '') for d in fulltext_docs}

    todo = []
    for a in keck_articles:
        bib = a['bibcode']
        abstract = a.get('abstract') or ''
        existing = ft_map.get(bib)
        if needs_fulltext(abstract, existing):
            todo.append((bib, abstract, existing))

    log.info(f"{len(todo)} articles need fulltext work (of {len(keck_articles)} keck articles)")

    year_counts_all = collections.Counter(bib[:4] for bib, _, _ in todo)
    log.info(f"todo by year: {dict(sorted(year_counts_all.items()))}")

    if args.sample:
        random.seed(args.seed)
        todo = random.sample(todo, min(args.sample, len(todo)))
        log.info(f"Randomly sampled {len(todo)} articles for this run (seed={args.seed})")
    elif args.limit:
        todo = todo[:args.limit]
        log.info(f"Limiting to first {len(todo)} articles for this run")

    stats = {'pdf_ok': 0, 'query_ok': 0, 'failed': 0, 'skipped_still_short': 0}
    year_stats = collections.defaultdict(collections.Counter)

    for idx, (bibcode, abstract, existing) in enumerate(todo):
        year = bibcode[:4]
        log.info(f"[{idx+1}/{len(todo)}] Processing {bibcode} "
                  f"(previously: {'missing' if existing is None else f'{len(existing.strip())} chars'})")
        fulltext = None
        source = None
        try:
            counts, fulltext = get_word_match_counts_by_pdf(bibcode, [], ads_api_key, [])
            source = 'pdf/html-download'
        except Exception as err:
            log.info(f"  download-based extraction failed: {err}. Trying ADS query fallback...")
            try:
                counts, fulltext = get_word_match_counts_by_query(bibcode, [], ads_api_key, [])
                source = 'ads-query'
            except Exception as err2:
                log.warning(f"  ADS query fallback also failed for {bibcode}: {err2}")
                fulltext = None

        if not fulltext or not fulltext.strip():
            log.warning(f"  No fulltext obtained for {bibcode}.")
            stats['failed'] += 1
            year_stats[year]['failed'] += 1
            continue

        if needs_fulltext(abstract, fulltext):
            log.warning(f"  New fulltext for {bibcode} is still short "
                        f"({len(fulltext.strip())} chars, source={source}); NOT saving, leaving as missing.")
            stats['skipped_still_short'] += 1
            year_stats[year]['skipped_still_short'] += 1
            continue

        if source == 'pdf/html-download':
            stats['pdf_ok'] += 1
            year_stats[year]['pdf_ok'] += 1
        else:
            stats['query_ok'] += 1
            year_stats[year]['query_ok'] += 1

        if args.dry_run:
            log.info(f"  [dry-run] would save {len(fulltext)} chars for {bibcode} (source={source})")
        else:
            db.save_fulltext(bibcode, fulltext)
            log.info(f"  Saved {len(fulltext)} chars for {bibcode} (source={source})")

    log.info(f"Done. stats={stats}")
    for year in sorted(year_stats):
        log.info(f"  {year}: {dict(year_stats[year])}")


if __name__ == '__main__':
    main()
