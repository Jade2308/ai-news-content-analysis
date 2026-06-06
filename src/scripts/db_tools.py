#!/usr/bin/env python3
"""Unified database utility commands."""

from __future__ import annotations

import argparse
import os
import sys

# Ensure project root (parent of `src`) is on sys.path.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.config import DB_PATH
from src.workflows import (
    check_database,
    get_articles,
    get_latest_articles,
    print_database_stats,
    search_articles,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Database tools for article store.")
    parser.add_argument("--db-path", default=DB_PATH, help="Path to SQLite DB.")

    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("check", help="Check DB health and key counts.")
    sub.add_parser("stats", help="Print aggregate source/category statistics.")

    latest = sub.add_parser("latest", help="Print latest articles.")
    latest.add_argument("--limit", type=int, default=5)

    search = sub.add_parser("search", help="Search by keyword.")
    search.add_argument("keyword")
    search.add_argument("--limit", type=int, default=10)

    list_parser = sub.add_parser("list", help="List articles with filters.")
    list_parser.add_argument("--category", default=None)
    list_parser.add_argument("--source", default=None)
    list_parser.add_argument("--limit", type=int, default=10)

    args = parser.parse_args()

    # Keep legacy behavior of query_articles.py when no subcommand is passed.
    if args.cmd is None:
        print_database_stats(db_path=args.db_path)
        get_latest_articles(limit=5, db_path=args.db_path)
        return

    if args.cmd == "check":
        check_database(db_path=args.db_path)
    elif args.cmd == "stats":
        print_database_stats(db_path=args.db_path)
    elif args.cmd == "latest":
        get_latest_articles(limit=args.limit, db_path=args.db_path)
    elif args.cmd == "search":
        search_articles(keyword=args.keyword, limit=args.limit, db_path=args.db_path)
    elif args.cmd == "list":
        get_articles(
            category=args.category,
            source=args.source,
            limit=args.limit,
            db_path=args.db_path,
        )


if __name__ == "__main__":
    main()
