# Advanced Tag System for TODO Application

A modern, production-ready tag system that extends a minimal TODO list with persistent storage, advanced tag features, query DSL, and a plugin architecture.

## Features

### Core Features
- **Backward Compatible**: Existing `todo_original.py` API works unchanged
- **Persistent Storage**: SQLite database with automatic schema management
- **Structured Tags**: Tags with metadata (colors, descriptions, aliases, timestamps)
- **Tag Relationships**: Automatic tracking of co-occurring tags
- **Usage Statistics**: Track how often each tag is used
- **Thread-Safe**: Concurrent operations protected by locks

### Advanced Features
- **Query DSL**: Mini language for complex tag queries
  ```
  tag:work AND (urgent OR personal) AND NOT archived
  ```
- **Tag Recommendations**: 
  - Keyword similarity matching
  - Co-occurrence based suggestions
  - Task context awareness
- **Plugin System**: Auto-discovery and hook-based plugin architecture
- **Tag Aliases**: Define alternative names for tags
- **Metrics & Analytics**: Built-in performance and usage tracking

## Installation

### Quick Start (Windows PowerShell)

```powershell
.\run_tests.ps1
```

### Manual Setup

1. **Create virtual environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **Install dependencies**:
   ```
   pip install -r requirements-dev.txt
   ```

3. **Run tests**:
   ```
   python -m pytest tests/
   ```

## Usage

### Basic Usage (Backward Compatible)

```python
import todo_advanced as todo

# Add tasks with tags
todo.add_todo("Buy groceries", tags=["shopping", "personal"])
todo.add_todo("Fix bug", tags=["work", "urgent"])

# List all tasks
print(todo.list_todos())

# Filter by tags (OR logic by default)
work_items = todo.filter_by_tags(["work"])

# Filter with AND logic
urgent_work = todo.filter_by_tags(["work", "urgent"], match_all=True)

# View statistics
print(todo.show_tag_stats())
```

### Advanced Usage

```python
from todo_advanced import TodoAdvanced

# Create advanced instance
todo = TodoAdvanced(db_path="my_todos.db")

# Query using DSL
results = todo.query("tag:work AND (urgent OR deadline)")

# Create tags with metadata
todo.create_tag_with_metadata(
    "work",
    color="#FF0000",
    description="Work-related tasks",
    aliases=["office", "job"]
)

# Get tag recommendations
recommendations = todo.recommend_tags_for_task(
    "Fix critical bug in payment system",
    existing_tags=["work"],
    top_n=3
)

# Get detailed tag info
tag_info = todo.get_tag_info("work")
print(tag_info)  # Returns metadata including usage count, co-occurrence graph

# Register plugin hooks
def on_task_added(task_id, task, tags):
    print(f"Task added: {task}")

plugin_manager = todo.plugin_manager
plugin_manager.register_hook("on_task_added", on_task_added)
```

## Query DSL Language

The query DSL supports:
- **Tags**: `work`, `urgent`, `meeting`
- **AND operator**: `work AND urgent`
- **OR operator**: `personal OR hobby`
- **NOT operator**: `NOT archived`
- **Parentheses**: `work AND (urgent OR deadline)`
- **Complex expressions**: `tag:work AND (urgent OR personal) AND NOT archived`

## Architecture

### Module Structure

```
todo_advanced/
├── __init__.py           # Package exports
├── api.py               # Main API and backward compatibility
├── storage.py           # SQLite storage with concurrency
├── tag_model.py         # Tag metadata and TagManager
├── query_engine.py      # DSL tokenizer, parser, evaluator
├── recommender.py       # Tag recommendations
└── plugin_manager.py    # Plugin system
```

### Storage Backend

- **SQLite Database** (`todo_advanced.db` by default)
- **Thread-safe** with RLock protection
- **Tables**:
  - `tasks`: Task data, tags, completion status
  - `tags`: Tag metadata, colors, descriptions
  - `cooccurrence`: Tag relationship tracking

## Performance

Performance targets (validated by `perf_test.py`):

| Operation | Target | Notes |
|-----------|--------|-------|
| Load 1,000 tasks | < 10 ms | Scales linearly |
| Simple query | < 50 ms | DSL parsing + evaluation |
| Tag creation | < 10 ms | Per tag |
| Tag recommendation | < 20 ms | Similarity + co-occurrence |
| Concurrent writes (30 threads) | Safe | No data corruption |

## Testing

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run Specific Test Category
```bash
python -m pytest tests/test_advanced_todo.py::TestBackwardCompatibility -v
python -m pytest tests/test_advanced_todo.py::TestPersistence -v
python -m pytest tests/test_advanced_todo.py::TestQueryDSL -v
python -m pytest tests/test_advanced_todo.py::TestConcurrency -v
```

### Performance Tests
```bash
python perf_test.py
```

### Coverage Report
```bash
python -m pytest tests/ --cov=todo_advanced --cov-report=html
```

## Plugin Development

Create a plugin file in `plugins/` directory:

```python
# plugins/my_plugin.py

def register(plugin_manager):
    """Called on plugin load."""
    plugin_manager.register_hook("on_task_added", handle_task_added)
    plugin_manager.register_hook("on_task_completed", handle_task_completed)

def handle_task_added(task_id, task, tags):
    """Called when a task is added."""
    print(f"Task added: {task}")

def handle_task_completed(task_id):
    """Called when a task is completed."""
    print(f"Task completed: {task_id}")
```

Load plugins:
```python
todo = TodoAdvanced(db_path="todos.db", plugin_dir="plugins/")
```

## API Reference

### Core API (Backward Compatible)

- `add_todo(task, tags)` - Add a task
- `list_todos()` - Get all tasks
- `filter_by_tags(tags, match_all)` - Filter tasks by tags
- `add_tag_to_task(index, tag)` - Add tag to task by index
- `remove_tag_from_task(index, tag)` - Remove tag from task
- `complete_task(index)` - Mark task completed
- `show_tag_stats()` - Get tag usage statistics
- `list_all_tags()` - Get all distinct tags

### Advanced API

- `TodoAdvanced(db_path, plugin_dir)` - Create advanced instance
- `query(expression)` - Execute DSL query
- `recommend_tags_for_task(task, tags, top_n)` - Get tag recommendations
- `create_tag_with_metadata(name, color, description, aliases)` - Create structured tag
- `get_tag_info(tag_name)` - Get tag metadata
- `plugin_manager.register_hook(hook_name, callback)` - Register plugin hook
- `plugin_manager.trigger_hook(hook_name, *args)` - Manually trigger hook

## File Structure

```
.
├── todo_original.py              # Original TODO list (unchanged)
├── todo_advanced.py              # Public API wrapper
├── todo_advanced/                # Main package
│   ├── __init__.py
│   ├── api.py
│   ├── storage.py
│   ├── tag_model.py
│   ├── query_engine.py
│   ├── recommender.py
│   └── plugin_manager.py
├── tests/
│   ├── __init__.py
│   └── test_advanced_todo.py     # Comprehensive test suite
├── perf_test.py                  # Performance validation
├── run_tests.ps1                 # Windows PowerShell test runner
├── run_tests.sh                  # Unix/Linux test runner
├── requirements.txt              # Core dependencies
├── requirements-dev.txt          # Development dependencies
├── FEATURE_SPEC.md              # Detailed feature specification
└── README.md                     # This file
```

## Development

### Code Quality
- Type hints throughout
- PEP 8 compliant
- Comprehensive docstrings
- Tested with pytest

### Testing Coverage
- Unit tests for all modules
- Integration tests for API
- Concurrency stress tests
- Performance regression tests
- Property-based tests (Hypothesis ready)

## License

MIT License - See LICENSE file for details

## Troubleshooting

### Database Lock Issues
- The system uses thread-safe locks automatically
- If you see "database is locked" errors, try closing other connections

### Import Errors
- Ensure `todo_advanced/` package is in Python path
- Use `sys.path.insert(0, os.path.dirname(__file__))`

### Performance Issues
- Check database file size: `ls -lh todo_advanced.db`
- Run `perf_test.py` to identify bottlenecks
- Consider indexing frequently queried tags

## Contributing

Contributions welcome! Please:
1. Add tests for new features
2. Follow PEP 8 style
3. Update documentation
4. Run full test suite before submitting

## FAQ

**Q: Is this a replacement for todo_original.py?**
A: No, it's an enhancement. The original API is preserved for backward compatibility.

**Q: Can I use both modules simultaneously?**
A: Yes, they're separate systems. `todo_advanced` uses SQLite storage while `todo_original` keeps data in memory.

**Q: How do I migrate data from todo_original?**
A: Import data by reading todos and adding them to the advanced system:
```python
import todo_original
from todo_advanced import TodoAdvanced

todos = todo_original.list_todos()
advanced = TodoAdvanced()
for todo_item in todos:
    advanced.add_todo(todo_item["task"], tags=todo_item["tags"])
```

**Q: Can I use custom database backends?**
A: Yes, create a class inheriting from `StorageBackend` and pass it to `TodoAdvanced`.

---

For detailed technical specifications, see [FEATURE_SPEC.md](FEATURE_SPEC.md)
