"""A small SQLite-backed storage backend with basic schema and concurrency
safeguards. This is an initial implementation meant to be extended.
"""
import sqlite3
import threading
import time
from typing import List, Dict, Optional

# Optional plugin layer
try:
    from . import plugins as _plugins
except Exception:
    _plugins = None


class SqliteBackend:
    def __init__(self, path: str):
        self._path = path
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        # Enable WAL for better concurrency
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        self._lock = threading.RLock()
        self._init_schema()

    def _init_schema(self):
        with self._lock, self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    completed INTEGER NOT NULL DEFAULT 0,
                    created_ts REAL NOT NULL DEFAULT (strftime('%s','now'))
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    color TEXT,
                    usage_count INTEGER NOT NULL DEFAULT 0,
                    created_ts REAL NOT NULL DEFAULT (strftime('%s','now')),
                    updated_ts REAL NOT NULL DEFAULT (strftime('%s','now'))
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_tags (
                    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
                    PRIMARY KEY (task_id, tag_id)
                )
                """
            )

    def add_todo(self, task: str, tags: Optional[List[str]] = None) -> None:
        if tags is None:
            tags = []
        with self._lock, self._conn:
            cur = self._conn.execute(
                "INSERT INTO tasks (task, completed) VALUES (?, 0);",
                (task,)
            )
            task_id = int(cur.lastrowid)
            for tag in tags:
                tag_id = self._ensure_tag(tag)
                self._conn.execute(
                    "INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?);",
                    (task_id, tag_id),
                )
                self._conn.execute(
                    "UPDATE tags SET usage_count = usage_count + 1, updated_ts = strftime('%s','now') WHERE id = ?",
                    (tag_id,)
                )
            # Plugin hook: notify listeners that a task was added
            if _plugins is not None:
                try:
                    for p in _plugins.list_plugins():
                        try:
                            p.on_task_added(task_id, task, tags)
                        except Exception:
                            # Plugin errors must not break core functionality
                            pass
                except Exception:
                    pass

    def _ensure_tag(self, tag_name: str) -> int:
        cur = self._conn.execute(
            "SELECT id FROM tags WHERE name = ?",
            (tag_name,)
        )
        row = cur.fetchone()
        if row:
            return row[0]
        cur = self._conn.execute(
            "INSERT INTO tags (name) VALUES (?)",
            (tag_name,)
        )
        return int(cur.lastrowid)

    def list_todos(self) -> List[Dict]:
        with self._lock, self._conn:
            cur = self._conn.execute("SELECT id, task, completed FROM tasks ORDER BY id ASC")
            tasks = []
            for row in cur.fetchall():
                task_id = row[0]
                tag_cur = self._conn.execute(
                    "SELECT t.name FROM tags t JOIN task_tags tt ON tt.tag_id = t.id WHERE tt.task_id = ? ORDER BY t.name",
                    (task_id,)
                )
                tags = [r[0] for r in tag_cur.fetchall()]
                tasks.append({
                    "task": row[1],
                    "completed": bool(row[2]),
                    "tags": tags,
                })
            return tasks

    def count_tasks(self) -> int:
        with self._lock, self._conn:
            cur = self._conn.execute("SELECT COUNT(1) FROM tasks")
            return int(cur.fetchone()[0])

    def add_tag_to_task(self, index: int, tag: str) -> None:
        # index maps to task id ordering by id asc starting at 0 to match original API
        with self._lock, self._conn:
            task_id = self._task_id_by_index(index)
            tag_id = self._ensure_tag(tag)
            self._conn.execute("INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)", (task_id, tag_id))
            self._conn.execute("UPDATE tags SET usage_count = usage_count + 1, updated_ts = strftime('%s','now') WHERE id = ?", (tag_id,))

    def remove_tag_from_task(self, index: int, tag: str) -> None:
        with self._lock, self._conn:
            task_id = self._task_id_by_index(index)
            cur = self._conn.execute("SELECT id FROM tags WHERE name = ?", (tag,))
            row = cur.fetchone()
            if not row:
                return
            tag_id = row[0]
            self._conn.execute("DELETE FROM task_tags WHERE task_id = ? AND tag_id = ?", (task_id, tag_id))
            self._conn.execute("UPDATE tags SET usage_count = MAX(0, usage_count - 1), updated_ts = strftime('%s','now') WHERE id = ?", (tag_id,))

    def filter_by_tags(self, tags: List[str], match_all: bool = False) -> List[Dict]:
        if not tags:
            return self.list_todos()
        with self._lock, self._conn:
            # Build a query that finds tasks that have any/all tags from the list
            tag_placeholders = ",".join(["?"] * len(tags))
            if match_all:
                # Tasks that have all tags: group by task_id and count matching tags = len(tags)
                q = f"""
                SELECT tt.task_id FROM task_tags tt JOIN tags t ON t.id = tt.tag_id
                WHERE t.name IN ({tag_placeholders})
                GROUP BY tt.task_id HAVING COUNT(DISTINCT t.name) = ?
                """
                params = list(tags) + [len(tags)]
            else:
                q = f"""
                SELECT DISTINCT tt.task_id FROM task_tags tt JOIN tags t ON t.id = tt.tag_id
                WHERE t.name IN ({tag_placeholders})
                """
                params = list(tags)
            cur = self._conn.execute(q, params)
            task_ids = [r[0] for r in cur.fetchall()]
            # map task ids to ordered index-based results to emulate original API's index semantics
            tasks = self.list_todos()
            result = []
            id_to_index = {}
            with self._conn:
                idcur = self._conn.execute("SELECT id FROM tasks ORDER BY id ASC")
                for idx, r in enumerate(idcur.fetchall()):
                    id_to_index[r[0]] = idx
            for task_id in task_ids:
                idx = id_to_index.get(task_id)
                if idx is not None:
                    result.append(tasks[idx])
            return result

    def show_tag_stats(self) -> Dict[str, int]:
        with self._lock, self._conn:
            cur = self._conn.execute("SELECT name, usage_count FROM tags ORDER BY name ASC")
            return {r[0]: r[1] for r in cur.fetchall()}

    def list_all_tags(self) -> List[str]:
        with self._lock, self._conn:
            cur = self._conn.execute("SELECT name FROM tags ORDER BY name ASC")
            return [r[0] for r in cur.fetchall()]

    def complete_task(self, index: int) -> None:
        with self._lock, self._conn:
            task_id = self._task_id_by_index(index)
            self._conn.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))

    def _task_id_by_index(self, index: int) -> int:
        cur = self._conn.execute("SELECT id FROM tasks ORDER BY id ASC LIMIT 1 OFFSET ?", (index,))
        row = cur.fetchone()
        if not row:
            raise IndexError("task index out of range")
        return row[0]

    def close(self):
        with self._lock:
            self._conn.close()
