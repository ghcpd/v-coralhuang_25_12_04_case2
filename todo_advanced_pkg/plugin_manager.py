import importlib
import pkgutil
from typing import List

# Hooks for plugins
HOOKS = ["on_task_added", "on_tag_added", "on_task_completed"]


class PluginManager:
    def __init__(self, package: str = "todo_advanced_pkg.plugins"):
        self.package = package
        self._plugins = []
        self._load_plugins()

    def _load_plugins(self):
        try:
            pkg = importlib.import_module(self.package)
        except Exception:
            # package might not exist yet -- that's okay
            return

        # If pkg has __path__ iterate modules; else nothing to load
        path = getattr(pkg, "__path__", None)
        if not path:
            return

        for finder, name, ispkg in pkgutil.iter_modules(path):
            full = f"{self.package}.{name}"
            try:
                m = importlib.import_module(full)
                self._plugins.append(m)
                # allow plugins to register query operators if they provide a hook
                reg = getattr(m, "register_query_operators", None)
                if callable(reg):
                    try:
                        ops = reg()
                        if isinstance(ops, dict):
                            # import local query module to register operators
                            from . import query as _query

                            for oname, ofn in ops.items():
                                _query.register_operator(oname, ofn)
                    except Exception:
                        # non-fatal
                        pass
            except Exception:
                # swallow plugin import errors
                continue

    def call_hook(self, hook_name: str, *args, **kwargs):
        if hook_name not in HOOKS:
            return
        for p in list(self._plugins):
            fn = getattr(p, hook_name, None)
            if callable(fn):
                try:
                    fn(*args, **kwargs)
                except Exception:
                    continue
