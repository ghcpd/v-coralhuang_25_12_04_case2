"""Simple caching utilities (placeholder).

This module will be extended with LRU caching, invalidation, and metrics.
"""
from typing import Any, Dict


class SimpleCache:
    def __init__(self):
        self._data: Dict[str, Any] = {}

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        self._data[key] = value

    def clear(self):
        self._data.clear()
