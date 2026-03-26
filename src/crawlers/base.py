from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta

import requests
from bs4 import BeautifulSoup

from core.shared_types import Article

logger = logging.getLogger(__name__)

class BaseCrawler(ABC):
    """Base class for all news crawlers, providing shared HTTP and orchestration logic."""
    
    def __init__(self, source_name: str, category: str):
        self.source = source_name
        self.category = category
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        # Vietnam Timezone (UTC+7)
        self.vn_tz = timezone(timedelta(hours=7))
    
    @abstractmethod
    def fetch_listing(self) -> List[str]:
        """Fetch a list of article URLs from a category or listing page."""
        pass
    
    @abstractmethod
    def parse_article(self, url: str) -> Optional[Article]:
        """Parse a single article page and return an Article instance."""
        pass
    
    def get_soup(self, url: str, timeout: int = 15) -> Optional[BeautifulSoup]:
        """Fetch a URL and return a BeautifulSoup object, handling common errors."""
        try:
            r = self.session.get(url, timeout=timeout)
            r.raise_for_status()
            # Default to lxml if available, fallback to html.parser
            try:
                return BeautifulSoup(r.content, 'lxml')
            except Exception:
                return BeautifulSoup(r.content, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def run(self, limit: Optional[int] = None) -> List[Article]:
        """Orchestrate the crawling and parsing process for the configured source/category."""
        logger.info(f"🚀 Starting crawl: source={self.source}, category={self.category}")
        
        try:
            listing = self.fetch_listing()
            if limit:
                listing = listing[:limit]
            
            logger.info(f"Found {len(listing)} potential articles in listing")
            
            articles: List[Article] = []
            for i, url in enumerate(listing, 1):
                try:
                    article = self.parse_article(url)
                    if article:
                        articles.append(article)
                        title_snip = (article.title[:50] + "...") if len(article.title) > 50 else article.title
                        logger.info(f"✅ [{self.source}] ({i}/{len(listing)}) Parsed: {title_snip}")
                except Exception as e:
                    logger.error(f"❌ Error parsing {url}: {e}")
            
            logger.info(f"🏁 Crawl finished: {len(articles)}/{len(listing)} articles parsed for {self.source}/{self.category}")
            return articles
        
        except Exception as e:
            logger.error(f"🔥 Crawl failed for {self.source}/{self.category}: {e}")
            return []