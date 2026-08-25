"""Unit tests for XoX (X-o-X) definite-return reachability analysis and MissingReturnError."""
import unittest
from trool.lexer import tokenize
from trool.parser import parse
from trool.types import BOOL, XOX
from trool.semantic import SemanticAnalyzer, TypeEnv, analyze, TypeError
from trool.diagnostics import ExhaustivenessError, MissingReturnError


class TestXoXDefiniteReturn(unittest.TestCase):
    def test_direct_return_is_valid(self):
        source = (
            "fn f() -> Bool:\n"
            "    return True\n"
        )
        ast = parse(tokenize(source))
        analyze(ast)

    def test_bool_if_else_both_returning_is_valid(self):
        source = (
            "fn f(b: Bool) -> Bool:\n"
            "    if b:\n"
            "        return True\n"
            "    else:\n"
            "        return False\n"
        )
        ast = parse(tokenize(source))
        analyze(ast)

    def test_bool_if_only_missing_return_error(self):
        source = (
            "fn f(b: Bool) -> Bool:\n"
            "    if b:\n"
            "        return True\n"
        )
        ast = parse(tokenize(source))
        with self.assertRaises(MissingReturnError) as ctx:
            analyze(ast)
        self.assertIn("does not return a value on every control-flow path", str(ctx.exception))

    def test_bool_if_only_with_subsequent_return_is_valid(self):
        source = (
            "fn f(b: Bool) -> Bool:\n"
            "    if b:\n"
            "        return True\n"
            "    return False\n"
        )
        ast = parse(tokenize(source))
        analyze(ast)

    def test_xox_all_branches_returning_is_valid(self):
        source = (
            "fn f(t: XoX) -> XoX:\n"
            "    if t:\n"
            "        return True\n"
            "    xen:\n"
            "        return Unknown\n"
            "    else:\n"
            "        return False\n"
        )
        ast = parse(tokenize(source))
        analyze(ast)

    def test_xox_xen_ignore_missing_return_error(self):
        source = (
            "fn f(t: XoX) -> XoX:\n"
            "    if t:\n"
            "        return True\n"
            "    xen:\n"
            "        ignore\n"
            "    else:\n"
            "        return False\n"
        )
        ast = parse(tokenize(source))
        with self.assertRaises(MissingReturnError) as ctx:
            analyze(ast)
        self.assertIn("does not return a value on every control-flow path", str(ctx.exception))

    def test_xox_xen_ignore_with_subsequent_return_is_valid(self):
        source = (
            "fn f(t: XoX) -> XoX:\n"
            "    if t:\n"
            "        return True\n"
            "    xen:\n"
            "        ignore\n"
            "    else:\n"
            "        return False\n"
            "    return Unknown\n"
        )
        ast = parse(tokenize(source))
        analyze(ast)

    def test_xox_non_returning_xen_block_missing_return_error(self):
        source = (
            "fn f(t: XoX) -> XoX:\n"
            "    flag = True\n"
            "    if t:\n"
            "        return True\n"
            "    xen:\n"
            "        flag = False\n"
            "    else:\n"
            "        return False\n"
        )
        ast = parse(tokenize(source))
        with self.assertRaises(MissingReturnError) as ctx:
            analyze(ast)
        self.assertIn("does not return a value on every control-flow path", str(ctx.exception))

    def test_nested_conditionals_definite_return(self):
        # Valid nested return
        source1 = (
            "fn f(a: Bool, b: Bool) -> Bool:\n"
            "    if a:\n"
            "        if b:\n"
            "            return True\n"
            "        else:\n"
            "            return False\n"
            "    else:\n"
            "        return False\n"
        )
        ast1 = parse(tokenize(source1))
        analyze(ast1)

        # Incomplete nested return
        source2 = (
            "fn f(a: Bool, b: Bool) -> Bool:\n"
            "    if a:\n"
            "        if b:\n"
            "            return True\n"
            "    else:\n"
            "        return False\n"
        )
        ast2 = parse(tokenize(source2))
        with self.assertRaises(MissingReturnError):
            analyze(ast2)

    def test_pass_and_assignments_do_not_satisfy_return(self):
        source = (
            "fn f() -> Bool:\n"
            "    x = True\n"
            "    pass\n"
        )
        ast = parse(tokenize(source))
        with self.assertRaises(MissingReturnError):
            analyze(ast)

    def test_diagnostic_precedence_type_error_over_missing_return(self):
        # Incompatible return type raises TypeError, not MissingReturnError
        source = (
            "fn f(t: XoX) -> XoX:\n"
            "    return t == Unknown\n"
        )
        ast = parse(tokenize(source))
        with self.assertRaises(TypeError):
            analyze(ast)

    def test_diagnostic_precedence_exhaustiveness_over_missing_return(self):
        # Missing xen on XoX conditional raises ExhaustivenessError, not MissingReturnError
        source = (
            "fn f(t: XoX) -> XoX:\n"
            "    if t:\n"
            "        return True\n"
            "    else:\n"
            "        return False\n"
        )
        ast = parse(tokenize(source))
        with self.assertRaises(ExhaustivenessError):
            analyze(ast)

    def test_unannotated_function_does_not_require_definite_return(self):
        source = (
            "fn f(b: Bool):\n"
            "    if b:\n"
            "        return True\n"
        )
        ast = parse(tokenize(source))
        analyze(ast)



if __name__ == "__main__":
    unittest.main()
