import os
from todo_advanced.cli import fuzzy_search_tasks, colorize_task
from todo_advanced.api import add_todo


def setup_function(fn):
    # remove db to start fresh
    db = os.path.join(os.path.dirname(__file__), '..', 'todo_data.db')
    try:
        os.remove(db)
    except Exception:
        pass


def test_fuzzy_and_colorize():
    add_todo('cli task example', tags=['cli'])
    results = fuzzy_search_tasks('cli task example')
    assert results
    # Find the task we just added
    cli_task = [t for t in results if t['task'] == 'cli task example'][0]
    s = colorize_task(cli_task)
    assert '[cli]' in s and 'cli task example' in s
