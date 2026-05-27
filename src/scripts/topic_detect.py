#!/usr/bin/env python3
"""Topic detection from recent articles with optional multi-timeframe mode."""

from __future__ import annotations

import argparse
import logging
import os
import sys

# Ensure project root (parent of `src`) is on sys.path.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_TIMEFRAMES_CONFIG = {
    1: 3,
    6: 5,
    12: 8,
    24: 10,
    168: 20,
}


def build_local_topic_name(keywords: list[str], max_keywords: int = 3) -> str:
    """Build a concise local-only topic label from top keywords."""
    cleaned = [str(k).strip() for k in keywords if str(k).strip()]
    if not cleaned:
        return "GENERAL NEWS"
    return " | ".join(cleaned[:max_keywords]).upper()


def run_topic_detection(hours: int = 24, top_n: int = 10) -> bool:
    """Detect topics in one timeframe. Returns True if completed."""
    from src.core.topic_bertopic import TopicAnalyzer
    from src.database.db import get_articles_by_timerange, save_hot_topics

    logger.info("Fetching articles from the last %s hours...", hours)
    articles = get_articles_by_timerange(hours=hours)
    if not articles:
        logger.info("No articles found in the specified time frame.")
        return False

    logger.info("Found %s articles. Preparing data...", len(articles))
    docs = []
    article_mapping = []
    for article in articles:
        title = (article.get("title") or "").strip()
        summary = (article.get("summary") or "").strip()
        text = f"{title}. {summary}".strip()
        if text:
            docs.append(text)
            article_mapping.append(article)

    if len(docs) < 15:
        logger.warning(
            "Not enough documents for HDBSCAN clustering (found %s, usually needs >=15). "
            "Try increasing --hours.",
            len(docs),
        )
        return False

    logger.info("Initializing TopicAnalyzer (first run may download models)...")
    analyzer = TopicAnalyzer()
    logger.info("Running BERTopic extraction...")
    topics, _ = analyzer.extract_hot_topics(docs)
    hot_topics = analyzer.get_top_topics(top_n=top_n)

    print("\n" + "=" * 60)
    print(f"HOT TOPICS IN THE LAST {hours} HOURS")
    print("=" * 60)
    if not hot_topics:
        print("\nNo prominent topics found.")
        return False

    logger.info("Using local keyword-based topic names (no external API).")

    topics_to_save = []
    for i, ht in enumerate(hot_topics, 1):
        rep_docs = analyzer.topic_model.get_representative_docs(ht["topic_id"])
        topic_name = build_local_topic_name(ht["keywords"])

        article_ids = []
        for idx, topic_id in enumerate(topics):
            if topic_id == ht["topic_id"]:
                article_ids.append(article_mapping[idx]["article_id"])

        topics_to_save.append(
            {
                "topic_name": topic_name,
                "keywords": ", ".join(ht["keywords"]),
                "article_count": ht["count"],
                "article_ids": article_ids,
            }
        )

        print(f"\n[{i}] TOPIC: {topic_name} (ID: {ht['topic_id']} | COUNT: {ht['count']})")
        print(f"    KEYWORDS: {', '.join(ht['keywords'][:5])}")
        print("    SAMPLE ARTICLES:")
        if rep_docs:
            for rep_text in rep_docs[:5]:
                try:
                    idx = docs.index(rep_text)
                    title = article_mapping[idx].get("title")
                    source = article_mapping[idx].get("source")
                    print(f"      - {title} ({source})")
                except ValueError:
                    title = rep_text.split(".", 1)[0]
                    print(f"      - {title}")

    print("\n" + "=" * 60 + "\n")
    if topics_to_save:
        save_hot_topics(topics_to_save, hours)
    return True


def run_topic_detection_all_timeframes() -> None:
    """Run topic detection for predefined timeframes."""
    for tf, top_n in DEFAULT_TIMEFRAMES_CONFIG.items():
        logger.info(
            "Starting topic detection for timeframe=%s hours (top_n=%s)",
            tf,
            top_n,
        )
        try:
            run_topic_detection(hours=tf, top_n=top_n)
            logger.info("Completed timeframe=%s hours.", tf)
        except Exception as exc:  # noqa: BLE001
            logger.error("Error for timeframe=%s hours: %s", tf, exc)


def main():
    parser = argparse.ArgumentParser(
        description="Detect hot topics from recent news using BERTopic."
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Number of hours to look back for articles.",
    )
    parser.add_argument(
        "--top_n",
        type=int,
        default=10,
        help="Number of top topics to display.",
    )
    parser.add_argument(
        "--all-timeframes",
        action="store_true",
        help="Run predefined 1h/6h/12h/24h/168h topic detection.",
    )
    args = parser.parse_args()

    if args.all_timeframes:
        run_topic_detection_all_timeframes()
    else:
        run_topic_detection(hours=args.hours, top_n=args.top_n)


if __name__ == "__main__":
    main()
