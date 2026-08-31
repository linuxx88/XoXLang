"""Deterministic type-agnostic Lexer for XoX (X-o-X) lexical core."""
from typing import Any, Dict, List, Optional, Sequence
from xoxlang.tokens import SourceLocation, SourceSpan, Token, TokenKind


class LexerError(Exception):
    def __init__(
        self,
        message: str,
        location: SourceLocation,
        filename: str = "<input>",
        *,
        note: Optional[str] = None,
        help: Optional[str] = None,
        alternatives: Optional[Sequence[str]] = None,
        annotations: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(f"{filename}:{location.line}:{location.column}: LexerError: {message}")
        self.message = message
        self.location = location
        self.filename = filename
        self.note = note
        self.help = help
        self.alternatives = list(alternatives) if alternatives is not None else None
        self.annotations = annotations

    def to_diagnostic(self) -> "Diagnostic":
        from xoxlang.diagnostics import Diagnostic, DiagnosticCategory
        span = SourceSpan(self.location, self.location) if self.location is not None else None
        return Diagnostic(
            category=DiagnosticCategory.SYNTAX_ERROR,
            message=self.message,
            span=span,
            primary_error=self.message,
            note=self.note,
            help=self.help,
            alternatives=self.alternatives,
            annotations=self.annotations,
        )

    def render(self, source_text: Optional[str] = None, filename: Optional[str] = None) -> str:
        from xoxlang.diagnostics import render_diagnostic
        effective_filename = filename if filename is not None else self.filename
        return render_diagnostic(self.to_diagnostic(), source_text=source_text, filename=effective_filename)


KEYWORDS = {
    "if": TokenKind.IF,
    "xen": TokenKind.XEN,
    "else": TokenKind.ELSE,
    "fn": TokenKind.FN,
    "return": TokenKind.RETURN,
    "AND": TokenKind.AND,
    "OR": TokenKind.OR,
    "NOT": TokenKind.NOT,
    "pass": TokenKind.PASS,
    "True": TokenKind.TRUE,
    "False": TokenKind.FALSE,
    "Unknown": TokenKind.UNKNOWN,
}


class Lexer:
    def __init__(self, source: str, filename: str = "<input>"):
        self.source = source
        self.filename = filename
        self.length = len(source)
        self.pos = 0
        self.line = 1
        self.col = 1
        self.indent_stack: List[int] = [0]
        self.paren_depth = 0
        self.tokens: List[Token] = []

    def _current_char(self) -> Optional[str]:
        if self.pos < self.length:
            return self.source[self.pos]
        return None

    def _peek_char(self, offset: int = 1) -> Optional[str]:
        target_pos = self.pos + offset
        if target_pos < self.length:
            return self.source[target_pos]
        return None

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def tokenize(self) -> List[Token]:
        at_line_start = True
        line_had_tokens = False

        while self.pos < self.length:
            # Handle Indentation at the start of a logical line outside parentheses
            if at_line_start and self.paren_depth == 0:
                # Count leading spaces
                indent_col = 0
                indent_start_loc = SourceLocation(self.line, self.col)
                while self._current_char() == " ":
                    self._advance()
                    indent_col += 1

                # Check if blank line or comment line
                curr = self._current_char()
                if curr in ("\n", "\r", None) or curr == "#":
                    # Ignore indentation on empty or comment-only lines
                    if curr == "#":
                        while self.pos < self.length and self._current_char() not in ("\n", "\r"):
                            self._advance()
                    if self._current_char() in ("\n", "\r"):
                        if self._current_char() == "\r" and self._peek_char() == "\n":
                            self._advance()
                        self._advance()
                    at_line_start = True
                    continue

                current_indent = self.indent_stack[-1]
                if indent_col > current_indent:
                    self.indent_stack.append(indent_col)
                    end_loc = SourceLocation(self.line, self.col)
                    self.tokens.append(Token(TokenKind.INDENT, " " * (indent_col - current_indent), SourceSpan(indent_start_loc, end_loc)))
                elif indent_col < current_indent:
                    while self.indent_stack and indent_col < self.indent_stack[-1]:
                        self.indent_stack.pop()
                        end_loc = SourceLocation(self.line, self.col)
                        self.tokens.append(Token(TokenKind.DEDENT, "", SourceSpan(indent_start_loc, end_loc)))
                    if not self.indent_stack or indent_col != self.indent_stack[-1]:
                        raise LexerError(
                            f"Unindent does not match any outer indentation level (col {indent_col})",
                            indent_start_loc,
                            self.filename,
                        )

                at_line_start = False

            if self.pos >= self.length:
                break

            ch = self._current_char()
            assert ch is not None

            # Normal whitespace outside indentation
            if ch in (" ", "\t"):
                if ch == "\t":
                    raise LexerError("Tab characters are forbidden in source indentation/spacing", SourceLocation(self.line, self.col), self.filename)
                self._advance()
                continue

            # Line comments
            if ch == "#":
                while self.pos < self.length and self._current_char() not in ("\n", "\r"):
                    self._advance()
                continue

            # Newlines
            if ch in ("\n", "\r"):
                loc = SourceLocation(self.line, self.col)
                if ch == "\r" and self._peek_char() == "\n":
                    self._advance()
                self._advance()
                if line_had_tokens and self.paren_depth == 0:
                    self.tokens.append(Token(TokenKind.NEWLINE, "\n", SourceSpan(loc, SourceLocation(self.line, self.col))))
                    line_had_tokens = False
                at_line_start = True
                continue

            # Punctuation and Operators
            if ch == ":":
                start_loc = SourceLocation(self.line, self.col)
                self._advance()
                end_loc = SourceLocation(self.line, self.col)
                self.tokens.append(Token(TokenKind.COLON, ":", SourceSpan(start_loc, end_loc)))
                line_had_tokens = True
                continue

            if ch == ",":
                start_loc = SourceLocation(self.line, self.col)
                self._advance()
                end_loc = SourceLocation(self.line, self.col)
                self.tokens.append(Token(TokenKind.COMMA, ",", SourceSpan(start_loc, end_loc)))
                line_had_tokens = True
                continue

            if ch == ".":
                start_loc = SourceLocation(self.line, self.col)
                self._advance()
                end_loc = SourceLocation(self.line, self.col)
                self.tokens.append(Token(TokenKind.DOT, ".", SourceSpan(start_loc, end_loc)))
                line_had_tokens = True
                continue

            if ch == "-":
                start_loc = SourceLocation(self.line, self.col)
                if self._peek_char() == ">":
                    self._advance()
                    self._advance()
                    end_loc = SourceLocation(self.line, self.col)
                    self.tokens.append(Token(TokenKind.ARROW, "->", SourceSpan(start_loc, end_loc)))
                    line_had_tokens = True
                    continue
                else:
                    self._advance()
                    raise LexerError("Unsupported character '-'. '-' is only valid as part of '->' in return type annotations.", start_loc, self.filename)

            if ch == "(":
                start_loc = SourceLocation(self.line, self.col)
                self._advance()
                end_loc = SourceLocation(self.line, self.col)
                self.tokens.append(Token(TokenKind.LPAREN, "(", SourceSpan(start_loc, end_loc)))
                self.paren_depth += 1
                line_had_tokens = True
                continue

            if ch == ")":
                start_loc = SourceLocation(self.line, self.col)
                self._advance()
                end_loc = SourceLocation(self.line, self.col)
                if self.paren_depth <= 0:
                    raise LexerError("Unmatched ')' parenthesis", start_loc, self.filename)
                self.paren_depth -= 1
                self.tokens.append(Token(TokenKind.RPAREN, ")", SourceSpan(start_loc, end_loc)))
                line_had_tokens = True
                continue

            if ch == "=":
                start_loc = SourceLocation(self.line, self.col)
                self._advance()
                if self.pos < self.length and self._current_char() == "=":
                    self._advance()
                    end_loc = SourceLocation(self.line, self.col)
                    self.tokens.append(Token(TokenKind.EQ_EQ, "==", SourceSpan(start_loc, end_loc)))
                    line_had_tokens = True
                    continue
                else:
                    end_loc = SourceLocation(self.line, self.col)
                    self.tokens.append(Token(TokenKind.ASSIGN, "=", SourceSpan(start_loc, end_loc)))
                    line_had_tokens = True
                    continue

            if ch == "!":
                start_loc = SourceLocation(self.line, self.col)
                self._advance()
                if self.pos < self.length and self._current_char() == "=":
                    self._advance()
                    end_loc = SourceLocation(self.line, self.col)
                    self.tokens.append(Token(TokenKind.EXCL_EQ, "!=", SourceSpan(start_loc, end_loc)))
                    line_had_tokens = True
                    continue
                else:
                    self._advance()
                    raise LexerError("Unsupported character '!'. Use 'NOT' for logical negation or '!=' for inequality.", start_loc, self.filename)

            if ch.isalpha() or ch == "_":
                start_loc = SourceLocation(self.line, self.col)
                ident_chars = []
                while self.pos < self.length and (self._current_char().isalnum() or self._current_char() == "_"):
                    ident_chars.append(self._advance())
                end_loc = SourceLocation(self.line, self.col)
                ident_str = "".join(ident_chars)

                kind = KEYWORDS.get(ident_str, TokenKind.IDENTIFIER)
                self.tokens.append(Token(kind, ident_str, SourceSpan(start_loc, end_loc)))
                line_had_tokens = True
                continue

            error_loc = SourceLocation(self.line, self.col)
            bad_char = self._advance()
            raise LexerError(f"Unsupported character {bad_char!r}", error_loc, self.filename)

        eof_loc = SourceLocation(self.line, self.col)
        if self.paren_depth > 0:
            raise LexerError("Unclosed '(' parenthesis at end of file", eof_loc, self.filename)

        if line_had_tokens and self.paren_depth == 0:
            self.tokens.append(Token(TokenKind.NEWLINE, "\n", SourceSpan(eof_loc, eof_loc)))

        # Emit remaining DEDENT tokens at EOF
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenKind.DEDENT, "", SourceSpan(eof_loc, eof_loc)))

        self.tokens.append(Token(TokenKind.EOF, "", SourceSpan(eof_loc, eof_loc)))
        return self.tokens


def tokenize(source: str, filename: str = "<input>") -> List[Token]:
    lexer = Lexer(source, filename=filename)
    return lexer.tokenize()
