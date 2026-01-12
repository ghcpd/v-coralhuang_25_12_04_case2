# Quick Examples - Advanced TODO System

This document shows practical examples of using the advanced TODO system.

## Setup

```python
import sys
sys.path.insert(0, '.')

# Simple usage (backward compatible)
import todo_advanced as todo

# Or advanced usage
from todo_advanced import TodoAdvanced
```

## Example 1: Backward Compatible Usage

```python
import todo_advanced as todo

# Add tasks
todo.add_todo("Buy groceries", tags=["shopping", "personal"])
todo.add_todo("Fix bug #123", tags=["work", "urgent"])
todo.add_todo("Read article", tags=["personal", "learning"])

# List all tasks
print("All tasks:")
for task in todo.list_todos():
    print(f"  - {task['task']} {task['tags']}")

# Filter by tags (OR logic)
print("\nWork or urgent tasks:")
work_tasks = todo.filter_by_tags(["work", "urgent"], match_all=False)
for task in work_tasks:
    print(f"  - {task['task']}")

# Filter with AND logic
print("\nUrgent work tasks:")
urgent_work = todo.filter_by_tags(["work", "urgent"], match_all=True)
for task in urgent_work:
    print(f"  - {task['task']}")

# Mark task complete
tasks = todo.list_todos()
if tasks:
    todo.complete_task(0)
    print(f"\n✓ Completed: {tasks[0]['task']}")

# View statistics
print("\nTag statistics:")
stats = todo.show_tag_stats()
for tag, count in sorted(stats.items(), key=lambda x: -x[1]):
    print(f"  {tag}: {count}")
```

## Example 2: Advanced Querying

```python
from todo_advanced import TodoAdvanced

# Create advanced instance
db = TodoAdvanced(db_path="my_todos.db")

# Add varied tasks
db.add_todo("Fix critical bug", tags=["work", "urgent", "bug"])
db.add_todo("Deploy to production", tags=["work", "urgent", "deployment"])
db.add_todo("Review code", tags=["work"])
db.add_todo("Team meeting", tags=["work", "meeting"])
db.add_todo("Read book", tags=["personal", "learning"])
db.add_todo("Archive old emails", tags=["administrative", "cleanup"])

# Simple queries
print("Tasks tagged 'work':")
results = db.query("work")
for task in results:
    print(f"  - {task['task']}")

# Complex queries
print("\nUrgent work (not archived):")
results = db.query("work AND urgent AND NOT administrative")
for task in results:
    print(f"  - {task['task']}")

print("\nBug fix or deployment:")
results = db.query("bug OR deployment")
for task in results:
    print(f"  - {task['task']}")

print("\nMeetings and reviews:")
results = db.query("(meeting OR review) AND work")
for task in results:
    print(f"  - {task['task']}")

db.close()
```

## Example 3: Tag Metadata and Recommendations

```python
from todo_advanced import TodoAdvanced

db = TodoAdvanced(db_path="todos.db")

# Create tags with metadata
work_tag = db.create_tag_with_metadata(
    "work",
    color="#FF6B6B",  # Red
    description="Work-related tasks",
    aliases=["job", "office"]
)

urgent_tag = db.create_tag_with_metadata(
    "urgent",
    color="#FFA500",  # Orange
    description="Needs immediate attention",
    aliases=["asap", "critical"]
)

# Add some tasks
db.add_todo("Fix bug in login", tags=["work", "urgent", "bug"])
db.add_todo("Update documentation", tags=["work"])
db.add_todo("Code review", tags=["work", "review"])

# Get tag info
print("Work tag info:")
info = db.get_tag_info("work")
if info:
    print(f"  Name: {info['name']}")
    print(f"  Color: {info['color']}")
    print(f"  Description: {info['description']}")
    print(f"  Usage: {info['usage_count']} tasks")
    print(f"  Aliases: {info['aliases']}")

# Get recommendations for a task
print("\nRecommended tags for a new task:")
task_text = "Critical performance issue in production database"
recommendations = db.recommend_tags_for_task(
    task_text,
    existing_tags=["work"],
    top_n=3
)
for tag, score in recommendations:
    print(f"  - {tag}: {score:.2f}")

db.close()
```

## Example 4: Using Plugins

```python
from todo_advanced import TodoAdvanced

# Create instance with plugin directory
db = TodoAdvanced(db_path="todos.db", plugin_dir="plugins/")

# Add tasks - plugins will be triggered automatically
db.add_todo("Task 1", tags=["work"])  # on_task_added hook fires
db.add_todo("Task 2", tags=["personal"])

# Get tasks
tasks = db.list_todos()

# Mark task complete - on_task_completed hook fires
if tasks:
    db.complete_task(tasks[0].get("id"))

# Manual hook trigger (if needed)
db.plugin_manager.trigger_hook("on_query", expression="work", results=tasks)

db.close()
```

## Example 5: Performance Testing

```python
import time
from todo_advanced import TodoAdvanced

db = TodoAdvanced(db_path="perf_test.db")

# Measure task creation
print("Performance Test:")
start = time.time()
for i in range(100):
    db.add_todo(f"Task {i}", tags=[f"tag_{i%10}"])
elapsed = time.time() - start
print(f"  Created 100 tasks in {elapsed:.2f}s")

# Measure query performance
start = time.time()
results = db.query("tag_0 OR tag_1 OR tag_2")
elapsed = time.time() - start
print(f"  Complex query in {elapsed*1000:.2f}ms (found {len(results)} tasks)")

# Measure tag stats
start = time.time()
stats = db.show_tag_stats()
elapsed = time.time() - start
print(f"  Tag stats in {elapsed*1000:.2f}ms ({len(stats)} unique tags)")

db.close()
```

## Example 6: Concurrent Operations

```python
import threading
from todo_advanced import TodoAdvanced

db = TodoAdvanced(db_path="concurrent.db")

def add_tasks(thread_id):
    """Add tasks from multiple threads."""
    for i in range(10):
        db.add_todo(
            f"Thread {thread_id} Task {i}",
            tags=[f"thread_{thread_id}"]
        )

# Create and start threads
threads = [
    threading.Thread(target=add_tasks, args=(i,))
    for i in range(5)
]

for t in threads:
    t.start()

# Wait for completion
for t in threads:
    t.join()

# Verify all tasks were created safely
tasks = db.list_todos()
print(f"✓ Created {len(tasks)} tasks across 5 threads safely")

db.close()
```

## Example 7: Data Migration from Original

```python
import todo_original
from todo_advanced import TodoAdvanced

# Get data from original TODO system
original_tasks = todo_original.list_todos()
original_tags = todo_original.list_all_tags()

# Migrate to advanced system
advanced = TodoAdvanced(db_path="migrated.db")

print(f"Migrating {len(original_tasks)} tasks...")
for task in original_tasks:
    advanced.add_todo(
        task["task"],
        tags=task.get("tags", [])
    )

print(f"Migrated {len(original_tasks)} tasks")
print(f"Found {len(original_tags)} tags")

# Verify
advanced_tasks = advanced.list_todos()
advanced_tags = advanced.list_all_tags()
print(f"Advanced system has {len(advanced_tasks)} tasks, {len(advanced_tags)} tags")

advanced.close()
```

## Example 8: Creating a Custom Plugin

```python
# File: plugins/my_plugin.py

statistics = {"added": 0, "completed": 0}

def register(plugin_manager):
    """Called when plugin loads."""
    plugin_manager.register_hook("on_task_added", on_task)
    plugin_manager.register_hook("on_task_completed", on_complete)
    print("[MyPlugin] Registered")

def on_task(task_id, task, tags):
    """Called when task is added."""
    global statistics
    statistics["added"] += 1
    if len(tags) > 2:
        print(f"[MyPlugin] Complex task added: {task}")

def on_complete(task_id):
    """Called when task is completed."""
    global statistics
    statistics["completed"] += 1
    if statistics["completed"] % 5 == 0:
        print(f"[MyPlugin] You've completed {statistics['completed']} tasks!")

# Usage:
# from todo_advanced import TodoAdvanced
# db = TodoAdvanced(plugin_dir="plugins/")
# db.add_todo("Task", tags=["a", "b", "c"])  # Triggers on_task
# db.complete_task(task_id)  # Triggers on_complete
```

## Example 9: Working with Different Tag Strategies

```python
from todo_advanced import TodoAdvanced

db = TodoAdvanced()

# Strategy 1: Many small tags (fine-grained)
db.add_todo("Fix login bug", tags=["bug", "auth", "high-priority"])
db.add_todo("Update docs", tags=["documentation", "low-priority"])

# Strategy 2: Hierarchical tags (using aliases)
work_tag = db.create_tag_with_metadata(
    "work",
    aliases=["job", "professional", "office"]
)

# Strategy 3: Status tags
db.create_tag_with_metadata("status:todo", color="#CCCCCC")
db.create_tag_with_metadata("status:in-progress", color="#FFFF00")
db.create_tag_with_metadata("status:done", color="#00FF00")

# Strategy 4: Context tags (GTD method)
db.create_tag_with_metadata("@home", color="#00FFFF")
db.create_tag_with_metadata("@work", color="#FF0000")
db.create_tag_with_metadata("@computer", color="#0000FF")

# Add task using multiple strategies
db.add_todo(
    "Email client about project",
    tags=["work", "@work", "status:todo", "high-priority"]
)

# Query across strategies
important_work = db.query("@work AND NOT status:done")
print(f"Found {len(important_work)} important work tasks")

db.close()
```

## Example 10: Analytics and Reporting

```python
from todo_advanced import TodoAdvanced
from collections import Counter

db = TodoAdvanced()

# Add varied tasks
tasks_data = [
    ("Bug in payment system", ["work", "urgent", "bug"]),
    ("Review PR", ["work", "code-review"]),
    ("Team standup", ["work", "meeting"]),
    ("Buy milk", ["personal", "shopping"]),
    ("Gym", ["personal", "health"]),
    ("Learn Python", ["personal", "learning"]),
]

for task, tags in tasks_data:
    db.add_todo(task, tags=tags)

# Analytics
all_tasks = db.list_todos()
all_tags = db.list_all_tags()
tag_stats = db.show_tag_stats()

print("=== TODO Analytics ===")
print(f"Total tasks: {len(all_tasks)}")
print(f"Total tags: {len(all_tags)}")
print(f"Completed: {sum(1 for t in all_tasks if t['completed'])}")
print(f"Pending: {sum(1 for t in all_tasks if not t['completed'])}")

print("\nTag frequency:")
for tag, count in sorted(tag_stats.items(), key=lambda x: -x[1]):
    print(f"  {tag}: {count}")

print("\nWork vs Personal:")
work_count = len(db.query("work"))
personal_count = len(db.query("personal"))
print(f"  Work: {work_count}")
print(f"  Personal: {personal_count}")

db.close()
```

---

These examples demonstrate:
- ✅ Backward compatibility with original API
- ✅ Advanced DSL queries
- ✅ Tag metadata management
- ✅ Plugin system
- ✅ Performance characteristics
- ✅ Concurrent operations
- ✅ Data migration
- ✅ Custom plugins
- ✅ Tag organization strategies
- ✅ Analytics capabilities

For complete API documentation, see `README.md` and `FEATURE_SPEC.md`.
