"""Unit tests for XoX (X-o-X) SemanticResult artifact, expression type side tables, and conditional classifications."""
import unittest
from trool.lexer import tokenize
from trool.parser import parse
from trool.types import BOOL, XOX, ConditionalKind
from trool.ast import (
    AssignmentStatement,
    BinaryExpr,
    ConditionalStatement,
    ExprStatement,
    FunctionDefinition,
    LiteralExpr,
    ReturnStatement,
    UnaryExpr,
)
from trool.semantic import SemanticAnalyzer, SemanticResult, analyze, TypeError


class TestXoXSemanticResult(unittest.TestCase):
    def test_unconstrained_literals_recorded_as_bool(self):
        source = "True\n"
        ast = parse(tokenize(source))
        analyzer = analyze(ast)
        stmt = ast.statements[0]
        self.assertIsInstance(stmt, ExprStatement)
        self.assertEqual(analyzer.result.type_of(stmt.expr), BOOL)

    def test_xox_contextual_literals_recorded_as_xox(self):
        source = "x: XoX = True\n"
        ast = parse(tokenize(source))
        analyzer = analyze(ast)
        stmt = ast.statements[0]
        self.assertIsInstance(stmt, AssignmentStatement)
        self.assertEqual(analyzer.result.type_of(stmt.value), XOX)

    def test_unknown_recorded_as_xox(self):
        source = "Unknown\n"
        ast = parse(tokenize(source))
        analyzer = analyze(ast)
        stmt = ast.statements[0]
        self.assertEqual(analyzer.result.type_of(stmt.expr), XOX)

    def test_logical_operations_persisted_types(self):
        # Bool AND
        ast_bool = parse(tokenize("True AND False\n"))
        analyzer_bool = analyze(ast_bool)
        expr_bool = ast_bool.statements[0].expr
        self.assertEqual(analyzer_bool.result.type_of(expr_bool), BOOL)

        # XoX AND
        ast_xox = parse(tokenize("t: XoX = Unknown\nt AND True\n"))
        analyzer_xox = analyze(ast_xox)
        expr_xox = ast_xox.statements[1].expr
        self.assertEqual(analyzer_xox.result.type_of(expr_xox), XOX)

    def test_not_operation_persisted_types(self):
        # NOT Bool
        ast_not_bool = parse(tokenize("NOT True\n"))
        analyzer_not_bool = analyze(ast_not_bool)
        self.assertEqual(analyzer_not_bool.result.type_of(ast_not_bool.statements[0].expr), BOOL)

        # NOT XoX
        ast_not_xox = parse(tokenize("t: XoX = Unknown\nNOT t\n"))
        analyzer_not_xox = analyze(ast_not_xox)
        self.assertEqual(analyzer_not_xox.result.type_of(ast_not_xox.statements[1].expr), XOX)

    def test_equality_result_type_and_operand_context(self):
        # True == Unknown -> result is Bool, left operand is contextualized as XoX
        ast = parse(tokenize("True == Unknown\n"))
        analyzer = analyze(ast)
        eq_expr = ast.statements[0].expr
        self.assertIsInstance(eq_expr, BinaryExpr)
        self.assertEqual(analyzer.result.type_of(eq_expr), BOOL)
        self.assertEqual(analyzer.result.type_of(eq_expr.left), XOX)
        self.assertEqual(analyzer.result.type_of(eq_expr.right), XOX)

    def test_function_return_literal_and_equality_persisted_types(self):
        # return True inside -> XoX
        source_fn = (
            "fn f(t: XoX) -> XoX:\n"
            "    return True\n"
        )
        ast_fn = parse(tokenize(source_fn))
        analyzer_fn = analyze(ast_fn)
        ret_stmt = ast_fn.statements[0].body.statements[0]
        self.assertIsInstance(ret_stmt, ReturnStatement)
        self.assertEqual(analyzer_fn.result.type_of(ret_stmt.value), XOX)

        # return equality inside -> Bool
        source_eq_fn = (
            "fn g(t: XoX) -> Bool:\n"
            "    return t == Unknown\n"
        )
        ast_eq_fn = parse(tokenize(source_eq_fn))
        analyzer_eq_fn = analyze(ast_eq_fn)
        ret_eq_stmt = ast_eq_fn.statements[0].body.statements[0]
        self.assertEqual(analyzer_eq_fn.result.type_of(ret_eq_stmt.value), BOOL)

    def test_conditional_classification_persisted(self):
        # Bool conditional
        ast_bool = parse(tokenize("if True:\n    pass\nelse:\n    pass\n"))
        analyzer_bool = analyze(ast_bool)
        cond_bool = ast_bool.statements[0]
        self.assertIsInstance(cond_bool, ConditionalStatement)
        self.assertEqual(analyzer_bool.result.conditional_kind(cond_bool), ConditionalKind.BOOL)

        # XoX conditional
        ast_xox = parse(tokenize("if Unknown:\n    pass\nxen:\n    ignore\nelse:\n    pass\n"))
        analyzer_xox = analyze(ast_xox)
        cond_xox = ast_xox.statements[0]
        self.assertIsInstance(cond_xox, ConditionalStatement)
        self.assertEqual(analyzer_xox.result.conditional_kind(cond_xox), ConditionalKind.XOX)

    def test_accessing_unanalyzed_node_fails_explicitly(self):
        result = SemanticResult()
        dummy_lit = LiteralExpr()
        dummy_cond = ConditionalStatement()

        with self.assertRaises(KeyError):
            result.type_of(dummy_lit)

        with self.assertRaises(KeyError):
            result.conditional_kind(dummy_cond)

    def test_independent_runs_do_not_leak_state(self):
        ast1 = parse(tokenize("x: XoX = True\n"))
        analyzer1 = analyze(ast1)

        ast2 = parse(tokenize("x = True\n"))
        analyzer2 = analyze(ast2)

        self.assertEqual(analyzer1.result.type_of(ast1.statements[0].value), XOX)
        self.assertEqual(analyzer2.result.type_of(ast2.statements[0].value), BOOL)
        # Verify node from ast1 is not in analyzer2.result
        self.assertFalse(analyzer2.result.has_type(ast1.statements[0].value))



if __name__ == "__main__":
    unittest.main()
