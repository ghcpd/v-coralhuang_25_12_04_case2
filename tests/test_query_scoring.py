from todo_advanced_pkg.api import TodoAdvanced


def test_query_scoring_orders_results():
    ta = TodoAdvanced()
    ta.add_todo("urgent review", ["work", "urgent"])
    ta.add_todo("work item", ["work"])
    ta.add_todo("personal note", ["personal"])

    scored = ta.query("tag:work OR tag:urgent", scored=True)
    # we expect the item matching both work and urgent to have higher score
    assert len(scored) >= 2
    assert scored[0]["task"] == "urgent review"
    assert scored[0]["_score"] >= scored[1]["_score"]
