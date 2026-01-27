import os
import tempfile
from hypothesis import given, strategies as st, settings, HealthCheck
from todo_advanced.manager import TodoManager
from todo_advanced.storage import SQLiteStorage


@st.composite
def tasks_with_tags(draw):
    task_text = draw(st.text(min_size=1, max_size=20).filter(lambda s: bool(s.strip())))
    tags = draw(st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=3))
    # normalize empty/whitespace tags out
    tags = [t.strip() for t in tags if t.strip()]
    return task_text, tags


def expected_filter(tasks, tag, match_all=False):
    if not tag:
        return tasks
    out = []
    target_tags = tag if match_all else [tag]
    for t in tasks:
        task_tags = set(t[1])
        if match_all:
            if all(tt in task_tags for tt in target_tags):
                out.append(t)
        else:
            if tag in task_tags:
                out.append(t)
    return out


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None, max_examples=50)
@given(st.lists(tasks_with_tags(), min_size=1, max_size=10), st.text(min_size=1, max_size=5))
def test_filter_matches_manual(tasks, tag):
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        db_path = os.path.join(td, "test.db")
        os.environ["TODO_DB_PATH"] = db_path
        storage = SQLiteStorage(db_path=db_path)
        mgr = TodoManager(storage=storage)
        added = []
        for task_text, tags in tasks:
            mgr.add_todo(task_text, tags=tags)
            added.append((task_text, tags))
        res = mgr.filter_by_tags([tag], match_all=False)
        expected = [t for t in added if tag in t[1]]
        assert {r["task"] for r in res} == {t[0] for t in expected}
