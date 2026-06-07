#!/usr/bin/env python3
"""
Clean old database data:
1. Keep articles from the last 14 days by default.
2. Keep hot topics from the last 14 days by default.
3. Remove orphaned topic_articles rows.
"""

import argparse
import logging
import os
import sys

# Ensure project root is in sys.path.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.config import DB_PATH
from src.database.db import clean_old_data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description="Clean old data from SQLite database.")
    parser.add_argument(
        '--days',
        type=int,
        default=14,
        help="Number of days of data to keep. Default: 14.",
    )
    parser.add_argument(
        '--db-path',
        default=DB_PATH,
        help=f"Path to SQLite database file. Default: {DB_PATH}",
    )

    args = parser.parse_args()

    logger.info(f"Starting database cleanup: {args.db_path}")
    logger.info(f"Keeping data from the last {args.days} days...")

    try:
        deleted_articles, deleted_topics, deleted_topic_articles = clean_old_data(
            days=args.days,
            db_path=args.db_path,
        )

        print("\n" + "=" * 50)
        print("DATABASE CLEANUP COMPLETED")
        print("=" * 50)
        print(f"Deleted articles:           {deleted_articles}")
        print(f"Deleted hot topics:         {deleted_topics}")
        print(f"Deleted topic/article links:{deleted_topic_articles}")
        print("=" * 50 + "\n")

    except Exception as e:
        logger.error(f"Database cleanup failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
