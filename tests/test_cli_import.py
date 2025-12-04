def test_cli_import():
    import todo_advanced_pkg.cli as cli
    assert hasattr(cli, 'print_tasks')
