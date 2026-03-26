import os
import logging
from typing import Any, Dict, Optional
from dotenv import load_dotenv

# Configure basic logging level from environment
load_dotenv()

# --- Base directory and Root ---
# src/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# project_root/
PROJECT_ROOT = os.path.dirname(BASE_DIR)

def get_env_or_default(key: str, default: Any) -> Any:
    """Helper to fetch environment variables with a default fallback."""
    return os.environ.get(key, default)

# --- Path settings ---
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# --- Database settings ---
# Default to articles.db in data directory if not specified
DB_PATH = get_env_or_default('DB_PATH', os.path.join(DATA_DIR, 'articles.db'))

# --- Crawler settings ---
CRAWL_INTERVAL_MINUTES = int(get_env_or_default('CRAWL_INTERVAL_MINUTES', 30))
CLICKBAIT_INTERVAL_MINUTES = int(get_env_or_default('CLICKBAIT_INTERVAL_MINUTES', 60))
TOPIC_INTERVAL_HOURS = int(get_env_or_default('TOPIC_INTERVAL_HOURS', 6))

SOURCES: Dict[str, Dict[str, Any]] = {
    'vnexpress': {
        'name': 'VNExpress',
        'categories': {
            'thoi-su': 'Thời sự',
            'kinh-doanh': 'Kinh doanh',
            'khoa-hoc': 'Công nghệ',
        }
    },
    'tuoitre': {
        'name': 'Tuổi Trẻ',
        'categories': {
            'thoi-su': 'Thời sự',
            'kinh-doanh': 'Kinh doanh',
            'cong-nghe': 'Công nghệ',
        }
    }
}

# --- ML & Analysis settings ---
N_TOPICS = int(get_env_or_default('N_TOPICS', 10))
TOPIC_METHOD = get_env_or_default('TOPIC_METHOD', 'lda')  # Options: 'lda', 'nmf', 'bertopic'
CLICKBAIT_SAMPLE_SIZE = int(get_env_or_default('CLICKBAIT_SAMPLE_SIZE', 100))