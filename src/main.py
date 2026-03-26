import argparse
import logging
import sys
import os
from typing import Optional

# Support running as a package or a direct script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.settings import DB_PATH
from database.models import init_db
from database.ingest import run_ingestion
from tools import check_vnexpress, check_tuoitre

def run_diagnostics():
    """Run scraper diagnostic tools to verify crawler health."""
    logging.info("🔍 Running crawler verification tests...")
    
    print("\n--- Checking VNExpress ---")
    check_vnexpress.run_check()
    
    print("\n--- Checking TuoiTre ---")
    check_tuoitre.run_check()
    print("\n")

def main():
    parser = argparse.ArgumentParser(
        description="AI News Content Analysis - Central CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: setup
    setup_parser = subparsers.add_parser("setup", help="Initialize the database schema")
    setup_parser.add_argument("--db-path", default=DB_PATH, help="Path to SQLite database file")

    # Command: ingest
    ingest_parser = subparsers.add_parser("ingest", help="Crawl and store news articles from sources")
    ingest_parser.add_argument("--source", choices=["vnexpress", "tuoitre", "all"], default="all", help="Source to crawl")
    ingest_parser.add_argument("--category", default=None, help="Specific category to crawl (optional)")
    ingest_parser.add_argument("--limit", type=int, default=50, help="Max articles per source category")
    ingest_parser.add_argument("--db-path", default=DB_PATH, help="Path to SQLite database file")

    # Command: check
    subparsers.add_parser("check", help="Run crawler diagnostic checks")

    args = parser.parse_args()

    # Configure root logging for the whole application
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
        datefmt='%H:%M:%S',
    )
    logger = logging.getLogger('main')

    if args.command == "setup":
        logger.info(f"🚀 Initializing database at {args.db_path}...")
        try:
            init_db(args.db_path)
            logger.info("✅ Database setup complete.")
        except Exception as e:
            logger.error(f"❌ Failed to setup database: {e}")
            sys.exit(1)

    elif args.command == "ingest":
        logger.info(f"📥 Starting ingestion sequence (source={args.source}, category={args.category}, limit={args.limit})")
        # Ensure database is initialized
        init_db(args.db_path)
        try:
            sources = ['vnexpress', 'tuoitre'] if args.source == 'all' else [args.source]
            total_new = 0
            for src in sources:
                ins, _, _ = run_ingestion(src, args.category, args.limit, args.db_path)
                total_new += ins
            logger.info(f"✨ Ingestion sequence finished. Total new articles: {total_new}")
        except Exception as e:
            logger.error(f"❌ Ingestion sequence failed: {e}")

    elif args.command == "check":
        run_diagnostics()

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
