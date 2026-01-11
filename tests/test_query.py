from todo_advanced_pkg import query


def test_parse_and_evaluate_simple():
    expr = "tag:work AND (urgent OR personal) AND NOT archived"
    tree = query.parse(expr)
    # simple shape check
    assert isinstance(tree, tuple)


def test_filter_tasks():
    tasks = [
        {"task": "finish report", "tags": ["work", "urgent"]},
        {"task": "take cat to vet", "tags": ["personal"]},
        {"task": "old", "tags": ["archived"]},
    ]
    res = query.filter_tasks(tasks, "tag:work AND (urgent OR personal) AND NOT archived")
    assert len(res) == 1 and res[0]["task"] == "finish report"
