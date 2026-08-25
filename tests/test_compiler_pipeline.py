"""End-to-end unit tests for the XoX compiler pipeline."""
import unittest
from trool import compile_source
from trool.lexer import LexerError
from trool.parser import ParseError
from trool.diagnostics import TypeDiagnosticError, ExhaustivenessError, MissingReturnError
from trool.lowering import map_identifier
from trool.runtime import XoX


class TestXoXCompilerPipeline(unittest.TestCase):
    def test_compile_bool_assignment(self):
        source = "x = True\n"
        py_code = compile_source(source)
        compile(py_code, "<test>", "exec")
        scope = {}
        exec(py_code, scope)
        self.assertIs(scope[map_identifier("x")], True)

    def test_compile_xox_assignment(self):
        source = "x: XoX = Unknown\n"
        py_code = compile_source(source)
        compile(py_code, "<test>", "exec")
        scope = {}
        exec(py_code, scope)
        self.assertIs(scope[map_identifier("x")], XoX.UNKNOWN)

    def test_compile_bool_conditional(self):
        source = (
            "x = True\n"
            "res = False\n"
            "if x:\n"
            "    res = True\n"
            "else:\n"
            "    res = False\n"
        )
        py_code = compile_source(source)
        compile(py_code, "<test>", "exec")
        scope = {}
        exec(py_code, scope)
        self.assertIs(scope[map_identifier("res")], True)

    def test_compile_xox_conditional(self):
        source = (
            "t: XoX = Unknown\n"
            "res = False\n"
            "if t:\n"
            "    res = False\n"
            "xen:\n"
            "    res = True\n"
            "else:\n"
            "    res = False\n"
        )
        py_code = compile_source(source)
        compile(py_code, "<test>", "exec")
        scope = {}
        exec(py_code, scope)
        self.assertIs(scope[map_identifier("res")], True)

    def test_compile_function_definition(self):
        source = (
            "fn check_xox(t: XoX) -> Bool:\n"
            "    return t == Unknown\n"
        )
        py_code = compile_source(source)
        compile(py_code, "<test>", "exec")
        scope = {}
        exec(py_code, scope)
        fn_name = map_identifier("check_xox")
        self.assertTrue(callable(scope[fn_name]))
        self.assertIs(scope[fn_name](XoX.UNKNOWN), True)
        self.assertIs(scope[fn_name](XoX.TRUE), False)

    def test_compile_full_program(self):
        source = (
            "fn classify(t: XoX) -> XoX:\n"
            "    if t:\n"
            "        return True\n"
            "    xen:\n"
            "        return Unknown\n"
            "    else:\n"
            "        return False\n"
            "\n"
            "val: XoX = Unknown\n"
        )
        py_code = compile_source(source)
        compile(py_code, "<test>", "exec")
        scope = {}
        exec(py_code, scope)
        fn_name = map_identifier("classify")
        val_name = map_identifier("val")
        self.assertIs(scope[fn_name](scope[val_name]), XoX.UNKNOWN)

    def test_deterministic_output(self):
        source = (
            "fn test(a: XoX, b: Bool) -> XoX:\n"
            "    if b:\n"
            "        return a AND True\n"
            "    else:\n"
            "        return Unknown\n"
        )
        out1 = compile_source(source)
        out2 = compile_source(source)
        self.assertEqual(out1, out2)

    def test_syntax_error_propagation(self):
        with self.assertRaises(LexerError):
            compile_source("fn broken(")
        with self.assertRaises(ParseError):
            compile_source("fn f() -> : pass\n")

    def test_type_error_propagation(self):
        with self.assertRaises(TypeDiagnosticError):
            compile_source("x: Bool = Unknown\n")

    def test_exhaustiveness_error_propagation(self):
        source = (
            "t: XoX = Unknown\n"
            "if t:\n"
            "    pass\n"
            "else:\n"
            "    pass\n"
        )
        with self.assertRaises(ExhaustivenessError):
            compile_source(source)

    def test_missing_return_error_propagation(self):
        source = (
            "fn f() -> Bool:\n"
            "    pass\n"
        )
        with self.assertRaises(MissingReturnError):
            compile_source(source)

    def test_diagnostic_precedence(self):
        # 1. SyntaxError (Parser/Lexer) before TypeError
        with self.assertRaises(ParseError):
            compile_source("x: Bool = = True\n")

        # 2. TypeError before ExhaustivenessError (Bool if with xen: ignore is a TypeError)
        with self.assertRaises(TypeDiagnosticError):
            compile_source("if True:\n    pass\nxen:\n    ignore\n")

        # 3. ExhaustivenessError before MissingReturnError (XoX conditional missing xen is ExhaustivenessError)
        source_ex = (
            "fn f(t: XoX) -> Bool:\n"
            "    if t:\n"
            "        return True\n"
            "    else:\n"
            "        return False\n"
        )
        with self.assertRaises(ExhaustivenessError):
            compile_source(source_ex)

    def test_no_state_leak_after_failure(self):
        # First: invalid compilation
        with self.assertRaises(TypeDiagnosticError):
            compile_source("x: Bool = Unknown\n")

        # Second: valid compilation
        valid_source = "x: XoX = Unknown\n"
        py_code = compile_source(valid_source)
        scope = {}
        exec(py_code, scope)
        self.assertIs(scope[map_identifier("x")], XoX.UNKNOWN)



if __name__ == "__main__":
    unittest.main()
