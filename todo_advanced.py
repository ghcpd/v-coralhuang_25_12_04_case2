"""
todo_advanced.py

Backward-compatible advanced TODO system. This module exposes the same
public API as todo_original.py but with persistent storage, advanced
tag features, and a plugin system.

Usage:
    import todo_advanced as todo
    
    # Use exactly like todo_original.py
    todo.add_todo("Buy groceries", tags=["shopping", "urgent"])
    print(todo.list_todos())
    print(todo.filter_by_tags(["urgent"]))
    
    # Or use advanced features
    from todo_advanced import TodoAdvanced
    advanced = TodoAdvanced(db_path="my_todos.db")
    results = advanced.query("tag:work AND (urgent OR personal)")
    recommendations = advanced.recommend_tags_for_task("Fix bug in parser")
"""

from todo_advanced.api import (
    TodoAdvanced,
    add_todo,
    list_todos,
    filter_by_tags,
    add_tag_to_task,
    remove_tag_from_task,
    complete_task,
    show_tag_stats,
    list_all_tags,
)

__all__ = [
    "TodoAdvanced",
    "add_todo",
    "list_todos",
    "filter_by_tags",
    "add_tag_to_task",
    "remove_tag_from_task",
    "complete_task",
    "show_tag_stats",
    "list_all_tags",
]
