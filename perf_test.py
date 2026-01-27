import time
from todo_advanced.api import add_todo, list_todos

if __name__ == '__main__':
    n = 10000
    for i in range(n):
        add_todo(f'perf_task_{i}', tags=[f'tag{i%100}'])
    t0 = time.time()
    tasks = list_todos()
    t1 = time.time()
    print(f"Loaded {len(tasks)} tasks in {t1-t0:.4f}s")
