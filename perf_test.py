"""Simple performance validation for todo_advanced.

Default: 10k tasks. Use --quick for 1k to speed up in CI.
"""
from __future__ import annotations
import os
import time
import argparse
from statistics import mean

from todo_advanced.storage import SQLiteStorage
from todo_advanced.manager import TodoManager


def run(num_tasks: int = 10000):
    # Use temp DB in cwd
    db_path = os.path.abspath("perf.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    storage = SQLiteStorage(db_path=db_path)
    mgr = TodoManager(storage=storage)

    t0 = time.perf_counter()
    for i in range(num_tasks):
        mgr.add_todo(f"task-{i}", tags=["bulk", "t" + str(i % 10)])
    t_add = (time.perf_counter() - t0) * 1000

    t1 = time.perf_counter()
    _ = mgr.list_todos()
    t_load = (time.perf_counter() - t1) * 1000

    # query a few
    q_times = []
    for tag in ["t1", "t5", "bulk"]:
        qs = time.perf_counter()
        _ = mgr.query(f"tag:{tag}")
        q_times.append((time.perf_counter() - qs) * 1000)

    print(f"Added {num_tasks} tasks in {t_add:.2f} ms ({t_add/num_tasks:.4f} ms/task)")
    print(f"Load all tasks: {t_load:.2f} ms")
    print(f"Query avg: {mean(q_times):.2f} ms (samples={len(q_times)})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="Use 1k tasks instead of 10k")
    args = parser.parse_args()
    num = 1000 if args.quick else 10000
    run(num)
