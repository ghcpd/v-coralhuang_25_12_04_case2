"""Configuration utilities for todo_advanced.

- Default storage backend: SQLite
- DB path can be overridden via environment variable `TODO_DB_PATH`.
- Plugin discovery can be configured via `TODO_PLUGINS` (comma-separated modules).
"""
from __future__ import annotations
import os
from pathlib import Path

DEFAULT_DB_FILENAME = "todo_data.db"
DEFAULT_DB_DIR = Path(os.getenv("TODO_DB_DIR", Path.cwd()))
DEFAULT_DB_PATH = Path(os.getenv("TODO_DB_PATH", DEFAULT_DB_DIR / DEFAULT_DB_FILENAME)).resolve()

# File lock path for concurrency safety
LOCK_FILE_PATH = Path(str(DEFAULT_DB_PATH) + ".lock")

# Plugin env var
PLUGIN_ENV_VAR = "TODO_PLUGINS"

# Query DSL
DEFAULT_QUERY_LIMIT = 1000

# Cache sizes
TAG_CACHE_SIZE = 256
ALIAS_CACHE_SIZE = 256

# Performance targets (for reporting/validation only)
PERF_TARGET_LOAD_MS = 80
PERF_TARGET_QUERY_MS = 50
PERF_TARGET_REL_MS = 10
