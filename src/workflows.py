"""Shared workflows for crawl, labeling, and database inspection.

This module centralizes logic that was previously duplicated across
multiple scripts under ``src/scripts``.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import time
from typing import Optional

from src.config import DB_PATH
from src.crawlers.tuoitre_crawler import TuoitreCrawler
from src.crawlers.vietnamnet_crawler import VietnamNetCrawler
from src.crawlers.vnexpress_crawler import VNExpressCrawler
from src.database.schema import init_db
from src.scripts.pred_label import run_labeling

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "phobert_clickbait")
CRAWLERS = [
    (TuoitreCrawler, "tuoitre"),
    (VNExpressCrawler, "vnexpress"),
    (VietnamNetCrawler, "vietnamnet"),
]


def crawl_newspaper(
    crawler_class,
    newspaper_name: str,
    *,
    max_articles: Optional[int] = None,
    stop_on_duplicate: bool = False,
    category_delay_seconds: int = 3,
) -> int:
    """Crawl all categories for one newspaper."""
    logger.info("\n%s", "=" * 70)
    logger.info("CRAWLING %s", newspaper_name.upper())
    logger.info("%s", "=" * 70)

    crawler = crawler_class()
    total_articles = []

    categories = list(crawler.category_urls.keys())
    logger.info("Found %s categories: %s", len(categories), ", ".join(categories))

    for i, category_slug in enumerate(categories, 1):
        logger.info("\n[%s/%s] Category: %s", i, len(categories), category_slug)
        try:
            crawler.category = category_slug
            run_kwargs = {}
            if max_articles is not None:
                run_kwargs["max_articles"] = max_articles
                run_kwargs["stop_on_duplicate"] = stop_on_duplicate

            articles = crawler.run(**run_kwargs)
            if articles:
                total_articles.extend(articles)
                logger.info("Crawled %s articles from %s", len(articles), category_slug)
            else:
                logger.info("No new articles in %s", category_slug)

            time.sleep(category_delay_seconds)
        except Exception as exc:  # noqa: BLE001
            logger.error("Error crawling %s: %s", category_slug, exc)
            continue

    if total_articles:
        logger.info("\n%s", "=" * 70)
        logger.info(
            "Saving %s articles from %s to database...",
            len(total_articles),
            newspaper_name,
        )
        saved = crawler.save_to_database(total_articles)
        logger.info("Saved %s articles from %s", saved, newspaper_name)
    else:
        logger.info("No articles to save from %s", newspaper_name)

    return len(total_articles)


def run_crawl(
    mode: str = "full",
    *,
    max_articles: int = 10,
    stop_on_duplicate: bool = True,
    run_label_after: bool = True,
    model_path: Optional[str] = None,
    model_version: str = "phobert_v1.0",
    batch_size: int = 32,
) -> tuple[dict[str, int], int]:
    """Run crawl pipeline in ``full`` or ``hourly`` mode."""
    if mode not in {"full", "hourly"}:
        raise ValueError("mode must be 'full' or 'hourly'")

    logger.info("%s", "=" * 70)
    logger.info("STARTING %s CRAWL", mode.upper())
    logger.info("%s", "=" * 70)

    logger.info("\nInitializing database...")
    init_db()

    total_all = 0
    results: dict[str, int] = {}

    for crawler_class, newspaper_name in CRAWLERS:
        try:
            if mode == "hourly":
                count = crawl_newspaper(
                    crawler_class,
                    newspaper_name,
                    max_articles=max_articles,
                    stop_on_duplicate=stop_on_duplicate,
                    category_delay_seconds=1,
                )
                time.sleep(2)
            else:
                count = crawl_newspaper(
                    crawler_class,
                    newspaper_name,
                    max_articles=None,
                    stop_on_duplicate=False,
                    category_delay_seconds=3,
                )
                time.sleep(5)
            results[newspaper_name] = count
            total_all += count
        except Exception as exc:  # noqa: BLE001
            logger.error("Error crawling %s: %s", newspaper_name, exc, exc_info=True)
            results[newspaper_name] = 0

    logger.info("\n%s", "=" * 70)
    logger.info("%s CRAWL SUMMARY", mode.upper())
    logger.info("%s", "=" * 70)
    for newspaper, count in results.items():
        label = "new articles" if mode == "hourly" else "articles"
        logger.info("%-15s : %5s %s", newspaper, count, label)
    logger.info("%s", "-" * 70)
    logger.info("%-15s : %5s %s", "TOTAL", total_all, "new articles" if mode == "hourly" else "articles")
    logger.info("%s", "=" * 70)

    if run_label_after:
        if mode == "hourly" and total_all == 0:
            logger.info("No new articles found. Skipping AI predictions.")
        else:
            logger.info("\nStarting automatic labeling after crawl...")
            run_labeling(
                model_path=model_path or DEFAULT_MODEL_PATH,
                model_version=model_version,
                batch_size=batch_size,
                show_samples=False,
            )

    return results, total_all


def check_database(db_path: str = DB_PATH) -> None:
    """Print database status and basic article statistics."""
    print(f"\n{'=' * 70}")
    print("DATABASE CHECK")
    print(f"{'=' * 70}")
    print(f"\nDatabase path: {db_path}")

    if os.path.exists(db_path):
        size = os.path.getsize(db_path) / (1024 * 1024)
        print(f"OK Database file exists ({size:.2f} MB)")
    else:
        print("ERROR Database file does NOT exist")
        print("Run: python main.py crawl-all")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='articles'
            """
        )
        if cursor.fetchone():
            print("OK Table 'articles' exists")
        else:
            print("ERROR Table 'articles' NOT found")
            conn.close()
            return

        cursor.execute("SELECT COUNT(*) FROM articles")
        total = cursor.fetchone()[0]
        print(f"OK Total articles: {total}")

        if total == 0:
            print("\nWARN Database is empty. Run: python main.py crawl-all")
            conn.close()
            return

        cursor.execute(
            """
            SELECT source, COUNT(*) as count
            FROM articles
            GROUP BY source
            """
        )
        sources = cursor.fetchall()
        print("\nArticles by source:")
        for source, count in sources:
            print(f"  - {source:<20}: {count:>5}")

        cursor.execute(
            """
            SELECT category, COUNT(*) as count
            FROM articles
            GROUP BY category
            ORDER BY count DESC
            LIMIT 10
            """
        )
        categories = cursor.fetchall()
        print("\nTop 10 categories:")
        for category, count in categories:
            print(f"  - {category:<30}: {count:>5}")

        cursor.execute(
            """
            SELECT title, source, published_at, crawled_at
            FROM articles
            ORDER BY crawled_at DESC
            LIMIT 3
            """
        )
        latest = cursor.fetchall()
        print("\nLatest 3 articles:")
        for i, (title, source, pub, crawl) in enumerate(latest, 1):
            print(f"  [{i}] {title[:60]}...")
            print(f"      Source: {source}, Published: {pub}, Crawled: {crawl}")

        conn.close()
        print("\nOK Database is in good condition.")
    except Exception as exc:  # noqa: BLE001
        print(f"\nERROR Error checking database: {exc}")


def print_database_stats(db_path: str = DB_PATH) -> None:
    """Print aggregate article statistics."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM articles")
        total = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT source, COUNT(*) as count
            FROM articles
            GROUP BY source
            """
        )
        by_source = cursor.fetchall()

        cursor.execute(
            """
            SELECT category, COUNT(*) as count
            FROM articles
            GROUP BY category
            ORDER BY count DESC
            """
        )
        by_category = cursor.fetchall()

        print("\n" + "=" * 70)
        print("DATABASE STATISTICS")
        print("=" * 70)
        print(f"\nTotal articles: {total}")

        print(f"\n{'Source':<20} {'Count':>10}")
        print("-" * 30)
        for source, count in by_source:
            print(f"{source:<20} {count:>10}")

        print(f"\n{'Category':<30} {'Count':>10}")
        print("-" * 40)
        for category, count in by_category:
            print(f"{category:<30} {count:>10}")

        conn.close()
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}")


def get_articles(
    *,
    category: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 10,
    db_path: str = DB_PATH,
) -> None:
    """Print article list with optional filters."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM articles WHERE 1=1"
        params = []
        if category:
            query += " AND category = ?"
            params.append(category)
        if source:
            query += " AND source = ?"
            params.append(source)
        query += " ORDER BY published_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        articles = cursor.fetchall()

        print(f"\n{'=' * 100}")
        print(f"ARTICLES (limit: {limit})")
        if category:
            print(f"Category: {category}")
        if source:
            print(f"Source: {source}")
        print(f"{'=' * 100}")

        for i, article in enumerate(articles, 1):
            print(f"\n[{i}] {article['source']} - {article['category']}")
            print(f"Title: {article['title'][:80]}")
            print(f"Published: {article['published_at']}")
            print(f"Author: {article['author'] or 'N/A'}")
            print(f"Tags: {article['tags'] or 'N/A'}")
            print(f"URL: {article['url'][:60]}...")

        conn.close()
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}")


def get_latest_articles(limit: int = 5, db_path: str = DB_PATH) -> None:
    """Print latest crawled articles."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM articles
            ORDER BY published_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        articles = cursor.fetchall()

        print(f"\n{'=' * 100}")
        print("LATEST ARTICLES")
        print(f"{'=' * 100}")

        for i, article in enumerate(articles, 1):
            print(f"\n[{i}] {article['published_at']}")
            print(f"Source: {article['source']} | Category: {article['category']}")
            print(f"Title: {article['title'][:90]}")
            print(f"Content preview: {article['content_text'][:100]}...")

        conn.close()
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}")


def search_articles(keyword: str, limit: int = 10, db_path: str = DB_PATH) -> None:
    """Search articles by keyword in title/content/summary."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        search_term = f"%{keyword}%"
        cursor.execute(
            """
            SELECT * FROM articles
            WHERE title LIKE ? OR content_text LIKE ? OR summary LIKE ?
            ORDER BY published_at DESC
            LIMIT ?
            """,
            (search_term, search_term, search_term, limit),
        )
        articles = cursor.fetchall()

        print(f"\n{'=' * 100}")
        print(f"SEARCH RESULTS FOR: '{keyword}' ({len(articles)} found)")
        print(f"{'=' * 100}")

        for i, article in enumerate(articles, 1):
            print(f"\n[{i}] {article['source']} - {article['category']}")
            print(f"Title: {article['title'][:80]}")
            print(f"Published: {article['published_at']}")
            print(f"Match: {article['content_text'][:100]}...")

        conn.close()
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}")
