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
        # generic operator tokens like starts:foo or hasprefix:bar
        ("OP", r"[A-Za-z0-9_\-]+:[A-Za-z0-9_\-]+"),
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
        if tok[0] == "OP":
            # operator tokens are like name:arg
            self.consume("OP")
            name, arg = tok[1].split(":", 1)
            return ("OP", name, arg)
        if tok[0] == "WORD":
            self.consume("WORD")
            return ("WORD", tok[1])
        raise ParseError(f"Unexpected token {tok}")


def parse(expr: str):
    tokens = tokenize(expr)
    p = Parser(tokens)
    return p.parse()


# extensible operator registry (plugins can register handlers)
_operator_registry: dict = {}


def register_operator(name: str, fn):
    """Register a custom operator handler.

    Handler signature: fn(arg: str, task: dict) -> (matched: bool, score: int)
    """
    _operator_registry[name] = fn


def unregister_operator(name: str):
    _operator_registry.pop(name, None)


def evaluate(node: Any, task: dict) -> bool:
    """Evaluate a parsed node against a single task (dict-like)."""
    matched, _ = evaluate_with_score(node, task)
    return matched


def evaluate_with_score(node: Any, task: dict) -> tuple[bool, int]:
    """Evaluate node and also compute an integer score for relevance.

    Scoring rules (simple demonstration):
    - TAG match: +10
    - WORD match: +1
    - OR sums max scores of sides when matching any
    - AND sums scores of both sides when both match
    - NOT negates matching
    Returns (matched: bool, score: int)
    """
    ttype = node[0]
    if ttype == "OR":
        left_match, left_score = evaluate_with_score(node[1], task)
        right_match, right_score = evaluate_with_score(node[2], task)
        if left_match and right_match:
            return True, left_score + right_score
        if left_match:
            return True, left_score
        if right_match:
            return True, right_score
        return False, 0
    if ttype == "AND":
        left_match, left_score = evaluate_with_score(node[1], task)
        right_match, right_score = evaluate_with_score(node[2], task)
        if left_match and right_match:
            return True, left_score + right_score
        return False, 0
    if ttype == "NOT":
        match, score = evaluate_with_score(node[1], task)
        return (not match), 0
    if ttype == "TAG":
        name = node[1]
        tags = task.get("tags", [])
        if name in tags:
            return True, 10
        return False, 0
    if ttype == "WORD":
        w = node[1].lower()
        if w in task.get("task", "").lower():
            return True, 1
        for tg in task.get("tags", []):
            if w == tg.lower():
                return True, 1
        return False, 0
    if ttype == "OP":
        # operator node: ('OP', name, arg)
        name = node[1]
        arg = node[2]
        fn = _operator_registry.get(name)
        if callable(fn):
            try:
                return fn(arg, task)
            except Exception:
                return False, 0
        return False, 0
    return False, 0


def filter_tasks(tasks: List[dict], expr: str, scored: bool = False) -> List[dict]:
    if not expr or not expr.strip():
        return list(tasks)
    tree = parse(expr)
    results = []
    for t in tasks:
        matched, score = evaluate_with_score(tree, t)
        if matched:
            if scored:
                out = dict(t)
                out["_score"] = score
                results.append(out)
            else:
                results.append(t)
    if scored:
        results.sort(key=lambda x: x.get("_score", 0), reverse=True)
    return results
