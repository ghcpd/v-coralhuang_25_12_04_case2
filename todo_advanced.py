"""Compatibility API wrapping advanced TODO backend.

This module preserves the original public functions from `todo_original.py`
so existing callers can import `todo_advanced` as a drop-in replacement.
"""
from __future__ import annotations
from typing import List, Optional, Dict

from todo_advanced import TodoManager

_mgr = TodoManager()


def add_todo(task: str, tags: Optional[List[str]] = None) -> None:
    _mgr.add_todo(task, tags)


def list_todos() -> List[Dict]:
    return _mgr.list_todos()


def filter_by_tags(tags: List[str], match_all: bool = False) -> List[Dict]:
    return _mgr.filter_by_tags(tags, match_all=match_all)


def add_tag_to_task(index: int, tag: str) -> None:
    _mgr.add_tag_to_task(index, tag)


def remove_tag_from_task(index: int, tag: str) -> None:
    _mgr.remove_tag_from_task(index, tag)


def show_tag_stats() -> Dict[str, int]:
    return _mgr.show_tag_stats()


def list_all_tags() -> List[str]:
    return _mgr.list_all_tags()


def complete_task(index: int) -> None:
    _mgr.complete_task(index)

# advanced extras
suggest_tags = _mgr.suggest_tags
query = _mgr.query
