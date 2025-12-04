"""Persistent storage layer using SQLite with basic migrations and concurrency.

This provides a minimal, safe implementation to satisfy the compatibility
wrapper in `todo_advanced.py`. It stores tasks and tag metadata and updates
co-occurrence counts on task changes.
"""
import sqlite3
import threading
import time
from typing import List, Dict, Optional, Tuple

DB_PATH = "todo_advanced.db"


def _now_ts() -> int:
    return int(time.time())


class AdvancedStorage:
    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self._conn:
            # simple versioning table
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)"""
            )
            # tasks
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    completed INTEGER NOT NULL DEFAULT 0,
                    created_ts INTEGER NOT NULL,
                    updated_ts INTEGER NOT NULL
                )"""
            )
            # tags
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    color TEXT,
                    aliases TEXT,
                    usage_count INTEGER NOT NULL DEFAULT 0,
                    created_ts INTEGER NOT NULL,
                    updated_ts INTEGER NOT NULL
                )"""
            )
            # task_tags
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS task_tags (
                    task_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    PRIMARY KEY (task_id, tag_id),
                    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                    FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
                )"""
            )
            # cooccurrence
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS tag_cooccurrence (
                    tag_a INTEGER NOT NULL,
                    tag_b INTEGER NOT NULL,
                    weight INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY(tag_a, tag_b)
                )"""
            )

    # Task operations
    def add_task(self, task: str, tags: List[str]) -> int:
        with self._lock, self._conn:
            now = _now_ts()
            cur = self._conn.execute(
                "INSERT INTO tasks (task, completed, created_ts, updated_ts) VALUES (?, 0, ?, ?)",
                (task, now, now),
            )
            task_id = cur.lastrowid
            tag_ids = [self._ensure_tag_row(t) for t in tags]
            for tid in tag_ids:
                self._conn.execute(
                    "INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)",
                    (task_id, tid),
                )
                self._conn.execute(
                    "UPDATE tags SET usage_count = usage_count + 1, updated_ts = ? WHERE id = ?",
                    (now, tid),
                )
            self._update_cooccurrence(tag_ids)
            return task_id

    def list_tasks(self) -> List[Dict]:
        with self._lock:
            cur = self._conn.execute("SELECT * FROM tasks ORDER BY id")
            rows = cur.fetchall()
            out = []
            for r in rows:
                tags = self._get_tags_for_task(r["id"])
                out.append({
                    "task": r["task"],
                    "completed": bool(r["completed"]),
                    "tags": tags,
                })
            return out

    def filter_tasks_by_tags(self, tags: List[str], match_all: bool = False) -> List[Dict]:
        if not tags:
            return self.list_tasks()
        with self._lock:
            # convert tag names to ids
            tag_ids = [self._get_tag_id_by_name(t) for t in tags]
            tag_ids = [t for t in tag_ids if t is not None]
            if not tag_ids:
                return []
            if match_all:
                # tasks that have all tag_ids
                placeholders = ",".join(["?"] * len(tag_ids))
                q = f"""
                    SELECT t.* FROM tasks t
                    JOIN task_tags tt ON t.id = tt.task_id
                    WHERE tt.tag_id IN ({placeholders})
                    GROUP BY t.id HAVING COUNT(DISTINCT tt.tag_id) = ?
                """
                params = tag_ids + [len(tag_ids)]
                cur = self._conn.execute(q, params)
            else:
                placeholders = ",".join(["?"] * len(tag_ids))
                q = f"SELECT DISTINCT t.* FROM tasks t JOIN task_tags tt ON t.id = tt.task_id WHERE tt.tag_id IN ({placeholders})"
                cur = self._conn.execute(q, tag_ids)
            rows = cur.fetchall()
            out = []
            for r in rows:
                out.append({
                    "task": r["task"],
                    "completed": bool(r["completed"]),
                    "tags": self._get_tags_for_task(r["id"]),
                })
            return out

    def add_tag_to_task(self, index: int, tag: str) -> None:
        with self._lock, self._conn:
            task_row = self._conn.execute("SELECT id FROM tasks ORDER BY id LIMIT 1 OFFSET ?", (index,)).fetchone()
            if not task_row:
                raise IndexError("task index out of range")
            task_id = task_row["id"]
            tid = self._ensure_tag_row(tag)
            self._conn.execute("INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)", (task_id, tid))
            self._conn.execute("UPDATE tags SET usage_count = usage_count + 1, updated_ts = ? WHERE id = ?", (_now_ts(), tid))
            self._update_cooccurrence(self._get_tags_for_task_ids(task_id))

    def remove_tag_from_task(self, index: int, tag: str) -> None:
        with self._lock, self._conn:
            task_row = self._conn.execute("SELECT id FROM tasks ORDER BY id LIMIT 1 OFFSET ?", (index,)).fetchone()
            if not task_row:
                raise IndexError("task index out of range")
            task_id = task_row["id"]
            tid = self._get_tag_id_by_name(tag)
            if tid is None:
                return
            self._conn.execute("DELETE FROM task_tags WHERE task_id = ? AND tag_id = ?", (task_id, tid))
            self._conn.execute("UPDATE tags SET usage_count = CASE WHEN usage_count>0 THEN usage_count-1 ELSE 0 END, updated_ts = ? WHERE id = ?", (_now_ts(), tid))
            self._update_cooccurrence(self._get_tags_for_task_ids(task_id))

    def complete_task(self, index: int) -> None:
        with self._lock, self._conn:
            task_row = self._conn.execute("SELECT id FROM tasks ORDER BY id LIMIT 1 OFFSET ?", (index,)).fetchone()
            if not task_row:
                raise IndexError("task index out of range")
            now = _now_ts()
            self._conn.execute("UPDATE tasks SET completed = 1, updated_ts = ? WHERE id = ?", (now, task_row["id"]))

    # Tag utilities
    def _ensure_tag_row(self, name: str) -> int:
        now = _now_ts()
        cur = self._conn.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()
        if cur:
            return cur["id"]
        cur = self._conn.execute(
            "INSERT INTO tags (name, description, color, aliases, usage_count, created_ts, updated_ts) VALUES (?, ?, ?, ?, 0, ?, ?)",
            (name, None, None, None, now, now),
        )
        return cur.lastrowid

    def _get_tag_id_by_name(self, name: str) -> Optional[int]:
        cur = self._conn.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()
        return cur["id"] if cur else None

    def list_tags(self) -> List[str]:
        with self._lock:
            cur = self._conn.execute("SELECT name FROM tags ORDER BY name")
            return [r["name"] for r in cur.fetchall()]

    def tag_stats(self) -> Dict[str, int]:
        with self._lock:
            cur = self._conn.execute("SELECT name, usage_count FROM tags")
            return {r["name"]: r["usage_count"] for r in cur.fetchall()}

    def _get_tags_for_task(self, task_id: int) -> List[str]:
        cur = self._conn.execute(
            "SELECT tags.name FROM tags JOIN task_tags ON tags.id = task_tags.tag_id WHERE task_tags.task_id = ? ORDER BY tags.name",
            (task_id,),
        )
        return [r[0] for r in cur.fetchall()]

    def _get_tags_for_task_ids(self, task_id: int) -> List[int]:
        cur = self._conn.execute("SELECT tag_id FROM task_tags WHERE task_id = ?", (task_id,))
        return [r[0] for r in cur.fetchall()]

    def _update_cooccurrence(self, tag_ids: List[int]) -> None:
        # increment pairwise weights
        if not tag_ids:
            return
        now = _now_ts()
        for i in range(len(tag_ids)):
            for j in range(i + 1, len(tag_ids)):
                a, b = tag_ids[i], tag_ids[j]
                # keep ordering a < b for canonical storage
                if a == b:
                    continue
                if a > b:
                    a, b = b, a
                self._conn.execute(
                    "INSERT INTO tag_cooccurrence (tag_a, tag_b, weight) VALUES (?, ?, 1) ON CONFLICT(tag_a, tag_b) DO UPDATE SET weight = weight + 1",
                    (a, b),
                )
