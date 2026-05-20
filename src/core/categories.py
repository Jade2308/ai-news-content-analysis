# src/core/categories.py
"""
Standard category mapping and normalization logic.
This unifies category classifications from different newspapers (VnExpress, Tuoi Tre, VietnamNet)
into a unified taxonomy for the user interface and system queries.
"""

# Map of raw category slug -> Unified category ID
CATEGORY_MAP = {
    # Thời sự - Chính trị
    'thoi-su': 'thoi-su',
    'chinh-tri': 'thoi-su',
    'tuan-viet-nam': 'thoi-su',
    'net-zero': 'thoi-su',
    'vne-go': 'thoi-su',
    
    # Thế giới
    'the-gioi': 'the-gioi',
    
    # Kinh doanh - Bất động sản
    'bat-đong-san': 'kinh-doanh-bds',
    'bat-dong-san': 'kinh-doanh-bds',
    'nha-đat': 'kinh-doanh-bds',
    'nha-dat': 'kinh-doanh-bds',
    'gia-that': 'kinh-doanh-bds',
    
    # Pháp luật
    'phap-luat': 'phap-luat',
    
    # Khoa học - Công nghệ
    'khoa-hoc-cong-nghe': 'khoa-hoc-cong-nghe',
    'cong-nghe': 'khoa-hoc-cong-nghe',
    
    # Thể thao
    'the-thao': 'the-thao',
    
    # Giải trí - Văn hóa
    'giai-tri': 'giai-tri-van-hoa',
    'van-hoa': 'giai-tri-van-hoa',
    'thu-gian': 'giai-tri-van-hoa',
    
    # Giáo dục
    'giao-duc': 'giao-duc',
    
    # Sức khỏe
    'suc-khoe': 'suc-khoe',
    
    # Du lịch
    'du-lich': 'du-lich',
    
    # Xe
    'xe': 'xe',
    
    # Đời sống - Bạn đọc
    'đoi-song': 'doi-song-ban-doc',
    'doi-song': 'doi-song-ban-doc',
    'nhip-song-tre': 'doi-song-ban-doc',
    'tam-su': 'doi-song-ban-doc',
    'ban-đoc': 'doi-song-ban-doc',
    'ban-doc': 'doi-song-ban-doc',
    'goc-nhin': 'doi-song-ban-doc',
    'y-kien': 'doi-song-ban-doc',
}

# Unified categories configuration
UNIFIED_CATEGORIES = {
    'thoi-su': {
        'label': 'Thời sự - Chính trị',
        'icon': '📰',
    },
    'the-gioi': {
        'label': 'Thế giới',
        'icon': '🌐',
    },
    'kinh-doanh-bds': {
        'label': 'Kinh doanh & Bất động sản',
        'icon': '🏢',
    },
    'phap-luat': {
        'label': 'Pháp luật',
        'icon': '⚖️',
    },
    'khoa-hoc-cong-nghe': {
        'label': 'Khoa học & Công nghệ',
        'icon': '💻',
    },
    'the-thao': {
        'label': 'Thể thao',
        'icon': '⚽',
    },
    'giai-tri-van-hoa': {
        'label': 'Giải trí & Văn hóa',
        'icon': '🎭',
    },
    'giao-duc': {
        'label': 'Giáo dục',
        'icon': '🎓',
    },
    'suc-khoe': {
        'label': 'Sức khỏe',
        'icon': '🏥',
    },
    'doi-song-ban-doc': {
        'label': 'Đời sống & Bạn đọc',
        'icon': '👥',
    },
    'du-lich': {
        'label': 'Du lịch',
        'icon': '✈️',
    },
    'xe': {
        'label': 'Xe',
        'icon': '🚗',
    },
    'khac': {
        'label': 'Khác',
        'icon': '📂',
    }
}

def get_unified_category(raw_category: str) -> str:
    """Trả về ID category thống nhất từ category thô."""
    if not raw_category:
        return 'khac'
    raw_clean = str(raw_category).strip().lower()
    if raw_clean in UNIFIED_CATEGORIES:
        return raw_clean
    return CATEGORY_MAP.get(raw_clean, 'khac')


def get_category_display_name(category_id: str) -> str:
    """Trả về tên hiển thị (Tiếng Việt) của category thống nhất."""
    return UNIFIED_CATEGORIES.get(category_id, {}).get('label', 'Khác')

def get_category_icon(category_id: str) -> str:
    """Trả về icon đại diện của category thống nhất."""
    return UNIFIED_CATEGORIES.get(category_id, {}).get('icon', '📂')

def get_raw_categories_for_unified(unified_id: str) -> list[str]:
    """Trả về danh sách các category thô tương ứng với category thống nhất."""
    if unified_id == 'khac':
        return []
    # Khởi tạo với chính ID thống nhất
    cats = [unified_id]
    for raw, mapped in CATEGORY_MAP.items():
        if mapped == unified_id and raw != unified_id:
            cats.append(raw)
    return cats
