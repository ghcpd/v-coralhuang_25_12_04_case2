"""SQLite storage backend for advanced TODO system."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Iterable, List, Optional, Tuple, Dict
from datetime import datetime

from .config import DEFAULT_DB_PATH, LOCK_FILE_PATH
from .locking import write_lock
from .models import Task, Tag
from .validation import normalize_tag, validate_tag_name, validate_task_text

SCHEMA_VERSION = 1


class SQLiteStorage:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH, lock_path: Path = LOCK_FILE_PATH):
        self.db_path = Path(db_path)
        self.lock_path = Path(lock_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # serialize initialization across processes
        with write_lock(self.lock_path):
            self._init_db()

    def _connect(self) -> sqlite3.Connection:
        # timeout handles concurrent writers; check_same_thread allows reuse across threads
        conn = sqlite3.connect(str(self.db_path), timeout=10.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL);
                """
            )
            # If empty, insert version
            cur = conn.execute("SELECT COUNT(*) as c FROM schema_version")
            if cur.fetchone()["c"] == 0:
                conn.execute("INSERT INTO schema_version(version) VALUES (?)", (SCHEMA_VERSION,))
            # Tasks
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    completed INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            # Tags
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    color TEXT,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    usage_count INTEGER NOT NULL DEFAULT 0
                );
                """
            )
            # Tag aliases
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tag_aliases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tag_id INTEGER NOT NULL,
                    alias TEXT NOT NULL UNIQUE,
                    FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
                );
                """
            )
            # Task-tag relations
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_tags (
                    task_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(task_id, tag_id),
                    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                    FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
                );
                """
            )
            # Tag cooccurrence
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tag_cooccurrence (
                    tag_id1 INTEGER NOT NULL,
                    tag_id2 INTEGER NOT NULL,
                    count INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY(tag_id1, tag_id2),
                    FOREIGN KEY(tag_id1) REFERENCES tags(id) ON DELETE CASCADE,
                    FOREIGN KEY(tag_id2) REFERENCES tags(id) ON DELETE CASCADE
                );
                """
            )

    # ------------------------- Tag helpers -------------------------
    def _get_tag_id_by_name_or_alias(self, conn: sqlite3.Connection, name_or_alias: str) -> Optional[int]:
        n = normalize_tag(name_or_alias)
        cur = conn.execute("SELECT id FROM tags WHERE name = ?", (n,))
        row = cur.fetchone()
        if row:
            return row["id"]
        cur = conn.execute(
            "SELECT tag_id FROM tag_aliases WHERE alias = ?", (n,)
        )
        r = cur.fetchone()
        return r["tag_id"] if r else None

    def _ensure_tag(self, conn: sqlite3.Connection, name: str) -> int:
        validate_tag_name(name)
        n = normalize_tag(name)
        tag_id = self._get_tag_id_by_name_or_alias(conn, n)
        if tag_id:
            return tag_id
        now = datetime.utcnow().isoformat()
        cur = conn.execute(
            "INSERT INTO tags(name, created_at, updated_at, usage_count) VALUES (?, ?, ?, 0)",
            (n, now, now),
        )
        assert cur.lastrowid is not None
        return int(cur.lastrowid)

    def add_alias(self, tag_name: str, alias: str) -> None:
        with write_lock(self.lock_path):
            with self._connect() as conn:
                tag_id = self._ensure_tag(conn, tag_name)
                validate_tag_name(alias)
                alias_norm = normalize_tag(alias)
                conn.execute(
                    "INSERT OR IGNORE INTO tag_aliases(tag_id, alias) VALUES (?, ?)",
                    (tag_id, alias_norm),
                )

    # ------------------------- Task operations -------------------------
    def add_task(self, task: str, tags: Optional[List[str]] = None, completed: bool = False) -> int:
        validate_task_text(task)
        tags = tags or []
        now = datetime.utcnow().isoformat()
        with write_lock(self.lock_path):
            with self._connect() as conn:
                cur = conn.execute(
                    "INSERT INTO tasks(task, completed, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (task, int(completed), now, now),
                )
                assert cur.lastrowid is not None
                task_id = int(cur.lastrowid)
                tag_ids = []
                for t in tags:
                    tag_id = self._ensure_tag(conn, t)
                    tag_ids.append(tag_id)
                    conn.execute("INSERT OR IGNORE INTO task_tags(task_id, tag_id, created_at) VALUES (?, ?, ?)", (task_id, tag_id, now))
                    conn.execute("UPDATE tags SET usage_count = usage_count + 1, updated_at = ? WHERE id = ?", (now, tag_id))
                # update cooccurrence
                self._update_cooccurrence(conn, tag_ids)
                return task_id

    def _update_cooccurrence(self, conn: sqlite3.Connection, tag_ids: List[int]) -> None:
        for i in range(len(tag_ids)):
            for j in range(i + 1, len(tag_ids)):
                a, b = sorted((tag_ids[i], tag_ids[j]))
                conn.execute(
                    "INSERT INTO tag_cooccurrence(tag_id1, tag_id2, count) VALUES (?, ?, 1) "
                    "ON CONFLICT(tag_id1, tag_id2) DO UPDATE SET count = count + 1",
                    (a, b),
                )

    def list_tasks(self) -> List[Task]:
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM tasks ORDER BY id ASC")
            tasks_rows = cur.fetchall()
            tasks: List[Task] = []
            for row in tasks_rows:
                tags = self._get_tags_for_task(conn, row["id"])
                tasks.append(
                    Task(
                        id=row["id"],
                        task=row["task"],
                        completed=bool(row["completed"]),
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                        tags=tags,
                    )
                )
            return tasks

    def _get_tags_for_task(self, conn: sqlite3.Connection, task_id: int) -> List[str]:
        cur = conn.execute(
            "SELECT t.name FROM tags t JOIN task_tags tt ON t.id = tt.tag_id WHERE tt.task_id = ? ORDER BY t.name ASC",
            (task_id,),
        )
        return [r["name"] for r in cur.fetchall()]

    def get_task_by_index(self, index: int) -> Task:
        with self._connect() as conn:
            cur = conn.execute("SELECT id FROM tasks ORDER BY id ASC LIMIT 1 OFFSET ?", (index,))
            row = cur.fetchone()
            if not row:
                raise IndexError("task index out of range")
            return self.get_task(row["id"])

    def get_task(self, task_id: int) -> Task:
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cur.fetchone()
            if not row:
                raise KeyError(f"task {task_id} not found")
            tags = self._get_tags_for_task(conn, task_id)
            return Task(
                id=row["id"],
                task=row["task"],
                completed=bool(row["completed"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                tags=tags,
            )

    def set_task_completed(self, task_id: int, completed: bool = True) -> None:
        now = datetime.utcnow().isoformat()
        with write_lock(self.lock_path):
            with self._connect() as conn:
                conn.execute("UPDATE tasks SET completed = ?, updated_at = ? WHERE id = ?", (int(completed), now, task_id))

    def add_tag_to_task(self, task_id: int, tag: str) -> None:
        with write_lock(self.lock_path):
            with self._connect() as conn:
                tag_id = self._ensure_tag(conn, tag)
                now = datetime.utcnow().isoformat()
                conn.execute(
                    "INSERT OR IGNORE INTO task_tags(task_id, tag_id, created_at) VALUES (?, ?, ?)",
                    (task_id, tag_id, now),
                )
                conn.execute(
                    "UPDATE tags SET usage_count = usage_count + 1, updated_at = ? WHERE id = ?",
                    (now, tag_id),
                )
                self._update_cooccurrence(conn, [tag_id] + self._get_tag_ids_for_task(conn, task_id))

    def remove_tag_from_task(self, task_id: int, tag: str) -> None:
        with write_lock(self.lock_path):
            with self._connect() as conn:
                tag_id = self._get_tag_id_by_name_or_alias(conn, tag)
                if not tag_id:
                    return
                conn.execute("DELETE FROM task_tags WHERE task_id = ? AND tag_id = ?", (task_id, tag_id))
                # decrement usage count carefully
                conn.execute(
                    "UPDATE tags SET usage_count = CASE WHEN usage_count > 0 THEN usage_count - 1 ELSE 0 END, updated_at = ? WHERE id = ?",
                    (datetime.utcnow().isoformat(), tag_id),
                )

    def _get_tag_ids_for_task(self, conn: sqlite3.Connection, task_id: int) -> List[int]:
        cur = conn.execute("SELECT tag_id FROM task_tags WHERE task_id = ?", (task_id,))
        return [r["tag_id"] for r in cur.fetchall()]

    def filter_tasks_by_tags(self, tags: List[str], match_all: bool = False) -> List[Task]:
        if not tags:
            return self.list_tasks()
        normalized = [normalize_tag(t) for t in tags]
        with self._connect() as conn:
            # Resolve tag ids
            tag_ids = []
            for t in normalized:
                tid = self._get_tag_id_by_name_or_alias(conn, t)
                if tid:
                    tag_ids.append(tid)
            if not tag_ids:
                return []
            placeholders = ",".join("?" for _ in tag_ids)
            if match_all:
                sql = f"""
                    SELECT task_id FROM task_tags
                    WHERE tag_id IN ({placeholders})
                    GROUP BY task_id
                    HAVING COUNT(DISTINCT tag_id) = ?
                """
                cur = conn.execute(sql, (*tag_ids, len(tag_ids)))
            else:
                sql = f"SELECT DISTINCT task_id FROM task_tags WHERE tag_id IN ({placeholders})"
                cur = conn.execute(sql, tag_ids)
            task_ids = [r["task_id"] for r in cur.fetchall()]
            return [self.get_task(tid) for tid in task_ids]

    def list_tags(self) -> List[Tag]:
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM tags ORDER BY name ASC")
            tags: List[Tag] = []
            for row in cur.fetchall():
                aliases = self._get_aliases(conn, row["id"])
                tags.append(
                    Tag(
                        id=row["id"],
                        name=row["name"],
                        color=row["color"],
                        description=row["description"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                        usage_count=row["usage_count"],
                        aliases=aliases,
                    )
                )
            return tags

    def _get_aliases(self, conn: sqlite3.Connection, tag_id: int) -> List[str]:
        cur = conn.execute("SELECT alias FROM tag_aliases WHERE tag_id = ? ORDER BY alias ASC", (tag_id,))
        return [r["alias"] for r in cur.fetchall()]

    def tag_stats(self) -> Dict[str, int]:
        with self._connect() as conn:
            cur = conn.execute("SELECT name, usage_count FROM tags ORDER BY name ASC")
            return {r["name"]: r["usage_count"] for r in cur.fetchall()}

    def cooccurring_tags(self, tag: str, limit: int = 5) -> List[Tuple[str, int]]:
        with self._connect() as conn:
            tag_id = self._get_tag_id_by_name_or_alias(conn, tag)
            if not tag_id:
                return []
            cur = conn.execute(
                """
                SELECT
                  CASE WHEN tag_id1 = ? THEN tag_id2 ELSE tag_id1 END AS other_id,
                  count
                FROM tag_cooccurrence
                WHERE tag_id1 = ? OR tag_id2 = ?
                ORDER BY count DESC
                LIMIT ?
                """,
                (tag_id, tag_id, tag_id, limit),
            )
            results = []
            for r in cur.fetchall():
                name = conn.execute("SELECT name FROM tags WHERE id = ?", (r["other_id"],)).fetchone()["name"]
                results.append((name, r["count"]))
            return results

    def suggest_tags(self, text: str, existing_tags: Optional[List[str]] = None, top_n: int = 5) -> List[Tuple[str, float]]:
        """Suggest tags based on keyword similarity and co-occurrence."""
        import difflib
        existing_tags = existing_tags or []
        suggestions: Dict[str, float] = {}
        words = set(text.lower().split())
        with self._connect() as conn:
            cur = conn.execute("SELECT name, usage_count FROM tags")
            all_tags = [(r["name"], r["usage_count"]) for r in cur.fetchall()]
            for name, usage in all_tags:
                if name in existing_tags:
                    continue
                # keyword similarity: longest matching word ratio
                sim = max((difflib.SequenceMatcher(None, name, w).ratio() for w in words), default=0)
                score = sim * 0.6 + min(usage, 100) / 100 * 0.4
                if score > 0:
                    suggestions[name] = max(suggestions.get(name, 0), score)
            # co-occurrence
            for et in existing_tags:
                for other, count in self.cooccurring_tags(et, limit=top_n * 2):
                    if other in existing_tags:
                        continue
                    suggestions[other] = max(suggestions.get(other, 0), 0.5 + min(count, 10) / 20)
        # return top_n
        return sorted(suggestions.items(), key=lambda kv: kv[1], reverse=True)[:top_n]

    def query_tasks(self, where_clause: str = "", params: Tuple = (), limit: Optional[int] = None) -> List[Task]:
        sql = "SELECT * FROM tasks"
        if where_clause:
            sql += f" WHERE {where_clause}"
        sql += " ORDER BY id ASC"
        if limit:
            sql += f" LIMIT {int(limit)}"
        with self._connect() as conn:
            cur = conn.execute(sql, params)
            rows = cur.fetchall()
            tasks: List[Task] = []
            for row in rows:
                tags = self._get_tags_for_task(conn, row["id"])
                tasks.append(
                    Task(
                        id=row["id"],
                        task=row["task"],
                        completed=bool(row["completed"]),
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                        tags=tags,
                    )
                )
            return tasks
