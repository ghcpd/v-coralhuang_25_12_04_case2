import os
import pytest
import todo_advanced
import todo_advanced_pkg


def test_persistence_backend_absent_by_default():
    # By default, without TODO_DB environment variable, no backend should be provided
    if "TODO_DB" in os.environ:
        del os.environ["TODO_DB"]
    # Ensure any previous singleton is cleared so get_backend reflects env
    todo_advanced_pkg.backend._backend_singleton = None
    backend = todo_advanced.get_backend()
    assert backend is None


def test_sqlite_backend_persists_across_instances(tmp_path, monkeypatch):
    db_file = tmp_path / "test_todos.db"
    monkeypatch.setenv("TODO_DB", str(db_file))
    # Ensure singleton cleared
    import importlib
    importlib.reload(todo_advanced_pkg.backend)
    backend = todo_advanced.get_backend()
    assert backend is not None
    backend.add_todo("Persisted Task", tags=["p"])
    todos = backend.list_todos()
    assert any(t["task"] == "Persisted Task" for t in todos)
    # Close and reset singleton so a fresh instance reads the DB file
    backend.close()
    todo_advanced_pkg.backend._backend_singleton = None
    backend2 = todo_advanced.get_backend()
    assert backend2 is not None
    todos2 = backend2.list_todos()
    assert any(t["task"] == "Persisted Task" for t in todos2)
