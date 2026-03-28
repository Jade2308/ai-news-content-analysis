import argparse
import logging
import sys
import os
from typing import Optional, Tuple, List, Dict, Type

# Support running as a package or a direct script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.settings import DB_PATH, SOURCES
from database.models import init_db
from database.engine import insert_article
from crawlers.base import BaseCrawler
from crawlers._vnexpress import VNExpressCrawler
from crawlers._tuoitre import TuoitreCrawler

logger = logging.getLogger('ingest')

_CRAWLER_MAP: Dict[str, Type[BaseCrawler]] = {
    'vnexpress': VNExpressCrawler,
    'tuoitre': TuoitreCrawler,
}

def resolve_categories(source: str, category: Optional[str]) -> List[str]:
    """Resolve which categories to crawl for a given source."""
    if category:
        return [category]
    return list(SOURCES[source]['categories'].keys())

def run_ingestion(source: str, category: Optional[str], limit: int, db_path: str = DB_PATH) -> Tuple[int, int, int]:
    """Execute crawl and store results for a single source."""
    if source not in _CRAWLER_MAP:
        logger.error(f"Unknown source: {source}")
        return 0, 0, 0

    CrawlerClass = _CRAWLER_MAP[source]
    categories = resolve_categories(source, category)
    
    total_inserted = total_skipped_url = total_skipped_fp = 0
    
    for cat in categories:
        logger.info(f"[{source}] Starting crawl for category: {cat}")
        try:
            crawler = CrawlerClass(category=cat)
            articles = crawler.run(limit=limit)

            cat_results = {'inserted': 0, 'dup_url': 0, 'dup_fp': 0, 'error': 0}
            for art in articles:
                if not art:
                    continue
                # insert_article now expects an Article object
                result = insert_article(art, db_path=db_path)
                cat_results[result] = cat_results.get(result, 0) + 1

            logger.info(
                f"[{source}/{cat}] Completed - {cat_results['inserted']} inserted, "
                f"{cat_results['dup_url']} skipped (URL), {cat_results['dup_fp']} skipped (FP)"
            )
            
            total_inserted += cat_results['inserted']
            total_skipped_url += cat_results['dup_url']
            total_skipped_fp += cat_results['dup_fp']
        except Exception as e:
            logger.error(f"[{source}/{cat}] Ingestion failed: {e}")

    return total_inserted, total_skipped_url, total_skipped_fp

def main():
    parser = argparse.ArgumentParser(description='AI News Crawler - Ingestion Tool')
    parser.add_argument('--source', choices=['vnexpress', 'tuoitre', 'all'], default='all', help='Source content to crawl')
    parser.add_argument('--category', default=None, help='Specific category to crawl (optional)')
    parser.add_argument('--limit', type=int, default=50, help='Max articles per category per source')
    parser.add_argument('--db-path', default=DB_PATH, help='SQLite database file path')
    
    args = parser.parse_args()

    # Ensure project-wide logging is configured if run as a script
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
        datefmt='%H:%M:%S',
    )

    # Ensure DB schema is initialized
    init_db(args.db_path)

    sources = ['vnexpress', 'tuoitre'] if args.source == 'all' else [args.source]
    
    overall_inserted = 0
    for src in sources:
        ins, _, _ = run_ingestion(src, args.category, args.limit, args.db_path)
        overall_inserted += ins

    logger.info(f"✨ Ingestion sequence finished. Total new articles: {overall_inserted}")

if __name__ == '__main__':
    main()
