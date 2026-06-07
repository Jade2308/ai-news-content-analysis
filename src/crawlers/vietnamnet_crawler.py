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


class VietnamNetCrawler(BaseCrawler):
    def __init__(self, category='thoi-su'):
        super().__init__('vietnamnet', category)
        self.base_url = 'https://vietnamnet.vn'

        self.category_urls = {
            'chinh-tri': 'https://vietnamnet.vn/chinh-tri',
            'thoi-su': 'https://vietnamnet.vn/thoi-su',
            'net-zero': 'https://vietnamnet.vn/net-zero',
            'giao-duc': 'https://vietnamnet.vn/giao-duc',
            'the-gioi': 'https://vietnamnet.vn/the-gioi',
            'the-thao': 'https://vietnamnet.vn/the-thao',
            'doi-song': 'https://vietnamnet.vn/doi-song',
            'tuan-viet-nam': 'https://vietnamnet.vn/tuan-viet-nam',
            'suc-khoe': 'https://vietnamnet.vn/suc-khoe',
            'cong-nghe': 'https://vietnamnet.vn/cong-nghe',
            'phap-luat': 'https://vietnamnet.vn/phap-luat',
            'xe': 'https://vietnamnet.vn/oto-xe-may',
            'bat-dong-san': 'https://vietnamnet.vn/bat-dong-san',
            'du-lich': 'https://vietnamnet.vn/du-lich',
            'ban-doc': 'https://vietnamnet.vn/ban-doc',
        }

    def fetch_listing(self):
        """Return article URLs from a VietnamNet category page."""
        url = self.category_urls.get(self.category, f'{self.base_url}/{self.category}')
        logger.info(f"Fetching listing from {url}")

        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, 'html.parser')

            urls = []
            for link in soup.select('h3 a, h2 a, h4 a, .vnn-title a'):
                if link and link.get('href'):
                    href = link['href']
                    if not href.startswith('http'):
                        href = self.base_url + href
                    if href not in urls:
                        urls.append(href)

            logger.info(f"Found {len(urls)} article items")
            return urls

        except Exception as e:
            logger.error(f"Error fetching listing: {e}")
            return []

    def parse_article(self, url):
        """Parse one VietnamNet article into the unified Article schema."""
        time.sleep(1)

        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            html = r.text
            soup = BeautifulSoup(r.content, 'html.parser')

            title_elem = soup.select_one('h1.content-detail-title, h1.title')
            title = normalize_text(title_elem.get_text()) if title_elem else ''
            if not title:
                logger.warning(f"No title found for {url}, skipping")
                return None

            summary_elem = soup.select_one('h2.content-detail-sapo, div.content-detail-sapo')
            summary = normalize_text(summary_elem.get_text()) if summary_elem else ''

            author_elem = soup.select_one('p.author-name, span.author, .author-info a')
            author = normalize_text(author_elem.get_text()) if author_elem else None

            tag_elems = soup.select('div.tags-box a.tag, div.tags a')
            tags = [normalize_text(t.get_text()) for t in tag_elems if t.get_text(strip=True)]

            content_elem = soup.select_one('div.maincontent, div.content-detail')
            content_html_raw = str(content_elem) if content_elem else ''
            content_text = extract_text_from_html(
                content_html_raw or html,
                content_selector='div.maincontent, div.content-detail',
            )
            content_text = clean_text(content_text)

            time_elem = soup.select_one('.bread-crumb-detail__time, .publish-time')
            published_at = None
            if time_elem:
                published_at = parse_time(normalize_text(time_elem.get_text()))

            crawled_at = datetime.now(_VN_TZ).strftime('%Y-%m-%d %H:%M:%S')

            return Article(
                url=url,
                source='vietnamnet',
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
    crawler_instance = VietnamNetCrawler()

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
