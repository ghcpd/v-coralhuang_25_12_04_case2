# Advanced TODO System (mini)

This workspace contains an advanced tag system built around SQLite with a modular package structure.

Quick start (dev):

```bash
python -m pip install -r requirements-dev.txt -r requirements.txt
pytest -q
```

Run a quick perf test (10k tasks):

```bash
python perf_test.py
```

Files:
- `todo_original.py` - original API preserved, unchanged
- `todo_advanced.py` - top-level compatibility wrapper (uses internal package)
- `todo_advanced_pkg/` - modular implementation: models, storage, query, plugin manager, cli
- `tests/` - pytest test-suite
