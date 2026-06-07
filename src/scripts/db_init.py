#!/usr/bin/env python3
"""
Initialize the SQLite database for the news-mining pipeline.

Usage:
    python src/scripts/db_init.py
    python src/scripts/db_init.py --db-path /path/to/custom.db
"""
import argparse
import os
import sys

# Ensure project root (parent of `src`) is on sys.path.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.config import DB_PATH
from src.database.schema import init_db


def main():
    parser = argparse.ArgumentParser(
        description='Initialize the SQLite database for news mining.'
    )
    parser.add_argument(
        '--db-path',
        default=DB_PATH,
        help=f'Path to the database file. Default: {DB_PATH}',
    )
    args = parser.parse_args()

    init_db(db_path=args.db_path)


if __name__ == '__main__':
    main()
