"""Top-level compatibility wrapper for the advanced TODO system.

This module exposes functions matching the original `todo_original.py` API
while also providing access to advanced features via a `global_todo` instance.
"""
from todo_advanced_pkg.api import TodoAdvanced

# default in-memory global instance
_global = TodoAdvanced(":memory:")


def add_todo(task: str, tags=None):
    return _global.add_todo(task, tags)


def list_todos():
    return _global.list_todos()


def filter_by_tags(tags, match_all=False):
    return _global.filter_by_tags(tags, match_all)


def add_tag_to_task(index: int, tag: str):
    return _global.add_tag_to_task(index, tag)


def remove_tag_from_task(index: int, tag: str):
    return _global.remove_tag_from_task(index, tag)


def show_tag_stats():
    return _global.show_tag_stats()


def list_all_tags():
    return _global.list_all_tags()


def complete_task(index: int):
    return _global.complete_task(index)


# Advanced access
def get_global():
    return _global
