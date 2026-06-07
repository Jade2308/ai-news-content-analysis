"""
processing/clean_text.py - Content cleaning utilities.

Removes noise from crawled Vietnamese news articles:
  - Script/style/nav/footer tags from raw HTML.
  - Vietnamese boilerplate phrases.
  - Advertisements and social prompts.
  - Excessive whitespace.
"""
from __future__ import annotations

import re
from typing import Optional

from bs4 import BeautifulSoup


_NOISE_PHRASES = [
    # Related article patterns.
    r'b\u00e0i li\u00ean quan[:\s]*',
    r'tin li\u00ean quan[:\s]*',
    r'xem th\u00eam[:\s]*',
    r'\u0111\u1ecdc th\u00eam[:\s]*',
    r'\u0111\u1ecdc ti\u1ebfp[:\s]*',
    r'xem ti\u1ebfp[:\s]*',
    r'c\u00f3 th\u1ec3 b\u1ea1n quan t\u00e2m[:\s]*',
    r'tin c\u00f9ng chuy\u00ean m\u1ee5c[:\s]*',
    r'video li\u00ean quan[:\s]*',
    # Social / sharing prompts.
    r'chia s\u1ebb b\u00e0i vi\u1ebft[:\s]*',
    r'theo d\u00f5i[:\s]+\w+\s+tr\u00ean',
    # Advertisement markers.
    r'\[qu\u1ea3ng c\u00e1o\]',
    r'\(qu\u1ea3ng c\u00e1o\)',
    r'advertisement',
    # Common VNExpress / Tuoi Tre noise.
    r'vnexpress\.net',
    r'tuoitre\.vn',
    # Comment / interaction prompts.
    r'g\u1eedi b\u00ecnh lu\u1eadn',
    r'vi\u1ebft b\u00ecnh lu\u1eadn',
    r'\u0111\u00e1nh gi\u00e1 b\u00e0i vi\u1ebft',
]

_NOISE_RE = re.compile(
    '|'.join(_NOISE_PHRASES),
    re.IGNORECASE | re.UNICODE,
)

_STRIP_TAGS = {
    'script', 'style', 'nav', 'footer', 'header', 'aside',
    'figure', 'figcaption', 'iframe', 'form', 'noscript',
    'ins',
}

_AD_CLASS_PATTERNS = re.compile(
    r'(advert|advertisement|banner|promo|related|suggest|sidebar|widget|social|share)',
    re.IGNORECASE,
)

DEFAULT_MAX_LEN = 0


def strip_html_noise(html: str) -> BeautifulSoup:
    """Parse raw HTML and remove noise elements."""
    soup = BeautifulSoup(html, 'lxml')

    for tag in _STRIP_TAGS:
        for elem in soup.find_all(tag):
            elem.decompose()

    for elem in soup.find_all(True):
        attrs = elem.attrs if isinstance(getattr(elem, 'attrs', None), dict) else {}

        classes_raw = attrs.get('class') or []
        if isinstance(classes_raw, (list, tuple, set)):
            classes = ' '.join(str(c) for c in classes_raw)
        else:
            classes = str(classes_raw)

        elem_id = str(attrs.get('id') or '')
        if _AD_CLASS_PATTERNS.search(classes) or _AD_CLASS_PATTERNS.search(elem_id):
            elem.decompose()

    return soup


def clean_text(text: str, max_len: int = DEFAULT_MAX_LEN) -> str:
    """Clean plain text extracted from an article."""
    if not text:
        return ''

    text = _NOISE_RE.sub(' ', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    if max_len and len(text) > max_len:
        truncated = text[:max_len]
        last_space = truncated.rfind(' ')
        if last_space > max_len // 2:
            truncated = truncated[:last_space]
        text = truncated

    return text


def extract_text_from_html(
    html: str,
    content_selector: Optional[str] = None,
    max_len: int = DEFAULT_MAX_LEN,
) -> str:
    """Strip HTML noise, extract article text, and clean it."""
    soup = strip_html_noise(html)

    root = soup
    if content_selector:
        found = soup.select_one(content_selector)
        if found:
            root = found

    paragraphs = root.find_all('p')
    if paragraphs:
        parts = [p.get_text(separator=' ') for p in paragraphs]
    else:
        parts = [root.get_text(separator='\n')]

    raw_text = '\n'.join(parts)
    return clean_text(raw_text, max_len=max_len)
