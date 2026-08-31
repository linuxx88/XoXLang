"""Unit tests for XoX (X-o-X) monomorphic variable binding and reassignment semantics."""
import unittest
from xoxlang.lexer import tokenize
from xoxlang.parser import parse
from xoxlang.types import BOOL, XOX
from xoxlang.semantic import SemanticAnalyzer, TypeError, analyze


def parse_and_analyze(source: str, env=None):
    ast = parse(tokenize(source))
    return analyze(ast, env=env)


class TestXoXVariableBindings(unittest.TestCase):
    def test_initial_inferred_bindings(self):
        # flag = True -> Bool
        sa1 = parse_and_analyze("flag = True\n")
        self.assertEqual(sa1.env.lookup("flag"), BOOL)

        # flag2 = False -> Bool
        sa2 = parse_and_analyze("flag2 = False\n")
        self.assertEqual(sa2.env.lookup("flag2"), BOOL)

        # status = Unknown -> XoX
        sa3 = parse_and_analyze("status = Unknown\n")
        self.assertEqual(sa3.env.lookup("status"), XOX)

    def test_annotated_xox_binding_contextualizes_literals(self):
        # status: XoX = True
        sa1 = parse_and_analyze("status: XoX = True\n")
        self.assertEqual(sa1.env.lookup("status"), XOX)

        # status: XoX = False
        sa2 = parse_and_analyze("status: XoX = False\n")
        self.assertEqual(sa2.env.lookup("status"), XOX)

        # status: XoX = Unknown
        sa3 = parse_and_analyze("status: XoX = Unknown\n")
        self.assertEqual(sa3.env.lookup("status"), XOX)

    def test_annotated_bool_binding(self):
        sa1 = parse_and_analyze("flag: Bool = True\n")
        self.assertEqual(sa1.env.lookup("flag"), BOOL)

        sa2 = parse_and_analyze("flag: Bool = False\n")
        self.assertEqual(sa2.env.lookup("flag"), BOOL)

        # flag: Bool = Unknown -> TypeError
        with self.assertRaises(TypeError):
            parse_and_analyze("flag: Bool = Unknown\n")

    def test_monomorphic_reassignment_bool(self):
        # flag = True; flag = False -> Valid
        source = "flag = True\nflag = False\n"
        sa = parse_and_analyze(source)
        self.assertEqual(sa.env.lookup("flag"), BOOL)

        # flag = True; flag = Unknown -> TypeError
        with self.assertRaises(TypeError):
            parse_and_analyze("flag = True\nflag = Unknown\n")

    def test_monomorphic_reassignment_xox(self):
        # status: XoX = Unknown; status = True; status = False -> Valid
        source = (
            "status: XoX = Unknown\n"
            "status = True\n"
            "status = False\n"
        )
        sa = parse_and_analyze(source)
        self.assertEqual(sa.env.lookup("status"), XOX)

    def test_cross_type_reassignment_rejection(self):
        # XoX reassigned already-typed Bool expression -> TypeError
        source1 = (
            "my_bool = True\n"
            "my_xox: XoX = Unknown\n"
            "my_xox = my_bool\n"
        )
        with self.assertRaises(TypeError):
            parse_and_analyze(source1)

        # Bool reassigned already-typed XoX expression -> TypeError
        source2 = (
            "my_xox = Unknown\n"
            "my_bool = True\n"
            "my_bool = my_xox\n"
        )
        with self.assertRaises(TypeError):
            parse_and_analyze(source2)

    def test_matching_annotation_on_existing_variable(self):
        source = (
            "status: XoX = True\n"
            "status: XoX = Unknown\n"
        )
        sa = parse_and_analyze(source)
        self.assertEqual(sa.env.lookup("status"), XOX)

    def test_conflicting_annotation_on_existing_variable(self):
        source = (
            "status: XoX = True\n"
            "status: Bool = True\n"
        )
        with self.assertRaises(TypeError):
            parse_and_analyze(source)

    def test_identifier_resolves_from_type_env(self):
        source = (
            "a = True\n"
            "b: XoX = Unknown\n"
            "c = a == a\n"
        )
        sa = parse_and_analyze(source)
        self.assertEqual(sa.env.lookup("a"), BOOL)
        self.assertEqual(sa.env.lookup("b"), XOX)
        self.assertEqual(sa.env.lookup("c"), BOOL)

    def test_unbound_identifier_fails(self):
        with self.assertRaises(TypeError) as ctx:
            parse_and_analyze("x = y\n")
        self.assertIn("Variable 'y' is not defined", str(ctx.exception))

    def test_annotated_xox_compound_initializer(self):
        # status: XoX = True AND False -> evaluates as XoX
        source = "status: XoX = True AND False\n"
        sa = parse_and_analyze(source)
        self.assertEqual(sa.env.lookup("status"), XOX)

    def test_annotated_xox_assignment_equality_barrier(self):
        # res: XoX = (a == b) -> equality returns Bool, assigning to XoX is TypeError
        source = (
            "a = True\n"
            "b = False\n"
            "res: XoX = a == b\n"
        )
        with self.assertRaises(TypeError):
            parse_and_analyze(source)



if __name__ == "__main__":
    unittest.main()
