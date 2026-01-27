"""
Advanced TODO system with structured tags, query DSL, plugins, and persistence.

This package exposes a `TodoManager` entry point and a small set of helper
APIs used by `todo_advanced.py` to preserve backward compatibility with the
original API surface.
"""
from .manager import TodoManager

__all__ = ["TodoManager"]
