"""
Backward-compatible API wrapper using advanced storage and tag features.
"""
from typing import List, Dict, Optional
from .storage import Storage

_storage = Storage()

# Backward-compatible APIs (preserve signatures)

def add_todo(task: str, tags: Optional[List[str]] = None) -> None:
    _storage.add_task(task, tags)


def list_todos() -> List[Dict]:
    return _storage.list_tasks()


def filter_by_tags(tags: List[str], match_all: bool = False) -> List[Dict]:
    return _storage.filter_by_tags(tags, match_all=match_all)


def add_tag_to_task(index: int, tag: str) -> None:
    """Index in old API was 0-based; new storage uses task id. Maintain compatibility by treating index as position order."""
    tasks = _storage.list_tasks()
    if index < 0 or index >= len(tasks):
        raise IndexError("task index out of range")
    task_id = tasks[index]['id']
    _storage.add_tag_to_task(task_id, tag)


def remove_tag_from_task(index: int, tag: str) -> None:
    tasks = _storage.list_tasks()
    if index < 0 or index >= len(tasks):
        raise IndexError("task index out of range")
    task_id = tasks[index]['id']
    _storage.remove_tag_from_task(task_id, tag)


def show_tag_stats() -> Dict[str, int]:
    return _storage.show_tag_stats()


def list_all_tags() -> List[str]:
    return _storage.list_all_tags()


def complete_task(index: int) -> None:
    tasks = _storage.list_tasks()
    if index < 0 or index >= len(tasks):
        raise IndexError("task index out of range")
    task_id = tasks[index]['id']
    _storage.complete_task(task_id)

# Advanced accessors (not required but handy)

def get_storage() -> Storage:
    return _storage

def set_tag_metadata(tag_name: str, alias_of: Optional[int] = None, color: Optional[str] = None, description: Optional[str] = None) -> None:
    _storage.set_tag_metadata(tag_name, alias_of=alias_of, color=color, description=description)

def get_tag(tag_name: str):
    return _storage.get_tag(tag_name)

def tag_cooccurrence(tag_name: str):
    return _storage.tag_cooccurrence(tag_name)
