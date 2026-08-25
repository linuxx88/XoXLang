"""Unit tests for XoX (X-o-X) post-type conditional semantic classification and exhaustiveness."""
import unittest
from trool.lexer import tokenize
from trool.parser import parse
from trool.types import BOOL, XOX
from trool.semantic import SemanticAnalyzer, TypeEnv, analyze, TypeError
from trool.diagnostics import ExhaustivenessError


class TestXoXConditionalSemantics(unittest.TestCase):
    def test_bool_conditional_if_only_valid(self):
        source = "if True:\n    pass\n"
        ast = parse(tokenize(source))
        analyzer = analyze(ast)
        self.assertIsNotNone(analyzer)

    def test_bool_conditional_if_else_valid(self):
        source = (
            "if False:\n"
            "    pass\n"
            "else:\n"
            "    pass\n"
        )
        ast = parse(tokenize(source))
        analyzer = analyze(ast)
        self.assertIsNotNone(analyzer)

    def test_bool_conditional_rejects_xen(self):
        samples = [
            "if True:\n    pass\nxen:\n    ignore\nelse:\n    pass\n",
            "flag: Bool = True\nif flag:\n    pass\nxen:\n    pass\n    flag\nelse:\n    pass\n",
            "if (Unknown == Unknown):\n    pass\nxen:\n    ignore\nelse:\n    pass\n",
        ]
        for src in samples:
            with self.subTest(src=src):
                ast = parse(tokenize(src))
                with self.assertRaises(TypeError) as ctx:
                    analyze(ast)
                self.assertIn("Bool conditional must not contain a 'xen' clause", str(ctx.exception))

    def test_xox_conditional_full_branches_valid(self):
        # xen with statements
        source1 = (
            "audit = True\n"
            "status: XoX = Unknown\n"
            "if status:\n"
            "    pass\n"
            "xen:\n"
            "    pass\n"
            "    audit\n"
            "else:\n"
            "    pass\n"
        )
        ast1 = parse(tokenize(source1))
        analyze(ast1)

        # xen: ignore
        source2 = (
            "status: XoX = Unknown\n"
            "if status:\n"
            "    pass\n"
            "xen:\n"
            "    ignore\n"
            "else:\n"
            "    pass\n"
        )
        ast2 = parse(tokenize(source2))
        analyze(ast2)

    def test_xox_conditional_missing_xen_emits_exhaustiveness_error(self):
        source = (
            "status: XoX = Unknown\n"
            "if status:\n"
            "    pass\n"
            "else:\n"
            "    pass\n"
        )
        ast = parse(tokenize(source))
        with self.assertRaises(ExhaustivenessError) as ctx:
            analyze(ast)
        self.assertIn("missing 'xen' clause", str(ctx.exception))

    def test_xox_conditional_missing_else_emits_exhaustiveness_error(self):
        source = (
            "status: XoX = Unknown\n"
            "if status:\n"
            "    pass\n"
            "xen:\n"
            "    ignore\n"
        )
        ast = parse(tokenize(source))
        with self.assertRaises(ExhaustivenessError) as ctx:
            analyze(ast)
        self.assertIn("missing 'else' clause", str(ctx.exception))

    def test_xox_conditional_missing_both_xen_and_else_emits_exhaustiveness_error(self):
        source = (
            "status: XoX = Unknown\n"
            "if status:\n"
            "    pass\n"
        )
        ast = parse(tokenize(source))
        with self.assertRaises(ExhaustivenessError) as ctx:
            analyze(ast)
        self.assertIn("both 'xen'", str(ctx.exception))

    def test_condition_resolves_via_type_system(self):
        # Unknown alone is XoX
        ast_unk = parse(tokenize("if Unknown:\n    pass\nxen:\n    ignore\nelse:\n    pass\n"))
        analyze(ast_unk)

        # Equality over XoX operands is Bool, so it accepts if/else without xen
        source_eq = (
            "t: XoX = Unknown\n"
            "if t == Unknown:\n"
            "    pass\n"
            "else:\n"
            "    pass\n"
        )
        ast_eq = parse(tokenize(source_eq))
        analyze(ast_eq)

        # XoX compound expression is XoX
        source_compound = (
            "t: XoX = Unknown\n"
            "if t AND True:\n"
            "    pass\n"
            "xen:\n"
            "    ignore\n"
            "else:\n"
            "    pass\n"
        )
        ast_compound = parse(tokenize(source_compound))
        analyze(ast_compound)

    def test_branch_internal_statement_and_return_typing(self):
        source = (
            "fn evaluate(t: XoX) -> XoX:\n"
            "    if t:\n"
            "        return True\n"
            "    xen:\n"
            "        return Unknown\n"
            "    else:\n"
            "        return False\n"
        )
        ast = parse(tokenize(source))
        analyze(ast)

        # Incompatible return in branch triggers TypeError
        bad_source = (
            "fn evaluate(t: XoX) -> Bool:\n"
            "    if t:\n"
            "        return True\n"
            "    xen:\n"
            "        return Unknown\n"
            "    else:\n"
            "        return False\n"
        )
        bad_ast = parse(tokenize(bad_source))
        with self.assertRaises(TypeError):
            analyze(bad_ast)



if __name__ == "__main__":
    unittest.main()
