"""Simple query DSL for tag expressions.

Supports expressions like: tag:work AND (urgent OR personal) AND NOT archived
This is a minimal parser and evaluator that translates expressions into a
callable which can be used to filter tasks.
"""
import re
from typing import List, Tuple, Callable, Any


TOKEN_RE = re.compile(r"\s*(AND|OR|NOT|\(|\)|tag:[A-Za-z0-9_\-]+)\s*", re.IGNORECASE)


def tokenize(expr: str) -> List[str]:
    tokens = TOKEN_RE.findall(expr)
    return [t.strip() for t in tokens if t.strip()]


def parse(expr: str):
    tokens = tokenize(expr)
    pos = 0

    def parse_primary():
        nonlocal pos
        if pos >= len(tokens):
            raise ValueError("Unexpected end of expression")
        tok = tokens[pos]
        if tok == "(":
            pos += 1
            node = parse_or()
            if pos >= len(tokens) or tokens[pos] != ")":
                raise ValueError("Missing )")
            pos += 1
            return node
        if tok.upper().startswith("TAG:"):
            pos += 1
            tag = tok.split(":", 1)[1]
            return ("TAG", tag)
        if tok.upper() == "NOT":
            pos += 1
            node = parse_primary()
            return ("NOT", node)
        raise ValueError(f"Unexpected token: {tok}")

    def parse_and():
        nonlocal pos
        left = parse_primary()
        while pos < len(tokens) and tokens[pos].upper() == "AND":
            pos += 1
            right = parse_primary()
            left = ("AND", left, right)
        return left

    def parse_or():
        nonlocal pos
        left = parse_and()
        while pos < len(tokens) and tokens[pos].upper() == "OR":
            pos += 1
            right = parse_and()
            left = ("OR", left, right)
        return left

    ast = parse_or()
    if pos != len(tokens):
        raise ValueError("Unexpected tokens at end")
    return ast


def compile_ast(ast) -> Callable[[dict], bool]:
    def eval_node(node, task: dict) -> bool:
        op = node[0]
        if op == "TAG":
            tag = node[1]
            return tag in task.get("tags", [])
        if op == "NOT":
            return not eval_node(node[1], task)
        if op == "AND":
            return eval_node(node[1], task) and eval_node(node[2], task)
        if op == "OR":
            return eval_node(node[1], task) or eval_node(node[2], task)
        raise ValueError("Unknown op")

    def matcher(task: dict) -> bool:
        return eval_node(ast, task)

    return matcher
