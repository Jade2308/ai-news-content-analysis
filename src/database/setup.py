#!/usr/bin/env python3
import argparse
import logging
import os
import sys

# Support running as a package or a direct script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.settings import DB_PATH
from database.models import init_db

def main():
    parser = argparse.ArgumentParser(
        description='Initialize the SQLite database schema for AI News Content Analysis.'
    )
    parser.add_argument(
        '--db-path',
        default=DB_PATH,
        help=f'Path to the SQLite database file (default: {DB_PATH})',
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
        datefmt='%H:%M:%S',
    )

    init_db(db_path=args.db_path)

if __name__ == '__main__':
    main()
