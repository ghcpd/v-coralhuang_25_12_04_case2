def on_task_added(task):
    # simple plugin which prints a notification when a task is added
    print(f"[plugin] task added: {task.get('task')} (id={task.get('id')})")

def on_tag_added(tag_name):
    print(f"[plugin] tag added: {tag_name}")


def on_task_completed(task):
    print(f"[plugin] task completed: id={task.get('id')}")
