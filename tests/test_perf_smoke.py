import time
import pytest


@pytest.mark.performance
def test_load_1000_tasks_under_500ms(manager):
    # create tasks
    for i in range(1000):
        manager.add_todo(f"task-{i}", tags=["bulk"])
    start = time.perf_counter()
    todos = manager.list_todos()
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert len(todos) == 1000
    assert elapsed_ms < 500  # generous for CI
