"""Dataclasses representing tasks and tags."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Tag:
    id: int
    name: str
    color: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    usage_count: int = 0
    aliases: List[str] = field(default_factory=list)


@dataclass
class Task:
    id: int
    task: str
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)

    def to_legacy_dict(self) -> dict:
        """Return a dict compatible with the original API: {task, completed, tags}."""
        return {
            "task": self.task,
            "completed": self.completed,
            "tags": list(self.tags),
        }
