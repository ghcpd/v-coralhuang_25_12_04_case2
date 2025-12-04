import os
import sys
import subprocess


def run_cli(args, env=None):
    cmd = [sys.executable, "-m", "todo_advanced.cli"] + args
    return subprocess.run(cmd, capture_output=True, text=True, env=env or os.environ.copy())


def test_cli_add_list(temp_db_path):
    env = os.environ.copy()
    env["TODO_DB_PATH"] = str(temp_db_path)
    res = run_cli(["add", "cli task", "--tags", "cli"], env=env)
    assert res.returncode == 0
    res2 = run_cli(["list"], env=env)
    assert "cli task" in res2.stdout


def test_cli_query(temp_db_path):
    env = os.environ.copy()
    env["TODO_DB_PATH"] = str(temp_db_path)
    run_cli(["add", "t1", "--tags", "x"], env=env)
    run_cli(["add", "t2", "--tags", "y"], env=env)
    res = run_cli(["query", "x"], env=env)
    assert "t1" in res.stdout and "t2" not in res.stdout
