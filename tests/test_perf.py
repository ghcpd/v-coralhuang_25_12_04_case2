import time
from todo_advanced.api import add_todo, list_todos


def test_perf_10k_insert_and_load():
    n = 10000
    for i in range(n):
        add_todo(f'p_task_{i}', tags=[f't{i%50}'])
    t0 = time.time()
    tasks = list_todos()
    t1 = time.time()
    elapsed = (t1 - t0)
    print(f"loaded {len(tasks)} tasks in {elapsed:.4f}s")
    assert len(tasks) >= n
    assert elapsed < 0.5  # fast enough on modern machines
