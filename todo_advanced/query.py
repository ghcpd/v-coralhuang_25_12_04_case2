"""
Mini DSL for tag queries: supports AND, OR, NOT, parentheses and tag:NAME tokens.

Simple recursive descent parser and evaluator producing sets of task ids.
"""
from typing import List, Set
import re
from .api import get_storage

TOKEN_REGEX = re.compile(r"\(|\)|AND|OR|NOT|tag:[A-Za-z0-9_\-]+|[A-Za-z0-9_\-]+", re.IGNORECASE)

class ParseError(Exception):
    pass

class Token:
    def __init__(self, text: str):
        self.text = text

    def __repr__(self):
        return f"Token({self.text})"


def tokenize(s: str) -> List[Token]:
    tokens = [Token(m.group(0)) for m in TOKEN_REGEX.finditer(s)]
    return tokens

# grammar:
# expr := term (OR term)*
# term := factor (AND factor)*
# factor := NOT factor | primary
# primary := ( expr ) | TAG

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else Token('')

    def consume(self, text=None) -> Token:
        t = self.peek()
        if text and t.text.upper() != text.upper():
            raise ParseError(f"Expected {text} but got {t.text}")
        self.pos += 1
        return t

    def parse(self):
        res = self.parse_expr()
        if self.pos < len(self.tokens):
            raise ParseError('Unexpected token: %s' % self.peek().text)
        return res

    def parse_expr(self):
        node = self.parse_term()
        while self.peek().text.upper() == 'OR':
            self.consume('OR')
            right = self.parse_term()
            node = ('OR', node, right)
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.peek().text.upper() == 'AND':
            self.consume('AND')
            right = self.parse_factor()
            node = ('AND', node, right)
        return node

    def parse_factor(self):
        if self.peek().text.upper() == 'NOT':
            self.consume('NOT')
            node = self.parse_factor()
            return ('NOT', node)
        return self.parse_primary()

    def parse_primary(self):
        if self.peek().text == '(':
            self.consume('(')
            node = self.parse_expr()
            self.consume(')')
            return node
        t = self.consume()
        if t.text.startswith('tag:'):
            tagname = t.text.split(':', 1)[1]
            return ('TAG', tagname)
        else:
            return ('TAG', t.text)


def evaluate(ast) -> Set[int]:
    storage = get_storage()

    def eval_node(node):
        op = node[0]
        if op == 'TAG':
            tagname = node[1]
            tasks = storage.filter_by_tags([tagname], match_all=False)
            return set(t['id'] for t in tasks)
        if op == 'OR':
            return eval_node(node[1]) | eval_node(node[2])
        if op == 'AND':
            return eval_node(node[1]) & eval_node(node[2])
        if op == 'NOT':
            universe = set(t['id'] for t in storage.list_tasks())
            return universe - eval_node(node[1])
        raise ValueError('Unknown node: %s' % op)

    return eval_node(ast)


def query(s: str) -> List[dict]:
    tokens = tokenize(s)
    parser = Parser(tokens)
    ast = parser.parse()
    ids = evaluate(ast)
    storage = get_storage()
    tasks = storage.list_tasks()
    return [t for t in tasks if t['id'] in ids]
