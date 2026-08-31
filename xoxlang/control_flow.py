"""Control-flow reachability and definite-return analysis for X-o-X."""
from typing import Union
from xoxlang.ast import (
    ASTNode,
    Block,
    ConditionalStatement,
    FunctionDefinition,
    IgnoreStatement,
    Program,
    ReturnStatement,
    Statement,
)
from xoxlang.diagnostics import MissingReturnError


def check_statement_definitely_returns(stmt: Statement) -> bool:
    """Check if a statement definitely returns on every execution path."""
    if isinstance(stmt, ReturnStatement):
        return True

    if isinstance(stmt, Block):
        return check_block_definitely_returns(stmt)

    if isinstance(stmt, ConditionalStatement):
        # XoX conditional (contains xen branch)
        if stmt.xen_branch is not None:

            # All three branches must definitely return
            if not check_block_definitely_returns(stmt.true_branch):
                return False

            if isinstance(stmt.xen_branch, IgnoreStatement):
                # xen: ignore explicitly falls through and does not return
                return False
            elif isinstance(stmt.xen_branch, Block):
                if not check_block_definitely_returns(stmt.xen_branch):
                    return False
            else:
                return False

            if stmt.else_branch is None or not check_block_definitely_returns(stmt.else_branch):
                return False

            return True

        # Bool conditional
        if stmt.else_branch is None:
            # Without else branch, False path falls through
            return False

        return check_block_definitely_returns(stmt.true_branch) and check_block_definitely_returns(stmt.else_branch)

    # PassStatement, IgnoreStatement, AssignmentStatement, ExprStatement are non-terminal
    return False


def check_block_definitely_returns(block: Block) -> bool:
    """Check if every reachable path entering the block encounters a terminal ReturnStatement."""
    for stmt in block.statements:
        if check_statement_definitely_returns(stmt):
            return True
    return False


def check_function_definite_returns(fn: FunctionDefinition) -> None:
    """Verify return path completeness on a function with an explicit return annotation."""
    if fn.return_annotation is not None:
        if not check_block_definitely_returns(fn.body):
            raise MissingReturnError(
                f"Function '{fn.name}' can finish without returning a value (does not return a value on every control-flow path).",
                span=fn.return_annotation_span or fn.span,
                violated_rule="§11, §19",
                note=f"The function is declared to return {fn.return_annotation}, so every possible execution path must return a {fn.return_annotation} value.",
                help=f"Make sure every possible path returns a {fn.return_annotation} value.",
                annotations={"function_name": fn.name, "return_type": fn.return_annotation},
            )


def check_definite_returns(ast: ASTNode) -> None:
    """Check definite returns across an entire AST program or function."""
    if isinstance(ast, Program):
        for stmt in ast.statements:
            if isinstance(stmt, FunctionDefinition):
                check_function_definite_returns(stmt)
    elif isinstance(ast, FunctionDefinition):
        check_function_definite_returns(ast)
