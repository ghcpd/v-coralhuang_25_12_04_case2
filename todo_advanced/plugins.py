import importlib
import pkgutil
from typing import Callable, Dict, List

# Hooks for plugins
HOOKS = ["on_task_added", "on_tag_added", "on_task_completed"]


class PluginManager:
    def __init__(self, package: str = "todo_advanced.plugins"):
        self.package = package
        self._plugins = []
        self._load_plugins()

    def _load_plugins(self):
        # simple discovery: import any module under the package
        try:
            pkg = importlib.import_module(self.package)
        except Exception:
            return

        for finder, name, ispkg in pkgutil.iter_modules(pkg.__path__):
            full = f"{self.package}.{name}"
            try:
                m = importlib.import_module(full)
                self._plugins.append(m)
            except Exception:
                # ignore failing plugins
                continue

    def call_hook(self, hook_name: str, *args, **kwargs):
        if hook_name not in HOOKS:
            return
        for p in self._plugins:
            fn = getattr(p, hook_name, None)
            if callable(fn):
                try:
                    fn(*args, **kwargs)
                except Exception:
                    # swallow plugin exceptions to avoid breaking core
                    continue
