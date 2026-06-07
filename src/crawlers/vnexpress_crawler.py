# crawlers/vnexpress_crawler.py
import logging
import time
from datetime import datetime, timedelta, timezone

from bs4 import BeautifulSoup

from src.core.clean_text import clean_text, extract_text_from_html
from src.core.types import Article
from src.core.utils import normalize_text, parse_time

from .base_crawler import BaseCrawler

logger = logging.getLogger(__name__)

_VN_TZ = timezone(timedelta(hours=7))


class VNExpressCrawler(BaseCrawler):
    def __init__(self, category='thoi-su'):
        super().__init__('vnexpress', category)
        self.base_url = 'https://vnexpress.net'

        self.category_urls = {
            'vne-go': 'https://vnexpress.net/vne-go',
            'thoi-su': 'https://vnexpress.net/thoi-su',
            'the-gioi': 'https://vnexpress.net/the-gioi',
            'khoa-hoc-cong-nghe': 'https://vnexpress.net/khoa-hoc-cong-nghe',
            'goc-nhin': 'https://vnexpress.net/goc-nhin',
            'bat-dong-san': 'https://vnexpress.net/bat-dong-san',
            'suc-khoe': 'https://vnexpress.net/suc-khoe',
            'the-thao': 'https://vnexpress.net/the-thao',
            'giai-tri': 'https://vnexpress.net/giai-tri',
            'phap-luat': 'https://vnexpress.net/phap-luat',
            'giao-duc': 'https://vnexpress.net/giao-duc',
            'doi-song': 'https://vnexpress.net/doi-song',
            'xe': 'https://vnexpress.net/oto-xe-may',
            'du-lich': 'https://vnexpress.net/du-lich',
            'y-kien': 'https://vnexpress.net/y-kien',
            'tam-su': 'https://vnexpress.net/tam-su',
            'thu-gian': 'https://vnexpress.net/thu-gian',
        }

    def fetch_listing(self):
        """Return article URLs from a VNExpress category page."""
        url = self.category_urls.get(self.category, f'{self.base_url}/{self.category}')
        logger.info(f"Fetching listing from {url}")

        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, 'html.parser')

            articles = soup.select('article.item-news')
            logger.info(f"Found {len(articles)} article items")

            urls = []
            for article in articles:
                link = article.select_one('a.title-news, h3 a, h2 a')
                if link and link.get('href'):
                    href = link['href']
                    if not href.startswith('http'):
                        href = self.base_url + href
                    urls.append(href)

            return urls

        except Exception as e:
            logger.error(f"Error fetching listing: {e}")
            return []

    def parse_article(self, url):
        """Parse one VNExpress article into the unified Article schema."""
        time.sleep(1)

        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            html = r.text
            soup = BeautifulSoup(r.content, 'html.parser')

            title_elem = soup.select_one('h1.title-detail')
            title = normalize_text(title_elem.get_text()) if title_elem else ''
            if not title:
                logger.warning(f"No title found for {url}, skipping")
                return None

            summary_elem = soup.select_one('p.description')
            summary = normalize_text(summary_elem.get_text()) if summary_elem else ''

            author_elem = soup.select_one('p.author_mail strong, p.author strong, span.author')
            author = normalize_text(author_elem.get_text()) if author_elem else None

            tag_elems = soup.select('ul.list-tag a, div.tags a')
            tags = [normalize_text(t.get_text()) for t in tag_elems if t.get_text(strip=True)]

            content_elem = soup.select_one('article.fck_detail, article')
            content_html_raw = str(content_elem) if content_elem else ''
            content_text = extract_text_from_html(
                content_html_raw or html,
                content_selector='article.fck_detail',
            )
            content_text = clean_text(content_text)

            time_elem = soup.select_one('span.date')
            published_at = None
            if time_elem:
                published_at = parse_time(normalize_text(time_elem.get_text()))

            crawled_at = datetime.now(_VN_TZ).strftime('%Y-%m-%d %H:%M:%S')

            return Article(
                url=url,
                source='vnexpress',
                category=self.category,
                title=title,
                summary=summary or None,
                content_text=content_text,
                author=author,
                tags=tags,
                published_at=published_at,
                crawled_at=crawled_at,
                content_html_raw=content_html_raw or None,
            ).to_dict()

        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            return None


if __name__ == '__main__':
    crawler_instance = VNExpressCrawler()

    total_articles = []
    for category_slug in crawler_instance.category_urls.keys():
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Crawling category: {category_slug}")
        logger.info(f"{'=' * 60}")

        crawler_instance.category = category_slug
        articles = crawler_instance.run()
        total_articles.extend(articles)
        time.sleep(2)

    logger.info(f"\n{'=' * 60}")
    logger.info(f"Total articles crawled: {len(total_articles)}")
    logger.info("Saving to database...")
    crawler_instance.save_to_database(total_articles)
    logger.info("Done!")
