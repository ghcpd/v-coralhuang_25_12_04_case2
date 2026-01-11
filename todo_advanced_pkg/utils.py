"""Utility helpers."""
from typing import Iterable


def ensure_list(x):
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]
