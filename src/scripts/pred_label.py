#!/usr/bin/env python3
"""
Predict labels for unlabeled articles and save the results to the database.
"""

import argparse
import logging
import os
import sqlite3
import sys

# Ensure project root (parent of `src`) is on sys.path.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.config import DB_PATH
from src.database.predictions import (
    add_batch_predictions,
    get_prediction_stats,
    get_sample_predictions,
    get_unpredicted_articles,
)
from src.database.schema import init_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_article_counts():
    """Return total and unlabeled article counts."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM articles')
    total_articles = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM articles WHERE predicted_label IS NULL')
    unlabeled_articles = cursor.fetchone()[0]

    conn.close()
    return total_articles, unlabeled_articles


def run_labeling(
    model_path: str = None,
    model_version: str = 'phobert_v1.0',
    batch_size: int = 32,
    show_samples: bool = False,
):
    """Run clickbait labeling for articles without predictions."""
    logger.info("=" * 70)
    logger.info("STARTING PREDICTION & LABELING")
    logger.info("=" * 70)

    if model_path is None:
        model_path = os.path.join(PROJECT_ROOT, 'models', 'phobert_clickbait')

    logger.info("Initializing database...")
    init_db()

    logger.info(f"Loading model from {model_path}...")
    try:
        from src.models.phobert_classifier import PhoBERTClickbaitClassifier
        classifier = PhoBERTClickbaitClassifier(model_name=model_path)
    except Exception as e:
        logger.error(f"Cannot load model: {e}")
        return

    logger.info("Fetching unpredicted articles...")
    articles = get_unpredicted_articles()

    if not articles:
        total_articles, unlabeled_articles = get_article_counts()

        if total_articles == 0:
            logger.warning("Database is empty: no crawled articles exist in the articles table.")
            logger.warning("Run: python src/scripts/crawl.py --mode full")
        else:
            logger.info("All articles already predicted!")
            logger.info(f"Total articles: {total_articles}")
            logger.info(f"Unlabeled articles: {unlabeled_articles}")

        if show_samples:
            show_sample_predictions(limit=10)
        return

    logger.info(f"Found {len(articles)} articles to predict")

    total_predicted = 0
    for i in range(0, len(articles), batch_size):
        batch = articles[i:i + batch_size]
        predictions = []

        for article in batch:
            article_id = article['article_id']
            title = article.get('title', '')
            content = article.get('content_text', '')

            text = f"{title} {content}".strip()

            if not text:
                logger.warning(f"Article {article_id} has no text, marking as error_no_text")
                predictions.append({
                    'article_id': article_id,
                    'predicted_label': 'error_no_text',
                    'prediction_score': 0.0,
                })
                continue

            try:
                label_val, score = classifier.predict(text)

                if isinstance(label_val, int) or str(label_val) in ['0', '1']:
                    label_str = 'clickbait' if int(label_val) == 1 else 'non-clickbait'
                else:
                    label_str = str(label_val)

                predictions.append({
                    'article_id': article_id,
                    'predicted_label': label_str,
                    'prediction_score': float(score),
                })
            except Exception as e:
                logger.error(f"Error predicting article {article_id}: {e}")
                predictions.append({
                    'article_id': article_id,
                    'predicted_label': 'error_predict',
                    'prediction_score': 0.0,
                })
                continue

        if predictions:
            count = add_batch_predictions(predictions, model_version)
            total_predicted += count
            logger.info(f"Saved {count} predictions [{i + len(batch)}/{len(articles)}]")

    logger.info(f"\n{'=' * 70}")
    logger.info("PREDICTION COMPLETED")
    logger.info(f"{'=' * 70}")
    stats = get_prediction_stats()

    if stats:
        logger.info(f"Total predicted: {stats['total_predictions']}")
        logger.info(f"Unique labels: {stats['unique_labels']}")
        logger.info(f"Avg score: {stats['avg_score']:.4f}")
        logger.info(f"Model version: {stats['model_version']}")

    if show_samples:
        show_sample_predictions(limit=10)

    logger.info(f"Saved in this run: {total_predicted}")
    logger.info("Done!")


def main():
    parser = argparse.ArgumentParser(description='Label articles with model predictions')
    parser.add_argument(
        '--model-path',
        default=os.path.join(PROJECT_ROOT, 'models', 'phobert_clickbait'),
        help='Path to model directory',
    )
    parser.add_argument(
        '--model-version',
        default='phobert_v1.0',
        help='Model version name',
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Batch size for processing',
    )
    parser.add_argument(
        '--show-samples',
        action='store_true',
        help='Show sample predictions after completion',
    )

    args = parser.parse_args()

    run_labeling(
        model_path=args.model_path,
        model_version=args.model_version,
        batch_size=args.batch_size,
        show_samples=args.show_samples,
    )


def show_sample_predictions(limit: int = 10):
    """Show sample predictions."""
    samples = get_sample_predictions(limit=limit)

    if not samples:
        logger.info("No predictions found to display")
        return

    logger.info(f"\n{'=' * 70}")
    logger.info("SAMPLE PREDICTIONS")
    logger.info(f"{'=' * 70}")

    for sample in samples:
        logger.info(f"\n{sample['title'][:80]}...")
        logger.info(f"Label: {sample['predicted_label']}")
        logger.info(f"Score: {sample['prediction_score']:.4f}")
        logger.info(f"Labeled at: {sample['labeled_at']}")


if __name__ == '__main__':
    main()
