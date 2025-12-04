from todo_advanced.manager import TodoManager


def test_query_dsl(manager):
    manager.add_todo("task1", tags=["work", "urgent"])
    manager.add_todo("task2", tags=["personal"])
    manager.add_todo("task3", tags=["work"])

    res = manager.query("tag:work AND NOT tag:urgent")
    assert len(res) == 1 and res[0]["task"] == "task3"

    res2 = manager.query("urgent OR personal")
    assert {r["task"] for r in res2} == {"task1", "task2"}
