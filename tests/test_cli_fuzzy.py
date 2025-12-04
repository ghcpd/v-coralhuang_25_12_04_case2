from todo_advanced_pkg.cli import fuzzy_search_tasks, paginate_tasks


def test_fuzzy_and_paging():
    tasks = [
        {"task": "buy milk", "tags": ["shopping"]},
        {"task": "buy almond milk", "tags": ["shopping"]},
        {"task": "review PR", "tags": ["work"]},
        {"task": "urgent meeting", "tags": ["work", "urgent"]},
    ]

    res = fuzzy_search_tasks(tasks, "milk")
    assert len(res) >= 2

    pages = list(paginate_tasks(res, page_size=1))
    assert len(pages) == len(res)
