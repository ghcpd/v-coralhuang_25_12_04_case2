"""
Storage backend with SQLite persistence and concurrency safety.
"""

import json
import sqlite3
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def save_task(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """Save a task."""
        pass

    @abstractmethod
    def load_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Load a task by ID."""
        pass

    @abstractmethod
    def delete_task(self, task_id: str) -> None:
        """Delete a task."""
        pass

    @abstractmethod
    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all tasks."""
        pass

    @abstractmethod
    def save_tag(self, tag_name: str, tag_data: Dict[str, Any]) -> None:
        """Save tag metadata."""
        pass

    @abstractmethod
    def load_tag(self, tag_name: str) -> Optional[Dict[str, Any]]:
        """Load tag metadata."""
        pass

    @abstractmethod
    def delete_tag(self, tag_name: str) -> None:
        """Delete a tag."""
        pass

    @abstractmethod
    def list_tags(self) -> List[str]:
        """List all tag names."""
        pass

    @abstractmethod
    def save_cooccurrence(self, tag1: str, tag2: str, count: int) -> None:
        """Save co-occurrence count between tags."""
        pass

    @abstractmethod
    def load_cooccurrence(self, tag1: str, tag2: str) -> int:
        """Load co-occurrence count."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the storage backend."""
        pass


class SQLiteStorage(StorageBackend):
    """SQLite-based persistent storage with threading safety."""

    def __init__(self, db_path: str = "todo_advanced.db"):
        """Initialize SQLite storage."""
        self.db_path = Path(db_path)
        self.lock = threading.RLock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self.lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()

                # Tasks table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id TEXT PRIMARY KEY,
                        task TEXT NOT NULL,
                        completed BOOLEAN DEFAULT 0,
                        tags TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Tags metadata table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tags (
                        name TEXT PRIMARY KEY,
                        color TEXT,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        usage_count INTEGER DEFAULT 0,
                        aliases TEXT
                    )
                """)

                # Tag co-occurrence table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cooccurrence (
                        tag1 TEXT,
                        tag2 TEXT,
                        count INTEGER DEFAULT 1,
                        PRIMARY KEY (tag1, tag2),
                        FOREIGN KEY (tag1) REFERENCES tags(name),
                        FOREIGN KEY (tag2) REFERENCES tags(name)
                    )
                """)

                # Indexes for performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_completed ON tasks(completed)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tags ON tasks(tags)
                """)

                conn.commit()
            finally:
                conn.close()

    def save_task(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """Save a task."""
        with self.lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                tags_json = json.dumps(task_data.get("tags", []))
                cursor.execute("""
                    INSERT OR REPLACE INTO tasks (id, task, completed, tags, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    task_id,
                    task_data.get("task", ""),
                    1 if task_data.get("completed", False) else 0,
                    tags_json
                ))
                conn.commit()
            finally:
                conn.close()

    def load_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Load a task."""
        with self.lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row["id"],
                        "task": row["task"],
                        "completed": bool(row["completed"]),
                        "tags": json.loads(row["tags"]) if row["tags"] else [],
                    }
                return None
            finally:
                conn.close()

    def delete_task(self, task_id: str) -> None:
        """Delete a task."""
        with self.lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                conn.commit()
            finally:
                conn.close()

    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all tasks."""
        with self.lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
                rows = cursor.fetchall()
                return [
                    {
                        "id": row["id"],
                        "task": row["task"],
                        "completed": bool(row["completed"]),
                        "tags": json.loads(row["tags"]) if row["tags"] else [],
                    }
                    for row in rows
                ]
            finally:
                conn.close()

    def save_tag(self, tag_name: str, tag_data: Dict[str, Any]) -> None:
        """Save tag metadata."""
        with self.lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                aliases_json = json.dumps(tag_data.get("aliases", []))
                cursor.execute("""
                    INSERT OR REPLACE INTO tags
                    (name, color, description, usage_count, aliases, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    tag_name,
                    tag_data.get("color"),
                    tag_data.get("description"),
                    tag_data.get("usage_count", 0),
                    aliases_json
                ))
                conn.commit()
            finally:
                conn.close()

    def load_tag(self, tag_name: str) -> Optional[Dict[str, Any]]:
        """Load tag metadata."""
        with self.lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tags WHERE name = ?", (tag_name,))
                row = cursor.fetchone()
                if row:
                    return {
                        "name": row["name"],
                        "color": row["color"],
                        "description": row["description"],
                        "usage_count": row["usage_count"],
                        "aliases": json.loads(row["aliases"]) if row["aliases"] else [],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                    }
                return None
            finally:
                conn.close()

    def delete_tag(self, tag_name: str) -> None:
        """Delete a tag."""
        with self.lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tags WHERE name = ?", (tag_name,))
                conn.commit()
            finally:
                conn.close()

    def list_tags(self) -> List[str]:
        """List all tag names."""
        with self.lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM tags ORDER BY usage_count DESC")
                return [row["name"] for row in cursor.fetchall()]
            finally:
                conn.close()

    def save_cooccurrence(self, tag1: str, tag2: str, count: int) -> None:
        """Save co-occurrence count."""
        with self.lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                # Normalize order for consistency
                if tag1 > tag2:
                    tag1, tag2 = tag2, tag1
                cursor.execute("""
                    INSERT OR REPLACE INTO cooccurrence (tag1, tag2, count)
                    VALUES (?, ?, ?)
                """, (tag1, tag2, count))
                conn.commit()
            finally:
                conn.close()

    def load_cooccurrence(self, tag1: str, tag2: str) -> int:
        """Load co-occurrence count."""
        with self.lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                # Normalize order
                if tag1 > tag2:
                    tag1, tag2 = tag2, tag1
                cursor.execute("""
                    SELECT count FROM cooccurrence WHERE tag1 = ? AND tag2 = ?
                """, (tag1, tag2))
                row = cursor.fetchone()
                return row["count"] if row else 0
            finally:
                conn.close()

    def close(self) -> None:
        """Close storage."""
        # SQLite connections close automatically
        pass
