"""Validation helpers for tasks and tags."""
from __future__ import annotations
from typing import Optional

MAX_TAG_LENGTH = 64
MAX_TASK_LENGTH = 1024


def validate_tag_name(name: str) -> None:
    if not name or not name.strip():
        raise ValueError("tag name cannot be empty")
    if len(name) > MAX_TAG_LENGTH:
        raise ValueError("tag name too long")


def validate_task_text(text: str) -> None:
    if not text or not text.strip():
        raise ValueError("task text cannot be empty")
    if len(text) > MAX_TASK_LENGTH:
        raise ValueError("task text too long")


def normalize_tag(name: str) -> str:
    return name.strip().lower()
