"""Semantic analysis, static truth-type checking, contextual literal resolution, and semantic artifact production."""
from dataclasses import dataclass, field
from typing import Dict, Optional, Union
from trool.tokens import TokenKind
from trool.ast import (
    ASTNode,
    AssignmentStatement,
    BinaryExpr,
    Block,
    ConditionalStatement,
    ExprStatement,
    Expression,
    FunctionDefinition,
    GroupExpr,
    IdentifierExpr,
    IgnoreStatement,
    LiteralExpr,
    Parameter,
    PassStatement,
    Program,
    ReturnStatement,
    Statement,
    UnaryExpr,
)
from trool.types import BOOL, XOX, ConditionalKind, TypeKind

from trool.diagnostics import ExhaustivenessError, TypeDiagnosticError
from trool.control_flow import check_function_definite_returns

# Alias for type error in semantic context
TypeError = TypeDiagnosticError


class TypeEnv:
    """Monomorphic variable type environment."""
    def __init__(self, bindings: Optional[Dict[str, TypeKind]] = None):
        self.bindings: Dict[str, TypeKind] = dict(bindings) if bindings else {}

    def lookup(self, name: str) -> Optional[TypeKind]:
        return self.bindings.get(name)

    def bind(self, name: str, type_kind: TypeKind) -> None:
        self.bindings[name] = type_kind

    def __contains__(self, name: str) -> bool:
        return name in self.bindings


@dataclass
class SemanticResult:
    """Persisted semantic analysis artifact recording resolved node types and conditional classifications for lowering."""
    node_types: Dict[int, TypeKind] = field(default_factory=dict)
    conditional_kinds: Dict[int, ConditionalKind] = field(default_factory=dict)

    def type_of(self, expr: Expression) -> TypeKind:
        """Retrieve the resolved static type of an Expression node."""
        t = self.node_types.get(id(expr))
        if t is None:
            raise KeyError(f"No semantic type recorded for expression node {expr!r}")
        return t

    def conditional_kind(self, stmt: ConditionalStatement) -> ConditionalKind:
        """Retrieve the post-type semantic classification of a ConditionalStatement."""
        k = self.conditional_kinds.get(id(stmt))
        if k is None:
            raise KeyError(f"No conditional classification recorded for statement node {stmt!r}")
        return k

    def has_type(self, expr: Expression) -> bool:
        return id(expr) in self.node_types

    def has_conditional_kind(self, stmt: ConditionalStatement) -> bool:
        return id(stmt) in self.conditional_kinds


def _inspect_domain_anchor(expr: Expression, env: TypeEnv) -> Optional[TypeKind]:
    """Inspect an expression tree to find an established domain anchor without prematurely committing uncommitted literals."""
    if isinstance(expr, LiteralExpr):
        if expr.kind == TokenKind.UNKNOWN:
            return XOX
        # True and False are uncommitted literals, so they provide no domain anchor on their own
        return None

    if isinstance(expr, IdentifierExpr):
        return env.lookup(expr.name)

    if isinstance(expr, GroupExpr):
        return _inspect_domain_anchor(expr.expr, env)

    if isinstance(expr, UnaryExpr):
        if expr.op == TokenKind.NOT:
            return _inspect_domain_anchor(expr.operand, env)
        return None

    if isinstance(expr, BinaryExpr):
        if expr.op in (TokenKind.AND, TokenKind.OR):
            left_anchor = _inspect_domain_anchor(expr.left, env)
            right_anchor = _inspect_domain_anchor(expr.right, env)
            if left_anchor == XOX or right_anchor == XOX:
                return XOX
            if left_anchor == BOOL or right_anchor == BOOL:
                return BOOL
            return None

        if expr.op in (TokenKind.EQ_EQ, TokenKind.EXCL_EQ):
            # Equality result is always Bool
            return BOOL

    return None


class SemanticAnalyzer:
    """Semantic analyzer implementing static truth-type checking, contextual literal resolution, and monomorphic binding semantics."""

    def __init__(
        self,
        env: Optional[Union[Dict[str, TypeKind], TypeEnv]] = None,
        current_return_annotation: Optional[TypeKind] = None,
        result: Optional[SemanticResult] = None,
    ):
        if isinstance(env, TypeEnv):
            self.env = env
        elif isinstance(env, dict):
            self.env = TypeEnv(env)
        else:
            self.env = TypeEnv()
        self.current_return_annotation: Optional[TypeKind] = current_return_annotation
        self.result: SemanticResult = result if result is not None else SemanticResult()

    def check_program(self, prog: Program) -> None:
        """Check all statements in a program sequentially."""
        for stmt in prog.statements:
            self.check_statement(stmt)

    def check_statement(self, stmt: Statement) -> None:
        """Type-check a statement node."""
        if isinstance(stmt, FunctionDefinition):
            self.check_function_definition(stmt)
        elif isinstance(stmt, ReturnStatement):
            self.check_return_statement(stmt)
        elif isinstance(stmt, AssignmentStatement):
            self.check_assignment_statement(stmt)
        elif isinstance(stmt, ExprStatement):
            self.check_expression(stmt.expr)
        elif isinstance(stmt, PassStatement) or isinstance(stmt, IgnoreStatement):
            pass
        elif isinstance(stmt, Block):
            for s in stmt.statements:
                self.check_statement(s)
        elif isinstance(stmt, ConditionalStatement):
            self.check_conditional_statement(stmt)
        else:
            raise TypeError(f"Unsupported statement type: {type(stmt).__name__}", span=stmt.span)

    def check_conditional_statement(self, stmt: ConditionalStatement) -> None:
        """Post-type conditional classification, xen legality, and exhaustiveness checking."""
        cond_type = self.check_expression(stmt.condition)

        if cond_type == BOOL:
            if stmt.xen_branch is not None:
                raise TypeError(
                    "A Bool conditional must not contain a 'xen' clause; 'xen' is reserved for 3-valued XoX conditionals",
                    span=stmt.xen_span or stmt.span,
                    violated_rule="§10, §12, §19",
                )
            self.result.conditional_kinds[id(stmt)] = ConditionalKind.BOOL
        elif cond_type == XOX:
            if stmt.xen_branch is None and stmt.else_branch is None:
                raise ExhaustivenessError(
                    "XoX conditional is non-exhaustive; both 'xen' (or 'xen: ignore') and 'else' clauses are required to cover Unknown and False",
                    span=stmt.span,
                    violated_rule="§10, §12, §13",
                )
            if stmt.xen_branch is None:
                raise ExhaustivenessError(
                    "XoX conditional is non-exhaustive; missing 'xen' clause to cover the Unknown state",
                    span=stmt.span,
                    violated_rule="§10, §12, §13",
                )
            if stmt.else_branch is None:
                raise ExhaustivenessError(
                    "XoX conditional is non-exhaustive; missing 'else' clause to cover the False state",
                    span=stmt.span,
                    violated_rule="§10, §12, §13",
                )
            self.result.conditional_kinds[id(stmt)] = ConditionalKind.XOX
        else:
            raise TypeError(
                f"Condition expression must evaluate to Bool or XoX, got {cond_type}",
                span=stmt.condition.span or stmt.span,
                violated_rule="§12, §19",
            )

        # Check branches
        self.check_statement(stmt.true_branch)
        if stmt.xen_branch is not None:
            self.check_statement(stmt.xen_branch)
        if stmt.else_branch is not None:
            self.check_statement(stmt.else_branch)

    def check_function_definition(self, fn: FunctionDefinition) -> None:
        """Type-check a function definition in an isolated local TypeEnv."""
        expected_return: Optional[TypeKind] = None
        if fn.return_annotation is not None:
            if fn.return_annotation == "Bool":
                expected_return = BOOL
            elif fn.return_annotation == "XoX":
                expected_return = XOX
            else:
                raise TypeError(
                    f"Unsupported return type annotation {fn.return_annotation!r}",
                    span=fn.return_annotation_span or fn.span,
                    violated_rule="§19",
                )

        # Seed isolated local environment with parameters
        local_env = TypeEnv(dict(self.env.bindings))
        for param in fn.parameters:
            if param.type_name == "Bool":
                param_type = BOOL
            elif param.type_name == "XoX":
                param_type = XOX
            else:
                raise TypeError(
                    f"Unsupported parameter type {param.type_name!r}",
                    span=param.type_span or param.span,
                    violated_rule="§19",
                )
            local_env.bind(param.name, param_type)

        # Analyze function body in local environment
        fn_analyzer = SemanticAnalyzer(
            env=local_env,
            current_return_annotation=expected_return,
            result=self.result,
        )
        fn_analyzer.check_statement(fn.body)

        # Phase 4: Definite-return reachability analysis
        check_function_definite_returns(fn)

    def check_return_statement(self, stmt: ReturnStatement) -> None:
        """Type-check a return statement against the current function return context."""
        if self.current_return_annotation is not None:
            ret_type = self.check_expression(stmt.value, expected=self.current_return_annotation)
            if ret_type != self.current_return_annotation:
                raise TypeError(
                    f"Cannot return {ret_type} expression from function with return annotation -> {self.current_return_annotation}",
                    span=stmt.value.span or stmt.span,
                    violated_rule="§19",
                )
        else:
            # Unannotated function: no expected type; unresolved literals default to Bool
            ret_type = self.check_expression(stmt.value, expected=None)
            if ret_type == XOX:
                raise TypeError(
                    "Returning a XoX expression from an unannotated function is forbidden; explicit '-> XoX' return annotation is required",
                    span=stmt.value.span or stmt.span,
                    violated_rule="§16, §19",
                )

    def check_assignment_statement(self, stmt: AssignmentStatement) -> None:
        """Type-check an initialized variable binding or reassignment."""
        if stmt.annotation is not None:
            if stmt.annotation == "Bool":
                annotated_type = BOOL
            elif stmt.annotation == "XoX":
                annotated_type = XOX
            else:
                raise TypeError(
                    f"Unsupported type annotation {stmt.annotation!r}",
                    span=stmt.annotation_span or stmt.span,
                    violated_rule="§19",
                )


            # Check if variable is already bound in environment
            existing_type = self.env.lookup(stmt.target)
            if existing_type is not None and existing_type != annotated_type:
                raise TypeError(
                    f"Conflicting type annotation '{stmt.annotation}' for existing variable '{stmt.target}' of type {existing_type}",
                    span=stmt.annotation_span or stmt.span,
                    violated_rule="§19",
                )

            # Evaluate initializer under expected annotated_type
            init_type = self.check_expression(stmt.value, expected=annotated_type)
            if init_type != annotated_type:
                raise TypeError(
                    f"Cannot assign {init_type} expression to variable '{stmt.target}' of type {annotated_type}",
                    span=stmt.value.span or stmt.span,
                    violated_rule="§19",
                )

            if existing_type is None:
                self.env.bind(stmt.target, annotated_type)
        else:
            existing_type = self.env.lookup(stmt.target)
            if existing_type is not None:
                # Reassignment: evaluate initializer under established variable type
                init_type = self.check_expression(stmt.value, expected=existing_type)
                if init_type != existing_type:
                    raise TypeError(
                        f"Cannot reassign variable '{stmt.target}' of type {existing_type} with incompatible {init_type} expression",
                        span=stmt.value.span or stmt.span,
                        violated_rule="§19",
                    )
            else:
                # Inferred binding: unconstrained initialization fixes permanent static type
                init_type = self.check_expression(stmt.value, expected=None)
                self.env.bind(stmt.target, init_type)

    def check_expression(
        self,
        expr: Expression,
        expected: Optional[TypeKind] = None,
    ) -> TypeKind:
        """Statically check an expression and resolve uncommitted literals under expected-type context."""
        resolved_type: TypeKind

        if isinstance(expr, LiteralExpr):
            if expr.kind == TokenKind.UNKNOWN:
                resolved_type = XOX
            elif expr.kind in (TokenKind.TRUE, TokenKind.FALSE):
                if expected == XOX:
                    resolved_type = XOX
                elif expected == BOOL:
                    resolved_type = BOOL
                else:
                    # Unconstrained literal defaults to Bool (§18)
                    resolved_type = BOOL
            else:
                raise TypeError(f"Unknown literal token kind: {expr.kind}", span=expr.span, violated_rule="§3")

        elif isinstance(expr, IdentifierExpr):
            t = self.env.lookup(expr.name)
            if t is None:
                raise TypeError(f"Unbound identifier {expr.name!r}", span=expr.span, violated_rule="§19")
            resolved_type = t

        elif isinstance(expr, GroupExpr):
            resolved_type = self.check_expression(expr.expr, expected=expected)

        elif isinstance(expr, UnaryExpr):
            if expr.op == TokenKind.NOT:
                # Expected context propagates through NOT to resolve uncommitted literals
                operand_type = self.check_expression(expr.operand, expected=expected)
                if operand_type == BOOL:
                    resolved_type = BOOL
                elif operand_type == XOX:
                    resolved_type = XOX
                else:
                    raise TypeError(f"Operator NOT requires Bool or XoX operand, got {operand_type}", span=expr.span, violated_rule="§7")
            else:
                raise TypeError(f"Unsupported unary operator: {expr.op}", span=expr.span, violated_rule="§7")

        elif isinstance(expr, BinaryExpr):
            if expr.op in (TokenKind.AND, TokenKind.OR):
                # 1. Determine expected domain for operands
                op_domain = expected
                if op_domain is None:
                    # Look for domain anchor among operands to preserve traversal-order invariance (§18)
                    left_anchor = _inspect_domain_anchor(expr.left, self.env)
                    right_anchor = _inspect_domain_anchor(expr.right, self.env)
                    if left_anchor == XOX or right_anchor == XOX:
                        op_domain = XOX
                    elif left_anchor == BOOL or right_anchor == BOOL:
                        op_domain = BOOL
                    else:
                        op_domain = None

                left_type = self.check_expression(expr.left, expected=op_domain)
                right_type = self.check_expression(expr.right, expected=op_domain)

                if left_type == BOOL and right_type == BOOL:
                    resolved_type = BOOL
                elif left_type == XOX and right_type == XOX:
                    resolved_type = XOX
                else:
                    raise TypeError(
                        f"Mixed logical operation '{expr.op.value}' between {left_type} and {right_type} is forbidden without explicit conversion (XoX.from_bool)",
                        span=expr.span,
                        violated_rule="§7, §19",
                    )

            elif expr.op in (TokenKind.EQ_EQ, TokenKind.EXCL_EQ):
                # Inward contextual resolution of operands without leaking outward expected type
                left_anchor = _inspect_domain_anchor(expr.left, self.env)
                right_anchor = _inspect_domain_anchor(expr.right, self.env)
                if left_anchor == XOX or right_anchor == XOX:
                    op_domain = XOX
                elif left_anchor == BOOL or right_anchor == BOOL:
                    op_domain = BOOL
                else:
                    op_domain = None

                left_type = self.check_expression(expr.left, expected=op_domain)
                right_type = self.check_expression(expr.right, expected=op_domain)

                if left_type != right_type:
                    raise TypeError(
                        f"Mixed equality comparison '{expr.op.value}' between {left_type} and {right_type} is forbidden without explicit conversion (XoX.from_bool)",
                        span=expr.span,
                        violated_rule="§8, §19",
                    )

                # Strict Result-Type Barrier: equality always returns Bool (§8, §18, §19)
                resolved_type = BOOL


            else:
                raise TypeError(f"Unsupported binary operator: {expr.op}", span=expr.span, violated_rule="§7, §8")

        else:
            raise TypeError(f"Cannot type-check unsupported AST node: {type(expr).__name__}", span=expr.span)

        # Record authoritative resolved type in semantic result side table
        self.result.node_types[id(expr)] = resolved_type
        return resolved_type



def check_expression(
    expr: Expression,
    env: Optional[Union[Dict[str, TypeKind], TypeEnv]] = None,
    expected: Optional[TypeKind] = None,
) -> TypeKind:
    """Helper function to type-check an expression."""
    analyzer = SemanticAnalyzer(env=env)
    return analyzer.check_expression(expr, expected=expected)


def analyze(ast: ASTNode, env: Optional[Union[Dict[str, TypeKind], TypeEnv]] = None) -> SemanticAnalyzer:
    """Perform semantic, monomorphic type, and definite-return analysis on an AST."""
    analyzer = SemanticAnalyzer(env=env)
    if isinstance(ast, Program):
        analyzer.check_program(ast)
    elif isinstance(ast, Statement):
        analyzer.check_statement(ast)
    elif isinstance(ast, Expression):
        analyzer.check_expression(ast)
    return analyzer
