"""Unit tests for XoX static truth-type system and contextual literal resolution."""
import unittest
from xoxlang.lexer import tokenize
from xoxlang.parser import parse
from xoxlang.types import BOOL, XOX, TypeKind, ConditionalKind
from xoxlang.semantic import SemanticAnalyzer, TypeEnv, check_expression, TypeError


def parse_expr(source: str):
    prog = parse(tokenize(source))
    return prog.statements[0].expr


class TestXoXTypeSystem(unittest.TestCase):
    def test_type_constants(self):
        self.assertEqual(str(TypeKind.XOX), "XoX")
        self.assertEqual(str(TypeKind.BOOL), "Bool")
        self.assertEqual(str(ConditionalKind.XOX), "XoX")
        self.assertEqual(XOX, TypeKind.XOX)

    def test_unconstrained_literals(self):
        self.assertEqual(check_expression(parse_expr("True")), BOOL)
        self.assertEqual(check_expression(parse_expr("False")), BOOL)
        self.assertEqual(check_expression(parse_expr("Unknown")), XOX)

    def test_expected_xox_context_on_literals(self):
        self.assertEqual(check_expression(parse_expr("True"), expected=XOX), XOX)
        self.assertEqual(check_expression(parse_expr("False"), expected=XOX), XOX)
        self.assertEqual(check_expression(parse_expr("Unknown"), expected=XOX), XOX)

    def test_compound_logical_expressions_without_context(self):
        self.assertEqual(check_expression(parse_expr("True AND False")), BOOL)
        self.assertEqual(check_expression(parse_expr("True OR False")), BOOL)
        self.assertEqual(check_expression(parse_expr("NOT True")), BOOL)

    def test_compound_logical_expressions_under_expected_xox_context(self):
        self.assertEqual(check_expression(parse_expr("True AND False"), expected=XOX), XOX)
        self.assertEqual(check_expression(parse_expr("True OR False"), expected=XOX), XOX)
        self.assertEqual(check_expression(parse_expr("NOT True"), expected=XOX), XOX)

    def test_unknown_anchor_propagates_xox_domain(self):
        # Unknown on left or right anchors uncommitted literals to XoX domain
        self.assertEqual(check_expression(parse_expr("Unknown AND True")), XOX)
        self.assertEqual(check_expression(parse_expr("True AND Unknown")), XOX)
        self.assertEqual(check_expression(parse_expr("False OR Unknown")), XOX)
        self.assertEqual(check_expression(parse_expr("Unknown OR False")), XOX)

    def test_typed_operands_provide_context(self):
        env = {"my_xox": XOX, "my_bool": BOOL}
        self.assertEqual(check_expression(parse_expr("my_xox AND True"), env=env), XOX)
        self.assertEqual(check_expression(parse_expr("True AND my_xox"), env=env), XOX)
        self.assertEqual(check_expression(parse_expr("my_bool AND True"), env=env), BOOL)
        self.assertEqual(check_expression(parse_expr("True AND my_bool"), env=env), BOOL)

    def test_mixed_already_typed_logical_operations_fail(self):
        env = {"my_xox": XOX, "my_bool": BOOL}
        with self.assertRaises(TypeError):
            check_expression(parse_expr("my_bool AND my_xox"), env=env)
        with self.assertRaises(TypeError):
            check_expression(parse_expr("my_bool AND Unknown"), env=env)
        with self.assertRaises(TypeError):
            check_expression(parse_expr("Unknown OR my_bool"), env=env)

    def test_equality_homogeneity_and_bool_result(self):
        env = {"my_xox": XOX, "my_bool": BOOL}
        self.assertEqual(check_expression(parse_expr("my_xox == my_xox"), env=env), BOOL)
        self.assertEqual(check_expression(parse_expr("my_xox != my_xox"), env=env), BOOL)
        self.assertEqual(check_expression(parse_expr("my_bool == my_bool"), env=env), BOOL)
        self.assertEqual(check_expression(parse_expr("my_bool != my_bool"), env=env), BOOL)

    def test_equality_contextual_literal_resolution(self):
        # True == Unknown: Unknown anchors True as XoX.TRUE, comparison returns Bool
        self.assertEqual(check_expression(parse_expr("True == Unknown")), BOOL)
        self.assertEqual(check_expression(parse_expr("Unknown != False")), BOOL)

        env = {"my_xox": XOX, "my_bool": BOOL}
        self.assertEqual(check_expression(parse_expr("my_xox == True"), env=env), BOOL)
        self.assertEqual(check_expression(parse_expr("my_bool == True"), env=env), BOOL)

    def test_mixed_already_typed_equality_fails(self):
        env = {"my_xox": XOX, "my_bool": BOOL}
        with self.assertRaises(TypeError):
            check_expression(parse_expr("my_bool == my_xox"), env=env)
        with self.assertRaises(TypeError):
            check_expression(parse_expr("my_bool == Unknown"), env=env)
        with self.assertRaises(TypeError):
            check_expression(parse_expr("Unknown != my_bool"), env=env)

    def test_equality_result_type_barrier(self):
        # Even with expected=XOX on outer context, equality expression itself returns Bool
        expr = parse_expr("True == Unknown")
        self.assertEqual(check_expression(expr, expected=XOX), BOOL)

    def test_traversal_order_independence(self):
        # Complex compound expressions with Unknown on either side
        expr1 = parse_expr("(True AND False) OR Unknown")
        expr2 = parse_expr("Unknown OR (True AND False)")
        self.assertEqual(check_expression(expr1), XOX)
        self.assertEqual(check_expression(expr2), XOX)



if __name__ == "__main__":
    unittest.main()
