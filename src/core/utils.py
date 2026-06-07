import logging
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

_VN_UTC_OFFSET = 7

_ABSOLUTE_FORMATS = [
    '%d/%m/%Y %H:%M',
    '%d/%m/%Y, %H:%M',
    '%d/%m/%Y - %H:%M',
    '%d-%m-%Y %H:%M',
    '%d/%m/%Y',
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%dT%H:%M:%S%z',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M',
    '%Y-%m-%d',
]

_DOW_PREFIX = re.compile(
    r'^(th\u1ee9\s+\w+,?\s*|ch\u1ee7\s+nh\u1eadt,?\s*)',
    re.IGNORECASE | re.UNICODE,
)

_TZ_SUFFIX = re.compile(
    r'\s*\(?\s*(?:GMT|UTC)\s*[+-]\s*\d{1,2}(?::\d{2})?\s*\)?\s*$',
    re.IGNORECASE,
)


def normalize_text(text: str) -> str:
    """Normalize text by collapsing repeated whitespace."""
    if not text:
        return ''
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_time(time_str: str) -> str | None:
    """
    Parse a Vietnamese news date/time string.

    Returns ``YYYY-MM-DD HH:MM:SS`` in Vietnam local time, or ``None`` if the
    string cannot be interpreted.
    """
    if not time_str:
        return None

    raw = time_str.strip()
    lower = raw.lower()

    now = datetime.utcnow() + timedelta(hours=_VN_UTC_OFFSET)

    if 'gi\u1edd tr\u01b0\u1edbc' in lower or 'ti\u1ebfng tr\u01b0\u1edbc' in lower:
        m = re.search(r'(\d+)', lower)
        if m:
            dt = now - timedelta(hours=int(m.group(1)))
            return dt.strftime('%Y-%m-%d %H:%M:%S')

    if 'ph\u00fat tr\u01b0\u1edbc' in lower:
        m = re.search(r'(\d+)', lower)
        if m:
            dt = now - timedelta(minutes=int(m.group(1)))
            return dt.strftime('%Y-%m-%d %H:%M:%S')

    if 'ng\u00e0y tr\u01b0\u1edbc' in lower:
        m = re.search(r'(\d+)', lower)
        if m:
            dt = now - timedelta(days=int(m.group(1)))
            return dt.strftime('%Y-%m-%d %H:%M:%S')

    if 'h\u00f4m qua' in lower:
        dt = now - timedelta(days=1)
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    if 'h\u00f4m nay' in lower:
        m = re.search(r'(\d{1,2}):(\d{2})', lower)
        if m:
            dt = now.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0)
        else:
            dt = now.replace(hour=0, minute=0, second=0)
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    cleaned = _DOW_PREFIX.sub('', raw).strip().lstrip(',').strip()
    cleaned = _TZ_SUFFIX.sub('', cleaned).strip().rstrip(',').strip()

    for fmt in _ABSOLUTE_FORMATS:
        try:
            dt = datetime.strptime(cleaned, fmt)
            if dt.tzinfo is not None:
                import calendar

                utc_ts = calendar.timegm(dt.utctimetuple())
                dt = datetime.utcfromtimestamp(utc_ts) + timedelta(hours=_VN_UTC_OFFSET)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue

    logger.warning("parse_time: cannot parse %r - returning None", time_str)
    return None
