# Advanced TODO with Structured Tags

`todo_advanced` upgrades the minimal `todo_original.py` with persistence, structured tags, a mini query DSL, plugins, concurrency safety, and a richer CLI—while keeping the original API compatible.

## Features
- **Persistent storage**: SQLite (WAL) with file locking.
- **Structured tags**: aliases, colors, descriptions, timestamps, usage counters, co-occurrence graph.
- **Query DSL**: `tag:work AND (urgent OR personal) AND NOT archived`.
- **Tag suggestions**: keyword similarity + co-occurrence.
- **Plugin hooks**: `on_task_added`, `on_task_completed`, `on_tag_added` with auto-discovery.
- **CLI**: colorized tables, fuzzy search, paging.
- **Backward compatible**: same public functions as `todo_original` via `todo_advanced.py`.

## Quickstart
```bash
pip install -r requirements.txt
python -m todo_advanced.cli add "Buy milk" --tags grocery,urgent
python -m todo_advanced.cli list
python -m todo_advanced.cli query "urgent AND NOT completed:true"
```

## Running Tests
Use the one-click scripts:
- **Linux/macOS**: `./run_tests.sh`
- **Windows (PowerShell)**: `./run_tests.ps1`

They create a virtualenv, install dev dependencies, run `pytest`, and print basics metrics.

## Layout
- `todo_original.py` – unchanged baseline API.
- `todo_advanced.py` – compatibility wrapper.
- `todo_advanced/` – modular package (storage, tags, query, plugins, CLI, etc.).
- `tests/` – pytest suite (persistence, concurrency, DSL, CLI, property, perf smoke).
- `perf_test.py` – simple performance harness.
- `FEATURE_SPEC.md` – design & behaviors.

## Configuration
- `TODO_DB_PATH` – override SQLite path (default: `./todo_data.db`).
- `TODO_PLUGINS` – comma-separated plugin modules.

## Performance Targets
- Load 10k tasks < 80 ms
- Typical query < 50 ms
- Tag-rel updates < 10 ms

(See `perf_test.py` for a baseline; actual numbers depend on hardware.)
