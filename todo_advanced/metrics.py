"""Simple metrics capturing helpers."""
from __future__ import annotations
import contextlib
import time
from typing import Dict

_metrics: Dict[str, float] = {}


@contextlib.contextmanager
def timed(name: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = (time.perf_counter() - start) * 1000.0
        _metrics[name] = elapsed


def get_metrics() -> Dict[str, float]:
    return dict(_metrics)
