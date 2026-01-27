"""
Simple plugin discovery and hook invocation.
Plugins are Python files under todo_advanced/plugins/ that expose hook functions.
Supported hooks: on_task_added(task_dict), on_tag_added(tag_name), on_task_completed(task_dict)
"""
import importlib.util
import pkgutil
from pathlib import Path
from typing import Callable, List

PLUGIN_DIR = Path(__file__).parent / 'plugin_modules'

_hooks = {
    'on_task_added': [],
    'on_tag_added': [],
    'on_task_completed': []
}


def discover_plugins():
    if not PLUGIN_DIR.exists():
        return []
    plugins = []
    for finder, name, ispkg in pkgutil.iter_modules([str(PLUGIN_DIR)]):
        spec = importlib.util.spec_from_file_location(name, PLUGIN_DIR / (name + '.py'))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        plugins.append(mod)
        for hook in _hooks.keys():
            if hasattr(mod, hook):
                _hooks[hook].append(getattr(mod, hook))
    return plugins


def call_hook(hook_name: str, *args, **kwargs):
    for h in _hooks.get(hook_name, []):
        try:
            h(*args, **kwargs)
        except Exception:
            # Plugins should not break the core app
            pass

# auto discover at import time
try:
    discover_plugins()
except Exception:
    pass
