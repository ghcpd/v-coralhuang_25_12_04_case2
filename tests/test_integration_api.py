import os
import importlib
import pytest
import todo_advanced
import todo_advanced_pkg


def test_advanced_api_uses_backend(tmp_path, monkeypatch):
    db_file = tmp_path / "integ.db"
    monkeypatch.setenv("TODO_DB", str(db_file))
    # reload backend module to ensure singleton reset
    importlib.reload(todo_advanced_pkg.backend)
    # Use advanced API which should now use the sqlite backend
    todo_advanced.add_todo("Advanced Task", tags=["x"])
    todos = todo_advanced.list_todos()
    assert any(t["task"] == "Advanced Task" for t in todos)
    # Modify via advanced API and assert persisted behavior
    todo_advanced.add_tag_to_task(0, "y")
    assert "y" in todo_advanced.list_todos()[0]["tags"]
    todo_advanced.remove_tag_from_task(0, "x")
    assert "x" not in todo_advanced.list_todos()[0]["tags"]
    todo_advanced.complete_task(0)
    assert todo_advanced.list_todos()[0]["completed"] is True
