from .api import TodoAdvanced
from colorama import Fore, Style, init as color_init
import shutil

color_init()


def _colorize_tag(tag: str) -> str:
    # simple fixed color mapping
    return Fore.CYAN + tag + Style.RESET_ALL


def print_tasks(tasks):
    if not tasks:
        print("(no tasks)")
        return
    width = shutil.get_terminal_size((80, 20)).columns
    for i, t in enumerate(tasks):
        status = "✓" if t.get("completed") else " "
        tags = ", ".join(_colorize_tag(x) for x in t.get("tags", []))
        line = f"{i+1:3d} [{status}] {t.get('task')}"
        if tags:
            line += f"  [{tags}]"
        print(line[: width - 1])


def run_cli_query(db_path: str, expr: str):
    ta = TodoAdvanced(db_path)
    res = ta.query(expr)
    print_tasks(res)
