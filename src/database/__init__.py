"""
database/__init__.py
Export main database functions
"""

from .schema import init_db
from .predictions import (
    add_prediction,
    add_batch_predictions,
    get_unpredicted_articles,
    get_prediction_stats,
    get_sample_predictions
)

__all__ = [
    'init_db',
    'add_prediction',
    'add_batch_predictions',
    'get_unpredicted_articles',
    'get_prediction_stats',
    'get_sample_predictions'
]
