"""Compatibility wrapper that exposes the original public API
and delegates to the new advanced backend located in
`todo_advanced_pkg` while preserving behavior and signatures.

This wrapper keeps `todo_original.py` intact and allows callers
to switch to the advanced system without changing their code.
"""
from typing import List, Dict, Optional

from todo_advanced_pkg.storage import AdvancedStorage

# Lazily create a single storage instance so behavior resembles
# the original module-level in-memory list.
_storage: Optional[AdvancedStorage] = None


def _get_storage() -> AdvancedStorage:
    global _storage
    if _storage is None:
        _storage = AdvancedStorage()
    return _storage


def add_todo(task: str, tags: Optional[List[str]] = None) -> None:
    """Add a task with optional string tags (backwards compatible)."""
    get = _get_storage()
    get.add_task(task, tags or [])


def list_todos() -> List[Dict]:
    """Return all tasks in their current form (backwards compatible)."""
    return _get_storage().list_tasks()


def filter_by_tags(tags: List[str], match_all: bool = False) -> List[Dict]:
    """Filter tasks by plain string tags (OR/AND)."""
    return _get_storage().filter_tasks_by_tags(tags, match_all=match_all)


def add_tag_to_task(index: int, tag: str) -> None:
    """Append a single string tag to a task by index."""
    return _get_storage().add_tag_to_task(index, tag)


def remove_tag_from_task(index: int, tag: str) -> None:
    """Remove a tag from a task."""
    return _get_storage().remove_tag_from_task(index, tag)


def show_tag_stats() -> Dict[str, int]:
    """Return a dict of tag -> count."""
    return _get_storage().tag_stats()


def list_all_tags() -> List[str]:
    """Return all distinct string tags."""
    return _get_storage().list_tags()


def complete_task(index: int) -> None:
    """Mark a task as completed."""
    return _get_storage().complete_task(index)
