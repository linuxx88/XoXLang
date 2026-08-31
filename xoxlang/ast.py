"""Generic AST node definitions for X-o-X syntax."""
from dataclasses import dataclass
from typing import List, Optional, Union
from xoxlang.tokens import SourceSpan, TokenKind


@dataclass
class ASTNode:
    """Base class for all X-o-X AST nodes."""
    pass


# Expressions
@dataclass
class Expression(ASTNode):
    """Base class for expression AST nodes."""
    span: Optional[SourceSpan] = None


@dataclass
class LiteralExpr(Expression):
    """Literal truth/uncertainty value (True, False, Unknown)."""
    kind: TokenKind = None  # type: ignore
    lexeme: str = ""
    span: Optional[SourceSpan] = None


@dataclass
class IdentifierExpr(Expression):
    """Identifier expression node."""
    name: str = ""
    span: Optional[SourceSpan] = None


@dataclass
class UnaryExpr(Expression):
    """Unary prefix expression (NOT)."""
    op: TokenKind = None  # type: ignore
    operand: Expression = None  # type: ignore
    span: Optional[SourceSpan] = None


@dataclass
class BinaryExpr(Expression):
    """Binary expression (AND, OR, ==, !=)."""
    left: Expression = None  # type: ignore
    op: TokenKind = None  # type: ignore
    right: Expression = None  # type: ignore
    span: Optional[SourceSpan] = None


@dataclass
class GroupExpr(Expression):
    """Parenthesized expression grouping."""
    expr: Expression = None  # type: ignore
    span: Optional[SourceSpan] = None


@dataclass
class InlineConditionalExpr(Expression):
    """Inline conditional expression (true_expr if condition [xen xen_expr] else else_expr)."""
    true_expr: Expression = None  # type: ignore
    condition: Expression = None  # type: ignore
    xen_expr: Optional[Expression] = None
    else_expr: Expression = None  # type: ignore
    span: Optional[SourceSpan] = None


@dataclass
class CollapseXoXToBoolWithDefault(Expression):
    """Special flow-control collapse primitive x.unwrap_or(default_bool) from XoX to Bool."""
    source: Expression = None  # type: ignore
    fallback: Expression = None  # type: ignore
    span: Optional[SourceSpan] = None


@dataclass
class PromoteBoolToXoX(Expression):
    """Explicit promotion construct xox(expr) from Bool to XoX."""
    expr: Expression = None  # type: ignore
    span: Optional[SourceSpan] = None



# Parameters
@dataclass
class Parameter(ASTNode):
    """Explicitly typed function parameter (name: TypeName)."""
    name: str = ""
    type_name: str = ""
    name_span: Optional[SourceSpan] = None
    type_span: Optional[SourceSpan] = None
    span: Optional[SourceSpan] = None


# Statements
@dataclass
class Statement(ASTNode):
    """Base class for statement AST nodes."""
    span: Optional[SourceSpan] = None


@dataclass
class PassStatement(Statement):
    """Ordinary pass statement."""
    span: Optional[SourceSpan] = None


@dataclass
class IgnoreStatement(Statement):
    """Dedicated explicit ignore marker for xen: ignore."""
    span: Optional[SourceSpan] = None


@dataclass
class ReturnStatement(Statement):
    """Value-returning statement (return Expression)."""
    value: Expression = None  # type: ignore
    return_span: Optional[SourceSpan] = None
    span: Optional[SourceSpan] = None


@dataclass
class AssignmentStatement(Statement):
    """Initialized variable binding or reassignment statement (x = expr or x: Type = expr)."""
    target: str = ""
    value: Expression = None  # type: ignore
    annotation: Optional[str] = None
    target_span: Optional[SourceSpan] = None
    annotation_span: Optional[SourceSpan] = None
    assign_span: Optional[SourceSpan] = None
    span: Optional[SourceSpan] = None


@dataclass
class ExprStatement(Statement):
    """Expression evaluated as a standalone statement."""
    expr: Expression = None  # type: ignore
    span: Optional[SourceSpan] = None


@dataclass
class Block(Statement):
    """Indented sequence of statements."""
    statements: List[Statement] = None  # type: ignore
    span: Optional[SourceSpan] = None

    def __post_init__(self):
        if self.statements is None:
            self.statements = []


@dataclass
class FunctionDefinition(Statement):
    """Function definition statement (fn name(params) -> ReturnType: Block)."""
    name: str = ""
    parameters: List[Parameter] = None  # type: ignore
    return_annotation: Optional[str] = None
    body: Block = None  # type: ignore
    fn_span: Optional[SourceSpan] = None
    name_span: Optional[SourceSpan] = None
    return_annotation_span: Optional[SourceSpan] = None
    span: Optional[SourceSpan] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []


@dataclass
class ConditionalStatement(Statement):
    """Generic conditional statement node (if [xen] [else])."""
    condition: Expression = None  # type: ignore
    true_branch: Block = None  # type: ignore
    xen_branch: Optional[Union[Block, IgnoreStatement]] = None
    else_branch: Optional[Block] = None
    if_span: Optional[SourceSpan] = None
    xen_span: Optional[SourceSpan] = None
    else_span: Optional[SourceSpan] = None
    span: Optional[SourceSpan] = None


@dataclass
class Program(ASTNode):
    """Root program node containing top-level statements."""
    statements: List[Statement] = None  # type: ignore
    span: Optional[SourceSpan] = None

    def __post_init__(self):
        if self.statements is None:
            self.statements = []
