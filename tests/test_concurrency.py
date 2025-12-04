import os
import importlib
import threading
import pytest
import todo_advanced
import todo_advanced_pkg


def worker_add(n, prefix="t"):
    for i in range(n):
        todo_advanced.add_todo(f"{prefix}-{i}")


def test_concurrent_writes(tmp_path, monkeypatch):
    db_file = tmp_path / "concurrent.db"
    monkeypatch.setenv("TODO_DB", str(db_file))
    importlib.reload(todo_advanced_pkg.backend)
    todo_advanced_pkg.backend._backend_singleton = None
    backend = todo_advanced.get_backend()
    assert backend is not None
    threads = []
    per_thread = 200
    num_threads = 5
    for i in range(num_threads):
        t = threading.Thread(target=worker_add, args=(per_thread, f"thread{i}"))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    # Check total tasks written
    assert backend.count_tasks() == per_thread * num_threads
