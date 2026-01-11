from todo_advanced_pkg.storage import SQLiteStorage


def test_bulk_add_and_counts(tmp_path):
    dbfile = str(tmp_path / "bulk.sqlite")
    s = SQLiteStorage(dbfile)
    items = [(f"t{i}", ["x", f"v{i%3}"]) for i in range(100)]
    s.add_tasks_bulk(items)
    all_tasks = s.list_tasks()
    assert len(all_tasks) == 100
    # check tag usage counts present
    tags = {t.name: t.usage_count for t in s.list_tags()}
    assert tags.get("x", 0) == 100
