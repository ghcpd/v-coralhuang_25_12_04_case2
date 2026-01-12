"""
Advanced TODO API - backward compatible wrapper for todo_original.py

This module provides the same public API as todo_original.py while adding
persistent storage, advanced tag features, and a plugin system.
"""

import uuid
from typing import Dict, List, Optional

from .query_engine import QueryEngine
from .recommender import TagRecommender
from .storage import SQLiteStorage
from .tag_model import Tag, TagManager
from .plugin_manager import PluginManager


class TodoAdvanced:
    """Advanced TODO system with persistent storage and tag management."""

    def __init__(self, db_path: str = "todo_advanced.db", plugin_dir: Optional[str] = None):
        """Initialize advanced TODO system."""
        self.storage = SQLiteStorage(db_path)
        self.tag_manager = TagManager(self.storage)
        self.query_engine = QueryEngine(self.tag_manager)
        self.recommender = TagRecommender(self.tag_manager)
        self.plugin_manager = PluginManager(plugin_dir)
        if plugin_dir:
            self.plugin_manager.load_plugins_from_directory(plugin_dir)
        self._tasks = []
        self._load_tasks()

    def _load_tasks(self) -> None:
        """Load tasks from storage."""
        self._tasks = self.storage.list_tasks()

    def add_todo(self, task: str, tags: Optional[List[str]] = None) -> str:
        """
        Add a task with optional tags.
        Returns the task ID.
        """
        if tags is None:
            tags = []

        task_id = str(uuid.uuid4())
        task_data = {
            "id": task_id,
            "task": task,
            "completed": False,
            "tags": tags,
        }

        self.storage.save_task(task_id, task_data)
        self._tasks.append(task_data)

        # Create/update tags in tag manager
        for tag_name in tags:
            tag = self.tag_manager.get_tag(tag_name)
            if not tag:
                tag = self.tag_manager.create_tag(tag_name)
            self.tag_manager.record_usage(tag_name)

        # Record co-occurrence
        if len(tags) > 1:
            self.tag_manager.record_cooccurrence(tags)

        # Trigger hook
        self.plugin_manager.trigger_hook("on_task_added", task_id=task_id, task=task, tags=tags)

        return task_id

    def list_todos(self) -> List[Dict]:
        """Return all tasks (backward compatible)."""
        return list(self._tasks)

    def filter_by_tags(
        self, tags: List[str], match_all: bool = False
    ) -> List[Dict]:
        """
        Filter tasks by tags (backward compatible).
        - match_all=False: OR logic
        - match_all=True: AND logic
        """
        if not tags:
            return list(self._tasks)

        filtered = []
        for item in self._tasks:
            item_tags = item.get("tags", [])
            if match_all:
                if all(tag in item_tags for tag in tags):
                    filtered.append(item)
            else:
                if any(tag in item_tags for tag in tags):
                    filtered.append(item)
        return filtered

    def add_tag_to_task(self, task_id: str, tag: str) -> None:
        """Add a tag to a task."""
        for item in self._tasks:
            if item.get("id") == task_id:
                if tag not in item.get("tags", []):
                    item["tags"].append(tag)
                    self.storage.save_task(task_id, item)
                    # Ensure tag exists
                    t = self.tag_manager.get_tag(tag)
                    if not t:
                        self.tag_manager.create_tag(tag)
                    self.tag_manager.record_usage(tag)
                break

    def remove_tag_from_task(self, task_id: str, tag: str) -> None:
        """Remove a tag from a task."""
        for item in self._tasks:
            if item.get("id") == task_id:
                if tag in item.get("tags", []):
                    item["tags"].remove(tag)
                    self.storage.save_task(task_id, item)
                break

    def complete_task(self, task_id: str) -> None:
        """Mark a task as completed."""
        for item in self._tasks:
            if item.get("id") == task_id:
                item["completed"] = True
                self.storage.save_task(task_id, item)
                self.plugin_manager.trigger_hook("on_task_completed", task_id=task_id)
                break

    def show_tag_stats(self) -> Dict[str, int]:
        """Return tag usage statistics."""
        stats = {}
        for item in self._tasks:
            for tag in item.get("tags", []):
                stats[tag] = stats.get(tag, 0) + 1
        return stats

    def list_all_tags(self) -> List[str]:
        """Return all distinct tags."""
        result = set()
        for item in self._tasks:
            for tag in item.get("tags", []):
                result.add(tag)
        return sorted(result)

    # Advanced features

    def query(self, expression: str) -> List[Dict]:
        """
        Find tasks using DSL query.
        Example: "tag:work AND (urgent OR personal) AND NOT archived"
        """
        matching, error = self.query_engine.find_tasks(self._tasks, expression)
        if error:
            raise ValueError(f"Query error: {error}")
        return matching

    def recommend_tags_for_task(
        self, task: str, existing_tags: Optional[List[str]] = None, top_n: int = 3
    ) -> List[tuple]:
        """Recommend tags for a task."""
        if existing_tags is None:
            existing_tags = []
        return self.recommender.recommend_for_task(task, existing_tags, top_n)

    def get_tag_info(self, tag_name: str) -> Optional[Dict]:
        """Get detailed tag information."""
        tag = self.tag_manager.get_tag(tag_name)
        return tag.to_dict() if tag else None

    def create_tag_with_metadata(
        self,
        name: str,
        color: Optional[str] = None,
        description: Optional[str] = None,
        aliases: Optional[List[str]] = None,
    ) -> Tag:
        """Create a tag with metadata."""
        return self.tag_manager.create_tag(name, color, description, aliases)

    def close(self) -> None:
        """Close the system."""
        self.storage.close()


# Module-level API for backward compatibility with todo_original.py

_instance: Optional[TodoAdvanced] = None


def _ensure_instance() -> TodoAdvanced:
    """Ensure a default instance exists."""
    global _instance
    if _instance is None:
        _instance = TodoAdvanced()
    return _instance


def add_todo(task: str, tags: Optional[List[str]] = None) -> None:
    """Add a task with optional tags (backward compatible)."""
    _ensure_instance().add_todo(task, tags)


def list_todos() -> List[Dict]:
    """Return all tasks (backward compatible)."""
    return _ensure_instance().list_todos()


def filter_by_tags(tags: List[str], match_all: bool = False) -> List[Dict]:
    """Filter tasks by tags (backward compatible)."""
    return _ensure_instance().filter_by_tags(tags, match_all)


def add_tag_to_task(index: int, tag: str) -> None:
    """Add a tag to a task by index (backward compatible)."""
    tasks = _ensure_instance().list_todos()
    if 0 <= index < len(tasks):
        task_id = tasks[index].get("id")
        if task_id:
            _ensure_instance().add_tag_to_task(task_id, tag)
    else:
        raise IndexError("task index out of range")


def remove_tag_from_task(index: int, tag: str) -> None:
    """Remove a tag from a task by index (backward compatible)."""
    tasks = _ensure_instance().list_todos()
    if 0 <= index < len(tasks):
        task_id = tasks[index].get("id")
        if task_id:
            _ensure_instance().remove_tag_from_task(task_id, tag)
    else:
        raise IndexError("task index out of range")


def complete_task(index: int) -> None:
    """Mark a task as completed by index (backward compatible)."""
    tasks = _ensure_instance().list_todos()
    if 0 <= index < len(tasks):
        task_id = tasks[index].get("id")
        if task_id:
            _ensure_instance().complete_task(task_id)
    else:
        raise IndexError("task index out of range")


def show_tag_stats() -> Dict[str, int]:
    """Return tag usage statistics (backward compatible)."""
    return _ensure_instance().show_tag_stats()


def list_all_tags() -> List[str]:
    """Return all distinct tags (backward compatible)."""
    return _ensure_instance().list_all_tags()
