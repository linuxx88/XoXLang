"""Unit tests for XoX (X-o-X) function semantic analysis and return typing."""
import unittest
from xoxlang.lexer import tokenize
from xoxlang.parser import parse
from xoxlang.types import BOOL, XOX
from xoxlang.semantic import SemanticAnalyzer, TypeEnv, analyze, TypeError


class TestXoXFunctionSemantics(unittest.TestCase):
    def test_typed_bool_parameter_resolves_as_bool(self):
        source = (
            "fn f(x: Bool) -> Bool:\n"
            "    return x\n"
        )
        ast = parse(tokenize(source))
        analyzer = analyze(ast)
        self.assertIsNotNone(analyzer)

    def test_typed_xox_parameter_resolves_as_xox(self):
        source = (
            "fn f(x: XoX) -> XoX:\n"
            "    return x\n"
        )
        ast = parse(tokenize(source))
        analyzer = analyze(ast)
        self.assertIsNotNone(analyzer)

    def test_function_local_bindings_and_parameters_do_not_leak(self):
        source = (
            "fn f(x: Bool):\n"
            "    local_var = True\n"
            "    return local_var\n"
        )
        ast = parse(tokenize(source))
        analyzer = SemanticAnalyzer()
        analyzer.check_program(ast)
        # Outside environment should not contain x or local_var
        self.assertIsNone(analyzer.env.lookup("x"))
        self.assertIsNone(analyzer.env.lookup("local_var"))

    def test_unannotated_function_returning_bool_literals(self):
        # return True
        ast1 = parse(tokenize("fn f():\n    return True\n"))
        analyzer1 = analyze(ast1)
        self.assertIsNotNone(analyzer1)

        # return False
        ast2 = parse(tokenize("fn f():\n    return False\n"))
        analyzer2 = analyze(ast2)
        self.assertIsNotNone(analyzer2)

    def test_unannotated_function_rejects_xox_returns(self):
        # return Unknown
        ast_unknown = parse(tokenize("fn f():\n    return Unknown\n"))
        with self.assertRaises(TypeError) as ctx1:
            analyze(ast_unknown)
        self.assertIn("explicit '-> XoX'", str(ctx1.exception))

        # return XoX parameter
        ast_param = parse(tokenize("fn f(x: XoX):\n    return x\n"))
        with self.assertRaises(TypeError) as ctx2:
            analyze(ast_param)
        self.assertIn("explicit '-> XoX'", str(ctx2.exception))

        # return XoX logical operation
        ast_logical = parse(tokenize("fn f(x: XoX):\n    return x AND True\n"))
        with self.assertRaises(TypeError) as ctx3:
            analyze(ast_logical)
        self.assertIn("explicit '-> XoX'", str(ctx3.exception))

    def test_annotated_bool_return(self):
        # Contextualizes literals as Bool
        ast1 = parse(tokenize("fn f() -> Bool:\n    return True\n"))
        analyze(ast1)

        # Rejects Unknown
        ast_unk = parse(tokenize("fn f() -> Bool:\n    return Unknown\n"))
        with self.assertRaises(TypeError) as ctx:
            analyze(ast_unk)
        self.assertIn("Cannot return XoX expression from function with return annotation -> Bool", str(ctx.exception))

        # Rejects XoX expression
        ast_xox = parse(tokenize("fn f(t: XoX) -> Bool:\n    return t\n"))
        with self.assertRaises(TypeError) as ctx:
            analyze(ast_xox)
        self.assertIn("Cannot return XoX expression from function with return annotation -> Bool", str(ctx.exception))

        # Accepts equality over XoX operands because equality returns Bool
        ast_eq = parse(tokenize("fn f(t: XoX) -> Bool:\n    return t == Unknown\n"))
        analyze(ast_eq)

    def test_annotated_xox_return(self):
        # Contextualizes literals as XoX
        ast1 = parse(tokenize("fn f() -> XoX:\n    return True\n"))
        analyze(ast1)

        ast2 = parse(tokenize("fn f() -> XoX:\n    return False\n"))
        analyze(ast2)

        # Accepts Unknown
        ast3 = parse(tokenize("fn f() -> XoX:\n    return Unknown\n"))
        analyze(ast3)

        # Accepts XoX parameter
        ast4 = parse(tokenize("fn f(t: XoX) -> XoX:\n    return t\n"))
        analyze(ast4)

        # Rejects already-typed Bool expression
        ast_bool = parse(tokenize("fn f(b: Bool) -> XoX:\n    return b\n"))
        with self.assertRaises(TypeError) as ctx:
            analyze(ast_bool)
        self.assertIn("Cannot return Bool expression from function with return annotation -> XoX", str(ctx.exception))

        # Rejects equality result because equality returns Bool
        ast_eq = parse(tokenize("fn f(t: XoX) -> XoX:\n    return t == Unknown\n"))
        with self.assertRaises(TypeError) as ctx:
            analyze(ast_eq)
        self.assertIn("Cannot return Bool expression from function with return annotation -> XoX", str(ctx.exception))

    def test_function_local_monomorphic_bindings_and_reassignments(self):
        source = (
            "fn f(t: XoX) -> XoX:\n"
            "    # Valid reassignment of XoX parameter\n"
            "    t = Unknown\n"
            "    # Inferred local binding\n"
            "    flag = True\n"
            "    flag = False\n"
            "    return t\n"
        )
        ast = parse(tokenize(source))
        analyze(ast)

    def test_parameter_reassignment_type_error(self):
        # Cannot assign XoX to Bool parameter
        source_bool = (
            "fn f(b: Bool) -> Bool:\n"
            "    b = Unknown\n"
            "    return b\n"
        )
        ast_bool = parse(tokenize(source_bool))
        with self.assertRaises(TypeError) as ctx:
            analyze(ast_bool)
        self.assertIn("Cannot reassign variable 'b'", str(ctx.exception))

        # Cannot assign already-typed Bool to XoX parameter
        source_xox = (
            "fn f(t: XoX, b: Bool) -> XoX:\n"
            "    t = b\n"
            "    return t\n"
        )
        ast_xox = parse(tokenize(source_xox))
        with self.assertRaises(TypeError) as ctx:
            analyze(ast_xox)
        self.assertIn("Cannot reassign variable 't'", str(ctx.exception))



if __name__ == "__main__":
    unittest.main()
