from __future__ import annotations
import re
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Final

logger = logging.getLogger(__name__)

# Vietnam UTC offset
_VN_UTC_OFFSET: Final[int] = 7
_VN_TZ: Final[timezone] = timezone(timedelta(hours=_VN_UTC_OFFSET))

# Common absolute date/time formats encountered on Vietnamese news sites
_ABSOLUTE_FORMATS: Final[List[str]] = [
    '%d/%m/%Y %H:%M',           # 25/12/2023 14:30
    '%d/%m/%Y, %H:%M',          # 25/12/2023, 14:30
    '%d/%m/%Y - %H:%M',         # 25/12/2023 - 14:30
    '%d-%m-%Y %H:%M',           # 25-12-2023 14:30
    '%d/%m/%Y',                  # 25/12/2023
    '%Y-%m-%dT%H:%M:%S',        # ISO 2023-12-25T14:30:00
    '%Y-%m-%dT%H:%M:%S%z',      # ISO with tz
    '%H:%M %d/%m/%Y',           # 14:30 25/12/2023
    '%Y-%m-%d %H:%M:%S',        # 2023-12-25 14:30:00
    '%Y-%m-%d %H:%M',           # 2023-12-25 14:30
    '%Y-%m-%d',                  # 2023-12-25
]

# Regex patterns for stripping metadata from date strings
# "Thứ X, dd/mm/yyyy, HH:MM" – strip the day-of-week prefix first
_DOW_PREFIX: Final[re.Pattern] = re.compile(
    r'^(thứ\s+\w+,?\s*|chủ\s+nhật,?\s*)',
    re.IGNORECASE | re.UNICODE,
)

# Timezone suffixes like "(GMT+7)", "GMT+7", "(UTC+7)", "(UTC+07:00)" at end of string
_TZ_SUFFIX: Final[re.Pattern] = re.compile(
    r'\s*\(?\s*(?:GMT|UTC)\s*[+-]\s*\d{1,2}(?::\d{2})?\s*\)?\s*$',
    re.IGNORECASE,
)


def normalize_text(text: str) -> str:
    """Normalize text by collapsing extra whitespace and stripping margins."""
    if not text:
        return ''
    return re.sub(r'\s+', ' ', text).strip()


def parse_time(time_str: str) -> Optional[str]:
    """
    Parse a Vietnamese news date/time string and return an ISO-formatted
    string ``"YYYY-MM-DD HH:MM:SS"`` in Vietnam local time.
    Supports both relative (e.g., '5 phút trước') and absolute formats.
    """
    if not time_str:
        return None

    raw = time_str.strip()
    lower = raw.lower()

    # --- 1. Relative expressions ---
    now = datetime.now(_VN_TZ)

    if 'giờ trước' in lower or 'tiếng trước' in lower:
        m = re.search(r'(\d+)', lower)
        if m:
            dt = now - timedelta(hours=int(m.group(1)))
            return dt.strftime('%Y-%m-%d %H:%M:%S')

    if 'phút trước' in lower:
        m = re.search(r'(\d+)', lower)
        if m:
            dt = now - timedelta(minutes=int(m.group(1)))
            return dt.strftime('%Y-%m-%d %H:%M:%S')

    if 'ngày trước' in lower:
        m = re.search(r'(\d+)', lower)
        if m:
            dt = now - timedelta(days=int(m.group(1)))
            return dt.strftime('%Y-%m-%d %H:%M:%S')

    if 'hôm qua' in lower:
        dt = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0)
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    if 'hôm nay' in lower:
        # Extract HH:MM if present, otherwise use start of day
        m = re.search(r'(\d{1,2}):(\d{2})', lower)
        if m:
            dt = now.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0)
        else:
            dt = now.replace(hour=0, minute=0, second=0)
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    # --- 2. Absolute expressions ---
    # Strip day-of-week and timezone info to simplify parsing
    cleaned = _DOW_PREFIX.sub('', raw).strip().lstrip(',').strip()
    cleaned = _TZ_SUFFIX.sub('', cleaned).strip().rstrip(',').strip()

    for fmt in _ABSOLUTE_FORMATS:
        try:
            dt = datetime.strptime(cleaned, fmt)
            # If the format doesn't have tz info, assume it's VN local time
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=_VN_TZ)
            else:
                dt = dt.astimezone(_VN_TZ)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue

    logger.warning(f"parse_time: unable to parse raw string: {time_str!r} (cleaned: {cleaned!r})")
    return None