#!/usr/bin/env python3
"""Topic detection from recent articles with optional multi-timeframe mode."""

from __future__ import annotations

import argparse
import logging
import os
import sys

import requests
from dotenv import load_dotenv

# Ensure project root (parent of `src`) is on sys.path.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

DEFAULT_TIMEFRAMES_CONFIG = {
    1: 3,
    6: 5,
    12: 8,
    24: 10,
    168: 20,
}


def generate_topic_name_with_gemma(keywords, titles, api_key):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash-lite:generateContent?key={api_key}"
    )
    prompt = (
        "Bạn là một biên tập viên báo chí thực hiện đặt tên chủ đề ngắn gọn.\n"
        "Hãy đọc danh sách từ khóa và tiêu đề nhóm bài báo dưới đây và đặt ra một câu tiêu đề chỉnh chu, "
        "ngắn gọn (tối đa 10 từ) làm tên chủ đề đại diện.\n"
        "YÊU CẦU BẮT BUỘC: CHỈ ĐƯA RA KẾT QUẢ CUỐI CÙNG (CÂU TIÊU ĐỀ). KHÔNG ĐƯỢC GIẢI THÍCH, "
        "KHÔNG PHÂN TÍCH, KHÔNG CHỈ RA CÁC BƯỚC SUY NGHĨ, KHÔNG TRÌNH BÀY CÁC BƯỚC KHỞI TẠO, "
        "KHÔNG PHÁT SINH BẤT KỲ VĂN BẢN NÀO KHÁC.\n\n"
        f"Từ khóa: {', '.join(keywords)}\n"
        f"Tiêu đề nhóm bài:\n{'\n'.join([f'- {t}' for t in titles])}\n\n"
        "Tên chủ đề ngắn gọn (Chỉ trả về 1 câu duy nhất):"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        if resp.status_code != 200:
            logger.warning("Gemini API Error [%s]: %s", resp.status_code, resp.text)
            return None

        data = resp.json()
        if "candidates" in data and data["candidates"]:
            parts = data["candidates"][0]["content"]["parts"]
            answer_parts = [p["text"] for p in parts if not p.get("thought")]
            answer = "".join(answer_parts).strip()
            for prefix in ["Tên chủ đề ngắn gọn:", "Tên chủ đề:", "Tiêu đề:"]:
                if answer.lower().startswith(prefix.lower()):
                    answer = answer[len(prefix) :].strip()
            return answer.replace('"', "").replace("*", "")

        logger.warning("Unexpected Gemini response: %s", data)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Error calling Gemini API: %s", exc)
    return None


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

    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        logger.info("GEMINI_API_KEY found. Generating topic names with Gemini.")

    topics_to_save = []
    for i, ht in enumerate(hot_topics, 1):
        rep_docs = analyzer.topic_model.get_representative_docs(ht["topic_id"])
        topic_name = " | ".join(ht["keywords"][:3]).upper()
        titles_for_llm = [text.split(".", 1)[0] for text in rep_docs[:5]] if rep_docs else []

        if api_key and rep_docs:
            ai_name = generate_topic_name_with_gemma(ht["keywords"], titles_for_llm, api_key)
            if ai_name:
                topic_name = ai_name.replace('"', "").replace("*", "").strip()

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
