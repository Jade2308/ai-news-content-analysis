#!/usr/bin/env python3
"""
Crawl, clean, and store articles in SQLite.

Usage:
    python src/scripts/db_seed.py --source vnexpress --category kinh-doanh --limit 50
    python src/scripts/db_seed.py --source tuoitre --category thoi-su --limit 50
    python src/scripts/db_seed.py --source all --limit 100

Rate-limit notes:
- VNExpress: 1 second between article requests.
- Tuoi Tre: 0.5 seconds between article requests.
Respect each publisher's terms of service and avoid crawling too quickly.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys

# Ensure project root (parent of `src`) is on sys.path.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.config import DB_PATH
from src.crawlers.tuoitre_crawler import TuoitreCrawler
from src.crawlers.vietnamnet_crawler import VietnamNetCrawler
from src.crawlers.vnexpress_crawler import VNExpressCrawler
from src.database.db import insert_article
from src.database.schema import init_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s - %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger('seed_db')

_CRAWLER_MAP = {
    'vnexpress': VNExpressCrawler,
    'tuoitre': TuoitreCrawler,
    'vietnamnet': VietnamNetCrawler,
}


def _categories_for_source(source: str, category: str | None) -> list[str]:
    """Resolve categories to crawl for one source."""
    if category:
        return [category]

    crawler = _CRAWLER_MAP[source]()
    return list(crawler.category_urls.keys())


def seed(source: str, category: str | None, limit: int, db_path: str):
    CrawlerClass = _CRAWLER_MAP[source]
    categories = _categories_for_source(source, category)
    logger.info(f"[{source}] categories={categories}, limit(each)={limit}, db={db_path}")

    inserted = skipped_url = skipped_fp = 0

    for cat in categories:
        crawler = CrawlerClass(category=cat)
        articles = crawler.run()

        if limit and len(articles) > limit:
            articles = articles[:limit]

        cat_inserted = cat_skipped_url = cat_skipped_fp = 0
        for art in articles:
            if not art:
                continue
            result = insert_article(art, db_path=db_path)
            if result == 'inserted':
                inserted += 1
                cat_inserted += 1
            elif result == 'dup_url':
                skipped_url += 1
                cat_skipped_url += 1
            elif result == 'dup_fp':
                skipped_fp += 1
                cat_skipped_fp += 1

        logger.info(
            f"[{source}/{cat}] Done - inserted={cat_inserted}, "
            f"skip_url={cat_skipped_url}, skip_fp(content_dup)={cat_skipped_fp}"
        )

    logger.info(
        f"[{source}] Total - inserted={inserted}, "
        f"skip_url={skipped_url}, skip_fp(content_dup)={skipped_fp}"
    )
    return inserted, skipped_url, skipped_fp


def main():
    parser = argparse.ArgumentParser(
        description='Crawl articles and store them in SQLite.'
    )
    parser.add_argument(
        '--source',
        choices=['vnexpress', 'tuoitre', 'vietnamnet', 'all'],
        default='all',
        help='Source to crawl. Default: all.',
    )
    parser.add_argument(
        '--category',
        default=None,
        help='Category to crawl. If omitted, all configured categories for the source are crawled.',
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Maximum articles per source/category. Default: 50.',
    )
    parser.add_argument(
        '--db-path',
        default=DB_PATH,
        help=f'Database path. Default: {DB_PATH}',
    )
    args = parser.parse_args()

    init_db(db_path=args.db_path)

    sources = list(_CRAWLER_MAP.keys()) if args.source == 'all' else [args.source]

    total_inserted = 0
    for src in sources:
        ins, _, _ = seed(src, args.category, args.limit, args.db_path)
        total_inserted += ins

    logger.info(f"Total inserted across all sources: {total_inserted}")


if __name__ == '__main__':
    main()
