"""
Basic CLI utilities: fuzzy search, colorized output, paging.
"""
from typing import List
from difflib import get_close_matches
import os

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init()
except Exception:
    class Fore:
        RED = ''
        GREEN = ''
        YELLOW = ''
        RESET = ''
    class Style:
        RESET_ALL = ''

from .api import list_todos, list_all_tags


def fuzzy_search_tasks(query: str, limit: int = 10):
    tasks = list_todos()
    names = [t['task'] for t in tasks]
    matches = get_close_matches(query, names, n=limit, cutoff=0.3)
    return [t for t in tasks if t['task'] in matches]


def colorize_task(t):
    tags = t.get('tags', [])
    tagpart = ' '.join(f'[{tag}]' for tag in tags)
    status = Fore.GREEN + 'done' + Fore.RESET if t.get('completed') else Fore.YELLOW + 'open' + Fore.RESET
    return f"{t['id']:4d} {status:6s} {t['task']} {tagpart}"


def paged_print(items: List[str], page_size: int = 20):
    for i in range(0, len(items), page_size):
        for line in items[i:i+page_size]:
            print(line)
        if i + page_size < len(items):
            input('Press Enter to continue...')


def run_search_cli(query: str):
    results = fuzzy_search_tasks(query)
    lines = [colorize_task(t) for t in results]
    paged_print(lines)


def run_list_tags():
    tags = list_all_tags()
    for t in tags:
        print(t)
