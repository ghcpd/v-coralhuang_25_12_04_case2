"""Lightweight CLI utilities for listing and querying tasks."""
from .storage import AdvancedStorage
from .query import parse, compile_ast
from typing import Optional


def run_query(expr: str, db_path: Optional[str] = None):
    st = AdvancedStorage(db_path or "todo_advanced.db")
    ast = parse(expr)
    matcher = compile_ast(ast)
    results = [t for t in st.list_tasks() if matcher(t)]
    return results
