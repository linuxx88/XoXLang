"""Unit tests for XoX (X-o-X) target namespace hygiene and identifier mapping."""
import unittest
from trool.lexer import tokenize
from trool.parser import parse
from trool.semantic import analyze
from trool.lowering import ExpressionLowerer, lower_expression, map_identifier
from trool.runtime import XoX, xox_not, xox_and, xox_or, UnknownValueError


class TestXoXLoweringIdentifiers(unittest.TestCase):
    def test_deterministic_and_valid_python_identifiers(self):
        target_x = map_identifier("x")
        self.assertTrue(target_x.isidentifier())
        self.assertEqual(target_x, map_identifier("x"))

    def test_injective_mapping(self):
        ids = ["x", "y", "x_1", "class", "def", "lambda", "XoX", "Trool", "_tmp_0", "_u_61"]
        mapped = [map_identifier(name) for name in ids]
        self.assertEqual(len(mapped), len(set(mapped)))
        for m in mapped:
            self.assertTrue(m.isidentifier())

    def test_python_keywords_map_to_valid_non_keywords(self):
        keywords = ["class", "def", "lambda", "import", "for", "while", "match", "case", "async", "await"]
        for kw in keywords:
            with self.subTest(kw=kw):
                mapped = map_identifier(kw)
                self.assertTrue(mapped.isidentifier())
                # Verify it can be used as a Python variable name in exec
                exec(f"{mapped} = True")

    def test_runtime_support_symbols_do_not_collide(self):
        runtime_names = ["XoX", "xox_not", "xox_and", "xox_or", "UnknownValueError"]
        for name in runtime_names:
            with self.subTest(name=name):
                mapped = map_identifier(name)

                self.assertNotEqual(mapped, name)
                self.assertTrue(mapped.startswith("_u_"))

    def test_compiler_temporaries_do_not_collide(self):
        lowerer = ExpressionLowerer(semantic_result=None)  # type: ignore
        temp0 = lowerer.new_temp()
        user_temp0 = map_identifier("_tmp_0")
        self.assertNotEqual(temp0, user_temp0)
        self.assertTrue(temp0.startswith("_tmp_"))
        self.assertTrue(user_temp0.startswith("_u_"))

    def test_identifier_expr_lowering_uses_mapped_name(self):
        ast = parse(tokenize("var: XoX = Unknown\nvar\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[1].expr, sem.result)
        self.assertEqual(lowered.expr, map_identifier("var"))
        self.assertNotEqual(lowered.expr, "var")


    def test_repeated_references_lower_consistently(self):
        ast = parse(tokenize("flag: Bool = True\nflag AND flag\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[1].expr, sem.result)
        mapped_flag = map_identifier("flag")
        self.assertEqual(lowered.expr, f"({mapped_flag} and {mapped_flag})")


if __name__ == "__main__":
    unittest.main()
