"""
Backward-compatible wrapper module providing advanced tag system API while preserving original function names.
"""
from todo_advanced.api import add_todo, list_todos, filter_by_tags, add_tag_to_task, remove_tag_from_task, show_tag_stats, list_all_tags, complete_task

__all__ = [
    'add_todo', 'list_todos', 'filter_by_tags', 'add_tag_to_task', 'remove_tag_from_task',
    'show_tag_stats', 'list_all_tags', 'complete_task'
]
