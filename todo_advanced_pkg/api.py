from typing import List, Dict, Optional
from .storage import SQLiteStorage
from .models import Tag, Task
from .plugin_manager import PluginManager
from . import query
import time


class TodoAdvanced:
    def __init__(self, db_path: str = ":memory:"):
        self.storage = SQLiteStorage(db_path)
        self.plugins = PluginManager()

    # Backwards-compatible API (mirrors todo_original.py behavior)
    def add_todo(self, task: str, tags: Optional[List[str]] = None) -> None:
        t = self.storage.add_task(task, tags)
        try:
            self.plugins.call_hook("on_task_added", t.to_dict())
        except Exception:
            pass

    def list_todos(self) -> List[Dict]:
        tasks = self.storage.list_tasks()
        # preserve legacy fields: task, completed, tags
        return [t.to_dict() for t in tasks]

    def filter_by_tags(self, tags: List[str], match_all: bool = False) -> List[Dict]:
        # Keep semantics: OR or AND matching against tag list
        all_tasks = self.list_todos()
        if not tags:
            return list(all_tasks)
        filtered = []
        for t in all_tasks:
            item_tags = t.get("tags", [])
            if match_all:
                if all(tag in item_tags for tag in tags):
                    filtered.append(t)
            else:
                if any(tag in item_tags for tag in tags):
                    filtered.append(t)
        return filtered

    def add_tag_to_task(self, index: int, tag: str) -> None:
        tasks = self.list_todos()
        if index < 0 or index >= len(tasks):
            raise IndexError("task index out of range")
        t = tasks[index]
        if tag not in t["tags"]:
            t["tags"].append(tag)
            # persist update by creating/updating a real tag and re-writing task row
            # naive persistence: add a new task with updated tags in DB and delete old one is not desirable
            # Instead, update the DB directly using storage
            # find task id via storage listing
            storage_tasks = self.storage.list_tasks()
            sid = storage_tasks[index].id
            # write back
            now = time.time()
            cur = self.storage._conn.cursor()
            cur.execute("UPDATE tasks SET tags = ?, updated_at = ? WHERE id = ?", (str(__import__('json').dumps(t['tags'])), now, sid))
            self.storage._conn.commit()
            # update tag metadata
            tag_obj = self.storage.get_tag(tag) or Tag(name=tag)
            tag_obj.usage_count += 1
            tag_obj.updated_at = time.time()
            self.storage.add_or_update_tag(tag_obj)
            self.plugins.call_hook("on_tag_added", tag, t)

    def remove_tag_from_task(self, index: int, tag: str) -> None:
        tasks = self.list_todos()
        if index < 0 or index >= len(tasks):
            raise IndexError("task index out of range")
        t = tasks[index]
        if tag in t["tags"]:
            t["tags"].remove(tag)
            storage_tasks = self.storage.list_tasks()
            sid = storage_tasks[index].id
            now = time.time()
            cur = self.storage._conn.cursor()
            cur.execute("UPDATE tasks SET tags = ?, updated_at = ? WHERE id = ?", (str(__import__('json').dumps(t['tags'])), now, sid))
            self.storage._conn.commit()

    def show_tag_stats(self) -> Dict[str, int]:
        tags = self.storage.list_tags()
        return {t.name: t.usage_count for t in tags}

    def list_all_tags(self) -> List[str]:
        tags = self.storage.list_tags()
        return sorted([t.name for t in tags])

    def complete_task(self, index: int) -> None:
        tasks = self.storage.list_tasks()
        if index < 0 or index >= len(tasks):
            raise IndexError("task index out of range")
        tid = tasks[index].id
        self.storage.complete_task(tid)
        self.plugins.call_hook("on_task_completed", tid)

    # Advanced: DSL query
    def query(self, dsl_expr: str, scored: bool = False) -> List[Dict]:
        tasks = self.list_todos()
        return query.filter_tasks(tasks, dsl_expr, scored=scored)

    # --- Structured tag utilities ---------------------------------------
    def create_or_update_tag(self, name: str, aliases=None, color=None, description=None) -> None:
        aliases = aliases or []
        now = time.time()
        tg = self.storage.get_tag(name) or Tag(name=name)
        tg.aliases = list(sorted(set(tg.aliases + list(aliases))))
        tg.color = color or tg.color
        tg.description = description or tg.description
        tg.updated_at = now
        if not getattr(tg, "created_at", None):
            tg.created_at = now
        self.storage.add_or_update_tag(tg)

    def get_tag_info(self, name: str) -> Optional[Dict]:
        tg = self.storage.get_tag(name)
        if not tg:
            return None
        return tg.to_dict()

    def get_cooccurrence(self, tag: str, limit: int = 10):
        return self.storage.get_cooccurrence(tag, limit)

