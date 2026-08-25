"""Python lowering / code generation for Trool prototype."""
from dataclasses import dataclass
from typing import List, Optional, Union
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
    PassStatement,
    Program,
    ReturnStatement,
    Statement,
    UnaryExpr,
)
from trool.tokens import TokenKind
from trool.types import BOOL, XOX, ConditionalKind
from trool.semantic import SemanticResult



def map_identifier(name: str) -> str:
    """Injective, deterministic mapping from Trool source identifier to safe Python target identifier."""
    return f"_u_{name.encode('utf-8').hex()}"


@dataclass(frozen=True)
class LoweredExpr:
    """Represents a lowered Python expression along with any prerequisite prelude statements."""
    prelude: List[str]
    expr: str


class ExpressionLowerer:
    """Lowers validated Trool expressions to Python using SemanticResult as the sole semantic authority."""

    def __init__(self, semantic_result: SemanticResult, temp_counter: int = 0):
        self.semantic_result: SemanticResult = semantic_result
        self._temp_counter: int = temp_counter

    def new_temp(self, prefix: str = "_tmp_") -> str:
        """Allocate a deterministic, hygienic temporary name disjoint from user identifiers."""
        name = f"{prefix}{self._temp_counter}"
        self._temp_counter += 1
        return name

    def lower_expression(self, expr: Expression) -> LoweredExpr:
        """Lower an Expression AST node into a LoweredExpr."""
        node_type = self.semantic_result.type_of(expr)

        if isinstance(expr, LiteralExpr):
            if expr.kind == TokenKind.UNKNOWN:
                return LoweredExpr([], "XoX.UNKNOWN")
            if expr.kind == TokenKind.TRUE:
                return LoweredExpr([], "True" if node_type == BOOL else "XoX.TRUE")
            if expr.kind == TokenKind.FALSE:
                return LoweredExpr([], "False" if node_type == BOOL else "XoX.FALSE")
            raise ValueError(f"Unknown literal kind {expr.kind}")

        if isinstance(expr, IdentifierExpr):
            return LoweredExpr([], map_identifier(expr.name))

        if isinstance(expr, GroupExpr):
            inner = self.lower_expression(expr.expr)
            return LoweredExpr(inner.prelude, f"({inner.expr})")

        if isinstance(expr, UnaryExpr):
            if expr.op == TokenKind.NOT:
                operand = self.lower_expression(expr.operand)
                if node_type == BOOL:
                    return LoweredExpr(operand.prelude, f"(not {operand.expr})")
                if node_type == XOX:
                    return LoweredExpr(operand.prelude, f"xox_not({operand.expr})")
                raise ValueError(f"Unsupported NOT node type {node_type}")
            raise ValueError(f"Unsupported unary operator {expr.op}")

        if isinstance(expr, BinaryExpr):
            if expr.op in (TokenKind.EQ_EQ, TokenKind.EXCL_EQ):
                left = self.lower_expression(expr.left)
                right = self.lower_expression(expr.right)
                prelude = list(left.prelude) + list(right.prelude)

                # Equality operand type from semantic result
                operand_type = self.semantic_result.type_of(expr.left)
                if operand_type == BOOL:
                    op_str = "==" if expr.op == TokenKind.EQ_EQ else "!="
                    return LoweredExpr(prelude, f"({left.expr} {op_str} {right.expr})")
                if operand_type == XOX:
                    op_str = "is" if expr.op == TokenKind.EQ_EQ else "is not"
                    return LoweredExpr(prelude, f"({left.expr} {op_str} {right.expr})")
                raise ValueError(f"Unsupported equality operand type {operand_type}")

            if expr.op == TokenKind.AND:
                if node_type == BOOL:
                    left = self.lower_expression(expr.left)
                    right = self.lower_expression(expr.right)
                    if not right.prelude:
                        return LoweredExpr(left.prelude, f"({left.expr} and {right.expr})")
                    res_var = self.new_temp()
                    prelude = list(left.prelude)
                    prelude.append(f"{res_var} = {left.expr}")
                    prelude.append(f"if {res_var}:")
                    for s in right.prelude:
                        prelude.append(f"    {s}")
                    prelude.append(f"    {res_var} = {right.expr}")
                    return LoweredExpr(prelude, res_var)

                if node_type == XOX:
                    # XoX AND with identity-based short-circuiting
                    left = self.lower_expression(expr.left)
                    right = self.lower_expression(expr.right)
                    left_var = self.new_temp()
                    res_var = self.new_temp()
                    prelude = list(left.prelude)
                    prelude.append(f"{left_var} = {left.expr}")
                    prelude.append(f"if {left_var} is XoX.FALSE:")
                    prelude.append(f"    {res_var} = XoX.FALSE")
                    prelude.append("else:")
                    for s in right.prelude:
                        prelude.append(f"    {s}")
                    prelude.append(f"    {res_var} = xox_and({left_var}, {right.expr})")
                    return LoweredExpr(prelude, res_var)

            if expr.op == TokenKind.OR:
                if node_type == BOOL:
                    left = self.lower_expression(expr.left)
                    right = self.lower_expression(expr.right)
                    if not right.prelude:
                        return LoweredExpr(left.prelude, f"({left.expr} or {right.expr})")
                    res_var = self.new_temp()
                    prelude = list(left.prelude)
                    prelude.append(f"{res_var} = {left.expr}")
                    prelude.append(f"if not {res_var}:")
                    for s in right.prelude:
                        prelude.append(f"    {s}")
                    prelude.append(f"    {res_var} = {right.expr}")
                    return LoweredExpr(prelude, res_var)

                if node_type == XOX:
                    # XoX OR with identity-based short-circuiting
                    left = self.lower_expression(expr.left)
                    right = self.lower_expression(expr.right)
                    left_var = self.new_temp()
                    res_var = self.new_temp()
                    prelude = list(left.prelude)
                    prelude.append(f"{left_var} = {left.expr}")
                    prelude.append(f"if {left_var} is XoX.TRUE:")
                    prelude.append(f"    {res_var} = XoX.TRUE")
                    prelude.append("else:")
                    for s in right.prelude:
                        prelude.append(f"    {s}")
                    prelude.append(f"    {res_var} = xox_or({left_var}, {right.expr})")
                    return LoweredExpr(prelude, res_var)


            raise ValueError(f"Unsupported binary operator {expr.op}")

        raise ValueError(f"Unsupported expression node type: {type(expr).__name__}")


class StatementLowerer:
    """Lowers validated statements, conditionals, and functions to Python code."""

    def __init__(self, semantic_result: SemanticResult, expr_lowerer: Optional[ExpressionLowerer] = None):
        self.semantic_result: SemanticResult = semantic_result
        self.expr_lowerer: ExpressionLowerer = (
            expr_lowerer if expr_lowerer is not None else ExpressionLowerer(semantic_result)
        )

    def lower_statement(self, stmt: Statement) -> List[str]:
        """Lower any validated statement node into Python statement lines."""
        if isinstance(stmt, FunctionDefinition):
            return self.lower_function_definition(stmt)
        if isinstance(stmt, ConditionalStatement):
            return self.lower_conditional_statement(stmt)
        if isinstance(stmt, Block):
            return self.lower_block(stmt)
        return self.lower_simple_statement(stmt)

    def lower_function_definition(self, fn: FunctionDefinition) -> List[str]:
        """Lower a FunctionDefinition node to a Python def block."""
        fn_name = map_identifier(fn.name)
        params = [map_identifier(p.name) for p in fn.parameters]
        header = f"def {fn_name}({', '.join(params)}):"
        body_lines = self.lower_block(fn.body)
        lines = [header]
        for l in body_lines:
            lines.append(f"    {l}")
        return lines

    def lower_simple_statement(self, stmt: Statement) -> List[str]:
        """Lower a non-conditional simple statement into Python statement strings."""
        if isinstance(stmt, AssignmentStatement):
            target = map_identifier(stmt.target)
            init = self.expr_lowerer.lower_expression(stmt.value)
            return list(init.prelude) + [f"{target} = {init.expr}"]

        if isinstance(stmt, ExprStatement):
            val = self.expr_lowerer.lower_expression(stmt.expr)
            return list(val.prelude) + [val.expr]

        if isinstance(stmt, PassStatement):
            return ["pass"]

        if isinstance(stmt, IgnoreStatement):
            return ["pass"]

        if isinstance(stmt, ReturnStatement):
            val = self.expr_lowerer.lower_expression(stmt.value)
            return list(val.prelude) + [f"return {val.expr}"]

        raise ValueError(f"Unsupported statement type for simple statement lowering: {type(stmt).__name__}")

    def lower_block(self, block: Union[Block, Statement]) -> List[str]:
        """Lower a branch/function block of statements into Python lines."""
        if isinstance(block, Block):
            lines: List[str] = []
            for s in block.statements:
                lines.extend(self.lower_statement(s))
            return lines if lines else ["pass"]
        return self.lower_statement(block)

    def lower_conditional_statement(self, stmt: ConditionalStatement) -> List[str]:
        """Lower a Bool or XoX ConditionalStatement using SemanticResult.conditional_kind()."""
        kind = self.semantic_result.conditional_kind(stmt)

        if kind == ConditionalKind.BOOL:
            cond = self.expr_lowerer.lower_expression(stmt.condition)
            lines = list(cond.prelude)
            true_body = self.lower_block(stmt.true_branch)
            lines.append(f"if {cond.expr}:")
            for l in true_body:
                lines.append(f"    {l}")
            if stmt.else_branch is not None:
                else_body = self.lower_block(stmt.else_branch)
                lines.append("else:")
                for l in else_body:
                    lines.append(f"    {l}")
            return lines

        if kind == ConditionalKind.XOX:
            cond = self.expr_lowerer.lower_expression(stmt.condition)

            lines = list(cond.prelude)
            cond_temp = self.expr_lowerer.new_temp()
            lines.append(f"{cond_temp} = {cond.expr}")

            true_body = self.lower_block(stmt.true_branch)
            lines.append(f"if {cond_temp} is XoX.TRUE:")
            for l in true_body:
                lines.append(f"    {l}")

            xen_body = self.lower_block(stmt.xen_branch) if stmt.xen_branch is not None else ["pass"]
            lines.append(f"elif {cond_temp} is XoX.UNKNOWN:")
            for l in xen_body:
                lines.append(f"    {l}")

            else_body = self.lower_block(stmt.else_branch) if stmt.else_branch is not None else ["pass"]
            lines.append(f"elif {cond_temp} is XoX.FALSE:")
            for l in else_body:
                lines.append(f"    {l}")

            lines.append("else:")
            lines.append(f"    raise TypeError(f'Invalid XoX runtime state: {{{cond_temp}!r}}')")
            return lines

        raise ValueError(f"Unsupported ConditionalKind: {kind}")


class ProgramLowerer:
    """Lowers a validated Program AST and SemanticResult to Python module source code."""

    def __init__(self, semantic_result: SemanticResult):
        self.semantic_result: SemanticResult = semantic_result
        self.stmt_lowerer: StatementLowerer = StatementLowerer(semantic_result=semantic_result)

    def lower_program(self, prog: Program) -> str:
        """Emit complete Python module source code for a Program AST."""
        if not isinstance(prog, Program):
            raise TypeError(f"Expected Program AST node, got {type(prog).__name__}")

        lines: List[str] = [
            "from trool.runtime import XoX, xox_not, xox_and, xox_or, UnknownValueError",
            "",
        ]

        for stmt in prog.statements:
            stmt_lines = self.stmt_lowerer.lower_statement(stmt)
            lines.extend(stmt_lines)

        return "\n".join(lines) + "\n"


def lower_expression(expr: Expression, semantic_result: SemanticResult) -> LoweredExpr:
    """Helper function to lower a validated Expression AST node."""
    lowerer = ExpressionLowerer(semantic_result=semantic_result)
    return lowerer.lower_expression(expr)


def lower_statement(stmt: Statement, semantic_result: SemanticResult) -> List[str]:
    """Helper function to lower a validated Statement AST node."""
    lowerer = StatementLowerer(semantic_result=semantic_result)
    return lowerer.lower_statement(stmt)


def lower_to_python(ast: ASTNode, semantic_result: SemanticResult) -> str:
    """Lower a validated Program AST to Python source code."""
    if isinstance(ast, Program):
        lowerer = ProgramLowerer(semantic_result=semantic_result)
        return lowerer.lower_program(ast)
    raise TypeError(f"lower_to_python expected a Program AST node, got {type(ast).__name__}")
