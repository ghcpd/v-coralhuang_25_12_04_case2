from dataclasses import dataclass, field
from typing import List, Optional, Dict
import time


def _now() -> float:
    return time.time()


@dataclass
class Tag:
    name: str
    aliases: List[str] = field(default_factory=list)
    color: Optional[str] = None
    description: Optional[str] = None
    created_at: float = field(default_factory=_now)
    updated_at: float = field(default_factory=_now)
    usage_count: int = 0

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "aliases": list(self.aliases),
            "color": self.color,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "usage_count": self.usage_count,
        }


@dataclass
class Task:
    id: int
    task: str
    completed: bool = False
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=_now)
    updated_at: float = field(default_factory=_now)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "task": self.task,
            "completed": self.completed,
            "tags": list(self.tags),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
