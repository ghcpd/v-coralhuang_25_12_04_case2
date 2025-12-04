"""Advanced TODO package: storage, tags, query language, plugins, CLI.

This package provides a modern tag system built on SQLite and a
modular architecture. The top-level wrapper `../todo_advanced.py` exposes
an easy-to-use API while keeping `todo_original.py` unchanged.
"""

from todo_advanced_pkg.api import TodoAdvanced

# Provide an API-compatible wrapper at package import-time so calling
# `import todo_advanced` yields functions similar to the original API.
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


def get_global():
	return _global

__all__ = [
	"TodoAdvanced",
	"add_todo",
	"list_todos",
	"filter_by_tags",
	"add_tag_to_task",
	"remove_tag_from_task",
	"show_tag_stats",
	"list_all_tags",
	"complete_task",
	"get_global",
]
