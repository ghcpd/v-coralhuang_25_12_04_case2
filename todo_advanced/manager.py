"""Core manager orchestrating storage, tags, query, and plugins."""
from __future__ import annotations
from typing import List, Optional

from .storage import SQLiteStorage
from .plugins import plugin_manager
from .query import run_query


class TodoManager:
    def __init__(self, storage: Optional[SQLiteStorage] = None):
        self.storage = storage or SQLiteStorage()

    # Legacy-compatible API facade
    def add_todo(self, task: str, tags: Optional[List[str]] = None) -> None:
        task_id = self.storage.add_task(task, tags=tags)
        plugin_manager.dispatch("on_task_added", task_id=task_id, task=task, tags=tags or [])

    def list_todos(self) -> List[dict]:
        return [t.to_legacy_dict() for t in self.storage.list_tasks()]

    def filter_by_tags(self, tags: List[str], match_all: bool = False) -> List[dict]:
        return [t.to_legacy_dict() for t in self.storage.filter_tasks_by_tags(tags, match_all=match_all)]

    def add_tag_to_task(self, index: int, tag: str) -> None:
        task = self.storage.get_task_by_index(index)
        self.storage.add_tag_to_task(task.id, tag)
        plugin_manager.dispatch("on_tag_added", task_id=task.id, tag=tag)

    def remove_tag_from_task(self, index: int, tag: str) -> None:
        task = self.storage.get_task_by_index(index)
        self.storage.remove_tag_from_task(task.id, tag)

    def complete_task(self, index: int) -> None:
        task = self.storage.get_task_by_index(index)
        self.storage.set_task_completed(task.id, True)
        plugin_manager.dispatch("on_task_completed", task_id=task.id)

    def show_tag_stats(self):
        return self.storage.tag_stats()

    def list_all_tags(self):
        return sorted(self.storage.tag_stats().keys())

    # Advanced APIs
    def suggest_tags(self, text: str, existing_tags: Optional[List[str]] = None, top_n: int = 5):
        return self.storage.suggest_tags(text, existing_tags, top_n)

    def query(self, expr: str):
        return [t.to_legacy_dict() for t in run_query(expr, storage=self.storage)]
