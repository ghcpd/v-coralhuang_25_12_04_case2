"""Concurrency utilities.

Uses file-based locks to guard write operations. SQLite with WAL mode handles
multiprocess concurrency fairly well, but we add an advisory lock to reduce
contention and avoid write-time errors under high load.
"""
from __future__ import annotations
import contextlib
from pathlib import Path
from typing import Iterator

try:
    from filelock import FileLock, Timeout
except ImportError:  # pragma: no cover - fallback
    FileLock = None
    Timeout = Exception

DEFAULT_TIMEOUT = 10.0  # seconds


@contextlib.contextmanager
def write_lock(path: Path, timeout: float = DEFAULT_TIMEOUT) -> Iterator[None]:
    if FileLock is None:
        # Best-effort: no-op if dependency missing
        yield
        return
    lock = FileLock(str(path))
    lock.acquire(timeout=timeout)
    try:
        yield
    finally:
        lock.release()
