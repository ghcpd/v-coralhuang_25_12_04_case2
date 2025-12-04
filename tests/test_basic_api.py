import os
import tempfile
import shutil
import time
from todo_advanced import add_todo, list_todos, filter_by_tags, add_tag_to_task, remove_tag_from_task, complete_task


def test_add_and_list():
    # use default DB in tempdir
    add_todo("write tests", ["dev", "urgent"])
    res = list_todos()
    assert any(r["task"] == "write tests" for r in res)


def test_filter_tags():
    add_todo("another task", ["personal"]) 
    res_or = filter_by_tags(["dev", "personal"], match_all=False)
    assert len(res_or) >= 1
    res_and = filter_by_tags(["dev", "urgent"], match_all=True)
    assert isinstance(res_and, list)


def test_tag_modification():
    add_todo("mod task", [])
    all_tasks = list_todos()
    idx = None
    for i, t in enumerate(all_tasks):
        if t["task"] == "mod task":
            idx = i
            break
    assert idx is not None
    add_tag_to_task(idx, "x")
    remove_tag_from_task(idx, "x")
    complete_task(idx)
