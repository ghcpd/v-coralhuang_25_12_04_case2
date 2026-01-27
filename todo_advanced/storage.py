"""
Lightweight SQLite-backed storage with basic concurrency protections and schema versioning.
"""
import sqlite3
import threading
from pathlib import Path
from typing import List, Dict, Optional
import time

from . import plugins

DB_FILE = Path(__file__).parent.parent / 'todo_data.db'

_lock = threading.RLock()


class Storage:
    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = DB_FILE
        self._conn = None
        self._init_db()

    def _connect(self):
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute('PRAGMA foreign_keys = ON')
            self._conn.execute('PRAGMA journal_mode = WAL')
        return self._conn

    def _init_db(self):
        with _lock:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute('''CREATE TABLE IF NOT EXISTS schema_info (version INTEGER)''')
            cur.execute('SELECT version FROM schema_info')
            r = cur.fetchone()
            version = r[0] if r else 0
            if version < 1:
                cur.executescript('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    completed INTEGER NOT NULL DEFAULT 0,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    alias_of INTEGER REFERENCES tags(id),
                    color TEXT,
                    description TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    usage_count INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS task_tags (
                    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
                    PRIMARY KEY (task_id, tag_id)
                );
                CREATE TABLE IF NOT EXISTS tag_cooccurrence (
                    tag_a INTEGER REFERENCES tags(id) ON DELETE CASCADE,
                    tag_b INTEGER REFERENCES tags(id) ON DELETE CASCADE,
                    weight INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (tag_a, tag_b)
                );
                INSERT OR REPLACE INTO schema_info(version) VALUES (1);
                ''')
                conn.commit()

    def add_task(self, task_text: str, tags: Optional[List[str]] = None) -> int:
        now = time.time()
        if tags is None:
            tags = []
        with _lock:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute('INSERT INTO tasks (task, completed, created_at, updated_at) VALUES (?, 0, ?, ?)',
                        (task_text, now, now))
            task_id = cur.lastrowid
            for t in tags:
                tag_id = self._ensure_tag(t)
                cur.execute('INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)', (task_id, tag_id))
                cur.execute('UPDATE tags SET usage_count = usage_count + 1, updated_at = ? WHERE id = ?', (now, tag_id))
            tag_ids = [self._get_tag_id(t) for t in tags]
            for i in range(len(tag_ids)):
                for j in range(i+1, len(tag_ids)):
                    a = tag_ids[i]
                    b = tag_ids[j]
                    if a and b:
                        cur.execute('INSERT OR IGNORE INTO tag_cooccurrence (tag_a, tag_b, weight) VALUES (?, ?, 0)', (a,b))
                        cur.execute('UPDATE tag_cooccurrence SET weight = weight + 1 WHERE tag_a = ? AND tag_b = ?', (a,b))
            conn.commit()
            plugins.call_hook('on_task_added', {
                'id': task_id,
                'task': task_text,
                'tags': tags,
                'created_at': now,
                'updated_at': now,
            })
            assert task_id is not None
            return int(task_id)

    def list_tasks(self) -> List[Dict]:
        with _lock:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute('SELECT * FROM tasks ORDER BY id')
            rows = cur.fetchall()
            result = []
            for r in rows:
                task_id = r['id']
                cur.execute('SELECT t.name FROM tags t JOIN task_tags tt ON t.id = tt.tag_id WHERE tt.task_id = ?', (task_id,))
                tags = [row['name'] for row in cur.fetchall()]
                result.append({
                    'id': task_id,
                    'task': r['task'],
                    'completed': bool(r['completed']),
                    'created_at': r['created_at'],
                    'updated_at': r['updated_at'],
                    'tags': tags
                })
            return result

    def filter_by_tags(self, tags: List[str], match_all: bool = False) -> List[Dict]:
        if not tags:
            return self.list_tasks()
        with _lock:
            conn = self._connect()
            cur = conn.cursor()
            placeholders = ','.join('?' for _ in tags)
            cur.execute(f'SELECT id, name FROM tags WHERE name IN ({placeholders})', tuple(tags))
            tag_ids = [r['id'] for r in cur.fetchall()]
            if not tag_ids:
                return []
            if match_all:
                q = f"SELECT t.* FROM tasks t JOIN task_tags tt ON t.id = tt.task_id WHERE tt.tag_id IN ({placeholders}) GROUP BY t.id HAVING COUNT(DISTINCT tt.tag_id) = ?"
                cur.execute(q, tuple(tag_ids) + (len(tag_ids),))
            else:
                q = f"SELECT DISTINCT t.* FROM tasks t JOIN task_tags tt ON t.id = tt.task_id WHERE tt.tag_id IN ({placeholders})"
                cur.execute(q, tuple(tag_ids))
            rows = cur.fetchall()
            result = []
            for r in rows:
                task_id = r['id']
                cur.execute('SELECT t.name FROM tags t JOIN task_tags tt ON t.id = tt.tag_id WHERE tt.task_id = ?', (task_id,))
                tags = [row['name'] for row in cur.fetchall()]
                result.append({
                    'id': task_id,
                    'task': r['task'],
                    'completed': bool(r['completed']),
                    'created_at': r['created_at'],
                    'updated_at': r['updated_at'],
                    'tags': tags
                })
            return result

    def add_tag_to_task(self, task_id: int, tag: str) -> None:
        with _lock:
            conn = self._connect()
            cur = conn.cursor()
            tag_id = self._ensure_tag(tag)
            cur.execute('INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)', (task_id, tag_id))
            cur.execute('UPDATE tags SET usage_count = usage_count + 1, updated_at = ? WHERE id = ?', (time.time(), tag_id))
            conn.commit()
            plugins.call_hook('on_tag_added', tag)

    def remove_tag_from_task(self, task_id: int, tag: str) -> None:
        with _lock:
            conn = self._connect()
            cur = conn.cursor()
            tag_id = self._get_tag_id(tag)
            if not tag_id:
                return
            cur.execute('DELETE FROM task_tags WHERE task_id = ? AND tag_id = ?', (task_id, tag_id))
            cur.execute('UPDATE tags SET usage_count = max(0, usage_count - 1), updated_at = ? WHERE id = ?', (time.time(), tag_id))
            conn.commit()

    def show_tag_stats(self) -> Dict[str, int]:
        with _lock:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute('SELECT name, usage_count FROM tags ORDER BY name')
            return {r['name']: r['usage_count'] for r in cur.fetchall()}

    def set_tag_metadata(self, tag_name: str, alias_of: Optional[int] = None, color: Optional[str] = None, description: Optional[str] = None) -> None:
        with _lock:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute('UPDATE tags SET alias_of = ?, color = ?, description = ?, updated_at = ? WHERE name = ?', (alias_of, color, description, time.time(), tag_name))
            conn.commit()

    def get_tag(self, tag_name: str) -> Optional[Dict]:
        with _lock:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute('SELECT * FROM tags WHERE name = ?', (tag_name,))
            r = cur.fetchone()
            if not r:
                return None
            return dict(r)

    def tag_cooccurrence(self, tag_name: str) -> Dict[str, int]:
        with _lock:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute('SELECT id FROM tags WHERE name = ?', (tag_name,))
            r = cur.fetchone()
            if not r:
                return {}
            tag_id = r['id']
            cur.execute('SELECT t2.name as other, tc.weight FROM tag_cooccurrence tc JOIN tags t2 ON t2.id = tc.tag_b WHERE tc.tag_a = ?', (tag_id,))
            out = {row['other']: row['weight'] for row in cur.fetchall()}
            return out

    def list_all_tags(self) -> List[str]:
        with _lock:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute('SELECT name FROM tags ORDER BY name')
            return [r['name'] for r in cur.fetchall()]

    def complete_task(self, task_id: int) -> None:
        with _lock:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute('UPDATE tasks SET completed = 1, updated_at = ? WHERE id = ?', (time.time(), task_id))
            conn.commit()
            plugins.call_hook('on_task_completed', {'id': task_id})

    def _ensure_tag(self, name: str) -> int:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute('SELECT id FROM tags WHERE name = ?', (name,))
        r = cur.fetchone()
        if r:
            return r['id']
        now = time.time()
        cur.execute('INSERT INTO tags (name, created_at, updated_at, usage_count) VALUES (?, ?, ?, 0)', (name, now, now))
        conn.commit()
        assert cur.lastrowid is not None
        tag_id = int(cur.lastrowid)
        plugins.call_hook('on_tag_added', name)
        return tag_id

    def _get_tag_id(self, name: str) -> Optional[int]:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute('SELECT id FROM tags WHERE name = ?', (name,))
        r = cur.fetchone()
        return r['id'] if r else None
