"""Adversarial and conformance tests for Bool-to-XoX promotion primitive xox(expr).

Verifies CTX-PROMOT-01 through CTX-PROMOT-04 from experiments/PROMOTION_COUNTEREXAMPLES.md.
"""
import unittest
from xoxlang import compile_source
from xoxlang.lexer import tokenize
from xoxlang.parser import parse, ParseError
from xoxlang.semantic import analyze
from xoxlang.ast import IdentifierExpr, LiteralExpr, PromoteBoolToXoX
from xoxlang.tokens import TokenKind
from xoxlang.diagnostics import TypeDiagnosticError
from xoxlang.types import BOOL, XOX
from xoxlang.lowering import lower_expression, map_identifier
from xoxlang.runtime import XoX, xox_and, xox_not, xox_or


class TestXoXPromotionAdversarial(unittest.TestCase):
    def test_ctx_promot_01_rejected_idempotence(self):
        """CTX-PROMOT-01: xox(xox(flag)) -> static TypeError (operand is XoX, expects Bool)."""
        source = (
            "flag: Bool = True\n"
            "res: XoX = xox(xox(flag))\n"
        )
        with self.assertRaises(TypeDiagnosticError) as ctx:
            compile_source(source)
        exc = ctx.exception
        self.assertIn("promotes Bool to XoX", exc.message)
        self.assertIn("already XoX", exc.message)
        self.assertEqual(exc.violated_rule, "§19")

    def test_ctx_promot_02_rejected_xox_compound(self):
        """CTX-PROMOT-02: xox(xox_a AND xox_b) -> static TypeError (operand is XoX compound)."""
        source = (
            "xox_a: XoX = True\n"
            "xox_b: XoX = Unknown\n"
            "res: XoX = xox(xox_a AND xox_b)\n"
        )
        with self.assertRaises(TypeDiagnosticError) as ctx:
            compile_source(source)
        exc = ctx.exception
        self.assertIn("promotes Bool to XoX", exc.message)
        self.assertIn("already XoX", exc.message)

    def test_ctx_promot_03_precedence_without_parentheses_rejected(self):
        """CTX-PROMOT-03: xox a == b -> ParseError / SyntaxError (mandatory parentheses)."""
        source = (
            "a: Bool = True\n"
            "b: Bool = True\n"
            "res = xox a == b\n"
        )
        with self.assertRaises(ParseError):
            compile_source(source)

    def test_ctx_promot_04_trace_and_single_evaluation(self):
        """CTX-PROMOT-04: xox(side_effect()) -> evaluated exactly once at exact sequential position."""
        source = (
            "b: Bool = True\n"
            "res: XoX = xox(b)\n"
        )
        ast = parse(tokenize(source))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[1].value, sem.result)

        expr_str = lowered.expr.replace(map_identifier('b'), 'eval_operand()')
        code_lines = [
            "trace = []",
            "def eval_operand():",
            "    trace.append('eval_operand')",
            "    return True",
            *lowered.prelude,
            f"res_out = {expr_str}",
        ]

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
        }
        exec("\n".join(code_lines), scope)

        self.assertEqual(scope["trace"], ["eval_operand"])
        self.assertEqual(scope["trace"].count("eval_operand"), 1)
        self.assertIs(scope["res_out"], XoX.TRUE)

    def test_promotion_true_and_false_values(self):
        """xox(True) -> XoX.TRUE and xox(False) -> XoX.FALSE."""
        src_true = "res: XoX = xox(True)\n"
        py_t = compile_source(src_true)
        scope_t = {}
        exec(py_t, scope_t)
        self.assertIs(scope_t[map_identifier("res")], XoX.TRUE)

        src_false = "res: XoX = xox(False)\n"
        py_f = compile_source(src_false)
        scope_f = {}
        exec(py_f, scope_f)
        self.assertIs(scope_f[map_identifier("res")], XoX.FALSE)

    def test_promotion_unknown_rejected(self):
        """xox(Unknown) -> static TypeError."""
        source = "res: XoX = xox(Unknown)\n"
        with self.assertRaises(TypeDiagnosticError) as ctx:
            compile_source(source)
        self.assertIn("promotes Bool to XoX", ctx.exception.message)
        self.assertIn("already XoX", ctx.exception.message)

    def test_promotion_ast_node_structure(self):
        """Verify AST node is PromoteBoolToXoX and preserves inner expression and span."""
        source = "res: XoX = xox(True)\n"
        ast = parse(tokenize(source))
        stmt = ast.statements[0]
        node = stmt.value
        self.assertIsInstance(node, PromoteBoolToXoX)
        self.assertIsInstance(node.expr, LiteralExpr)
        self.assertEqual(node.expr.kind, TokenKind.TRUE)
        self.assertIsNotNone(node.span)

    def test_empty_xox_call_rejected(self):
        """xox() without arguments -> static ParseError."""
        source = "res = xox()\n"
        with self.assertRaises(ParseError) as ctx:
            compile_source(source)
        self.assertIn("missing expression in 'xox()'", str(ctx.exception).lower())

    def test_readme_promotion_example(self):
        """Verify the exact README promotion example compiles and executes correctly."""
        source = (
            "is_ready: Bool = True\n"
            "status: XoX = xox(is_ready)\n"
        )
        py_code = compile_source(source)
        scope = {}
        exec(py_code, scope)
        self.assertIs(scope[map_identifier("is_ready")], True)
        self.assertIs(scope[map_identifier("status")], XoX.TRUE)

    def test_promotion_of_comparison_result(self):
        """xox(a == b) and xox(t1 == t2) validly promote Bool equality result to XoX."""
        source = (
            "t1: XoX = Unknown\n"
            "t2: XoX = Unknown\n"
            "eq_xox: XoX = xox(t1 == t2)\n"
        )
        py_code = compile_source(source)
        scope = {}
        exec(py_code, scope)
        self.assertIs(scope[map_identifier("eq_xox")], XoX.TRUE)

    def test_exception_propagates_and_is_not_masked(self):
        """Runtime exception in operand evaluation propagates without duplication."""
        source = "b: Bool = True\nres: XoX = xox(b)\n"
        ast = parse(tokenize(source))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[1].value, sem.result)

        code_lines = [
            "def failing_operand():",
            "    raise RuntimeError('boom')",
            f"res = (XoX.TRUE if failing_operand() else XoX.FALSE)",
        ]
        scope = {"XoX": XoX}
        with self.assertRaises(RuntimeError) as ctx:
            exec("\n".join(code_lines), scope)
        self.assertEqual(str(ctx.exception), "boom")


if __name__ == "__main__":
    unittest.main()
