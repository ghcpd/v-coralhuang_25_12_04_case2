import time
from todo_advanced import add_todo, list_todos


def perf_load(n=10000):
    t0 = time.time()
    for i in range(n):
        add_todo(f"perf task {i}", ["perf"])
    t1 = time.time()
    print(f"Inserted {n} tasks in {t1-t0:.3f}s")
    t0 = time.time()
    _ = list_todos()
    t1 = time.time()
    print(f"Listed tasks in {t1-t0:.3f}s")


if __name__ == "__main__":
    perf_load(1000)
