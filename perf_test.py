import os
import time
from todo_advanced_pkg.sqlite_backend import SqliteBackend


def make_tasks(backend: SqliteBackend, n: int = 10000):
    start = time.time()
    for i in range(n):
        backend.add_todo(f"task-{i}", tags=["tag1", "auto"])
    dur = time.time() - start
    print(f"Inserted {n} tasks in {dur:.3f}s ({dur*1000/n:.2f} ms/insert)")
    return dur


def load_tasks(backend: SqliteBackend):
    start = time.time()
    tasks = backend.list_todos()
    dur = time.time() - start
    print(f"Loaded {len(tasks)} tasks in {dur:.3f}s ({dur*1000/len(tasks):.3f} ms/op)")
    return dur


if __name__ == "__main__":
    import tempfile
    db = tempfile.NamedTemporaryFile(prefix="todo_perf_", delete=False)
    db_path = db.name
    db.close()
    print("DB:", db_path)
    backend = SqliteBackend(db_path)
    n = 10000
    insert_dur = make_tasks(backend, n)
    load_dur = load_tasks(backend)
    print("Summary:")
    print(f"Insert total: {insert_dur:.3f}s; load: {load_dur:.3f}s")
    backend.close()
