"""Deterministic type-agnostic parser for X-o-X syntax."""
from typing import Any, Dict, List, Optional, Sequence, Union
from xoxlang.tokens import SourceLocation, SourceSpan, Token, TokenKind
from xoxlang.ast import (
    ASTNode,
    AssignmentStatement,
    BinaryExpr,
    Block,
    CollapseXoXToBoolWithDefault,
    ConditionalStatement,
    ExprStatement,
    Expression,
    FunctionDefinition,
    GroupExpr,
    IdentifierExpr,
    IgnoreStatement,
    InlineConditionalExpr,
    LiteralExpr,
    Parameter,
    PassStatement,
    Program,
    PromoteBoolToXoX,
    ReturnStatement,
    Statement,
    UnaryExpr,
)


class ParseError(Exception):
    """Syntax or structural error emitted during parsing."""
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
        super().__init__(f"{filename}:{location.line}:{location.column}: SyntaxError: {message}")
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


def _format_token_name(kind: TokenKind) -> str:
    names = {
        TokenKind.LPAREN: "'('",
        TokenKind.RPAREN: "')'",
        TokenKind.COLON: "':'",
        TokenKind.ASSIGN: "'='",
        TokenKind.ARROW: "'->'",
        TokenKind.DOT: "'.'",
        TokenKind.COMMA: "','",
        TokenKind.EQ_EQ: "'=='",
        TokenKind.EXCL_EQ: "'!='",
        TokenKind.IF: "'if'",
        TokenKind.XEN: "'xen'",
        TokenKind.ELSE: "'else'",
        TokenKind.FN: "'fn'",
        TokenKind.RETURN: "'return'",
        TokenKind.PASS: "'pass'",
        TokenKind.AND: "'AND'",
        TokenKind.OR: "'OR'",
        TokenKind.NOT: "'NOT'",
        TokenKind.TRUE: "'True'",
        TokenKind.FALSE: "'False'",
        TokenKind.UNKNOWN: "'Unknown'",
        TokenKind.IDENTIFIER: "an identifier",
        TokenKind.NEWLINE: "newline",
        TokenKind.INDENT: "indented block",
        TokenKind.DEDENT: "dedent",
        TokenKind.EOF: "end of file",
    }
    return names.get(kind, kind.name.lower())


def _format_found_token(tok: Token) -> str:
    if tok.kind == TokenKind.EOF:
        return "end of file"
    if tok.kind == TokenKind.NEWLINE:
        return "newline"
    if tok.kind == TokenKind.INDENT:
        return "indented block"
    if tok.kind == TokenKind.DEDENT:
        return "dedent"
    if tok.lexeme:
        return f"{tok.lexeme!r}"
    return _format_token_name(tok.kind)


class Parser:
    def __init__(self, tokens: List[Token], filename: str = "<input>"):
        self.tokens = tokens
        self.filename = filename
        self.pos = 0

    def _current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def _peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def _advance(self) -> Token:
        tok = self._current()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def _expect(self, kind: TokenKind, msg: str = "") -> Token:
        curr = self._current()
        if curr.kind == kind:
            return self._advance()
        err_msg = msg if msg else f"Expected {_format_token_name(kind)}, but found {_format_found_token(curr)}"
        raise ParseError(err_msg, curr.span.start, self.filename)

    def _skip_newlines(self) -> None:
        while self._current().kind == TokenKind.NEWLINE:
            self._advance()

    def parse(self) -> Program:
        statements: List[Statement] = []
        self._skip_newlines()

        while self._current().kind != TokenKind.EOF:
            stmt = self.parse_statement()
            statements.append(stmt)
            self._skip_newlines()

        start_loc = statements[0].span.start if statements and statements[0].span else SourceLocation(1, 1)
        end_loc = statements[-1].span.end if statements and statements[-1].span else SourceLocation(1, 1)
        return Program(statements=statements, span=SourceSpan(start_loc, end_loc))

    def parse_statement(self) -> Statement:
        self._skip_newlines()
        curr = self._current()

        # Check for orphan clauses
        if curr.kind == TokenKind.XEN:
            raise ParseError("Orphan 'xen' clause without a preceding 'if'", curr.span.start, self.filename)
        if curr.kind == TokenKind.ELSE:
            raise ParseError("Orphan 'else' clause without a preceding 'if'", curr.span.start, self.filename)

        # Check for elif rejection
        if curr.kind == TokenKind.IDENTIFIER and curr.lexeme == "elif":
            raise ParseError(
                "'elif' is not supported; multi-branch conditionals must use nested if/else or if/xen/else",
                curr.span.start,
                self.filename,
            )

        if curr.kind == TokenKind.FN:
            return self.parse_function_definition()

        if curr.kind == TokenKind.IF:
            return self.parse_conditional_statement()

        if curr.kind == TokenKind.PASS:
            pass_tok = self._advance()
            if self._current().kind == TokenKind.NEWLINE:
                self._advance()
            return PassStatement(span=pass_tok.span)

        if curr.kind == TokenKind.RETURN:
            return_tok = self._advance()
            if self._current().kind in (TokenKind.NEWLINE, TokenKind.EOF):
                raise ParseError("Bare 'return' is not supported; 'return' requires a value expression (e.g. 'return expression')", return_tok.span.end, self.filename)
            value = self.parse_expression()
            if self._current().kind not in (TokenKind.NEWLINE, TokenKind.EOF):
                raise ParseError(f"Unexpected {_format_found_token(self._current())} after return expression", self._current().span.start, self.filename)
            if self._current().kind == TokenKind.NEWLINE:
                self._advance()
            total_span = SourceSpan(return_tok.span.start, value.span.end if value.span else return_tok.span.end)
            return ReturnStatement(value=value, return_span=return_tok.span, span=total_span)

        # Variable binding or reassignment statement
        if curr.kind == TokenKind.IDENTIFIER:
            next_tok = self._peek()
            if next_tok.kind == TokenKind.ASSIGN:
                target_tok = self._advance()
                assign_tok = self._advance()
                if self._current().kind in (TokenKind.NEWLINE, TokenKind.EOF):
                    raise ParseError("Missing initializer expression in assignment statement", assign_tok.span.end, self.filename)
                value = self.parse_expression()
                if self._current().kind not in (TokenKind.NEWLINE, TokenKind.EOF):
                    raise ParseError(f"Unexpected {_format_found_token(self._current())} after expression in assignment statement", self._current().span.start, self.filename)
                if self._current().kind == TokenKind.NEWLINE:
                    self._advance()
                total_span = SourceSpan(target_tok.span.start, value.span.end if value.span else assign_tok.span.end)
                return AssignmentStatement(
                    target=target_tok.lexeme,
                    value=value,
                    annotation=None,
                    target_span=target_tok.span,
                    assign_span=assign_tok.span,
                    span=total_span,
                )

            if next_tok.kind == TokenKind.COLON:
                target_tok = self._advance()
                colon_tok = self._advance()
                type_tok = self._current()
                if type_tok.kind != TokenKind.IDENTIFIER or type_tok.lexeme not in ("Bool", "XoX"):
                    raise ParseError(
                        f"Invalid or unsupported type annotation {type_tok.lexeme!r}; expected 'Bool' or 'XoX'",
                        type_tok.span.start,
                        self.filename,
                    )
                self._advance()
                assign_curr = self._current()
                if assign_curr.kind != TokenKind.ASSIGN:
                    raise ParseError(
                        "Uninitialized variable declarations are not supported; variables must be initialized when declared using '=' (e.g. 'name: Type = value')",
                        assign_curr.span.start,
                        self.filename,
                    )
                assign_tok = self._advance()
                if self._current().kind in (TokenKind.NEWLINE, TokenKind.EOF):
                    raise ParseError("Missing initializer expression in annotated assignment statement", assign_tok.span.end, self.filename)
                value = self.parse_expression()
                if self._current().kind not in (TokenKind.NEWLINE, TokenKind.EOF):
                    raise ParseError(f"Unexpected {_format_found_token(self._current())} after expression in annotated assignment statement", self._current().span.start, self.filename)
                if self._current().kind == TokenKind.NEWLINE:
                    self._advance()
                total_span = SourceSpan(target_tok.span.start, value.span.end if value.span else assign_tok.span.end)
                return AssignmentStatement(
                    target=target_tok.lexeme,
                    value=value,
                    annotation=type_tok.lexeme,
                    target_span=target_tok.span,
                    annotation_span=type_tok.span,
                    assign_span=assign_tok.span,
                    span=total_span,
                )

        # Expression statement (e.g. standalone identifier or expression)
        expr = self.parse_expression()
        if self._current().kind not in (TokenKind.NEWLINE, TokenKind.EOF):
            raise ParseError(f"Unexpected {_format_found_token(self._current())} after expression", self._current().span.start, self.filename)
        if self._current().kind == TokenKind.NEWLINE:
            self._advance()
        return ExprStatement(expr=expr, span=expr.span)

    def parse_function_definition(self) -> FunctionDefinition:
        fn_tok = self._expect(TokenKind.FN)
        name_tok = self._expect(TokenKind.IDENTIFIER, "Expected function name after 'fn'")
        self._expect(TokenKind.LPAREN, "Expected '(' after function name")

        parameters: List[Parameter] = []
        if self._current().kind != TokenKind.RPAREN:
            while True:
                param = self.parse_parameter()
                parameters.append(param)
                if self._current().kind == TokenKind.COMMA:
                    comma_tok = self._advance()
                    if self._current().kind == TokenKind.RPAREN:
                        raise ParseError("Trailing comma in parameter list is not supported", comma_tok.span.start, self.filename)
                else:
                    break

        rparen_tok = self._expect(TokenKind.RPAREN, "Expected ')' after parameter list")

        return_annotation: Optional[str] = None
        return_annotation_span: Optional[SourceSpan] = None
        if self._current().kind == TokenKind.ARROW:
            arrow_tok = self._advance()
            type_tok = self._current()
            if type_tok.kind != TokenKind.IDENTIFIER or type_tok.lexeme not in ("Bool", "XoX"):
                raise ParseError(
                    f"Invalid or unsupported return type annotation {type_tok.lexeme!r}; expected 'Bool' or 'XoX'",
                    type_tok.span.start,
                    self.filename,
                )
            self._advance()
            return_annotation = type_tok.lexeme
            return_annotation_span = SourceSpan(arrow_tok.span.start, type_tok.span.end)

        self._expect(TokenKind.COLON, "Expected ':' after function signature")
        body = self.parse_block()
        total_span = SourceSpan(fn_tok.span.start, body.span.end if body.span else fn_tok.span.end)

        return FunctionDefinition(
            name=name_tok.lexeme,
            parameters=parameters,
            return_annotation=return_annotation,
            body=body,
            fn_span=fn_tok.span,
            name_span=name_tok.span,
            return_annotation_span=return_annotation_span,
            span=total_span,
        )

    def parse_parameter(self) -> Parameter:
        curr = self._current()
        if curr.kind != TokenKind.IDENTIFIER:
            raise ParseError(f"Expected parameter name, but found {_format_found_token(curr)}", curr.span.start, self.filename)
        name_tok = self._advance()

        if self._current().kind != TokenKind.COLON:
            raise ParseError(f"Parameter '{name_tok.lexeme}' must be explicitly typed with ': TypeName'", self._current().span.start, self.filename)
        colon_tok = self._advance()

        type_tok = self._current()
        if type_tok.kind != TokenKind.IDENTIFIER or type_tok.lexeme not in ("Bool", "XoX"):
            raise ParseError(
                f"Invalid or unsupported parameter type annotation {type_tok.lexeme!r}; expected 'Bool' or 'XoX'",
                type_tok.span.start,
                self.filename,
            )


        self._advance()
        param_span = SourceSpan(name_tok.span.start, type_tok.span.end)
        return Parameter(
            name=name_tok.lexeme,
            type_name=type_tok.lexeme,
            name_span=name_tok.span,
            type_span=type_tok.span,
            span=param_span,
        )

    def parse_conditional_statement(self) -> ConditionalStatement:
        if_tok = self._expect(TokenKind.IF)
        cond = self.parse_expression()
        self._expect(TokenKind.COLON, "Expected ':' after if condition")
        true_branch = self.parse_block()

        self._skip_newlines()

        xen_branch: Optional[Union[Block, IgnoreStatement]] = None
        xen_span: Optional[SourceSpan] = None
        if self._current().kind == TokenKind.XEN:
            xen_tok = self._advance()
            xen_span = xen_tok.span
            self._expect(TokenKind.COLON, "Expected ':' after xen")
            xen_branch = self.parse_xen_block()

        self._skip_newlines()

        else_branch: Optional[Block] = None
        else_span: Optional[SourceSpan] = None
        if self._current().kind == TokenKind.ELSE:
            else_tok = self._advance()
            else_span = else_tok.span
            self._expect(TokenKind.COLON, "Expected ':' after else")
            else_branch = self.parse_block()

        self._skip_newlines()

        # Check for invalid ordering or duplicate clauses
        if self._current().kind == TokenKind.XEN:
            curr = self._current()
            raise ParseError("Duplicate or misplaced 'xen' clause in conditional statement", curr.span.start, self.filename)
        if self._current().kind == TokenKind.ELSE:
            curr = self._current()
            raise ParseError("Duplicate 'else' clause in conditional statement", curr.span.start, self.filename)
        if self._current().kind == TokenKind.IDENTIFIER and self._current().lexeme == "elif":
            curr = self._current()
            raise ParseError(
                "'elif' is not supported; multi-branch conditionals must use nested if/else or if/xen/else",
                curr.span.start,
                self.filename,
            )

        end_span = else_branch.span if else_branch else (xen_branch.span if xen_branch else true_branch.span)
        total_span = SourceSpan(if_tok.span.start, end_span.end) if end_span else if_tok.span

        return ConditionalStatement(
            condition=cond,
            true_branch=true_branch,
            xen_branch=xen_branch,
            else_branch=else_branch,
            if_span=if_tok.span,
            xen_span=xen_span,
            else_span=else_span,
            span=total_span,
        )

    def parse_block(self) -> Block:
        self._expect(TokenKind.NEWLINE, "Expected newline before block indentation")
        indent_tok = self._expect(TokenKind.INDENT, "Expected indented block")

        statements: List[Statement] = []
        self._skip_newlines()

        while self._current().kind not in (TokenKind.DEDENT, TokenKind.EOF):
            stmt = self.parse_statement()
            statements.append(stmt)
            self._skip_newlines()

        dedent_tok = self._expect(TokenKind.DEDENT, "Expected dedent at block end")
        span = SourceSpan(indent_tok.span.start, dedent_tok.span.end)
        return Block(statements=statements, span=span)

    def parse_xen_block(self) -> Union[Block, IgnoreStatement]:
        curr = self._current()

        # Check for compact single-line 'xen: ignore'
        if curr.kind == TokenKind.IDENTIFIER and curr.lexeme == "ignore":
            ignore_tok = self._advance()
            if self._current().kind not in (TokenKind.NEWLINE, TokenKind.EOF):
                raise ParseError(
                    "Non-exclusive 'xen: ignore'; 'ignore' cannot coexist with other statements in a xen clause",
                    self._current().span.start,
                    self.filename,
                )
            if self._current().kind == TokenKind.NEWLINE:
                self._advance()
            return IgnoreStatement(span=ignore_tok.span)

        if curr.kind != TokenKind.NEWLINE:
            raise ParseError(
                "Illegal inline statement under 'xen'; only 'xen: ignore' is permitted inline",
                curr.span.start,
                self.filename,
            )

        self._expect(TokenKind.NEWLINE, "Expected newline before xen block indentation")
        indent_tok = self._expect(TokenKind.INDENT, "Expected indented xen block")

        self._skip_newlines()
        curr = self._current()

        # Check for exclusive atomic 'xen: ignore'
        if curr.kind == TokenKind.IDENTIFIER and curr.lexeme == "ignore":
            ignore_tok = self._advance()
            if self._current().kind == TokenKind.NEWLINE:
                self._advance()
            self._skip_newlines()

            if self._current().kind != TokenKind.DEDENT:
                raise ParseError(
                    "Non-exclusive 'xen: ignore'; 'ignore' cannot coexist with other statements in a xen clause",
                    ignore_tok.span.start,
                    self.filename,
                )
            dedent_tok = self._advance()
            return IgnoreStatement(span=SourceSpan(ignore_tok.span.start, dedent_tok.span.end))

        # Multi-statement or standard block in xen
        statements: List[Statement] = []
        while self._current().kind not in (TokenKind.DEDENT, TokenKind.EOF):
            if self._current().kind == TokenKind.IDENTIFIER and self._current().lexeme == "ignore":
                raise ParseError(
                    "Non-exclusive 'xen: ignore'; 'ignore' cannot coexist with other statements in a xen clause",
                    self._current().span.start,
                    self.filename,
                )
            stmt = self.parse_statement()
            statements.append(stmt)
            self._skip_newlines()

        dedent_tok = self._expect(TokenKind.DEDENT, "Expected dedent at xen block end")
        block_span = SourceSpan(indent_tok.span.start, dedent_tok.span.end)

        # Check for prohibition of all-pass xen clauses
        if len(statements) > 0 and all(isinstance(s, PassStatement) for s in statements):
            raise ParseError(
                "A 'xen' clause containing only 'pass' is invalid; explicit no-op handling of Unknown requires 'xen: ignore'",
                block_span.start,
                self.filename,
            )

        return Block(statements=statements, span=block_span)

    def parse_expression(self) -> Expression:
        return self.parse_conditional()

    def parse_conditional(self) -> Expression:
        left = self.parse_or()
        if self._current().kind == TokenKind.IF:
            if_tok = self._advance()
            condition = self.parse_or()
            if self._current().kind == TokenKind.XEN:
                xen_tok = self._advance()
                xen_expr = self.parse_or()
                else_tok = self._expect(TokenKind.ELSE, "Expected 'else' keyword in XoX inline conditional expression")
                else_expr = self.parse_conditional()
                span = SourceSpan(left.span.start, else_expr.span.end) if left.span and else_expr.span else None
                return InlineConditionalExpr(
                    true_expr=left,
                    condition=condition,
                    xen_expr=xen_expr,
                    else_expr=else_expr,
                    span=span,
                )
            elif self._current().kind == TokenKind.ELSE:
                else_tok = self._advance()
                else_expr = self.parse_conditional()
                span = SourceSpan(left.span.start, else_expr.span.end) if left.span and else_expr.span else None
                return InlineConditionalExpr(
                    true_expr=left,
                    condition=condition,
                    xen_expr=None,
                    else_expr=else_expr,
                    span=span,
                )
            else:
                bad_tok = self._current()
                raise ParseError(
                    "Expected 'else' or 'xen' after condition in inline conditional expression",
                    bad_tok.span.start,
                    self.filename,
                )
        return left

    def parse_or(self) -> Expression:
        left = self.parse_and()
        while self._current().kind == TokenKind.OR:
            op_tok = self._advance()
            right = self.parse_and()
            span = SourceSpan(left.span.start, right.span.end) if left.span and right.span else None
            left = BinaryExpr(left=left, op=op_tok.kind, right=right, span=span)
        return left

    def parse_and(self) -> Expression:
        left = self.parse_equality()
        while self._current().kind == TokenKind.AND:
            op_tok = self._advance()
            right = self.parse_equality()
            span = SourceSpan(left.span.start, right.span.end) if left.span and right.span else None
            left = BinaryExpr(left=left, op=op_tok.kind, right=right, span=span)
        return left

    def parse_equality(self) -> Expression:
        left = self.parse_not()
        if self._current().kind in (TokenKind.EQ_EQ, TokenKind.EXCL_EQ):
            op_tok = self._advance()
            right = self.parse_not()
            span = SourceSpan(left.span.start, right.span.end) if left.span and right.span else None
            left = BinaryExpr(left=left, op=op_tok.kind, right=right, span=span)

            # Reject chained comparisons (e.g. a == b == c, a == b != c)
            if self._current().kind in (TokenKind.EQ_EQ, TokenKind.EXCL_EQ):
                bad_tok = self._current()
                raise ParseError(
                    "Chained comparisons (e.g. 'a == b == c' or 'a == b != c') are not supported; comparisons must be written explicitly (e.g. '(a == b) AND (b == c)')",
                    bad_tok.span.start,
                    self.filename,
                )
        return left

    def parse_not(self) -> Expression:
        if self._current().kind == TokenKind.NOT:
            not_tok = self._advance()
            operand = self.parse_not()
            span = SourceSpan(not_tok.span.start, operand.span.end) if operand.span else not_tok.span
            return UnaryExpr(op=TokenKind.NOT, operand=operand, span=span)
        return self.parse_postfix()

    def parse_postfix(self) -> Expression:
        expr = self.parse_primary()
        while self._current().kind == TokenKind.DOT:
            dot_tok = self._advance()
            ident_tok = self._expect(TokenKind.IDENTIFIER, "Expected identifier after '.'")
            if ident_tok.lexeme != "unwrap_or":
                raise ParseError(
                    f"Unsupported postfix method or attribute '{ident_tok.lexeme}'; only 'unwrap_or' is supported",
                    ident_tok.span.start,
                    self.filename,
                )
            self._expect(TokenKind.LPAREN, "Expected '(' after 'unwrap_or'")
            if self._current().kind == TokenKind.RPAREN:
                bad_tok = self._current()
                raise ParseError(
                    "Missing mandatory fallback argument in 'unwrap_or()'",
                    bad_tok.span.start,
                    self.filename,
                )
            fallback = self.parse_expression()
            rparen_tok = self._expect(TokenKind.RPAREN, "Expected ')' after 'unwrap_or' fallback argument")
            span = SourceSpan(expr.span.start, rparen_tok.span.end) if expr.span and rparen_tok.span else None
            expr = CollapseXoXToBoolWithDefault(source=expr, fallback=fallback, span=span)
        return expr

    def parse_primary(self) -> Expression:
        curr = self._current()

        if curr.kind == TokenKind.LPAREN:
            lparen_tok = self._advance()
            expr = self.parse_expression()
            rparen_tok = self._expect(TokenKind.RPAREN, "Expected ')' to close grouped expression")
            span = SourceSpan(lparen_tok.span.start, rparen_tok.span.end)
            return GroupExpr(expr=expr, span=span)

        if curr.kind in (TokenKind.TRUE, TokenKind.FALSE, TokenKind.UNKNOWN):
            lit_tok = self._advance()
            return LiteralExpr(kind=lit_tok.kind, lexeme=lit_tok.lexeme, span=lit_tok.span)

        if curr.kind == TokenKind.IDENTIFIER:
            if curr.lexeme == "xox" and self._peek().kind == TokenKind.LPAREN:
                xox_tok = self._advance()
                lparen_tok = self._advance()
                if self._current().kind == TokenKind.RPAREN:
                    raise ParseError(
                        "Missing expression in 'xox()'",
                        self._current().span.start,
                        self.filename,
                    )
                inner_expr = self.parse_expression()
                rparen_tok = self._expect(TokenKind.RPAREN, "Expected ')' after 'xox(' expression")
                span = SourceSpan(xox_tok.span.start, rparen_tok.span.end)
                return PromoteBoolToXoX(expr=inner_expr, span=span)

            if curr.lexeme == "elif":
                raise ParseError(
                    "'elif' is not supported; multi-branch conditionals must use nested if/else or if/xen/else",
                    curr.span.start,
                    self.filename,
                )
            ident_tok = self._advance()
            return IdentifierExpr(name=ident_tok.lexeme, span=ident_tok.span)

        raise ParseError(
            f"Unexpected {_format_found_token(curr)} in expression",
            curr.span.start,
            self.filename,
        )


def parse(tokens: List[Token], filename: str = "<input>") -> Program:
    parser = Parser(tokens, filename=filename)
    return parser.parse()
