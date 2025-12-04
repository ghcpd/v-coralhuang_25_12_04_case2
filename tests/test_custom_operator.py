from todo_advanced_pkg.api import TodoAdvanced


def test_custom_operator_starts():
    ta = TodoAdvanced()
    ta.add_todo("urgent:send invoice", ["finance"])
    ta.add_todo("urgent meeting", ["work"])
    ta.add_todo("normal note", ["misc"])

    res = ta.query("starts:urgent", scored=False)
    assert any("send invoice" in t["task"] for t in res)
    assert any("urgent meeting" in t["task"] for t in res)

    scored = ta.query("starts:urgent", scored=True)
    assert scored[0]["_score"] >= scored[-1]["_score"]
