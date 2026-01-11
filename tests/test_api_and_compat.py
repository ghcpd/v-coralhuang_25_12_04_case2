import os
import tempfile
from todo_advanced_pkg.api import TodoAdvanced
import todo_advanced as ta_wrapper


def test_basic_add_list_and_compat_wrapper():
    t = TodoAdvanced()
    t.add_todo("buy milk", ["shopping", "urgent"])
    t.add_todo("read book", ["personal"])
    todos = t.list_todos()
    assert any("buy milk" == item["task"] for item in todos)

    # wrapper module exists and supports same simple function names
    ta_wrapper.add_todo("wrap task", ["wrap"])
    wlist = ta_wrapper.list_todos()
    assert any("wrap task" == item["task"] for item in wlist)

