from __future__ import annotations
import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

@dataclass
class Article:
    """Standardized article data container with hashing for ID & fingerprint."""
    url: str
    source: str  # 'vnexpress' | 'tuoitre'
    category: str
    title: str
    summary: Optional[str] = None
    content_text: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    published_at: Optional[str] = None
    crawled_at: Optional[str] = None
    content_html_raw: Optional[str] = None
    thumbnail_url: Optional[str] = None
    fingerprint: Optional[str] = None
    article_id: str = field(init=False)

    def __post_init__(self) -> None:
        # Generate stable unique ID based on URL
        self.article_id = hashlib.sha1(self.url.encode('utf-8')).hexdigest()
        
        # Generate content fingerprint if text is available and FP not provided
        if not self.fingerprint and self.content_text:
            # Simple normalization for fingerprinting
            text_norm = "".join(self.content_text.split()).lower()
            self.fingerprint = hashlib.sha1(text_norm.encode('utf-8')).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary suitable for database insertion/JSON."""
        data = asdict(self)
        # Convert tags list to comma-separated string for DB storage
        if isinstance(data.get('tags'), list):
            data['tags'] = ",".join(data['tags'])
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Article:
        """Hydrate an Article instance from a dictionary (e.g., from DB or API)."""
        # Handle tags string conversion back to list
        if 'tags' in data and isinstance(data['tags'], str):
            data['tags'] = [t.strip() for t in data['tags'].split(',') if t.strip()]
        
        # Extract only known fields to avoid TypeError on extra keys
        field_names = {f.name for f in cls.__dataclass_fields__.values() if f.init}
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        
        return cls(**filtered_data)
