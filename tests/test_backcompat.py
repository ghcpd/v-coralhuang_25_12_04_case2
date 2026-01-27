from todo_advanced import TodoManager


def test_basic_add_and_list(manager):
    manager.add_todo("task1", tags=["work"])
    manager.add_todo("task2", tags=["personal", "urgent"])

    todos = manager.list_todos()
    assert len(todos) == 2
    assert todos[0]["task"] == "task1"
    assert todos[0]["tags"] == ["work"]
    assert todos[0]["completed"] is False


def test_filter_by_tags(manager):
    manager.add_todo("task1", tags=["work"])
    manager.add_todo("task2", tags=["personal", "urgent"])
    manager.add_todo("task3", tags=["work", "urgent"])

    res_or = manager.filter_by_tags(["urgent"], match_all=False)
    res_and = manager.filter_by_tags(["work", "urgent"], match_all=True)

    assert {r["task"] for r in res_or} == {"task2", "task3"}
    assert len(res_and) == 1 and res_and[0]["task"] == "task3"


def test_complete_and_tags(manager):
    manager.add_todo("task1", tags=["work"])
    manager.complete_task(0)
    todos = manager.list_todos()
    assert todos[0]["completed"] is True

    manager.add_tag_to_task(0, "urgent")
    todos = manager.list_todos()
    assert "urgent" in todos[0]["tags"]
    manager.remove_tag_from_task(0, "work")
    todos = manager.list_todos()
    assert "work" not in todos[0]["tags"]
