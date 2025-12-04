# Feature Specification — Advanced Tag System

## Overview
Upgrade the minimal in-memory TODO list to a persistent, modular, concurrency-safe system with structured tags, a query DSL, recommendations, plugins, and CLI enhancements. Preserve the original public API.

## Storage & Concurrency
- SQLite backend (WAL mode); schema versioned.
- Tables: `tasks`, `tags`, `tag_aliases`, `task_tags`, `tag_cooccurrence`, `schema_version`.
- File-based advisory write lock (`filelock`).
- Transactions wrap writes; foreign keys enforced.

## Tag Model
- Fields: name (unique), aliases (table), color, description, created/updated timestamps, usage_count.
- Co-occurrence graph: `tag_cooccurrence(tag_id1, tag_id2, count)`.

## Query DSL
- Grammar: expressions with `AND | OR | NOT`, parentheses, predicates.
- Predicates: `tag:<name>` (default), `text:<substr>`/`task:<substr>`, `completed:true|false`.
- Extensible operator registry (`query.register_operator`).
- Compiles to SQL WHERE clause for performance.

## Tag Recommendations
- Keyword similarity (difflib) + usage frequency.
- Co-occurrence-based boosting for existing tags.
- API: `TodoManager.suggest_tags(text, existing_tags, top_n=5)`.

## Plugins
- Auto-discovery via `TODO_PLUGINS` env var and entry points `todo_advanced.plugins`.
- Hooks: `on_task_added`, `on_task_completed`, `on_tag_added`.
- Built-in stub module `todo_advanced.plugins_builtin`.

## CLI Enhancements
- `python -m todo_advanced.cli` subcommands: `add`, `list`, `complete`, `query`, `tags`, `recommend`, `search` (fuzzy).
- Colorized tables via `rich` (optional) with plaintext fallback.

## Backward Compatibility
- `todo_advanced.py` exposes the same functions as `todo_original.py`.
- Returns dicts with keys: `task`, `completed`, `tags`.

## Testing & Tooling
- `tests/`: pytest suite (persistence, concurrency, DSL, tags, CLI, property-based, perf smoke).
- `perf_test.py`: rudimentary performance validation.
- `run_tests.sh` / `run_tests.ps1`: one-click env + tests.
- `requirements.txt` / `requirements-dev.txt`: dependencies.
