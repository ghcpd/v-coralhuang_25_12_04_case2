# FEATURE SPEC: Advanced Tag System

See repository README for a quick overview. This file outlines intended features, data model, concurrency, and plugin hooks.

- Storage: SQLite with WAL mode, schema versioning
- Tag metadata: alias_of, color, description, created_at, updated_at, usage_count
- Co-occurrence graph maintained on tag additions
- Query DSL: supports AND, OR, NOT, parentheses, tag:NAME syntax
- Plugin hooks: on_task_added, on_tag_added, on_task_completed
- CLI: fuzzy search and colorized output

This is a minimal reference implementation to be extended further.
