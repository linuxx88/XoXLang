"""Adversarial and conformance tests for XoX-to-Bool collapse primitive unwrap_or(default_bool).

Verifies CTX-COLLAPSE-01 through CTX-COLLAPSE-06 from experiments/COLLAPSE_COUNTEREXAMPLES.md.
"""
import unittest
from xoxlang import compile_source
from xoxlang.lexer import tokenize
from xoxlang.parser import parse, ParseError
from xoxlang.semantic import analyze
from xoxlang.ast import CollapseXoXToBoolWithDefault, IdentifierExpr, LiteralExpr
from xoxlang.tokens import TokenKind
from xoxlang.diagnostics import TypeDiagnosticError
from xoxlang.types import BOOL, XOX
from xoxlang.lowering import lower_expression, map_identifier
from xoxlang.runtime import XoX, xox_and, xox_not, xox_or


class TestXoXCollapseAdversarial(unittest.TestCase):
    def test_ctx_collapse_01_true_short_circuit_no_fallback(self):
        """CTX-COLLAPSE-01: XoX.True.unwrap_or(trace_effect()) -> Bool.True; fallback called 0 times."""
        ast = parse(tokenize("t: XoX = True\nfb: Bool = False\nres = t.unwrap_or(fb)\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[2].value, sem.result)

        code_lines = [
            "trace = []",
            "def eval_source():",
            "    trace.append('eval_source')",
            "    return XoX.TRUE",
            "def eval_fallback():",
            "    trace.append('eval_fallback')",
            "    return False",
            *lowered.prelude,
        ]
        for i, line in enumerate(code_lines):
            if f"= {map_identifier('t')}" in line:
                code_lines[i] = line.replace(f"= {map_identifier('t')}", "= eval_source()")
            elif f"= {map_identifier('fb')}" in line:
                code_lines[i] = line.replace(f"= {map_identifier('fb')}", "= eval_fallback()")

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("t"): XoX.TRUE,
            map_identifier("fb"): False,
        }
        exec("\n".join(code_lines), scope)

        self.assertEqual(scope["trace"], ["eval_source"])
        self.assertEqual(scope["trace"].count("eval_source"), 1)
        self.assertEqual(scope["trace"].count("eval_fallback"), 0)
        res_val = scope[lowered.expr]
        self.assertIs(res_val, True)

    def test_ctx_collapse_02_false_short_circuit_no_fallback(self):
        """CTX-COLLAPSE-02: XoX.False.unwrap_or(trace_effect()) -> Bool.False; fallback called 0 times."""
        ast = parse(tokenize("t: XoX = False\nfb: Bool = True\nres = t.unwrap_or(fb)\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[2].value, sem.result)

        code_lines = [
            "trace = []",
            "def eval_source():",
            "    trace.append('eval_source')",
            "    return XoX.FALSE",
            "def eval_fallback():",
            "    trace.append('eval_fallback')",
            "    return True",
            *lowered.prelude,
        ]
        for i, line in enumerate(code_lines):
            if f"= {map_identifier('t')}" in line:
                code_lines[i] = line.replace(f"= {map_identifier('t')}", "= eval_source()")
            elif f"= {map_identifier('fb')}" in line:
                code_lines[i] = line.replace(f"= {map_identifier('fb')}", "= eval_fallback()")

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("t"): XoX.FALSE,
            map_identifier("fb"): True,
        }
        exec("\n".join(code_lines), scope)

        self.assertEqual(scope["trace"], ["eval_source"])
        self.assertEqual(scope["trace"].count("eval_source"), 1)
        self.assertEqual(scope["trace"].count("eval_fallback"), 0)
        res_val = scope[lowered.expr]
        self.assertIs(res_val, False)

    def test_ctx_collapse_03_unknown_exact_single_fallback_evaluation(self):
        """CTX-COLLAPSE-03: XoX.Unknown.unwrap_or(fallback) -> fallback Bool result; fallback evaluated exactly once after source."""
        # Sub-case A: Fallback returns True
        ast_a = parse(tokenize("t: XoX = Unknown\nfb: Bool = True\nres = t.unwrap_or(fb)\n"))
        sem_a = analyze(ast_a)
        lowered_a = lower_expression(ast_a.statements[2].value, sem_a.result)

        code_lines_a = [
            "trace = []",
            "def eval_source():",
            "    trace.append('eval_source')",
            "    return XoX.UNKNOWN",
            "def eval_fallback():",
            "    trace.append('eval_fallback')",
            "    return True",
            *lowered_a.prelude,
        ]
        for i, line in enumerate(code_lines_a):
            if f"= {map_identifier('t')}" in line:
                code_lines_a[i] = line.replace(f"= {map_identifier('t')}", "= eval_source()")
            elif f"= {map_identifier('fb')}" in line:
                code_lines_a[i] = line.replace(f"= {map_identifier('fb')}", "= eval_fallback()")

        scope_a = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("t"): XoX.UNKNOWN,
            map_identifier("fb"): True,
        }
        exec("\n".join(code_lines_a), scope_a)

        self.assertEqual(scope_a["trace"], ["eval_source", "eval_fallback"])
        self.assertEqual(scope_a["trace"].count("eval_source"), 1)
        self.assertEqual(scope_a["trace"].count("eval_fallback"), 1)
        res_val_a = scope_a[lowered_a.expr]
        self.assertIs(res_val_a, True)

        # Sub-case B: Fallback returns False
        ast_b = parse(tokenize("t: XoX = Unknown\nfb: Bool = False\nres = t.unwrap_or(fb)\n"))
        sem_b = analyze(ast_b)
        lowered_b = lower_expression(ast_b.statements[2].value, sem_b.result)

        code_lines_b = [
            "trace = []",
            "def eval_source():",
            "    trace.append('eval_source')",
            "    return XoX.UNKNOWN",
            "def eval_fallback():",
            "    trace.append('eval_fallback')",
            "    return False",
            *lowered_b.prelude,
        ]
        for i, line in enumerate(code_lines_b):
            if f"= {map_identifier('t')}" in line:
                code_lines_b[i] = line.replace(f"= {map_identifier('t')}", "= eval_source()")
            elif f"= {map_identifier('fb')}" in line:
                code_lines_b[i] = line.replace(f"= {map_identifier('fb')}", "= eval_fallback()")

        scope_b = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("t"): XoX.UNKNOWN,
            map_identifier("fb"): False,
        }
        exec("\n".join(code_lines_b), scope_b)

        self.assertEqual(scope_b["trace"], ["eval_source", "eval_fallback"])
        self.assertEqual(scope_b["trace"].count("eval_source"), 1)
        self.assertEqual(scope_b["trace"].count("eval_fallback"), 1)
        res_val_b = scope_b[lowered_b.expr]
        self.assertIs(res_val_b, False)

    def test_ctx_collapse_04_non_bool_fallback_statically_rejected(self):
        """CTX-COLLAPSE-04: xox_val.unwrap_or(Unknown) -> static TypeError."""
        source_unknown = (
            "x: XoX = True\n"
            "res = x.unwrap_or(Unknown)\n"
        )
        with self.assertRaises(TypeDiagnosticError):
            compile_source(source_unknown)

        source_xox = (
            "x: XoX = True\n"
            "other: XoX = False\n"
            "res = x.unwrap_or(other)\n"
        )
        with self.assertRaises(TypeDiagnosticError):
            compile_source(source_xox)

    def test_ctx_collapse_05_non_xox_source_statically_rejected(self):
        """CTX-COLLAPSE-05: bool_val.unwrap_or(False) -> static TypeError."""
        source = (
            "b: Bool = True\n"
            "res = b.unwrap_or(False)\n"
        )
        with self.assertRaises(TypeDiagnosticError):
            compile_source(source)

    def test_ctx_collapse_06_absent_fallback_statically_rejected(self):
        """CTX-COLLAPSE-06: xox_val.unwrap_or() -> static ParseError."""
        source = (
            "x: XoX = True\n"
            "res = x.unwrap_or()\n"
        )
        with self.assertRaises(ParseError) as ctx:
            compile_source(source)
        self.assertIn("missing mandatory fallback", str(ctx.exception).lower())

    def test_collapse_ast_node_structure(self):
        """Verify AST node is CollapseXoXToBoolWithDefault and preserves exact fields."""
        source = "x: XoX = True\nres = x.unwrap_or(False)\n"
        ast = parse(tokenize(source))
        stmt = ast.statements[1]
        node = stmt.value
        self.assertIsInstance(node, CollapseXoXToBoolWithDefault)
        self.assertIsInstance(node.source, IdentifierExpr)
        self.assertEqual(node.source.name, "x")
        self.assertIsInstance(node.fallback, LiteralExpr)
        self.assertEqual(node.fallback.kind, TokenKind.FALSE)

    def test_reject_arbitrary_method_or_property_access(self):
        """Verify arbitrary method calls or attributes are strictly rejected by the parser."""
        with self.assertRaises(ParseError) as ctx:
            compile_source("x: XoX = True\nres = x.foo(False)\n")
        self.assertIn("unsupported postfix method", str(ctx.exception).lower())

        with self.assertRaises(ParseError) as ctx:
            compile_source("x: XoX = True\nres = x.bar\n")
        self.assertIn("unsupported postfix method", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
