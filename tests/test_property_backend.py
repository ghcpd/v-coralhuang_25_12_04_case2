import os
import importlib
import random
import tempfile
import pytest
pytest.importorskip("hypothesis")
from hypothesis import given, strategies as st
import todo_original
import todo_advanced
import todo_advanced_pkg


OP_ADD = "add"
OP_ADD_TAG = "add_tag"
OP_REMOVE_TAG = "remove_tag"
OP_COMPLETE = "complete"

@st.composite
def op_sequence(draw):
    length = draw(st.integers(min_value=1, max_value=30))
    ops = []
    for _ in range(length):
        op = draw(st.sampled_from([OP_ADD, OP_ADD_TAG, OP_REMOVE_TAG, OP_COMPLETE]))
        if op == OP_ADD:
            task = draw(st.text(min_size=1, max_size=20))
            tags = draw(st.lists(st.text(min_size=1, max_size=10), max_size=3))
            ops.append((OP_ADD, task, tags))
        elif op == OP_ADD_TAG:
            idx = draw(st.integers(min_value=0, max_value=5))
            tag = draw(st.text(min_size=1, max_size=10))
            ops.append((OP_ADD_TAG, idx, tag))
        elif op == OP_REMOVE_TAG:
            idx = draw(st.integers(min_value=0, max_value=5))
            tag = draw(st.text(min_size=1, max_size=10))
            ops.append((OP_REMOVE_TAG, idx, tag))
        else:
            idx = draw(st.integers(min_value=0, max_value=5))
            ops.append((OP_COMPLETE, idx))
    return ops


@given(op_sequence())
def test_random_operations_equivalence(ops):
    # Reset original in-memory and a fresh sqlite backend
    todo_original._todos.clear()
    db_file = tempfile.NamedTemporaryFile(prefix="prop_", delete=False)
    db_path = db_file.name
    db_file.close()
    # ensure fresh backend
    importlib.reload(todo_advanced_pkg.backend)
    todo_advanced_pkg.backend._backend_singleton = None
    os.environ["TODO_DB"] = db_path
    backend = todo_advanced.get_backend()
    assert backend is not None

    for op in ops:
        if op[0] == OP_ADD:
            _, task, tags = op
            todo_original.add_todo(task, tags=tags)
            todo_advanced.add_todo(task, tags=tags)
        elif op[0] == OP_ADD_TAG:
            _, idx, tag = op
            try:
                todo_original.add_tag_to_task(idx, tag)
            except IndexError:
                pass
            try:
                todo_advanced.add_tag_to_task(idx, tag)
            except IndexError:
                pass
        elif op[0] == OP_REMOVE_TAG:
            _, idx, tag = op
            try:
                todo_original.remove_tag_from_task(idx, tag)
            except IndexError:
                pass
            try:
                todo_advanced.remove_tag_from_task(idx, tag)
            except IndexError:
                pass
        elif op[0] == OP_COMPLETE:
            _, idx = op
            try:
                todo_original.complete_task(idx)
            except IndexError:
                pass
            try:
                todo_advanced.complete_task(idx)
            except IndexError:
                pass

    # Compare visible states
    o = todo_original.list_todos()
    a = todo_advanced.list_todos()
    assert o == a
