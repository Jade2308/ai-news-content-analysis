# crawlers/base_crawler.py
import requests
from bs4 import BeautifulSoup
import logging
import sqlite3
import json
from abc import ABC, abstractmethod
from datetime import datetime
from config import DB_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseCrawler(ABC):
    """Base class cho tất cả crawler"""
    
    def __init__(self, source_name, category):
        self.source = source_name
        self.category = category
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.db_path = DB_PATH
    
    @abstractmethod
    def fetch_listing(self):
        """Lấy danh sách URL bài mới - cần override"""
        raise NotImplementedError
    
    @abstractmethod
    def parse_article(self, url):
        """Parse 1 bài - cần override"""
        raise NotImplementedError
    
    def run(self):
        """Orchestrate: fetch listing → parse từng bài"""
        logger.info(f"Starting crawl for {self.source} - {self.category}")
        
        try:
            listing = self.fetch_listing()
            logger.info(f"Found {len(listing)} articles in listing")
            
            articles = []
            for i, url in enumerate(listing, 1):
                try:
                    article = self.parse_article(url)
                    if article:
                        articles.append(article)
                        logger.info(f"✅ Parsed {i}/{len(listing)}: {article['title'][:50]}")
                except Exception as e:
                    logger.error(f"❌ Error parsing {url}: {e}")
                    continue
            
            logger.info(f"✅ Crawl completed: {len(articles)} articles parsed")
            return articles
        
        except Exception as e:
            logger.error(f"❌ Crawl failed: {e}")
            return []
    
    def save_to_database(self, articles):
        """Lưu danh sách bài viết vào database"""
        if not articles:
            logger.warning("No articles to save")
            return 0
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            saved_count = 0
            duplicate_count = 0
            
            for article in articles:
                # Chuyển tags từ list sang string
                tags = article.get('tags', [])
                if isinstance(tags, list):
                    tags = ','.join(tags)
                
                try:
                    cursor.execute('''
                    INSERT INTO articles 
                    (article_id, url, source, category, title, summary, content_text, 
                     author, tags, published_at, crawled_at, content_html_raw, fingerprint)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        article.get('article_id'),
                        article.get('url'),
                        article.get('source'),
                        article.get('category'),
                        article.get('title'),
                        article.get('summary'),
                        article.get('content_text'),
                        article.get('author'),
                        tags,
                        article.get('published_at'),
                        article.get('crawled_at'),
                        article.get('content_html_raw'),
                        article.get('fingerprint')
                    ))
                    saved_count += 1
                except sqlite3.IntegrityError:
                    duplicate_count += 1
                    logger.debug(f"Article already exists: {article.get('url')[:50]}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Saved {saved_count} articles, skipped {duplicate_count} duplicates")
            return saved_count
            
        except Exception as e:
            logger.error(f"❌ Error saving to database: {e}")
            return 0

if __name__ == '__main__':
    pass