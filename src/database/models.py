import logging
from core.settings import DB_PATH
from database.engine import get_db_cursor

logger = logging.getLogger(__name__)

def init_db(db_path: str = DB_PATH) -> None:
    """Initialize database with the required schema and indices."""
    try:
        with get_db_cursor(db_path) as cursor:
            # Create articles table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id      TEXT UNIQUE NOT NULL,   -- sha1(url)
                url             TEXT UNIQUE NOT NULL,
                source          TEXT NOT NULL,           -- 'vnexpress' | 'tuoitre'
                category        TEXT,                    -- 'kinh-doanh', 'thoi-su', …
                title           TEXT NOT NULL,
                summary         TEXT,
                content_text    TEXT,                    -- cleaned plain-text body
                author          TEXT,
                tags            TEXT,                    -- comma-separated tag list
                published_at    TEXT,                    -- "YYYY-MM-DD HH:MM:SS" or NULL
                crawled_at      TEXT NOT NULL,           -- "YYYY-MM-DD HH:MM:SS"
                content_html_raw TEXT,                   -- raw HTML snippet (debug)
                thumbnail_url   TEXT,                    -- article image URL
                fingerprint     TEXT,                    -- sha1(normalised content_text)
                created_at      TEXT DEFAULT (datetime('now'))
            )
            ''')

            # Create indices for common queries
            indices = {
                'idx_fingerprint': 'articles(fingerprint)',
                'idx_crawled_at': 'articles(crawled_at)',
                'idx_published_at': 'articles(published_at)',
                'idx_url': 'articles(url)'
            }
            for name, target in indices.items():
                cursor.execute(f'CREATE INDEX IF NOT EXISTS {name} ON {target}')

            logger.info(f"✅ Database schema verified at: {db_path}")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise e

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    init_db()