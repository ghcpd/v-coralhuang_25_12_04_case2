"""Mini DSL for tag queries: supports expressions like

    tag:work AND (urgent OR personal) AND NOT archived

This initial implementation tokenizes, parses to an AST, and evaluates against
an in-memory snapshot of tasks returned by the backend.
"""
from typing import List, Set, Dict, Any
import re


TOKEN_RE = re.compile(r"\s*(?:(AND|OR|NOT)|\(|\)|tag:([A-Za-z0-9_-]+)|(.+?))\s*")


class ParseError(Exception):
    pass


def tokenize(expr: str):
    pos = 0
    tokens = []
    while pos < len(expr):
        m = TOKEN_RE.match(expr, pos)
        if not m:
            raise ParseError(f"Invalid token at position {pos}")
        op, tag, other = m.group(1), m.group(2), m.group(3)
        if op:
            tokens.append((op, op))
        elif tag:
            tokens.append(("TAG", tag))
        elif m.group(0).strip() == '(':
            tokens.append(("LPAREN", '('))
        elif m.group(0).strip() == ')':
            tokens.append(("RPAREN", ')'))
        else:
            # unrecognized token
            raise ParseError(f"Unrecognized token: {m.group(0)}")
        pos = m.end()
    return tokens


# AST node types
class TagNode:
    def __init__(self, tag: str):
        self.tag = tag

class NotNode:
    def __init__(self, child):
        self.child = child

class AndNode:
    def __init__(self, left, right):
        self.left = left
        self.right = right

class OrNode:
    def __init__(self, left, right):
        self.left = left
        self.right = right


# Recursive descent parser using operator precedence: NOT > AND > OR
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, expected=None):
        t = self.peek()
        if not t:
            return None
        if expected and t[0] != expected:
            raise ParseError(f"Expected {expected} but got {t}")
        self.pos += 1
        return t

    def parse(self):
        node = self.parse_or()
        if self.peek() is not None:
            raise ParseError("Unexpected token at end")
        return node

    def parse_or(self):
        node = self.parse_and()
        while self.peek() and self.peek()[0] == 'OR':
            self.consume('OR')
            right = self.parse_and()
            node = OrNode(node, right)
        return node

    def parse_and(self):
        node = self.parse_not()
        while self.peek() and self.peek()[0] == 'AND':
            self.consume('AND')
            right = self.parse_not()
            node = AndNode(node, right)
        return node

    def parse_not(self):
        if self.peek() and self.peek()[0] == 'NOT':
            self.consume('NOT')
            child = self.parse_not()
            return NotNode(child)
        return self.parse_primary()

    def parse_primary(self):
        t = self.peek()
        if not t:
            raise ParseError("Unexpected end of input")
        if t[0] == 'TAG':
            self.consume('TAG')
            return TagNode(t[1])
        if t[0] == 'LPAREN':
            self.consume('LPAREN')
            node = self.parse_or()
            if not self.peek() or self.peek()[0] != 'RPAREN':
                raise ParseError("Unclosed parenthesis")
            self.consume('RPAREN')
            return node
        raise ParseError(f"Unexpected token in primary: {t}")


def parse_expression(expr: str):
    tokens = tokenize(expr)
    parser = Parser(tokens)
    return parser.parse()


def evaluate_ast(node, tasks: List[Dict[str, Any]]) -> Set[int]:
    """Return set of task indices matching the AST node."""
    if isinstance(node, TagNode):
        tag = node.tag
        return {i for i, t in enumerate(tasks) if tag in t.get('tags', [])}
    if isinstance(node, NotNode):
        child_set = evaluate_ast(node.child, tasks)
        all_set = set(range(len(tasks)))
        return all_set - child_set
    if isinstance(node, AndNode):
        left = evaluate_ast(node.left, tasks)
        right = evaluate_ast(node.right, tasks)
        return left & right
    if isinstance(node, OrNode):
        left = evaluate_ast(node.left, tasks)
        right = evaluate_ast(node.right, tasks)
        return left | right
    raise ValueError("Unknown AST node")


class QueryEngine:
    def __init__(self, backend):
        self.backend = backend

    def query(self, expr: str) -> List[Dict[str, Any]]:
        ast = parse_expression(expr)
        tasks = self.backend.list_todos()
        idxs = evaluate_ast(ast, tasks)
        return [tasks[i] for i in sorted(idxs)]
