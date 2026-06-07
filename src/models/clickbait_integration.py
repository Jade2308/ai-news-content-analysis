"""Integration helpers for PhoBERT clickbait detection."""
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

# Ensure project root is in Python path when running as a script.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)

_CLICKBAIT_MODEL = None
_MODEL_PATH = 'results/models/phobert_clickbait'


def get_clickbait_model():
    """Lazy-load the PhoBERT model."""
    global _CLICKBAIT_MODEL

    if _CLICKBAIT_MODEL is not None:
        return _CLICKBAIT_MODEL

    try:
        if not Path(_MODEL_PATH).exists():
            logger.warning(f"Model not found at {_MODEL_PATH}")
            logger.info("Please train the model first using:")
            logger.info("python src/models/train_clickbait.py")
            return None

        from src.models.phobert_classifier import PhoBERTClickbaitClassifier
        logger.info(f"Loading PhoBERT model from {_MODEL_PATH}")
        _CLICKBAIT_MODEL = PhoBERTClickbaitClassifier(model_name=_MODEL_PATH)
        logger.info("PhoBERT model loaded successfully")
        return _CLICKBAIT_MODEL

    except ImportError as e:
        logger.error(f"Could not import PhoBERT: {e}")
        logger.info("Make sure transformers and torch are installed:")
        logger.info("pip install -r requirements.txt")
        return None
    except Exception as e:
        logger.error(f"Error loading PhoBERT model: {e}")
        return None


def detect_clickbait(
    title: str,
    summary: Optional[str] = None,
    use_summary: bool = False
) -> Tuple[int, float, str]:
    """Detect whether an article is clickbait."""
    model = get_clickbait_model()

    if model is None:
        logger.debug("PhoBERT model not available, defaulting to non-clickbait")
        return 0, 0.5, 'non-clickbait'

    try:
        text = f"{title} {summary}" if use_summary and summary else title
        label, confidence = model.predict(text)
        label_name = 'clickbait' if label == 1 else 'non-clickbait'
        return label, confidence, label_name

    except Exception as e:
        logger.error(f"Error in clickbait detection: {e}")
        return 0, 0.5, 'non-clickbait'


def detect_clickbait_batch(
    articles: list,
    title_key: str = 'title',
    summary_key: Optional[str] = 'summary',
    use_summary: bool = False
) -> list:
    """Detect clickbait for multiple article dictionaries."""
    results = []

    for i, article in enumerate(articles):
        try:
            title = str(article.get(title_key, ''))
            summary = str(article.get(summary_key, '')) if summary_key else None

            if not title:
                logger.warning(f"Article {i} has no title, skipping")
                continue

            label, confidence, label_name = detect_clickbait(
                title, summary, use_summary
            )

            result = {
                **article,
                'clickbait_label': label,
                'clickbait_confidence': confidence,
                'clickbait_label_name': label_name,
            }
            results.append(result)

        except Exception as e:
            logger.error(f"Error processing article {i}: {e}")
            continue

    return results


def filter_clickbait(articles: list, keep_clickbait: bool = False) -> list:
    """Filter articles by clickbait status."""
    filtered = []

    for article in articles:
        label = article.get('clickbait_label', 0)

        if keep_clickbait:
            if label == 1:
                filtered.append(article)
        else:
            if label == 0:
                filtered.append(article)

    return filtered


def insert_article_with_clickbait_detection(
    data: dict,
    detect_clickbait_flag: bool = True,
    db_path: str = None
) -> Tuple[str, Optional[dict]]:
    """Insert an article and optionally attach clickbait detection metadata."""
    from src.database.db import insert_article

    clickbait_result = None

    if detect_clickbait_flag:
        title = data.get('title', '')
        summary = data.get('summary', '')

        label, confidence, label_name = detect_clickbait(title, summary, use_summary=True)

        clickbait_result = {
            'label': label,
            'confidence': confidence,
            'label_name': label_name,
        }

        if label == 1:
            logger.warning(
                f"CLICKBAIT DETECTED: {title[:60]}... (confidence: {confidence:.2%})"
            )

        data['clickbait_label'] = label
        data['clickbait_confidence'] = confidence

    insert_status = insert_article(data, db_path=db_path) if db_path else insert_article(data)

    return insert_status, clickbait_result


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    test_titles = [
        "Government announces new public transport investment plan",
        "You will not believe what happens next",
        "Five people rescued after car is swept away by floodwaters",
        "The hidden secret everyone is talking about today",
    ]

    logger.info("Testing PhoBERT clickbait detection")
    logger.info("=" * 60)

    for title in test_titles:
        label, confidence, label_name = detect_clickbait(title)
        logger.info(f"Title: {title[:50]}...")
        logger.info(f"  -> {label_name.upper()} (confidence: {confidence:.2%})")
        logger.info("")
