from .api import TodoAdvanced
from colorama import Fore, Style, init as color_init
import shutil
import difflib

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


def fuzzy_search_tasks(tasks, term: str, limit: int = 20):
    # simple fuzzy matching: prefer substring matches, then close matches
    term_l = term.lower()
    substr = [t for t in tasks if term_l in t.get("task", "").lower()]
    if len(substr) >= limit:
        return substr[:limit]

    # use difflib to find close matches on task text
    texts = [t.get("task", "") for t in tasks]
    close = difflib.get_close_matches(term, texts, n=limit, cutoff=0.6)
    picks = [t for t in tasks if t.get("task", "") in close]
    # also include tag hits
    tag_hits = [t for t in tasks if any(term_l in tg.lower() for tg in t.get("tags", []))]
    result = []
    # preserve order: substr -> tag_hits -> close matches
    seen = set()
    for seq in (substr, tag_hits, picks):
        for t in seq:
            key = t.get("task")
            if key not in seen:
                seen.add(key)
                result.append(t)
            if len(result) >= limit:
                return result[:limit]
    return result[:limit]


def paginate_tasks(tasks, page_size=20):
    for i in range(0, len(tasks), page_size):
        yield tasks[i : i + page_size]


def run_cli_query(db_path: str, expr: str):
    ta = TodoAdvanced(db_path)
    res = ta.query(expr)
    print_tasks(res)


def run_cli_fuzzy_search(db_path: str, term: str, page_size=10):
    ta = TodoAdvanced(db_path)
    tasks = ta.list_todos()
    found = fuzzy_search_tasks(tasks, term)
    for page in paginate_tasks(found, page_size):
        print_tasks(page)
        # in a real CLI we'd pause for user response; tests just print pages
