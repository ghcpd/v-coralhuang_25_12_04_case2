import time
from todo_advanced_pkg.api import TodoAdvanced


def perf_add_and_query(n=10000):
    ta = TodoAdvanced(":memory:")
    start = time.time()
    items = [(f"task-{i}", ["bulk", f"i{i%20}"]) for i in range(n)]
    ta.storage.add_tasks_bulk(items)
    add_time = (time.time() - start) * 1000.0

    qstart = time.time()
    res = ta.query("tag:bulk AND tag:i3")
    qtime = (time.time() - qstart) * 1000.0

    print(f"added {n} tasks in {add_time:.2f}ms")
    print(f"query matched {len(res)} tasks in {qtime:.2f}ms")


if __name__ == "__main__":
    perf_add_and_query(10000)
