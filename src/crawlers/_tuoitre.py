import re
import logging
from datetime import datetime
from urllib.parse import urljoin
from typing import Optional, List

from crawlers.base import BaseCrawler
from crawlers.helpers import normalize_text, parse_time
from core.shared_types import Article
from core.cleaner import extract_text_from_html, clean_text

logger = logging.getLogger(__name__)

class TuoitreCrawler(BaseCrawler):
    """Crawler implementation for TuoiTre news site."""
    
    def __init__(self, category: str = 'thoi-su'):
        super().__init__('tuoitre', category)
        self.base_url = 'https://tuoitre.vn'
        self.category_urls = {
            'thoi-su': 'https://tuoitre.vn/thoi-su.htm',
            'kinh-doanh': 'https://tuoitre.vn/kinh-doanh.htm',
            'cong-nghe': 'https://tuoitre.vn/cong-nghe.htm',
            'giai-tri': 'https://tuoitre.vn/giai-tri.htm',
            'the-thao': 'https://tuoitre.vn/the-thao.htm',
            'suc-khoe': 'https://tuoitre.vn/suc-khoe.htm',
        }
        # Avoid non-article content
        self._blacklist = ['/video', '/podcast', '/infographic', '/multimedia', '/tag/', '/tim-kiem.htm']
        # Articles usually have an ID at the end before .htm
        self._article_re = re.compile(r'-\d{7,}\.htm$')

    def fetch_listing(self) -> List[str]:
        """Fetch article URLs from the listing page."""
        url = self.category_urls.get(self.category, self.base_url)
        soup = self.get_soup(url)
        if not soup:
            return []

        urls = []
        selectors = ['h3 a[href]', 'h2 a[href]', 'article a[href]', 'a.box-category-link-with-avatar[href]']
        for sel in selectors:
            for a in soup.select(sel):
                href = a.get('href', '').strip()
                if not href:
                    continue
                full_url = urljoin(self.base_url, href)
                
                # Validation: must be within TuoiTre and look like an article
                if (full_url.startswith(self.base_url) and 
                    '.htm' in full_url and 
                    not any(x in full_url for x in self._blacklist) and 
                    self._article_re.search(full_url)):
                    urls.append(full_url)
        
        return list(dict.fromkeys(urls))  # Remove duplicates

    def parse_article(self, url: str) -> Optional[Article]:
        """Parse the content of a single TuoiTre article."""
        soup = self.get_soup(url)
        if not soup:
            return None

        try:
            # --- Title ---
            title_elem = soup.select_one('h1.detail-title, h1.article-title, h1')
            title = normalize_text(title_elem.get_text()) if title_elem else ''
            if not title:
                logger.warning(f"Skipping article with no title: {url}")
                return None

            # --- Summary (Sapo) ---
            summary_elem = soup.select_one('h2.detail-sapo, p.detail-sapo, p.sapo, p.article__summary')
            summary = normalize_text(summary_elem.get_text()) if summary_elem else ''

            # --- Author ---
            author_elem = soup.select_one('div.author-info strong, p.author-name, span.author')
            author = normalize_text(author_elem.get_text()) if author_elem else None

            # --- Tags ---
            tag_elems = soup.select('ul.tags a, div.tags a, a.tag-item')
            tags = [normalize_text(t.get_text()) for t in tag_elems if t.get_text(strip=True)]

            # --- Thumbnail Image ---
            img_url = None
            og_img = soup.select_one('meta[property="og:image"]')
            if og_img:
                img_url = og_img.get('content')
            if not img_url:
                tw_img = soup.select_one('meta[name="twitter:image"]')
                if tw_img:
                    img_url = tw_img.get('content')

            # --- Content Extraction & Cleaning ---
            content_elem = soup.select_one('div.detail-content, div#main-detail-body, div.article__content')
            content_html_raw = str(content_elem) if content_elem else ''
            content_text = extract_text_from_html(
                content_html_raw or str(soup),
                content_selector='div.detail-content, div#main-detail-body',
            )
            content_text = clean_text(content_text)

            # --- Publication Time ---
            published_at = None
            # Method 1: Meta tags
            meta_time = soup.select_one('meta[property="article:published_time"], meta[name="pubdate"]')
            if meta_time and meta_time.get('content'):
                published_at = parse_time(str(meta_time.get('content')))
            
            # Method 2: Element extraction
            if not published_at:
                time_elem = soup.select_one('div.date-time, div.detail-time, span.article__time, time[datetime]')
                if time_elem:
                    dt_attr = time_elem.get('datetime')
                    published_at = parse_time(str(dt_attr) if dt_attr else normalize_text(time_elem.get_text()))

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
            logger.error(f"Error parsing TuoiTre article at {url}: {e}")
            return None

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    crawler = TuoitreCrawler(category='thoi-su')
    articles = crawler.run(limit=1)
    if articles:
        from dataclasses import asdict
        import json
        print(json.dumps(asdict(articles[0]), indent=2, ensure_ascii=False))