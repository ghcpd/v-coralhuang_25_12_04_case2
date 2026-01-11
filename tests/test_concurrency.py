import threading
from todo_advanced import add_todo, list_todos


def worker(n):
    for i in range(n):
        add_todo(f"coro task {i}", ["concurrent"])


def test_concurrent_writes():
    threads = [threading.Thread(target=worker, args=(10,)) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    res = list_todos()
    assert len([r for r in res if r["task"].startswith("coro task")]) >= 40
