"""
Plugin system with auto-discovery and hook management.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class PluginManager:
    """Manages plugin discovery, registration, and execution."""

    def __init__(self, plugin_dir: Optional[str] = None):
        """Initialize plugin manager."""
        self.plugin_dir = Path(plugin_dir) if plugin_dir else None
        self.hooks: Dict[str, List[Callable]] = {
            "on_task_added": [],
            "on_task_removed": [],
            "on_task_completed": [],
            "on_tag_added": [],
            "on_tag_removed": [],
            "on_query": [],
        }
        self.plugins: Dict[str, Any] = {}

    def register_hook(self, hook_name: str, callback: Callable) -> None:
        """Register a callback for a hook."""
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(callback)

    def unregister_hook(self, hook_name: str, callback: Callable) -> None:
        """Unregister a callback."""
        if hook_name in self.hooks:
            self.hooks[hook_name] = [
                c for c in self.hooks[hook_name] if c != callback
            ]

    def trigger_hook(self, hook_name: str, *args, **kwargs) -> None:
        """Trigger all callbacks for a hook."""
        if hook_name in self.hooks:
            for callback in self.hooks[hook_name]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    print(f"Error in hook {hook_name}: {e}")

    def load_plugins_from_directory(self, plugin_dir: str) -> None:
        """Auto-discover and load plugins from a directory."""
        plugin_path = Path(plugin_dir)
        if not plugin_path.exists():
            return

        for plugin_file in plugin_path.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
            self._load_plugin(plugin_file)

    def _load_plugin(self, plugin_file: Path) -> None:
        """Load a single plugin file."""
        try:
            spec = importlib.util.spec_from_file_location(
                plugin_file.stem, plugin_file
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[plugin_file.stem] = module
                spec.loader.exec_module(module)

                self.plugins[plugin_file.stem] = module

                # Auto-register hooks if the module has them
                if hasattr(module, "register"):
                    module.register(self)
        except Exception as e:
            print(f"Error loading plugin {plugin_file}: {e}")

    def get_hooks_for(self, hook_name: str) -> List[Callable]:
        """Get all callbacks for a hook."""
        return self.hooks.get(hook_name, [])
