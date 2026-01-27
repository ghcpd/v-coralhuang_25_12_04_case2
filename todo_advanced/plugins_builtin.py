"""Built-in plugins (minimal)."""
from __future__ import annotations

# Example hooks; by default they do nothing but can be extended.

def on_task_added(task_id: int, task: str, tags):
    # placeholder: could implement auto-tagging
    return None


def on_task_completed(task_id: int):
    return None


def on_tag_added(task_id: int, tag: str):
    return None
