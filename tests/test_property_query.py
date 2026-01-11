import pytest

# Hypothesis is an optional dev dependency; skip property tests when not installed
hypothesis = pytest.importorskip("hypothesis", reason="hypothesis not installed; skipping property tests")
from hypothesis import given, strategies as st
from todo_advanced_pkg import query


words = st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=8)


@given(st.lists(st.tuples(words, st.lists(words, max_size=3)), min_size=1, max_size=10))
def test_random_tasks_do_not_crash(data):
    # construct a few tasks with random words and tags, then run random simple queries
    tasks = []
    for t, tags in data:
        tasks.append({"task": t, "tags": tags})

    # build a trivial query from a random word
    if tasks:
        qword = tasks[0]["task"][:4]
        # ensure parser doesn't throw on basic queries
        res = query.filter_tasks(tasks, f"{qword} OR tag:{(tasks[0]['tags'][0] if tasks[0]['tags'] else 'x')}")
        assert isinstance(res, list)
