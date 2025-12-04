# todo_original.py
# A minimal in-memory TODO system with simple string tags.
# This file intentionally keeps a very small feature set so that
# the advanced tag system can extend it without breaking behavior.

from typing import List, Optional, Dict


# ---------------------------------------------------------------------------
# Internal in-memory storage (baseline behavior)
# ---------------------------------------------------------------------------

_todos: List[Dict] = []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def add_todo(task: str, tags: Optional[List[str]] = None) -> None:
    """Add a task with optional string tags."""
    if tags is None:
        tags = []
    _todos.append({
        "task": task,
        "completed": False,
        "tags": list(tags),
    })


def list_todos() -> List[Dict]:
    """Return all tasks in their current form."""
    return list(_todos)


def filter_by_tags(tags: List[str], match_all: bool = False) -> List[Dict]:
    """
    Filter tasks by plain string tags.
    - match_all=False: OR logic
    - match_all=True:  AND logic
    """
    if not tags:
        return list(_todos)

    filtered = []
    for item in _todos:
        item_tags = item.get("tags", [])
        if match_all:
            if all(tag in item_tags for tag in tags):
                filtered.append(item)
        else:
            if any(tag in item_tags for tag in tags):
                filtered.append(item)
    return filtered


def add_tag_to_task(index: int, tag: str) -> None:
    """Append a single string tag to a task by index."""
    if index < 0 or index >= len(_todos):
        raise IndexError("task index out of range")
    if tag not in _todos[index]["tags"]:
        _todos[index]["tags"].append(tag)


def remove_tag_from_task(index: int, tag: str) -> None:
    """Remove a tag from a task."""
    if index < 0 or index >= len(_todos):
        raise IndexError("task index out of range")
    if tag in _todos[index]["tags"]:
        _todos[index]["tags"].remove(tag)


def show_tag_stats() -> Dict[str, int]:
    """Return a dict of tag -> count."""
    stats = {}
    for item in _todos:
        for tag in item.get("tags", []):
            stats[tag] = stats.get(tag, 0) + 1
    return stats


def list_all_tags() -> List[str]:
    """Return all distinct string tags."""
    result = set()
    for item in _todos:
        for tag in item.get("tags", []):
            result.add(tag)
    return sorted(result)


# ---------------------------------------------------------------------------
# Convenience API for demonstration (not required)
# ---------------------------------------------------------------------------

def complete_task(index: int) -> None:
    """Mark a task as completed. (Included for realism but not required.)"""
    if index < 0 or index >= len(_todos):
        raise IndexError("task index out of range")
    _todos[index]["completed"] = True
