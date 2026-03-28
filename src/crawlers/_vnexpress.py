import logging
from datetime import datetime
from typing import Optional, List

from crawlers.base import BaseCrawler
from crawlers.helpers import normalize_text, parse_time
from core.shared_types import Article
from core.cleaner import extract_text_from_html, clean_text

logger = logging.getLogger(__name__)

class VNExpressCrawler(BaseCrawler):
    """Crawler implementation for VNExpress news site."""
    
    def __init__(self, category: str = 'thoi-su'):
        super().__init__('vnexpress', category)
        self.base_url = 'https://vnexpress.net'
        self.category_urls = {
            'thoi-su': 'https://vnexpress.net/thoi-su',
            'kinh-doanh': 'https://vnexpress.net/kinh-doanh',
            'cong-nghe': 'https://vnexpress.net/khoa-hoc',
            'giai-tri': 'https://vnexpress.net/giai-tri',
            'the-thao': 'https://vnexpress.net/the-thao',
            'suc-khoe': 'https://vnexpress.net/suc-khoe',
        }

    def fetch_listing(self) -> List[str]:
        """Fetch article URLs from the category listing page."""
        url = self.category_urls.get(self.category, f'{self.base_url}/{self.category}')
        soup = self.get_soup(url)
        if not soup:
            return []

        urls = []
        # Target main article items in the listing
        for item in soup.select('article.item-news'):
            link = item.select_one('a.title-news, h3 a, h2 a')
            if link and link.get('href'):
                href = str(link['href'])
                if not href.startswith('http'):
                    if href.startswith('/'):
                        href = self.base_url + href
                    else:
                        href = f"{self.base_url}/{href}"
                urls.append(href)
        
        return list(dict.fromkeys(urls))  # Maintain order but remove duplicates

    def parse_article(self, url: str) -> Optional[Article]:
        """Parse the content of a single VNExpress article."""
        soup = self.get_soup(url)
        if not soup:
            return None

        try:
            # --- Title ---
            title_elem = soup.select_one('h1.title-detail')
            title = normalize_text(title_elem.get_text()) if title_elem else ''
            if not title:
                logger.warning(f"Skipping article with no title: {url}")
                return None

            # --- Summary (Sapo) ---
            summary_elem = soup.select_one('p.description')
            summary = normalize_text(summary_elem.get_text()) if summary_elem else ''

            # --- Author ---
            author_elem = soup.select_one('p.author_mail strong, p.author strong, span.author')
            author = normalize_text(author_elem.get_text()) if author_elem else None

            # --- Tags ---
            tag_elems = soup.select('ul.list-tag a, div.tags a')
            tags = [normalize_text(t.get_text()) for t in tag_elems if t.get_text(strip=True)]

            # --- Thumbnail Image ---
            img_url = None
            og_img = soup.select_one('meta[property="og:image"]')
            if og_img:
                img_url = og_img.get('content')
            if not img_url:
                thumb_meta = soup.select_one('meta[itemprop="thumbnailUrl"]')
                if thumb_meta:
                    img_url = thumb_meta.get('content')

            # --- Content Extraction & Cleaning ---
            content_elem = soup.select_one('article.fck_detail, article')
            content_html_raw = str(content_elem) if content_elem else ''
            content_text = extract_text_from_html(
                content_html_raw or str(soup),
                content_selector='article.fck_detail',
            )
            content_text = clean_text(content_text)

            # --- Publication Time ---
            time_elem = soup.select_one('span.date')
            published_at = parse_time(normalize_text(time_elem.get_text())) if time_elem else None

            return Article(
                url=url,
                source=self.source,
                category=self.category,
                title=title,
                summary=summary or None,
                content_text=content_text,
                author=author,
                tags=tags,
                published_at=published_at,
                crawled_at=datetime.now(self.vn_tz).strftime('%Y-%m-%d %H:%M:%S'),
                content_html_raw=content_html_raw or None,
                thumbnail_url=img_url,
            )

        except Exception as e:
            logger.error(f"Error parsing article at {url}: {e}")
            return None

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    crawler = VNExpressCrawler(category='thoi-su')
    articles = crawler.run(limit=1)
    if articles:
        from dataclasses import asdict
        import json
        print(json.dumps(asdict(articles[0]), indent=2, ensure_ascii=False))