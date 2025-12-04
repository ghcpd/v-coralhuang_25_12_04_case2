from hypothesis import given, strategies as st
from todo_advanced.api import add_todo, show_tag_stats, list_todos

@given(st.lists(st.text(min_size=1, max_size=6), min_size=1, max_size=10))
def test_usage_counts(tags):
    # add a task with given tags and check usage counts > 0
    add_todo('prop_task', tags=[t.replace(' ', '_') for t in tags])
    stats = show_tag_stats()
    for t in tags:
        name = t.replace(' ', '_')
        assert stats.get(name, 0) >= 1
