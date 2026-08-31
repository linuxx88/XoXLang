"""Token and source location definitions for XoX (X-o-X) lexical core."""
from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class SourceLocation:
    line: int
    column: int

    def __str__(self) -> str:
        return f"{self.line}:{self.column}"


@dataclass(frozen=True)
class SourceSpan:
    start: SourceLocation
    end: SourceLocation

    def __str__(self) -> str:
        return f"{self.start}-{self.end}"


class TokenKind(Enum):
    # Control Flow Keywords
    IF = "if"
    XEN = "xen"
    ELSE = "else"

    # Function Keywords
    FN = "fn"
    RETURN = "return"

    # Logical Operators
    AND = "AND"
    OR = "OR"
    NOT = "NOT"

    # Auxiliary Statements
    PASS = "pass"

    # Truth & Uncertainty Literals
    TRUE = "True"
    FALSE = "False"
    UNKNOWN = "Unknown"

    # Identifiers (includes contextual 'ignore', 'elif', type names 'Bool', 'XoX', user variables, etc.)
    IDENTIFIER = "IDENTIFIER"



    # Punctuation & Operators
    COLON = ":"
    COMMA = ","
    DOT = "."
    ARROW = "->"
    ASSIGN = "="
    LPAREN = "("
    RPAREN = ")"
    EQ_EQ = "=="
    EXCL_EQ = "!="

    # Structural Layout Tokens
    NEWLINE = "NEWLINE"
    INDENT = "INDENT"
    DEDENT = "DEDENT"
    EOF = "EOF"


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    lexeme: str
    span: SourceSpan

    def __str__(self) -> str:
        return f"Token({self.kind.name}, {self.lexeme!r}, {self.span})"
