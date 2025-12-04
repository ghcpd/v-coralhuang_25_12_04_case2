"""
todo_advanced.py

Compatibility wrapper and entry point for the Advanced Tag System.
This initial version preserves the public API from todo_original.py while
providing hooks for the new persistent/tagging implementation.

The intent is to keep the same function signatures and behavior as the
original module so callers don't break. Later commits will implement the
full feature set inside the `todo_advanced` package.
"""
from typing import List, Optional, Dict
import os

# Try to use the original in-memory module as the baseline implementation
try:
    from todo_original import (
        add_todo as _orig_add_todo,
        list_todos as _orig_list_todos,
        filter_by_tags as _orig_filter_by_tags,
        add_tag_to_task as _orig_add_tag_to_task,
        remove_tag_from_task as _orig_remove_tag_from_task,
        show_tag_stats as _orig_show_tag_stats,
        list_all_tags as _orig_list_all_tags,
        complete_task as _orig_complete_task,
    )
except Exception:
    # Fallback: simple in-module reimplementation (shouldn't happen in tests)
    from todo_original import *  # type: ignore

# The advanced system will live in the `advanced` package; import lazily if present
_ADV_PACKAGE_AVAILABLE = False
try:
    import todo_advanced_pkg  # placeholder for the advanced package
    _ADV_PACKAGE_AVAILABLE = True
except Exception:
    _ADV_PACKAGE_AVAILABLE = False

# Public API (kept exactly as original)

def add_todo(task: str, tags: Optional[List[str]] = None) -> None:
    """Add a task with optional string tags. Backwards-compatible facade."""
    backend = get_backend()
    if backend is not None:
        return backend.add_todo(task, tags)
    return _orig_add_todo(task, tags)


def list_todos() -> List[Dict]:
    """Return all tasks in their current form."""
    backend = get_backend()
    if backend is not None:
        return backend.list_todos()
    return _orig_list_todos()


def filter_by_tags(tags: List[str], match_all: bool = False) -> List[Dict]:
    """Filter tasks by plain string tags. Preserves previous semantics."""
    backend = get_backend()
    if backend is not None:
        return backend.filter_by_tags(tags, match_all=match_all)
    return _orig_filter_by_tags(tags, match_all=match_all)


def add_tag_to_task(index: int, tag: str) -> None:
    """Append a single string tag to a task by index."""
    backend = get_backend()
    if backend is not None:
        return backend.add_tag_to_task(index, tag)
    return _orig_add_tag_to_task(index, tag)


def remove_tag_from_task(index: int, tag: str) -> None:
    """Remove a tag from a task."""
    backend = get_backend()
    if backend is not None:
        return backend.remove_tag_from_task(index, tag)
    return _orig_remove_tag_from_task(index, tag)


def show_tag_stats() -> Dict[str, int]:
    """Return a dict of tag -> count."""
    backend = get_backend()
    if backend is not None:
        return backend.show_tag_stats()
    return _orig_show_tag_stats()


def list_all_tags() -> List[str]:
    """Return all distinct string tags."""
    backend = get_backend()
    if backend is not None:
        return backend.list_all_tags()
    return _orig_list_all_tags()


def complete_task(index: int) -> None:
    """Mark a task as completed."""
    backend = get_backend()
    if backend is not None:
        return backend.complete_task(index)
    return _orig_complete_task(index)


# Placeholder for programmatic access to advanced system components. Tests and
# future implementation can import `todo_advanced.get_backend()` to access
# the advanced storage and tag manager once available.
def get_backend():
    if _ADV_PACKAGE_AVAILABLE:
        return todo_advanced_pkg.get_backend()
    return None
