"""Plugin loader and hooks.

Auto-discovers modules under `todo_plugins` package (if present) and exposes
hook invocation functions. Plugins are simple modules that export functions
named `on_task_added`, `on_tag_added`, etc.
"""
import importlib
import pkgutil
from typing import List, Callable, Any


def discover_plugins(package_name: str = "todo_plugins") -> List[Any]:
    plugins = []
    try:
        pkg = importlib.import_module(package_name)
    except Exception:
        return []
    if not hasattr(pkg, "__path__"):
        return []
    for finder, name, ispkg in pkgutil.iter_modules(pkg.__path__):
        full = f"{package_name}.{name}"
        try:
            mod = importlib.import_module(full)
            plugins.append(mod)
        except Exception:
            continue
    return plugins


_PLUGINS = discover_plugins()


def call_hook(hook_name: str, *args, **kwargs):
    for p in _PLUGINS:
        fn = getattr(p, hook_name, None)
        if callable(fn):
            try:
                fn(*args, **kwargs)
            except Exception:
                # plugin errors should not break main flow
                continue
