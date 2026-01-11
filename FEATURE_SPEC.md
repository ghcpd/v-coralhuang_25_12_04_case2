# Feature Spec: Advanced Tag System (mini)

Goals:
- Persistent tasks and tags using SQLite; WAL mode for concurrent writes.
- Structured Tag model with aliases, colors, description, timestamps, usage counts.
- Co-occurrence graph for tag relationships.
- Mini query language for tag expressions: supports AND, OR, NOT, parentheses, tag:name tokens, and word matching.
- Plugin discovery and hooks for simple extensibility.
- Backwards compatibility with `todo_original.py` semantics.

Notes: This mini-implementation demonstrates core capabilities and provides a scaffold for further work (caching, metrics, fuzzy search, advanced CLI paging, property tests, and more). Tests and scripts included for validation.
