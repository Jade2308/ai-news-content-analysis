#!/usr/bin/env python3
"""
scripts/db_clean.py
Dọn dẹp dữ liệu cũ trong database:
1. Giữ lại articles trong 14 ngày gần đây.
2. Giữ lại hot_topics trong 14 ngày gần đây.
3. Xóa các bản ghi trong topic_articles mồ côi.
"""

import sys
import os
import argparse
import logging

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.database.db import clean_old_data
from src.config import DB_PATH

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
        help="Number of days of data to keep (default: 14)"
    )
    parser.add_argument(
        '--db-path', 
        default=DB_PATH, 
        help=f"Path to SQLite database file (default: {DB_PATH})"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Bat dau don dep database: {args.db_path}")
    logger.info(f"Chi giu lai du lieu trong vong {args.days} ngay gan day...")
    
    try:
        deleted_articles, deleted_topics, deleted_topic_articles = clean_old_data(
            days=args.days,
            db_path=args.db_path
        )
        
        print("\n" + "="*50)
        print("HOAN THANH DON DEP DATABASE")
        print("="*50)
        print(f"So bai viet (articles) da xoa:   {deleted_articles}")
        print(f"So chu de hot (hot_topics) da xoa: {deleted_topics}")
        print(f"So lien ket (topic_articles) da xoa: {deleted_topic_articles}")
        print("="*50 + "\n")
        
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi khi dọn dẹp database: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
