from typing import List, Any, Tuple
import re

# Mini DSL: supports expressions like
#   tag:work AND (urgent OR personal) AND NOT archived


Token = Tuple[str, str]


def tokenize(expr: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    expr = expr.strip()
    token_spec = [
        ("LPAREN", r"\("),
        ("RPAREN", r"\)"),
        ("AND", r"\bAND\b"),
        ("OR", r"\bOR\b"),
        ("NOT", r"\bNOT\b"),
        ("TAG", r"tag:[A-Za-z0-9_\-]+"),
        ("WORD", r"[A-Za-z0-9_\-]+"),
        ("SKIP", r"[ \t]+"),
    ]
    regex = "|".join("(?P<%s>%s)" % pair for pair in token_spec)
    for mo in re.finditer(regex, expr):
        kind = mo.lastgroup
        val = mo.group()
        if kind == "SKIP":
            continue
        tokens.append((kind, val))
    return tokens


class ParseError(ValueError):
    pass


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else ("EOF", "")

    def consume(self, expected_kind=None):
        tok = self.peek()
        if expected_kind and tok[0] != expected_kind:
            raise ParseError(f"Expected {expected_kind} but got {tok}")
        self.pos += 1
        return tok

    def parse(self):
        node = self._parse_or()
        if self.pos != len(self.tokens):
            raise ParseError("Unexpected token at end")
        return node

    # OR has lowest precedence
    def _parse_or(self):
        left = self._parse_and()
        while True:
            tok = self.peek()
            if tok[0] == "OR":
                self.consume("OR")
                right = self._parse_and()
                left = ("OR", left, right)
            else:
                break
        return left

    def _parse_and(self):
        left = self._parse_not()
        while True:
            tok = self.peek()
            if tok[0] == "AND":
                self.consume("AND")
                right = self._parse_not()
                left = ("AND", left, right)
            else:
                break
        return left

    def _parse_not(self):
        tok = self.peek()
        if tok[0] == "NOT":
            self.consume("NOT")
            node = self._parse_not()
            return ("NOT", node)
        return self._parse_atom()

    def _parse_atom(self):
        tok = self.peek()
        if tok[0] == "LPAREN":
            self.consume("LPAREN")
            node = self._parse_or()
            self.consume("RPAREN")
            return node
        if tok[0] == "TAG":
            self.consume("TAG")
            name = tok[1].split(":", 1)[1]
            return ("TAG", name)
        if tok[0] == "WORD":
            self.consume("WORD")
            return ("WORD", tok[1])
        raise ParseError(f"Unexpected token {tok}")


def parse(expr: str):
    tokens = tokenize(expr)
    p = Parser(tokens)
    return p.parse()


def evaluate(node: Any, task: dict) -> bool:
    """Evaluate a parsed node against a single task (dict-like)."""
    ttype = node[0]
    if ttype == "OR":
        return evaluate(node[1], task) or evaluate(node[2], task)
    if ttype == "AND":
        return evaluate(node[1], task) and evaluate(node[2], task)
    if ttype == "NOT":
        return not evaluate(node[1], task)
    if ttype == "TAG":
        name = node[1]
        tags = task.get("tags", [])
        return name in tags
    if ttype == "WORD":
        w = node[1].lower()
        return w in task.get("task", "").lower()
    return False


def filter_tasks(tasks: List[dict], expr: str) -> List[dict]:
    if not expr or not expr.strip():
        return list(tasks)
    tree = parse(expr)
    return [t for t in tasks if evaluate(tree, t)]
