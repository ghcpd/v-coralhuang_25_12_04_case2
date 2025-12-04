"""Simple CLI helpers (initial stub) with optional color output."""
from typing import List
try:
    from colorama import Fore, Style, init as _init_colorama
    _init_colorama()
    _COLORS_AVAILABLE = True
except Exception:
    _COLORS_AVAILABLE = False


def colorize(text: str, color: str = "GREEN") -> str:
    if _COLORS_AVAILABLE and hasattr(Fore, color):
        return getattr(Fore, color) + text + Style.RESET_ALL
    return text


def print_tasks(tasks: List[dict], page: int = 0, page_size: int = 20) -> None:
    start = page * page_size
    for i, t in enumerate(tasks[start:start+page_size], start=start):
        status = "[x]" if t.get("completed") else "[ ]"
        print(f"{i:3d} {status} {colorize(t['task'], 'GREEN')} {t.get('tags', [])}")
