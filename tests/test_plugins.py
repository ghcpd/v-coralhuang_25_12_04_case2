import io
import sys
import todo_advanced.plugins as plugins_module
from todo_advanced.api import add_todo, get_storage


def test_plugins_discovery_and_hooks(capsys):
    # Ensure plugins discovered and hooks list populated
    plugins_module.discover_plugins()
    assert 'on_task_added' in plugins_module._hooks
    # add a task — sample_plugin prints a message
    add_todo('plug1', tags=['plugtag'])
    captured = capsys.readouterr()
    assert 'plugin' in captured.out
