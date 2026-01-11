CALLS = {"added": [], "tags": [], "completed": []}


def on_task_added(task):
    CALLS["added"].append(task)


def on_tag_added(tag, task):
    CALLS["tags"].append((tag, task))


def on_task_completed(task_id):
    CALLS["completed"].append(task_id)


def register_query_operators():
    def starts_op(arg, task):
        # match if task text or any tag starts with arg
        t = task.get("task", "")
        if t.lower().startswith(arg.lower()):
            return True, 5
        for tg in task.get("tags", []):
            if tg.lower().startswith(arg.lower()):
                return True, 3
        return False, 0

    return {"starts": starts_op}
