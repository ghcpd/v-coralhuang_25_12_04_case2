"""Tag management API built on storage."""
from __future__ import annotations
from typing import Optional, List

from .storage import SQLiteStorage
from .models import Tag
from .validation import validate_tag_name, normalize_tag


class TagService:
    def __init__(self, storage: Optional[SQLiteStorage] = None):
        self.storage = storage or SQLiteStorage()

    def list_tags(self) -> List[Tag]:
        return self.storage.list_tags()

    def add_alias(self, tag_name: str, alias: str) -> None:
        self.storage.add_alias(tag_name, alias)

    def set_color(self, tag_name: str, color: str) -> None:
        validate_tag_name(tag_name)
        with self.storage._connect() as conn:
            tag_id = self.storage._ensure_tag(conn, tag_name)
            conn.execute(
                "UPDATE tags SET color = ?, updated_at = datetime('now') WHERE id = ?",
                (color, tag_id),
            )

    def set_description(self, tag_name: str, description: str) -> None:
        validate_tag_name(tag_name)
        with self.storage._connect() as conn:
            tag_id = self.storage._ensure_tag(conn, tag_name)
            conn.execute(
                "UPDATE tags SET description = ?, updated_at = datetime('now') WHERE id = ?",
                (description, tag_id),
            )
