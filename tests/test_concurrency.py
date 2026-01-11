import threading
import tempfile
import os
from todo_advanced_pkg.storage import SQLiteStorage


def _worker(storage, count, prefix):
    for i in range(count):
        storage.add_task(f"{prefix}-{i}", ["concurrency"])


def test_concurrent_writes(tmp_path):
    dbfile = os.path.join(tmp_path, "concurrent.sqlite")
    s = SQLiteStorage(dbfile)
    threads = []
    for n in range(5):
        t = threading.Thread(target=_worker, args=(s, 50, f"t{n}"))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    rows = s.list_tasks()
    assert len(rows) == 5 * 50
