import io
import sys
from todo_advanced.plugins import discover_plugins, _hooks
from todo_advanced.api import add_todo, get_storage


def test_plugins_discovery_and_hooks(capsys):
    # Ensure plugins discovered and hooks list populated
    discover_plugins()
    assert 'on_task_added' in _hooks
    # add a task — sample_plugin prints a message
    add_todo('plug1', tags=['plugtag'])
    captured = capsys.readouterr()
    assert 'plugin' in captured.out
