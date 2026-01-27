import os
import sys
import multiprocessing as mp

from todo_advanced.storage import SQLiteStorage


def _worker(db_path, n):
    os.environ["TODO_DB_PATH"] = db_path
    from todo_advanced.manager import TodoManager  # imported after env set
    mgr = TodoManager()
    for i in range(n):
        mgr.add_todo(f"task-{mp.current_process().name}-{i}", tags=["concurrent"])


def test_concurrent_writes(temp_db_path):
    db_path = str(temp_db_path)
    os.environ["TODO_DB_PATH"] = db_path
    num_procs = 4
    per_proc = 20
    procs = [mp.Process(target=_worker, args=(db_path, per_proc)) for _ in range(num_procs)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()

    storage = SQLiteStorage(db_path=temp_db_path)
    tasks = storage.list_tasks()
    assert len(tasks) == num_procs * per_proc
