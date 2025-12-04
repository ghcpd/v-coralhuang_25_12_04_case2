from todo_advanced.tags import TagService


def test_tag_alias_and_metadata(manager):
    svc = TagService(storage=manager.storage)
    svc.set_color("work", "blue")
    svc.set_description("work", "Work related tasks")
    svc.add_alias("work", "office")

    manager.add_todo("task1", tags=["office"])
    tags = svc.list_tags()
    names = [t.name for t in tags]
    assert "work" in names
    work_tag = next(t for t in tags if t.name == "work")
    assert "office" in work_tag.aliases
    assert work_tag.color == "blue"


def test_suggestions(manager):
    manager.add_todo("file report", tags=["work"])
    manager.add_todo("gym", tags=["personal"])
    suggestions = manager.suggest_tags("report", existing_tags=[])
    assert suggestions and suggestions[0][0] == "work"
