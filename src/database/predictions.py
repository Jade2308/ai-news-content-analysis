"""
Helpers for adding and reading model prediction results in the articles table.
"""

import sqlite3
from datetime import datetime
from typing import Dict, List

from src.config import DB_PATH


def add_prediction(
    article_id: str,
    predicted_label: str,
    prediction_score: float,
    model_version: str,
    db_path: str = DB_PATH
) -> bool:
    """Add or update a prediction result for one article."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        labeled_at = datetime.now().isoformat()

        cursor.execute('''
            UPDATE articles
            SET predicted_label = ?,
                prediction_score = ?,
                model_version = ?,
                labeled_at = ?
            WHERE article_id = ?
        ''', (predicted_label, prediction_score, model_version, labeled_at, article_id))

        conn.commit()
        conn.close()

        return cursor.rowcount > 0

    except Exception as e:
        print(f"Error adding prediction: {e}")
        return False


def add_batch_predictions(
    predictions: List[Dict],
    model_version: str,
    db_path: str = DB_PATH
) -> int:
    """Add or update prediction results for a batch of articles."""
    if not predictions:
        return 0

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        labeled_at = datetime.now().isoformat()
        inserted_count = 0

        for pred in predictions:
            article_id = pred.get('article_id')
            predicted_label = pred.get('predicted_label')
            prediction_score = pred.get('prediction_score')

            if article_id is None or predicted_label is None or prediction_score is None:
                continue

            if not (0 <= prediction_score <= 1):
                continue

            try:
                cursor.execute('''
                    UPDATE articles
                    SET predicted_label = ?,
                        prediction_score = ?,
                        model_version = ?,
                        labeled_at = ?
                    WHERE article_id = ?
                ''', (predicted_label, prediction_score, model_version, labeled_at, article_id))

                if cursor.rowcount > 0:
                    inserted_count += 1
            except Exception:
                continue

        conn.commit()
        conn.close()

        return inserted_count

    except Exception as e:
        print(f"Error in batch add: {e}")
        return 0


def get_unpredicted_articles(db_path: str = DB_PATH) -> List[Dict]:
    """Return articles that do not yet have a model prediction."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT article_id, title, content_text, summary
            FROM articles
            WHERE predicted_label IS NULL
            ORDER BY crawled_at DESC
        ''')

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    except Exception as e:
        print(f"Error fetching unpredicted articles: {e}")
        return []


def get_prediction_stats(db_path: str = DB_PATH) -> Dict:
    """Return prediction summary statistics."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                COUNT(*) as total_predictions,
                COUNT(DISTINCT predicted_label) as unique_labels,
                AVG(prediction_score) as avg_score,
                MIN(prediction_score) as min_score,
                MAX(prediction_score) as max_score,
                model_version
            FROM articles
            WHERE predicted_label IS NOT NULL
        ''')

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'total_predictions': row[0],
                'unique_labels': row[1],
                'avg_score': round(row[2], 4) if row[2] else 0,
                'min_score': row[3],
                'max_score': row[4],
                'model_version': row[5],
            }
        return {
            'total_predictions': 0,
            'unique_labels': 0,
            'avg_score': 0,
            'min_score': None,
            'max_score': None,
            'model_version': None,
        }

    except Exception as e:
        print(f"Error fetching stats: {e}")
        return {}


def get_sample_predictions(limit: int = 10, db_path: str = DB_PATH) -> List[Dict]:
    """Return a small sample of recent predictions."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT article_id, title, predicted_label, prediction_score, labeled_at
            FROM articles
            WHERE predicted_label IS NOT NULL
            ORDER BY labeled_at DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    except Exception as e:
        print(f"Error fetching samples: {e}")
        return []
