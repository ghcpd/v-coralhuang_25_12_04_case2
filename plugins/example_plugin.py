"""
Example plugin demonstrating the plugin hook system.

This plugin shows how to:
- Register hooks
- Handle task events
- Perform custom logic
"""

task_count = 0
completion_count = 0


def register(plugin_manager):
    """Called when plugin is loaded."""
    print("[Plugin] Registering example plugin hooks...")
    plugin_manager.register_hook("on_task_added", handle_task_added)
    plugin_manager.register_hook("on_task_completed", handle_task_completed)
    print("[Plugin] Example plugin ready")


def handle_task_added(task_id, task, tags):
    """Called when a task is added."""
    global task_count
    task_count += 1
    print(f"[Plugin] Task #{task_count} added: {task}")
    if tags:
        print(f"[Plugin]   Tags: {', '.join(tags)}")


def handle_task_completed(task_id):
    """Called when a task is completed."""
    global completion_count
    completion_count += 1
    print(f"[Plugin] Task completed! ({completion_count} total completions)")
