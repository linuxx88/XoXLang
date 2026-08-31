"""Semantic analysis, static truth-type checking, contextual literal resolution, and semantic artifact production."""
from dataclasses import dataclass, field
from typing import Dict, Optional, Union
from xoxlang.tokens import TokenKind
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
from xoxlang.types import BOOL, XOX, ConditionalKind, TypeKind

from xoxlang.diagnostics import ExhaustivenessError, TypeDiagnosticError
from xoxlang.control_flow import check_function_definite_returns

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

    if isinstance(expr, InlineConditionalExpr):
        true_anchor = _inspect_domain_anchor(expr.true_expr, env)
        else_anchor = _inspect_domain_anchor(expr.else_expr, env)
        xen_anchor = _inspect_domain_anchor(expr.xen_expr, env) if expr.xen_expr is not None else None
        if true_anchor == XOX or else_anchor == XOX or xen_anchor == XOX:
            return XOX
        if true_anchor == BOOL or else_anchor == BOOL or xen_anchor == BOOL:
            return BOOL
        return None

    if isinstance(expr, CollapseXoXToBoolWithDefault):
        # Collapse primitive always yields Bool
        return BOOL

    if isinstance(expr, PromoteBoolToXoX):
        # Promotion primitive always yields XoX
        return XOX

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
            raise TypeError(
                "Unsupported statement syntax.",
                span=stmt.span,
                help="Supported statements are variable assignments, expressions, conditionals, functions, pass, and ignore.",
            )

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
                    "This XoX condition does not handle Unknown or False (missing both 'xen' and 'else' clauses).",
                    span=stmt.span,
                    violated_rule="§10",
                    note="XoX conditions can be True, False, or Unknown.",
                    help="Add an 'else' branch to handle False.",
                    alternatives=[
                        "Add a 'xen' branch to handle Unknown.",
                        "Use 'xen: ignore' if intentionally doing nothing for Unknown is correct.",
                    ],
                )
            if stmt.xen_branch is None:
                raise ExhaustivenessError(
                    "This XoX condition does not handle Unknown (missing 'xen' clause).",
                    span=stmt.span,
                    violated_rule="§10",
                    note="A 'xen' branch handles the case where an XoX condition evaluates to Unknown.",
                    alternatives=[
                        "Add a 'xen' branch to handle Unknown.",
                        "Use 'xen: ignore' if intentionally doing nothing for Unknown is correct.",
                    ],
                )
            if stmt.else_branch is None:
                raise ExhaustivenessError(
                    "This XoX condition does not handle False (missing 'else' clause).",
                    span=stmt.span,
                    violated_rule="§10",
                    note="An 'else' branch handles the False case.",
                    help="Add an 'else' branch to handle False.",
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
                lit_name = getattr(expr.kind, "value", str(expr.kind))
                raise TypeError(
                    f"Unsupported literal value '{lit_name}'.",
                    span=expr.span,
                    violated_rule="§3",
                    help="Supported truth literals are 'True', 'False', and 'Unknown'.",
                )

        elif isinstance(expr, IdentifierExpr):
            t = self.env.lookup(expr.name)
            if t is None:
                raise TypeError(
                    f"Variable '{expr.name}' is not defined.",
                    span=expr.span,
                    violated_rule="§19",
                    help=f"Define and initialize '{expr.name}' before using it.",
                )
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
                    raise TypeError(
                        f"Operator 'NOT' cannot be applied to type '{operand_type}'.",
                        span=expr.span,
                        violated_rule="§7",
                        note="Logical NOT operates exclusively on truth-typed expressions.",
                        help="Ensure the operand evaluates to a Bool or XoX value.",
                    )
            else:
                op_name = getattr(expr.op, "value", str(expr.op))
                raise TypeError(
                    f"Unsupported unary operator '{op_name}'.",
                    span=expr.span,
                    violated_rule="§7",
                    help="Only 'NOT' is supported for logical unary negation.",
                )

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
                    raise TypeDiagnosticError(
                        f"Cannot combine {left_type} and {right_type} with logical operator '{expr.op.value}'.",
                        span=expr.span,
                        violated_rule="§7, §19",
                        note="Bool has only True and False, while XoX can also be Unknown. XoXLang does not combine those domains implicitly.",
                        alternatives=[
                            "If three-state logic is intended, convert the Bool operand with xox(...).",
                            "If two-state Bool logic is intended, keep both operands in the Bool domain instead.",
                        ],
                        annotations={"left_type": str(left_type), "right_type": str(right_type)},
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
                    raise TypeDiagnosticError(
                        f"Cannot compare {left_type} and {right_type} with equality operator '{expr.op.value}'.",
                        span=expr.span,
                        violated_rule="§8, §19",
                        note="Bool and XoX are different semantic domains, so equality requires both operands to use the same domain.",
                        alternatives=[
                            "If you want to compare in three-state logic, convert the Bool operand with xox(...).",
                            "If the comparison should remain two-state, keep both values as Bool.",
                        ],
                        annotations={"left_type": str(left_type), "right_type": str(right_type)},
                    )

                # Strict Result-Type Barrier: equality always returns Bool (§8, §18, §19)
                resolved_type = BOOL

            else:
                op_name = getattr(expr.op, "value", str(expr.op))
                raise TypeError(
                    f"Unsupported binary operator '{op_name}'.",
                    span=expr.span,
                    violated_rule="§7, §8",
                    help="Supported binary operators are 'AND', 'OR', '==', and '!='.",
                )

        elif isinstance(expr, InlineConditionalExpr):
            cond_type = self.check_expression(expr.condition, expected=None)
            if cond_type == BOOL:
                if expr.xen_expr is not None:
                    raise TypeError(
                        "Bool inline conditional expression cannot have a 'xen' branch",
                        span=expr.xen_expr.span,
                        violated_rule="§5, §18",
                    )
                branch_domain = expected
                if branch_domain is None:
                    true_anchor = _inspect_domain_anchor(expr.true_expr, self.env)
                    else_anchor = _inspect_domain_anchor(expr.else_expr, self.env)
                    if true_anchor == XOX or else_anchor == XOX:
                        branch_domain = XOX
                    elif true_anchor == BOOL or else_anchor == BOOL:
                        branch_domain = BOOL
                    else:
                        branch_domain = None

                true_type = self.check_expression(expr.true_expr, expected=branch_domain)
                else_type = self.check_expression(expr.else_expr, expected=branch_domain)

                if true_type != else_type:
                    raise TypeError(
                        f"Inline conditional expression branches have incompatible types: true branch is '{true_type}', else branch is '{else_type}'",
                        span=expr.span,
                        violated_rule="§18, §19",
                    )
                resolved_type = true_type
            elif cond_type == XOX:
                if expr.xen_expr is None:
                    raise ExhaustivenessError(
                        "This inline XoX conditional has no result for Unknown (missing 'xen' branch).",
                        span=expr.span,
                        violated_rule="§5, §10",
                        note="The 'xen' branch supplies the result when the condition is Unknown.",
                        help="Add a 'xen' result for the Unknown case.",
                    )
                branch_domain = expected
                if branch_domain is None:
                    true_anchor = _inspect_domain_anchor(expr.true_expr, self.env)
                    else_anchor = _inspect_domain_anchor(expr.else_expr, self.env)
                    xen_anchor = _inspect_domain_anchor(expr.xen_expr, self.env)
                    if true_anchor == XOX or else_anchor == XOX or xen_anchor == XOX:
                        branch_domain = XOX
                    elif true_anchor == BOOL or else_anchor == BOOL or xen_anchor == BOOL:
                        branch_domain = BOOL
                    else:
                        branch_domain = None

                true_type = self.check_expression(expr.true_expr, expected=branch_domain)
                xen_type = self.check_expression(expr.xen_expr, expected=branch_domain)
                else_type = self.check_expression(expr.else_expr, expected=branch_domain)

                if not (true_type == xen_type == else_type):
                    raise TypeError(
                        f"XoX inline conditional expression branches have incompatible types: true branch is '{true_type}', xen branch is '{xen_type}', else branch is '{else_type}'",
                        span=expr.span,
                        violated_rule="§18, §19",
                    )
                resolved_type = true_type
            else:
                raise TypeError(
                    f"Inline conditional expression condition must be Bool or XoX, got {cond_type}",
                    span=expr.condition.span,
                    violated_rule="§5",
                )

        elif isinstance(expr, CollapseXoXToBoolWithDefault):
            source_type = self.check_expression(expr.source, expected=XOX)
            if source_type != XOX:
                raise TypeDiagnosticError(
                    f"'unwrap_or(...)' works on an XoX value, but this value is {source_type}.",
                    span=expr.source.span or expr.span,
                    violated_rule="§3, §19",
                    note="The fallback is only used when an XoX value is Unknown.",
                    alternatives=[
                        "If you intended three-state logic here, convert the Bool with xox(...)."
                    ],
                    annotations={"source_type": str(source_type)},
                )
            fallback_type = self.check_expression(expr.fallback, expected=BOOL)
            if fallback_type != BOOL:
                raise TypeDiagnosticError(
                    f"'unwrap_or(...)' needs a Bool fallback, but this fallback is {fallback_type}.",
                    span=expr.fallback.span or expr.span,
                    violated_rule="§3, §19",
                    note="The fallback is evaluated only when the source is Unknown and must produce the final True or False result.",
                    help="Use an expression whose type is Bool as the fallback.",
                    annotations={"fallback_type": str(fallback_type)},
                )
            resolved_type = BOOL

        elif isinstance(expr, PromoteBoolToXoX):
            operand_type = self.check_expression(expr.expr, expected=BOOL)
            if operand_type != BOOL:
                raise TypeDiagnosticError(
                    f"'xox(...)' promotes Bool to XoX, but the supplied expression is already {operand_type}.",
                    span=expr.span,
                    violated_rule="§19",
                    note="Explicit promotion 'xox(...)' requires a Bool operand.",
                    help="Remove 'xox(...)' if the value is already XoX." if operand_type == XOX else None,
                    annotations={"operand_type": str(operand_type)},
                )
            resolved_type = XOX

        else:
            raise TypeError(
                "Unsupported expression syntax.",
                span=expr.span,
                help="Use supported literals, identifiers, unary NOT, logical binary expressions, inline conditionals, xox promotion, or unwrap_or.",
            )

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
