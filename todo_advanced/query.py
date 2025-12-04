"""Mini DSL query engine.

Supports expressions like: `tag:work AND (urgent OR personal) AND NOT archived`.

The engine parses the expression into an AST and compiles to a SQL WHERE clause
against the `tasks` table, using subqueries for tag predicates. Operators are
pluggable via `register_operator(name, handler)` where handler returns a tuple
 `(sql_fragment, params)` evaluated in the context of the tasks table.
"""
from __future__ import annotations
import re
from typing import List, Tuple, Callable, Dict, Optional

from .storage import SQLiteStorage
from .config import DEFAULT_QUERY_LIMIT

# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------
TOKEN_REGEX = re.compile(r"\s*(AND|OR|NOT|\(|\)|[^\s()]+)", re.IGNORECASE)


class Token:
    def __init__(self, value: str):
        self.value = value

    def __repr__(self):
        return f"Token({self.value!r})"


def tokenize(expr: str) -> List[Token]:
    tokens = []
    for match in TOKEN_REGEX.finditer(expr):
        tokens.append(Token(match.group(1)))
    return tokens


# ---------------------------------------------------------------------------
# AST Nodes
# ---------------------------------------------------------------------------
class Node:
    pass


class And(Node):
    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right


class Or(Node):
    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right


class Not(Node):
    def __init__(self, node: Node):
        self.node = node


class Predicate(Node):
    def __init__(self, raw: str):
        self.raw = raw  # like tag:work or urgent


# ---------------------------------------------------------------------------
# Parser (recursive descent)
# ---------------------------------------------------------------------------
class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Optional[Token]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def parse(self) -> Node:
        if not self.tokens:
            raise ValueError("empty query")
        return self.parse_or()

    def parse_or(self) -> Node:
        node = self.parse_and()
        tok = self.peek()
        while tok and tok.value.upper() == "OR":
            self.consume()
            node = Or(node, self.parse_and())
            tok = self.peek()
        return node

    def parse_and(self) -> Node:
        node = self.parse_not()
        tok = self.peek()
        while tok and tok.value.upper() == "AND":
            self.consume()
            node = And(node, self.parse_not())
            tok = self.peek()
        return node

    def parse_not(self) -> Node:
        tok = self.peek()
        if tok and tok.value.upper() == "NOT":
            self.consume()
            return Not(self.parse_not())
        return self.parse_primary()

    def parse_primary(self) -> Node:
        tok = self.peek()
        if tok is None:
            raise ValueError("unexpected end of query")
        if tok.value == "(":
            self.consume()
            node = self.parse_or()
            peek_tok = self.peek()
            if not peek_tok or peek_tok.value != ")":
                raise ValueError("missing closing parenthesis")
            self.consume()
            return node
        # predicate token
        self.consume()
        return Predicate(tok.value)


# ---------------------------------------------------------------------------
# Operator registry
# ---------------------------------------------------------------------------
OperatorHandler = Callable[[str], Tuple[str, Tuple]]

_operator_registry: Dict[str, OperatorHandler] = {}


def register_operator(name: str, handler: OperatorHandler) -> None:
    _operator_registry[name.lower()] = handler


# default operators

def _op_tag(arg: str) -> Tuple[str, Tuple]:
    # Tag predicate: anywhere in tags or alias
    return (
        "EXISTS (SELECT 1 FROM task_tags tt JOIN tags t ON t.id = tt.tag_id "
        "LEFT JOIN tag_aliases ta ON ta.tag_id = t.id WHERE tt.task_id = tasks.id "
        "AND (t.name = ? OR ta.alias = ?))",
        (arg.lower(), arg.lower()),
    )


def _op_text(arg: str) -> Tuple[str, Tuple]:
    return ("tasks.task LIKE ?", (f"%{arg}%",))


def _op_completed(arg: str) -> Tuple[str, Tuple]:
    val = arg.lower()
    if val in ("1", "true", "yes", "y"):  # noqa: SIM103
        return ("tasks.completed = 1", ())
    else:
        return ("tasks.completed = 0", ())


# register defaults
register_operator("tag", _op_tag)
register_operator("text", _op_text)
register_operator("task", _op_text)
register_operator("completed", _op_completed)


# ---------------------------------------------------------------------------
# Compiler
# ---------------------------------------------------------------------------
def compile_predicate(pred: Predicate) -> Tuple[str, Tuple]:
    raw = pred.raw
    if ":" in raw:
        op, arg = raw.split(":", 1)
        handler = _operator_registry.get(op.lower())
        if not handler:
            raise ValueError(f"unknown operator: {op}")
        return handler(arg)
    else:
        # default: treat as tag
        return _operator_registry["tag"](raw)


def compile_node(node: Node) -> Tuple[str, Tuple]:
    if isinstance(node, Predicate):
        return compile_predicate(node)
    elif isinstance(node, And):
        l_sql, l_params = compile_node(node.left)
        r_sql, r_params = compile_node(node.right)
        return (f"({l_sql}) AND ({r_sql})", l_params + r_params)
    elif isinstance(node, Or):
        l_sql, l_params = compile_node(node.left)
        r_sql, r_params = compile_node(node.right)
        return (f"({l_sql}) OR ({r_sql})", l_params + r_params)
    elif isinstance(node, Not):
        sql, params = compile_node(node.node)
        return (f"NOT ({sql})", params)
    else:
        raise TypeError(node)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def run_query(expr: str, storage: Optional[SQLiteStorage] = None, limit: Optional[int] = DEFAULT_QUERY_LIMIT):
    storage = storage or SQLiteStorage()
    tokens = tokenize(expr)
    parser = Parser(tokens)
    ast = parser.parse()
    where_sql, params = compile_node(ast)
    return storage.query_tasks(where_clause=where_sql, params=params, limit=limit)
