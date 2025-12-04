"""
Advanced Tag System for TODO Application.

A modern, persistent, concurrent-safe tag system that extends the basic TODO list
with structured tags, advanced querying, and a plugin architecture.
"""

__version__ = "1.0.0"

from .storage import StorageBackend, SQLiteStorage
from .tag_model import Tag, TagManager
from .query_engine import QueryEngine
from .recommender import TagRecommender
from .plugin_manager import PluginManager
from .api import TodoAdvanced

__all__ = [
    "StorageBackend",
    "SQLiteStorage",
    "Tag",
    "TagManager",
    "QueryEngine",
    "TagRecommender",
    "PluginManager",
    "TodoAdvanced",
]
