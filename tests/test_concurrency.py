import threading
from todo_advanced.api import add_todo, list_todos


def worker(n):
    for i in range(n):
        add_todo(f'c_task_{i}', tags=['concurrent'])


def test_concurrent_writes():
    threads = [threading.Thread(target=worker, args=(50,)) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    tasks = list_todos()
    assert sum(1 for t in tasks if 'concurrent' in t['tags']) >= 200
