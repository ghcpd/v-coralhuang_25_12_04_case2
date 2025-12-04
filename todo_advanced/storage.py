import sqlite3
import json
from threading import RLock
from typing import List, Dict, Optional, Tuple
from .models import Task, Tag
import time


class StorageError(RuntimeError):
    pass


class SQLiteStorage:
    """Basic SQLite storage with simple migrations and concurrency.

    Uses WAL mode and a process-wide lock for safety in tests. For real
    deployments, SQLite's own locking plus WAL ensures crash-safe writes.
    """

    def __init__(self, path: str = ":memory:"):
        self._path = path
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = RLock()
        self._apply_pragmas()
        self._migrate()

    def _apply_pragmas(self):
        # Improve concurrency
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")

    def _migrate(self):
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                tags TEXT DEFAULT '[]',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                name TEXT PRIMARY KEY,
                aliases TEXT DEFAULT '[]',
                color TEXT,
                description TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                usage_count INTEGER DEFAULT 0
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS tag_cooccurrence (
                a TEXT NOT NULL,
                b TEXT NOT NULL,
                weight INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (a,b)
            );
            """)

            self._conn.commit()

    # -- Tasks -------------------------------------------------------------
    def add_task(self, task: str, tags: Optional[List[str]] = None) -> Task:
        if tags is None:
            tags = []
        ts = time.time()
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "INSERT INTO tasks (task, completed, tags, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (task, 0, json.dumps(tags), ts, ts),
            )
            tid = cur.lastrowid
            self._conn.commit()

        # update tag metadata / cooccurrence
        if tags:
            self._update_tags_after_addition(tags)

        return Task(id=tid, task=task, completed=False, tags=tags, created_at=ts, updated_at=ts)

    def list_tasks(self) -> List[Task]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM tasks ORDER BY id ASC")
            rows = cur.fetchall()
        return [self._row_to_task(r) for r in rows]

    def _row_to_task(self, row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"],
            task=row["task"],
            completed=bool(row["completed"]),
            tags=json.loads(row["tags"] or "[]"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def complete_task(self, task_id: int) -> None:
        now = time.time()
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("UPDATE tasks SET completed = 1, updated_at = ? WHERE id = ?", (now, task_id))
            self._conn.commit()

    # -- Tags --------------------------------------------------------------
    def add_or_update_tag(self, tag: Tag) -> None:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "INSERT INTO tags (name, aliases, color, description, created_at, updated_at, usage_count) VALUES (?, ?, ?, ?, ?, ?, ?)"
                "ON CONFLICT(name) DO UPDATE SET aliases=excluded.aliases, color=excluded.color, description=excluded.description, updated_at=excluded.updated_at, usage_count=excluded.usage_count",
                (
                    tag.name,
                    json.dumps(tag.aliases),
                    tag.color,
                    tag.description,
                    tag.created_at,
                    tag.updated_at,
                    tag.usage_count,
                ),
            )
            self._conn.commit()

    def get_tag(self, name: str) -> Optional[Tag]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM tags WHERE name = ?", (name,))
            row = cur.fetchone()
        if not row:
            return None
        return Tag(
            name=row["name"],
            aliases=json.loads(row["aliases"] or "[]"),
            color=row["color"],
            description=row["description"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            usage_count=row["usage_count"],
        )

    def list_tags(self) -> List[Tag]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM tags ORDER BY name ASC")
            rows = cur.fetchall()
        result = []
        for r in rows:
            result.append(
                Tag(
                    name=r["name"],
                    aliases=json.loads(r["aliases"] or "[]"),
                    color=r["color"],
                    description=r["description"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    usage_count=r["usage_count"],
                )
            )
        return result

    # Co-occurrence: update counts for pairs
    def _update_tags_after_addition(self, tags: List[str]):
        now = time.time()
        tags = sorted(set(tags))
        with self._lock:
            cur = self._conn.cursor()
            # increment usage_count on tags
            for t in tags:
                cur.execute(
                    "INSERT INTO tags (name, aliases, created_at, updated_at, usage_count) VALUES (?, '[]', ?, ?, 1) "
                    "ON CONFLICT(name) DO UPDATE SET usage_count = usage_count + 1, updated_at = ?",
                    (t, now, now, now),
                )

            # update co-occurrence
            for i in range(len(tags)):
                for j in range(i + 1, len(tags)):
                    a, b = tags[i], tags[j]
                    cur.execute(
                        "INSERT INTO tag_cooccurrence (a,b,weight) VALUES (?, ?, 1) "
                        "ON CONFLICT(a,b) DO UPDATE SET weight = weight + 1",
                        (a, b),
                    )

            self._conn.commit()

    def get_cooccurrence(self, tag: str, limit: int = 10) -> List[Tuple[str, int]]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT b, weight FROM tag_cooccurrence WHERE a = ? ORDER BY weight DESC LIMIT ?",
                (tag, limit),
            )
            rows = cur.fetchall()
        return [(r["b"], r["weight"]) for r in rows]
