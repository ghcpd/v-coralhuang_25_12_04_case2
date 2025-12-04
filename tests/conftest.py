import os
import shutil
import tempfile
import pytest

from todo_advanced.manager import TodoManager
from todo_advanced.storage import SQLiteStorage


@pytest.fixture()
def temp_db_path(tmp_path):
    db_path = tmp_path / "test.db"
    os.environ["TODO_DB_PATH"] = str(db_path)
    yield db_path
    # cleanup best-effort (on Windows, SQLite may hold locks briefly)
    try:
        if db_path.exists():
            db_path.unlink()
    except PermissionError:
        pass


@pytest.fixture()
def manager(temp_db_path):
    # ensure fresh DB
    if temp_db_path.exists():
        temp_db_path.unlink()
    storage = SQLiteStorage(db_path=temp_db_path)
    return TodoManager(storage=storage)
