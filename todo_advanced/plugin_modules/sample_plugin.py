"""
Sample plugin demonstrating hook usage.
"""

def on_task_added(task_dict):
    print(f"[plugin] Task added: {task_dict['task']}")

def on_tag_added(tag_name):
    print(f"[plugin] Tag added: {tag_name}")

def on_task_completed(task_dict):
    print(f"[plugin] Task completed: {task_dict['task']}")
