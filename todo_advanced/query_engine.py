"""
Query DSL engine for advanced tag filtering.
Supports: tag:work AND (urgent OR personal) AND NOT archived
"""

import re
from enum import Enum
from typing import List, Optional, Set, Tuple


class TokenType(Enum):
    """Token types for DSL parsing."""

    TAG = "TAG"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    EOF = "EOF"


class Token:
    """Represents a token in the DSL."""

    def __init__(self, type_: TokenType, value: str):
        self.type = type_
        self.value = value

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value})"


class Tokenizer:
    """Tokenizes DSL expressions."""

    def __init__(self, expression: str):
        self.expression = expression
        self.pos = 0

    def tokenize(self) -> List[Token]:
        """Tokenize the expression."""
        tokens = []
        while self.pos < len(self.expression):
            self._skip_whitespace()
            if self.pos >= len(self.expression):
                break

            if self.expression[self.pos] == "(":
                tokens.append(Token(TokenType.LPAREN, "("))
                self.pos += 1
            elif self.expression[self.pos] == ")":
                tokens.append(Token(TokenType.RPAREN, ")"))
                self.pos += 1
            else:
                word = self._read_word()
                if word.upper() == "AND":
                    tokens.append(Token(TokenType.AND, word))
                elif word.upper() == "OR":
                    tokens.append(Token(TokenType.OR, word))
                elif word.upper() == "NOT":
                    tokens.append(Token(TokenType.NOT, word))
                else:
                    tokens.append(Token(TokenType.TAG, word))

        tokens.append(Token(TokenType.EOF, ""))
        return tokens

    def _skip_whitespace(self) -> None:
        """Skip whitespace."""
        while self.pos < len(self.expression) and self.expression[self.pos].isspace():
            self.pos += 1

    def _read_word(self) -> str:
        """Read a word."""
        start = self.pos
        while (
            self.pos < len(self.expression)
            and (
                self.expression[self.pos].isalnum()
                or self.expression[self.pos] in "_:-"
            )
        ):
            self.pos += 1
        return self.expression[start : self.pos]


class ASTNode:
    """Abstract syntax tree node."""

    pass


class TagNode(ASTNode):
    """Tag node."""

    def __init__(self, name: str):
        self.name = name

    def __repr__(self) -> str:
        return f"TagNode({self.name})"


class AndNode(ASTNode):
    """AND operator node."""

    def __init__(self, left: ASTNode, right: ASTNode):
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return f"AndNode({self.left}, {self.right})"


class OrNode(ASTNode):
    """OR operator node."""

    def __init__(self, left: ASTNode, right: ASTNode):
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return f"OrNode({self.left}, {self.right})"


class NotNode(ASTNode):
    """NOT operator node."""

    def __init__(self, child: ASTNode):
        self.child = child

    def __repr__(self) -> str:
        return f"NotNode({self.child})"


class Parser:
    """Parses DSL tokens into AST."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> ASTNode:
        """Parse tokens into AST."""
        return self._parse_or()

    def _parse_or(self) -> ASTNode:
        """Parse OR expression."""
        left = self._parse_and()
        while self._current_token().type == TokenType.OR:
            self.pos += 1
            right = self._parse_and()
            left = OrNode(left, right)
        return left

    def _parse_and(self) -> ASTNode:
        """Parse AND expression."""
        left = self._parse_not()
        while self._current_token().type == TokenType.AND:
            self.pos += 1
            right = self._parse_not()
            left = AndNode(left, right)
        return left

    def _parse_not(self) -> ASTNode:
        """Parse NOT expression."""
        if self._current_token().type == TokenType.NOT:
            self.pos += 1
            child = self._parse_not()
            return NotNode(child)
        return self._parse_primary()

    def _parse_primary(self) -> ASTNode:
        """Parse primary expression."""
        token = self._current_token()

        if token.type == TokenType.LPAREN:
            self.pos += 1
            expr = self._parse_or()
            if self._current_token().type != TokenType.RPAREN:
                raise SyntaxError("Expected ')'")
            self.pos += 1
            return expr
        elif token.type == TokenType.TAG:
            self.pos += 1
            return TagNode(token.value)
        else:
            raise SyntaxError(f"Unexpected token: {token}")

    def _current_token(self) -> Token:
        """Get current token."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, "")


class QueryEvaluator:
    """Evaluates parsed queries against task tags."""

    def evaluate(self, ast: ASTNode, task_tags: Set[str]) -> bool:
        """Evaluate AST against task tags."""
        if isinstance(ast, TagNode):
            return ast.name in task_tags
        elif isinstance(ast, AndNode):
            return self.evaluate(ast.left, task_tags) and self.evaluate(
                ast.right, task_tags
            )
        elif isinstance(ast, OrNode):
            return self.evaluate(ast.left, task_tags) or self.evaluate(
                ast.right, task_tags
            )
        elif isinstance(ast, NotNode):
            return not self.evaluate(ast.child, task_tags)
        return False


class QueryEngine:
    """High-level query engine."""

    def __init__(self, tag_manager=None):
        """Initialize query engine."""
        self.tag_manager = tag_manager

    def parse_and_evaluate(
        self, expression: str, task_tags: List[str]
    ) -> Tuple[bool, Optional[str]]:
        """Parse and evaluate a DSL expression."""
        try:
            tokenizer = Tokenizer(expression)
            tokens = tokenizer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            evaluator = QueryEvaluator()
            result = evaluator.evaluate(ast, set(task_tags))
            return result, None
        except Exception as e:
            return False, str(e)

    def find_tasks(
        self, tasks: List[dict], expression: str
    ) -> Tuple[List[dict], Optional[str]]:
        """Find tasks matching a DSL expression."""
        matching = []
        for task in tasks:
            result, error = self.parse_and_evaluate(
                expression, task.get("tags", [])
            )
            if error:
                return [], error
            if result:
                matching.append(task)
        return matching, None
