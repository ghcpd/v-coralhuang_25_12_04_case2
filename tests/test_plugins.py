from todo_advanced_pkg.api import TodoAdvanced
from todo_advanced_pkg.plugins import sample_plugin


def test_plugin_hooks(tmp_path):
    ta = TodoAdvanced()
    ta.add_todo("call friend", ["personal"])
    # plugin should have recorded calls
    assert any("call friend" in t["task"] for t in sample_plugin.CALLS["added"])
