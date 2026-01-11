import tempfile
import os
from todo_advanced_pkg.storage import SQLiteStorage


def test_persistence_roundtrip(tmp_path):
    dbfile = os.path.join(tmp_path, "testdb.sqlite")
    s1 = SQLiteStorage(dbfile)
    s1.add_task("a task", ["t1"])
    s1.add_task("another task", ["t2"])
    s1._conn.close()

    s2 = SQLiteStorage(dbfile)
    all_tasks = s2.list_tasks()
    assert len(all_tasks) == 2
