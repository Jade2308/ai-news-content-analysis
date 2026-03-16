import re
import time
import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from crawlers.base_crawler import BaseCrawler
from crawlers.utils import normalize_text, parse_relative_time

logger = logging.getLogger(__name__)


class TuoitreCrawler(BaseCrawler):
    def __init__(self, category='thoi-su'):
        super().__init__('tuoitre', category)
        self.base_url = 'https://tuoitre.vn'

        # Mapping category -> URL đúng của Tuổi Trẻ
        self.category_urls = {
            'thoi-su': 'https://tuoitre.vn/thoi-su.htm',
            'cong-nghe': 'https://tuoitre.vn/nhip-song-so.htm',
            'the-thao': 'https://tuoitre.vn/the-thao.htm',
            'giao-duc': 'https://tuoitre.vn/giao-duc.htm',
        }

    def fetch_listing(self):
        """Lấy danh sách URL bài từ trang chuyên mục Tuổi Trẻ"""
        url = self.category_urls.get(self.category, self.base_url)
        logger.info(f"Fetching listing from {url}")

        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, 'html.parser')

            # Lấy tất cả link có thể là bài viết
            # Fallback nhiều selector vì layout có thể thay đổi
            candidate_links = []
            selectors = [
                'h3 a[href]',
                'h2 a[href]',
                'article a[href]',
                'a.box-category-link-with-avatar[href]',
                'a[href*=".htm"]',
            ]
            for sel in selectors:
                candidate_links.extend(soup.select(sel))

            urls = []
            seen = set()

            for a in candidate_links:
                href = a.get('href', '').strip()
                if not href:
                    continue

                full_url = urljoin(self.base_url, href)

                # Chỉ lấy link bài viết thật của tuoitre
                if not full_url.startswith(self.base_url):
                    continue
                if '.htm' not in full_url:
                    continue

                # Loại trừ trang chủ/chuyên mục/tag/video...
                blacklist = [
                    '/video', '/podcast', '/infographic', '/multimedia',
                    '/tag/', '/tim-kiem.htm', '/rss.htm'
                ]
                if any(x in full_url for x in blacklist):
                    continue

                # Loại trừ duplicate
                if full_url in seen:
                    continue
                seen.add(full_url)
                urls.append(full_url)

                if len(urls) >= 50:
                    break

            logger.info(f"Found {len(urls)} article urls")
            return urls

        except Exception as e:
            logger.error(f"Error fetching listing: {e}")
            return []

    def parse_article(self, url):
        """Parse 1 bài từ Tuổi Trẻ"""
        time.sleep(0.5)

        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, 'html.parser')

            # Title
            title_elem = soup.select_one('h1.detail-title, h1.article-title, h1')
            title = normalize_text(title_elem.get_text()) if title_elem else ''

            # Summary / sapo
            summary_elem = soup.select_one('h2.detail-sapo, p.detail-sapo, p.sapo, p.article__summary')
            summary = normalize_text(summary_elem.get_text()) if summary_elem else ''

            # Content
            content = ''
            content_elem = soup.select_one('div.detail-content, div#main-detail-body, div.article__content')
            if content_elem:
                paragraphs = content_elem.select('p')
                texts = [normalize_text(p.get_text()) for p in paragraphs if normalize_text(p.get_text())]
                content = ' '.join(texts[:12])

            # Published time
            published_at = None
            time_elem = soup.select_one('div.date-time, span.date-time, span.article__time, time')
            if time_elem:
                time_text = normalize_text(time_elem.get_text())
                # parse_relative_time của bạn có thể parse dạng "2 giờ trước"
                # nếu gặp format dd/mm/yyyy HH:MM thì nên bổ sung parser sau
                published_at = parse_relative_time(time_text)

            # Nếu title rỗng thì coi là parse fail
            if not title:
                return None

            return {
                'url': url,
                'source': 'tuoitre',
                'category': self.category,
                'title': title,
                'summary': summary,
                'content': content[:1000],  # có thể giảm xuống 500 nếu muốn nhẹ DB
                'published_at': published_at,
            }

        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            return None


if __name__ == '__main__':
    crawler = TuoitreCrawler(category='thoi-su')
    articles = crawler.run()
    print(f"Crawled {len(articles)} articles")
    if articles:
        print(articles[0]['title'])