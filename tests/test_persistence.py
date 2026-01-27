from todo_advanced.storage import SQLiteStorage
from todo_advanced.manager import TodoManager


def test_persistence_across_manager_instances(temp_db_path):
    storage1 = SQLiteStorage(db_path=temp_db_path)
    mgr1 = TodoManager(storage=storage1)
    mgr1.add_todo("persisted", tags=["work"])

    storage2 = SQLiteStorage(db_path=temp_db_path)
    mgr2 = TodoManager(storage=storage2)
    todos = mgr2.list_todos()
    assert len(todos) == 1
    assert todos[0]["task"] == "persisted"
