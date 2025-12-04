"""Simple plugin discovery and hook registry (initial stub).

Plugins can register to hooks by subclassing Plugin and calling
register_plugin(plugin_instance). Auto-discovery can be added later.
"""
from typing import List, Any


class Plugin:
    def on_task_added(self, task_id: int, task: str, tags: List[str]) -> None:
        pass

    def on_tag_added(self, task_id: int, tag: str) -> None:
        pass

    def on_task_completed(self, task_id: int) -> None:
        pass


_PLUGINS: List[Plugin] = []


def register_plugin(plugin: Plugin) -> None:
    _PLUGINS.append(plugin)


def list_plugins() -> List[Plugin]:
    return list(_PLUGINS)


# Auto-discovery placeholder: in future this can search installed packages
def discover_plugins() -> List[Plugin]:
    return list(_PLUGINS)
