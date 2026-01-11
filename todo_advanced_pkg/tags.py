"""Tag model helpers (metadata management)."""
from typing import Optional, Dict
import time


def now_ts() -> int:
    return int(time.time())


def make_tag_metadata(name: str, description: Optional[str] = None, color: Optional[str] = None) -> Dict:
    ts = now_ts()
    return {
        "name": name,
        "description": description,
        "color": color,
        "aliases": [],
        "usage_count": 0,
        "created_ts": ts,
        "updated_ts": ts,
    }
