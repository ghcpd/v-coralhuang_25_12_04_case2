CALLS = {"added": [], "tags": [], "completed": []}


def on_task_added(task):
    CALLS["added"].append(task)


def on_tag_added(tag, task):
    CALLS["tags"].append((tag, task))


def on_task_completed(task_id):
    CALLS["completed"].append(task_id)
