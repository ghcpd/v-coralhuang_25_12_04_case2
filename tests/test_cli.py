from todo_advanced.cli import fuzzy_search_tasks, colorize_task
from todo_advanced.api import add_todo


def test_fuzzy_and_colorize():
    add_todo('cli task example', tags=['cli'])
    results = fuzzy_search_tasks('cl task')
    assert results
    s = colorize_task(results[0])
    assert 'cli' in s
