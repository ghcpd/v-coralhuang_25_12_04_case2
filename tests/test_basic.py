import os
import time
from todo_advanced.api import get_storage, add_todo, list_todos, add_tag_to_task, remove_tag_from_task, show_tag_stats, list_all_tags, complete_task


def setup_function(fn):
    # remove db to start fresh
    db = os.path.join(os.path.dirname(__file__), '..', 'todo_data.db')
    try:
        os.remove(db)
    except Exception:
        pass


def test_add_and_list():
    add_todo('task1', tags=['work'])
    add_todo('task2', tags=['personal', 'urgent'])
    tasks = list_todos()
    assert len(tasks) == 2
    assert any('work' in t['tags'] for t in tasks)


def test_tag_add_remove_and_stats():
    add_todo('task3', tags=['misc'])
    tasks = list_todos()
    idx = [i for i,t in enumerate(tasks) if t['task']=='task3'][0]
    add_tag_to_task(idx, 'newtag')
    tasks = list_todos()
    assert 'newtag' in tasks[idx]['tags']
    remove_tag_from_task(idx, 'newtag')
    tasks = list_todos()
    assert 'newtag' not in tasks[idx]['tags']
    stats = show_tag_stats()
    assert isinstance(stats, dict)
    tags = list_all_tags()
    assert 'misc' in tags


def test_complete_task():
    add_todo('task4')
    tasks = list_todos()
    idx = [i for i,t in enumerate(tasks) if t['task']=='task4'][0]
    complete_task(idx)
    tasks = list_todos()
    assert tasks[idx]['completed'] is True
