import pytest
import todo_original
import todo_advanced


def setup_function(func):
    # Reset the in-memory baseline storage before each test
    todo_original._todos.clear()


def test_add_and_list_via_advanced():
    todo_advanced.add_todo("Buy milk", tags=["groceries"])
    todos_from_advanced = todo_advanced.list_todos()
    todos_direct = todo_original.list_todos()
    assert todos_from_advanced == todos_direct
    assert len(todos_from_advanced) == 1
    assert todos_from_advanced[0]["task"] == "Buy milk"
    assert todos_from_advanced[0]["tags"] == ["groceries"]


def test_tag_manipulation_preserved():
    todo_advanced.add_todo("Call Alice", tags=["personal"])
    todo_advanced.add_tag_to_task(0, "urgent")
    assert "urgent" in todo_advanced.list_todos()[0]["tags"]
    todo_advanced.remove_tag_from_task(0, "personal")
    assert "personal" not in todo_advanced.list_todos()[0]["tags"]


def test_filter_and_stats_preserved():
    todo_advanced.add_todo("X", tags=["a", "b"])
    todo_advanced.add_todo("Y", tags=["b"])
    filtered = todo_advanced.filter_by_tags(["b"], match_all=False)
    assert len(filtered) == 2
    stats = todo_advanced.show_tag_stats()
    assert stats.get("b") == 2
    assert sorted(todo_advanced.list_all_tags()) == ["a", "b"]


def test_complete_task():
    todo_advanced.add_todo("Finish", tags=[]) 
    todo_advanced.complete_task(0)
    assert todo_advanced.list_todos()[0]["completed"] is True
