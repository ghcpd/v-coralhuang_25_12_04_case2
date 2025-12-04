"""CLI for todo_advanced.

Usage examples:
  python -m todo_advanced.cli add "Buy milk" --tags grocery,urgent
  python -m todo_advanced.cli list
  python -m todo_advanced.cli query "tag:urgent AND NOT completed:true"
"""
from __future__ import annotations
import argparse
import sys
import difflib
import json
from typing import List

from .manager import TodoManager

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:  # pragma: no cover
    Console = None
    Table = None


def _console():
    return Console() if Console else None


def render_table(rows: List[dict]):
    if Console and Table:
        console = _console()
        if console is None:
            # fallback to plaintext
            for idx, row in enumerate(rows):
                print(f"[{idx}] {row['task']} ({'done' if row['completed'] else 'pending'}) tags={row['tags']}")
            return
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", justify="right")
        table.add_column("Task")
        table.add_column("Completed")
        table.add_column("Tags")
        for idx, row in enumerate(rows):
            table.add_row(str(idx), row["task"], "✔" if row["completed"] else "", ", ".join(row["tags"]))
        console.print(table)
    else:
        for idx, row in enumerate(rows):
            print(f"[{idx}] {row['task']} ({'done' if row['completed'] else 'pending'}) tags={row['tags']}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(prog="todo-adv", description="Advanced TODO CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="Add a task")
    p_add.add_argument("task")
    p_add.add_argument("--tags", help="Comma-separated tags", default="")

    sub.add_parser("list", help="List tasks")

    p_complete = sub.add_parser("complete", help="Complete a task by index")
    p_complete.add_argument("index", type=int)

    p_query = sub.add_parser("query", help="Run a query expression")
    p_query.add_argument("expr")

    p_tags = sub.add_parser("tags", help="List tags")

    p_reco = sub.add_parser("recommend", help="Recommend tags for text")
    p_reco.add_argument("text")

    p_search = sub.add_parser("search", help="Fuzzy search tasks by text")
    p_search.add_argument("text")

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    mgr = TodoManager()

    if args.cmd == "add":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        mgr.add_todo(args.task, tags=tags)
        print("Task added")
    elif args.cmd == "list":
        rows = mgr.list_todos()
        render_table(rows)
    elif args.cmd == "complete":
        mgr.complete_task(args.index)
        print("Completed")
    elif args.cmd == "query":
        rows = mgr.query(args.expr)
        render_table(rows)
    elif args.cmd == "tags":
        tags = mgr.list_all_tags()
        print("\n".join(tags))
    elif args.cmd == "recommend":
        suggestions = mgr.suggest_tags(args.text)
        # print as JSON
        print(json.dumps(suggestions, indent=2))
    elif args.cmd == "search":
        rows = mgr.list_todos()
        # simple fuzzy search on task text
        matches = difflib.get_close_matches(args.text, [r["task"] for r in rows], n=10, cutoff=0.3)
        filtered = [r for r in rows if r["task"] in matches]
        render_table(filtered)


if __name__ == "__main__":
    main(sys.argv[1:])
