"""
Structured tag model with metadata, relationships, and usage tracking.
"""

from datetime import datetime
from typing import Dict, List, Optional, Set


class Tag:
    """Represents a structured tag with metadata."""

    def __init__(
        self,
        name: str,
        color: Optional[str] = None,
        description: Optional[str] = None,
        aliases: Optional[List[str]] = None,
    ):
        """Initialize a tag."""
        self.name = name
        self.color = color or "#808080"  # Default gray
        self.description = description or ""
        self.aliases = aliases or []
        self.usage_count = 0
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.cooccurrence: Dict[str, int] = {}  # tag_name -> count

    def increment_usage(self) -> None:
        """Increment usage counter."""
        self.usage_count += 1
        self.updated_at = datetime.now().isoformat()

    def add_cooccurrence(self, other_tag: str, amount: int = 1) -> None:
        """Track co-occurrence with another tag."""
        self.cooccurrence[other_tag] = self.cooccurrence.get(other_tag, 0) + amount

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "color": self.color,
            "description": self.description,
            "aliases": self.aliases,
            "usage_count": self.usage_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "cooccurrence": self.cooccurrence,
        }

    @staticmethod
    def from_dict(data: Dict) -> "Tag":
        """Create from dictionary."""
        tag = Tag(
            name=data["name"],
            color=data.get("color"),
            description=data.get("description"),
            aliases=data.get("aliases"),
        )
        tag.usage_count = data.get("usage_count", 0)
        tag.created_at = data.get("created_at", datetime.now().isoformat())
        tag.updated_at = data.get("updated_at", datetime.now().isoformat())
        tag.cooccurrence = data.get("cooccurrence", {})
        return tag


class TagManager:
    """Manages tags and their relationships."""

    def __init__(self, storage):
        """Initialize tag manager."""
        self.storage = storage
        self._tag_cache: Dict[str, Tag] = {}
        self._load_tags()

    def _load_tags(self) -> None:
        """Load all tags from storage."""
        for tag_name in self.storage.list_tags():
            data = self.storage.load_tag(tag_name)
            if data:
                self._tag_cache[tag_name] = Tag.from_dict(data)

    def create_tag(
        self,
        name: str,
        color: Optional[str] = None,
        description: Optional[str] = None,
        aliases: Optional[List[str]] = None,
    ) -> Tag:
        """Create a new tag."""
        if name in self._tag_cache:
            return self._tag_cache[name]

        tag = Tag(name, color, description, aliases)
        self._tag_cache[name] = tag
        self.storage.save_tag(name, tag.to_dict())
        return tag

    def get_tag(self, name: str) -> Optional[Tag]:
        """Get a tag by name."""
        if name not in self._tag_cache:
            data = self.storage.load_tag(name)
            if data:
                self._tag_cache[name] = Tag.from_dict(data)
        return self._tag_cache.get(name)

    def add_alias(self, tag_name: str, alias: str) -> None:
        """Add an alias to a tag."""
        tag = self.get_tag(tag_name)
        if tag and alias not in tag.aliases:
            tag.aliases.append(alias)
            self.storage.save_tag(tag_name, tag.to_dict())

    def resolve_alias(self, name: str) -> str:
        """Resolve an alias to the canonical tag name."""
        for tag_name, tag in self._tag_cache.items():
            if name in tag.aliases:
                return tag_name
        return name

    def record_usage(self, tag_name: str) -> None:
        """Record a tag usage."""
        tag = self.get_tag(tag_name)
        if tag:
            tag.increment_usage()
            self.storage.save_tag(tag_name, tag.to_dict())

    def record_cooccurrence(self, tag_names: List[str]) -> None:
        """Record co-occurrence of tags in a task."""
        for i, tag1 in enumerate(tag_names):
            for tag2 in tag_names[i + 1 :]:
                self.storage.save_cooccurrence(tag1, tag2, 1)
                t1 = self.get_tag(tag1)
                t2 = self.get_tag(tag2)
                if t1:
                    t1.add_cooccurrence(tag2)
                if t2:
                    t2.add_cooccurrence(tag1)

    def get_all_tags(self) -> List[Tag]:
        """Get all tags sorted by usage."""
        return sorted(
            self._tag_cache.values(),
            key=lambda t: -t.usage_count,
        )

    def get_tag_names(self) -> List[str]:
        """Get all tag names."""
        return list(self._tag_cache.keys())

    def delete_tag(self, name: str) -> None:
        """Delete a tag."""
        if name in self._tag_cache:
            del self._tag_cache[name]
        self.storage.delete_tag(name)
