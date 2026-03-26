import sqlite3
import logging
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Iterator

from core.settings import DB_PATH
from core.shared_types import Article

logger = logging.getLogger(__name__)

@contextmanager
def get_db_cursor(db_path: str = DB_PATH) -> Iterator[sqlite3.Cursor]:
    """Context manager for SQLite database connection and cursor."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable access by column name
    try:
        yield conn.cursor()
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database transaction failed: {e}")
        raise e
    finally:
        conn.close()

def insert_article(article: Article, db_path: str = DB_PATH) -> str:
    """
    Insert an article into the DB with de-duplication logic.
    Returns: 'inserted', 'dup_url', 'dup_fp', or 'error'.
    """
    data = article.to_dict()
    try:
        with get_db_cursor(db_path) as cursor:
            # 1. URL-based de-duplication
            cursor.execute('SELECT id FROM articles WHERE url = ?', (data['url'],))
            if cursor.fetchone():
                return 'dup_url'

            # 2. Fingerprint-based de-duplication
            fp = data.get('fingerprint')
            if fp:
                cursor.execute('SELECT id FROM articles WHERE fingerprint = ?', (fp,))
                if cursor.fetchone():
                    return 'dup_fp'

            # 3. Insertion
            fields = [
                'article_id', 'url', 'source', 'category', 'title', 'summary',
                'content_text', 'author', 'tags', 'published_at', 'crawled_at',
                'content_html_raw', 'thumbnail_url', 'fingerprint'
            ]
            placeholders = ', '.join(['?' for _ in fields])
            sql = f'INSERT INTO articles ({", ".join(fields)}) VALUES ({placeholders})'
            
            values = [data.get(f) for f in fields]
            cursor.execute(sql, values)
            return 'inserted'
            
    except sqlite3.IntegrityError:
        return 'dup_url'
    except Exception as e:
        logger.error(f"Database error during insertion of {data['url']}: {e}")
        return 'error'

def get_all_articles(limit: int = 1000, db_path: str = DB_PATH) -> List[Article]:
    """Return latest articles as a list of Article objects."""
    with get_db_cursor(db_path) as cursor:
        cursor.execute('SELECT * FROM articles ORDER BY crawled_at DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        return [Article.from_dict(dict(row)) for row in rows]

def get_articles_by_timerange(hours: int = 24, limit: int = 1000, db_path: str = DB_PATH) -> List[Article]:
    """Return articles crawled within a specific time range."""
    with get_db_cursor(db_path) as cursor:
        cursor.execute('''
            SELECT * FROM articles 
            WHERE crawled_at > datetime('now', '-' || ? || ' hours')
            ORDER BY crawled_at DESC 
            LIMIT ?
        ''', (hours, limit))
        rows = cursor.fetchall()
        return [Article.from_dict(dict(row)) for row in rows]

def count_articles(db_path: str = DB_PATH) -> int:
    """Return total article count."""
    try:
        with get_db_cursor(db_path) as cursor:
            cursor.execute('SELECT COUNT(*) FROM articles')
            res = cursor.fetchone()
            return res[0] if res else 0
    except Exception:
        return 0

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger.info(f"Connected to database: {DB_PATH}")
    logger.info(f"Total articles: {count_articles()}")