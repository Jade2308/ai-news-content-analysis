"""Simple inference script for the PhoBERT clickbait classifier."""
import logging
import sys
from pathlib import Path

# Ensure project root is in Python path when running as a script.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.phobert_classifier import PhoBERTClickbaitClassifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Test the local model on readable sample titles."""
    model_path = 'results/models/phobert_clickbait'

    if not Path(model_path).exists():
        logger.error(f"Model not found at {model_path}")
        logger.info("Please train the model first:")
        logger.info("  python src/models/train_clickbait.py")
        return

    logger.info(f"Loading model from {model_path}")
    model = PhoBERTClickbaitClassifier(model_name=model_path)

    test_titles = [
        "Government announces new public transport investment plan",
        "Airport closes for six months of infrastructure upgrades",
        "Five people rescued after car is swept away by floodwaters",
        "City approves nine new functional zones in the eastern district",
        "Minister announces creation of a new central committee agency",
        "You will not believe what happens next",
        "This secret trick changes everything overnight",
        "Watch this video before it disappears forever",
        "The shocking reason everyone is talking about this story",
        "One simple habit that can transform your life in a day",
    ]

    logger.info("\n" + "=" * 80)
    logger.info("TESTING PHOBERT CLICKBAIT CLASSIFIER")
    logger.info("=" * 80 + "\n")

    for i, title in enumerate(test_titles, 1):
        label, probs = model.predict(title, return_probs=True)
        label_name = "CLICKBAIT" if label == 1 else "NON-CLICKBAIT"

        logger.info(f"[{i:2d}] {label_name}")
        logger.info(f"      Title: {title[:70]}")
        if len(title) > 70:
            logger.info(f"             {title[70:]}")
        logger.info(f"      Confidence: {probs[label]:.2%}")
        logger.info(f"      Probs: Non-clickbait={probs[0]:.2%}, Clickbait={probs[1]:.2%}")
        logger.info("")

    logger.info("=" * 80)
    logger.info("Testing completed!")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
