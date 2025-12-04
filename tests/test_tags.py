from todo_advanced_pkg.api import TodoAdvanced


def test_tag_create_and_info():
    ta = TodoAdvanced()
    ta.create_or_update_tag("work", aliases=["office"], color="#ff0000", description="work-related")
    info = ta.get_tag_info("work")
    assert info is not None
    assert "office" in info["aliases"]
    assert info["color"] == "#ff0000"


def test_tag_usage_and_cooccurrence():
    ta = TodoAdvanced()
    ta.add_todo("task1", ["a", "b"])
    ta.add_todo("task2", ["a", "c"])
    # usage counts should reflect occurrences
    info_a = ta.get_tag_info("a")
    assert info_a is not None and info_a["usage_count"] >= 2

    # cooccurrence: a->b and a->c should exist
    co = ta.get_cooccurrence("a", limit=10)
    assert any(pair[0] == "b" for pair in co)
    assert any(pair[0] == "c" for pair in co)
