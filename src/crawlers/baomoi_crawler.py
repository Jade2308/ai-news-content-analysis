import logging
import re
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.core.clean_text import clean_text, extract_text_from_html
from src.core.types import Article
from src.core.utils import normalize_text, parse_time

from .base_crawler import BaseCrawler

logger = logging.getLogger(__name__)

_VN_TZ = timezone(timedelta(hours=7))
_ARTICLE_URL_RE = re.compile(r'-c\d+\.epi$')


class BaomoiCrawler(BaseCrawler):
    """Crawler for baomoi.com."""

    def __init__(self, category='trang-chu'):
        super().__init__('baomoi', category)
        self.base_url = 'https://www.baomoi.com'

        self.category_urls = {
            'trang-chu': 'https://www.baomoi.com',
            'bong-da': 'https://www.baomoi.com/bong-da.epi',
            'the-gioi': 'https://www.baomoi.com/the-gioi.epi',
            'xa-hoi': 'https://www.baomoi.com/xa-hoi.epi',
            'van-hoa': 'https://www.baomoi.com/van-hoa.epi',
            'kinh-te': 'https://www.baomoi.com/kinh-te.epi',
            'giao-duc': 'https://www.baomoi.com/giao-duc.epi',
            'the-thao': 'https://www.baomoi.com/the-thao.epi',
            'giai-tri': 'https://www.baomoi.com/giai-tri.epi',
            'phap-luat': 'https://www.baomoi.com/phap-luat.epi',
            'cong-nghe': 'https://baomoi.com/khoa-hoc-cong-nghe.epi',
            'khoa-hoc': 'https://baomoi.com/khoa-hoc.epi',
            'doi-song': 'https://www.baomoi.com/doi-song.epi',
            'xe-co': 'https://www.baomoi.com/xe-co.epi',
            'nha-dat': 'https://www.baomoi.com/nha-dat.epi',
        }

    def fetch_listing(self):
        """Return article URLs from a Baomoi category page."""
        url = self.category_urls.get(self.category) or self.category_urls.get('trang-chu') or self.base_url
        logger.info(f"Fetching listing from {url}")

        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, 'html.parser')

            urls = []
            seen = set()

            article_links = soup.select('a[href]')

            blacklist_patterns = [
                '/tag/', '/tim-kiem', '/video', '/photo', '/comment',
                '/tin-video', '/tin-anh', '/chu-de', '/livescore', '/top',
            ]

            for a in article_links:
                href = a.get('href', '').strip()
                if not href:
                    continue

                full_url = urljoin(self.base_url, href)

                if not full_url.startswith(self.base_url):
                    continue

                if any(pattern in full_url for pattern in blacklist_patterns):
                    continue

                if not _ARTICLE_URL_RE.search(full_url):
                    continue

                if full_url in seen:
                    continue

                if full_url.endswith(('.jpg', '.png', '.gif', '.css', '.js')):
                    continue

                seen.add(full_url)
                urls.append(full_url)

                if len(urls) >= 50:
                    break

            logger.info(f"Found {len(urls)} article URLs")
            return urls

        except Exception as e:
            logger.error(f"Error fetching listing: {e}", exc_info=True)
            return []

    def parse_article(self, url):
        """Parse one Baomoi article into the unified Article schema."""
        time.sleep(1)

        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            html = r.text
            soup = BeautifulSoup(r.content, 'html.parser')

            title = None
            title_selectors = [
                'h1.title-detail',
                'h1.article-title',
                'h1',
                'meta[property="og:title"]',
            ]

            for sel in title_selectors:
                if sel.startswith('meta'):
                    meta = soup.select_one(sel)
                    if meta:
                        title = meta.get('content', '').strip()
                        break
                else:
                    elem = soup.select_one(sel)
                    if elem:
                        title = elem.get_text(strip=True)
                        break

            if not title:
                logger.warning(f"Could not find title for {url}")
                return None

            summary = None
            summary_selectors = [
                'meta[property="og:description"]',
                'meta[name="description"]',
                'p.description',
                'p.lead',
                '.article-description',
            ]

            for sel in summary_selectors:
                elem = soup.select_one(sel)
                if elem:
                    if sel.startswith('meta'):
                        summary = elem.get('content', '').strip()
                    else:
                        summary = elem.get_text(strip=True)
                    if summary:
                        break

            content_html_raw = None
            content_selectors = [
                'div.detail-content',
                'div.article-content',
                'div.content-news',
                'article',
                '.news-detail-content',
            ]

            for sel in content_selectors:
                elem = soup.select_one(sel)
                if elem:
                    content_html_raw = str(elem)
                    break

            if not content_html_raw:
                logger.warning(f"Could not find content for {url}")
                return None

            content_text = extract_text_from_html(content_html_raw or html)
            content_text = clean_text(content_text)

            if not content_text:
                logger.warning(f"No text content extracted for {url}")
                return None

            published_at = None
            time_selectors = [
                'span.publish-time',
                'span.time-publish',
                'time',
                'meta[property="article:published_time"]',
                '.article-time',
                '.publish-time',
            ]

            for sel in time_selectors:
                time_str = None
                if sel.startswith('meta'):
                    elem = soup.select_one(sel)
                    if elem:
                        time_str = elem.get('content', '').strip()
                else:
                    elem = soup.select_one(sel)
                    if elem:
                        time_str = elem.get('datetime', '') if sel == 'time' else elem.get_text(strip=True)

                if time_str:
                    parsed = parse_time(time_str)
                    if parsed:
                        published_at = parsed
                        break

            author = None
            author_selectors = [
                'span.author-name',
                'a.author-link',
                '.article-author',
                'meta[name="author"]',
            ]

            for sel in author_selectors:
                if sel.startswith('meta'):
                    elem = soup.select_one(sel)
                    if elem:
                        author = elem.get('content', '').strip()
                else:
                    elem = soup.select_one(sel)
                    if elem:
                        author = elem.get_text(strip=True)
                if author:
                    break

            crawled_at = datetime.now(_VN_TZ).strftime('%Y-%m-%d %H:%M:%S')

            return Article(
                url=url,
                source=self.source,
                category=self.category,
                title=normalize_text(title),
                summary=normalize_text(summary) if summary else None,
                content_text=content_text,
                author=author or None,
                tags=[],
                published_at=published_at,
                crawled_at=crawled_at,
                content_html_raw=content_html_raw,
            ).to_dict()

        except Exception as e:
            logger.error(f"Error parsing article {url}: {e}", exc_info=True)
            return None


if __name__ == '__main__':
    crawler = BaomoiCrawler()

    total_articles = []
    for category_slug in crawler.category_urls.keys():
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Crawling category: {category_slug}")
        logger.info(f"{'=' * 60}")

        crawler.category = category_slug
        articles = crawler.run()
        total_articles.extend(articles)
        time.sleep(2)

    logger.info(f"\n{'=' * 60}")
    logger.info(f"Total articles crawled: {len(total_articles)}")
    logger.info("Saving to database...")
    crawler.save_to_database(total_articles)
    logger.info("Done!")
