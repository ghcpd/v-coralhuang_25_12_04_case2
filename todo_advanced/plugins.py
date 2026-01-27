"""Plugin discovery and hook dispatch."""
from __future__ import annotations
import importlib
import os
from typing import Callable, Dict, List, Any

from .config import PLUGIN_ENV_VAR

Hook = Callable[..., None]


class PluginManager:
    def __init__(self):
        self.hooks: Dict[str, List[Hook]] = {
            "on_task_added": [],
            "on_task_completed": [],
            "on_tag_added": [],
        }
        self._load_plugins()

    def register(self, hook_name: str, fn: Hook) -> None:
        self.hooks.setdefault(hook_name, []).append(fn)

    def dispatch(self, hook_name: str, *args, **kwargs) -> None:
        for fn in self.hooks.get(hook_name, []):
            try:
                fn(*args, **kwargs)
            except Exception:
                # Plugins shouldn't crash core; swallow errors
                pass

    def _load_plugins(self):
        # Environment variable listing modules
        env_val = os.getenv(PLUGIN_ENV_VAR)
        modules = []
        if env_val:
            modules.extend([m.strip() for m in env_val.split(",") if m.strip()])
        # Built-in plugins package
        modules.append("todo_advanced.plugins_builtin")
        for mod_name in modules:
            try:
                mod = importlib.import_module(mod_name)
            except Exception:
                continue
            for hook_name in self.hooks.keys():
                fn = getattr(mod, hook_name, None)
                if fn:
                    self.register(hook_name, fn)
        # Entry points (if available)
        try:
            import importlib.metadata as metadata
            eps = metadata.entry_points()
            if hasattr(eps, "select"):
                group_eps = eps.select(group="todo_advanced.plugins")  # type: ignore[attr-defined]
            else:
                group_eps = eps.get("todo_advanced.plugins", [])  # type: ignore[call-arg]
            for ep in group_eps:
                try:
                    mod = ep.load()
                    for hook_name in self.hooks.keys():
                        fn = getattr(mod, hook_name, None)
                        if fn:
                            self.register(hook_name, fn)
                except Exception:
                    continue
        except Exception:
            pass


# A default global manager
plugin_manager = PluginManager()
