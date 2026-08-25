"""Unit tests for XoX (X-o-X) full program lowering."""
import unittest
from trool.lexer import tokenize
from trool.parser import parse
from trool.semantic import analyze
from trool.lowering import ProgramLowerer, lower_to_python, map_identifier
from trool.runtime import XoX


class TestXoXLoweringProgram(unittest.TestCase):
    def test_empty_program_lowering(self):
        ast = parse(tokenize(""))
        sem = analyze(ast)
        output = lower_to_python(ast, sem.result)

        self.assertIn("from trool.runtime import XoX", output)
        scope = {}
        exec(output, scope)
        self.assertIs(scope["XoX"], XoX)

    def test_top_level_assignments_and_order(self):
        source = (
            "a = True\n"
            "b: XoX = Unknown\n"
            "c = False\n"
        )
        ast = parse(tokenize(source))
        sem = analyze(ast)
        output = lower_to_python(ast, sem.result)

        scope = {}
        exec(output, scope)
        self.assertIs(scope[map_identifier("a")], True)
        self.assertIs(scope[map_identifier("b")], XoX.UNKNOWN)
        self.assertIs(scope[map_identifier("c")], False)

    def test_top_level_conditionals(self):
        source = (
            "t: XoX = Unknown\n"
            "res: Bool = False\n"
            "if t:\n"
            "    res = False\n"
            "xen:\n"
            "    res = True\n"
            "else:\n"
            "    res = False\n"
        )
        ast = parse(tokenize(source))
        sem = analyze(ast)
        output = lower_to_python(ast, sem.result)

        scope = {}
        exec(output, scope)
        self.assertIs(scope[map_identifier("res")], True)

    def test_program_combining_functions_and_globals(self):
        source = (
            "fn is_unknown(t: XoX) -> Bool:\n"
            "    return t == Unknown\n"
            "\n"
            "status: XoX = Unknown\n"
        )
        ast = parse(tokenize(source))
        sem = analyze(ast)
        output = lower_to_python(ast, sem.result)

        scope = {}
        exec(output, scope)
        fn_name = map_identifier("is_unknown")
        status_name = map_identifier("status")
        self.assertTrue(callable(scope[fn_name]))
        self.assertIs(scope[fn_name](scope[status_name]), True)

    def test_deterministic_reproducible_output(self):
        source = (
            "t: XoX = Unknown\n"
            "x = t AND True\n"
            "fn f(p: XoX) -> XoX:\n"
            "    return p OR Unknown\n"
        )
        ast1 = parse(tokenize(source))
        sem1 = analyze(ast1)
        out1 = lower_to_python(ast1, sem1.result)

        ast2 = parse(tokenize(source))
        sem2 = analyze(ast2)
        out2 = lower_to_python(ast2, sem2.result)

        self.assertEqual(out1, out2)

    def test_runtime_symbol_hygiene_at_module_level(self):
        source = (
            "XoX: Bool = True\n"
            "xox_and: Bool = False\n"
        )
        ast = parse(tokenize(source))
        sem = analyze(ast)
        output = lower_to_python(ast, sem.result)

        scope = {}
        exec(output, scope)
        self.assertIs(scope[map_identifier("XoX")], True)
        self.assertIs(scope[map_identifier("xox_and")], False)
        self.assertIs(scope["XoX"], XoX)

    def test_unsupported_ast_fails(self):
        from trool.ast import LiteralExpr
        from trool.semantic import SemanticResult
        with self.assertRaises(TypeError):
            lower_to_python(LiteralExpr(), SemanticResult())



if __name__ == "__main__":
    unittest.main()
