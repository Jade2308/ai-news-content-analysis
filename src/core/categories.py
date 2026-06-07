# src/core/categories.py
"""
Standard category mapping and normalization logic.

This unifies category classifications from different newspapers into one
taxonomy for the dashboard and query filters.
"""

# Map raw category slugs to unified category IDs.
CATEGORY_MAP = {
    # Current affairs and politics
    'thoi-su': 'thoi-su',
    'chinh-tri': 'thoi-su',
    'tuan-viet-nam': 'thoi-su',
    'net-zero': 'thoi-su',
    'vne-go': 'thoi-su',

    # World
    'the-gioi': 'the-gioi',

    # Business and real estate
    'bat-dong-san': 'kinh-doanh-bds',
    'nha-dat': 'kinh-doanh-bds',
    'gia-that': 'kinh-doanh-bds',

    # Law
    'phap-luat': 'phap-luat',

    # Science and technology
    'khoa-hoc-cong-nghe': 'khoa-hoc-cong-nghe',
    'cong-nghe': 'khoa-hoc-cong-nghe',

    # Sports
    'the-thao': 'the-thao',
    'bong-da': 'the-thao',

    # Entertainment and culture
    'giai-tri': 'giai-tri-van-hoa',
    'van-hoa': 'giai-tri-van-hoa',
    'thu-gian': 'giai-tri-van-hoa',

    # Education
    'giao-duc': 'giao-duc',

    # Health
    'suc-khoe': 'suc-khoe',

    # Travel
    'du-lich': 'du-lich',

    # Automotive
    'xe': 'xe',

    # Lifestyle and readers
    'doi-song': 'doi-song-ban-doc',
    'nhip-song-tre': 'doi-song-ban-doc',
    'tam-su': 'doi-song-ban-doc',
    'ban-doc': 'doi-song-ban-doc',
    'goc-nhin': 'doi-song-ban-doc',
    'y-kien': 'doi-song-ban-doc',
}


UNIFIED_CATEGORIES = {
    'thoi-su': {
        'label': 'Current Affairs & Politics',
        'icon': '',
    },
    'the-gioi': {
        'label': 'World',
        'icon': '',
    },
    'kinh-doanh-bds': {
        'label': 'Business & Real Estate',
        'icon': '',
    },
    'phap-luat': {
        'label': 'Law',
        'icon': '',
    },
    'khoa-hoc-cong-nghe': {
        'label': 'Science & Technology',
        'icon': '',
    },
    'the-thao': {
        'label': 'Sports',
        'icon': '',
    },
    'giai-tri-van-hoa': {
        'label': 'Entertainment & Culture',
        'icon': '',
    },
    'giao-duc': {
        'label': 'Education',
        'icon': '',
    },
    'suc-khoe': {
        'label': 'Health',
        'icon': '',
    },
    'doi-song-ban-doc': {
        'label': 'Lifestyle & Readers',
        'icon': '',
    },
    'du-lich': {
        'label': 'Travel',
        'icon': '',
    },
    'xe': {
        'label': 'Automotive',
        'icon': '',
    },
    'khac': {
        'label': 'Other',
        'icon': '',
    },
}


def get_unified_category(raw_category: str) -> str:
    """Return the unified category ID for a raw category slug."""
    if not raw_category:
        return 'khac'
    raw_clean = str(raw_category).strip().lower()
    if raw_clean in UNIFIED_CATEGORIES:
        return raw_clean
    return CATEGORY_MAP.get(raw_clean, 'khac')


def get_category_display_name(category_id: str) -> str:
    """Return the English display name for a unified category."""
    return UNIFIED_CATEGORIES.get(category_id, {}).get('label', 'Other')


def get_category_icon(category_id: str) -> str:
    """Return an optional category icon prefix."""
    return UNIFIED_CATEGORIES.get(category_id, {}).get('icon', '')


def get_raw_categories_for_unified(unified_id: str) -> list[str]:
    """Return raw category slugs that map to a unified category."""
    if unified_id == 'khac':
        return []
    cats = [unified_id]
    for raw, mapped in CATEGORY_MAP.items():
        if mapped == unified_id and raw != unified_id:
            cats.append(raw)
    return cats
