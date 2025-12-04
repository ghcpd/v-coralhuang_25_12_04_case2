"""Backend factory and minimal backend implementation."""
import os
from .sqlite_backend import SqliteBackend

_backend_singleton = None


def get_backend():
    global _backend_singleton
    if _backend_singleton is not None:
        return _backend_singleton
    db_path = os.environ.get("TODO_DB")
    if not db_path:
        return None
    _backend_singleton = SqliteBackend(db_path)
    return _backend_singleton
