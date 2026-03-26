"""
core/cleaner.py – Content cleaning utilities.

Removes noise from crawled Vietnamese news articles:
  - Script/style/nav/footer/aside and ad-related tags
  - Vietnamese boilerplate phrases
  - Excessive whitespace
"""
from __future__ import annotations

import re
import logging
from typing import Optional, List, Set, Final
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Noise phrases – Vietnamese news boilerplate / ads / related-article blocks
# ---------------------------------------------------------------------------
_NOISE_PHRASES: Final[List[str]] = [
    r'bài liên quan[:\s]*',
    r'tin liên quan[:\s]*',
    r'xem thêm[:\s]*',
    r'đọc thêm[:\s]*',
    r'đọc tiếp[:\s]*',
    r'xem tiếp[:\s]*',
    r'có thể bạn quan tâm[:\s]*',
    r'tin cùng chuyên mục[:\s]*',
    r'video liên quan[:\s]*',
    r'chia sẻ bài viết[:\s]*',
    r'theo dõi[:\s]+\w+\s+trên',
    r'\[quảng cáo\]',
    r'\(quảng cáo\)',
    r'advertisement',
    r'vnexpress\.net',
    r'tuoitre\.vn',
    r'gửi bình luận',
    r'viết bình luận',
    r'đánh giá bài viết',
]

_NOISE_RE: Final[re.Pattern] = re.compile('|'.join(_NOISE_PHRASES), re.IGNORECASE | re.UNICODE)

# Tags whose entire subtree should be stripped from HTML before text extraction
_STRIP_TAGS: Final[Set[str]] = {
    'script', 'style', 'nav', 'footer', 'header', 'aside',
    'figure', 'figcaption', 'iframe', 'form', 'noscript',
    'ins',
}

# CSS class / id fragments that indicate ad / related-article boxes
_AD_CLASS_PATTERNS: Final[re.Pattern] = re.compile(
    r'(advert|advertisement|banner|promo|related|suggest|sidebar|widget|social|share)',
    re.IGNORECASE,
)

DEFAULT_MAX_LEN: Final[int] = 0


def strip_html_noise(html: str) -> BeautifulSoup:
    """Parse raw HTML and remove noise elements (ads, navigation, scripts)."""
    # Use lxml if available, otherwise html.parser
    try:
        soup = BeautifulSoup(html, 'lxml')
    except Exception:
        soup = BeautifulSoup(html, 'html.parser')

    # 1. Remove by tag name
    for tag_name in _STRIP_TAGS:
        for elem in soup.find_all(tag_name):
            elem.decompose()

    # 2. Remove elements whose class or id looks like an ad / sidebar
    for elem in soup.find_all(True):
        if not isinstance(elem, Tag):
            continue
            
        attrs = elem.attrs
        
        # Combine class and id for searching
        cls_attr = attrs.get('class', [])
        classes = " ".join(cls_attr) if isinstance(cls_attr, list) else str(cls_attr)
        elem_id = str(attrs.get('id', ''))
        
        if _AD_CLASS_PATTERNS.search(classes) or _AD_CLASS_PATTERNS.search(elem_id):
            elem.decompose()

    return soup


def clean_text(text: str, max_len: int = DEFAULT_MAX_LEN) -> str:
    """Clean plain text extracted from an article (normalize whitespace, remove boilerplate)."""
    if not text:
        return ''

    # Remove noise phrases
    text = _NOISE_RE.sub(' ', text)

    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    if max_len > 0 and len(text) > max_len:
        # Truncate at word boundary
        truncated = text[:max_len]
        last_space = truncated.rfind(' ')
        if last_space > max_len // 2:
            truncated = truncated[:last_space]
        text = truncated + "..."

    return text


def extract_text_from_html(
    html: str,
    content_selector: Optional[str] = None,
    max_len: int = DEFAULT_MAX_LEN,
) -> str:
    """Extract and clean text from raw HTML, optionally targeting a specific sub-element."""
    if not html:
        return ""

    try:
        soup = strip_html_noise(html)
        root = soup.select_one(content_selector) if content_selector else soup
        if not root:
            root = soup

        # Prefer paragraph extraction to avoid getting junk text between divs
        paragraphs = root.find_all('p')
        if paragraphs:
            parts = [p.get_text(separator=' ', strip=True) for p in paragraphs if p.get_text(strip=True)]
        else:
            # Fallback to whole text if no paragraphs found
            parts = [root.get_text(separator='\n', strip=True)]

        return clean_text('\n'.join(parts), max_len=max_len)
    except Exception as e:
        logger.error(f"Error extracting text from HTML: {e}")
        return ""
