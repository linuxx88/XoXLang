"""Unit tests for XoX (X-o-X) function definition lowering."""
import unittest
from xoxlang.lexer import tokenize
from xoxlang.parser import parse
from xoxlang.semantic import analyze
from xoxlang.lowering import lower_statement, map_identifier
from xoxlang.runtime import XoX, xox_not, xox_and, xox_or


class TestXoXLoweringFunctions(unittest.TestCase):
    def test_zero_parameter_function_lowering(self):
        source = (
            "fn f() -> Bool:\n"
            "    return True\n"
        )
        ast = parse(tokenize(source))
        sem = analyze(ast)
        lowered = lower_statement(ast.statements[0], sem.result)

        scope = {}
        exec("\n".join(lowered), scope)
        fn_mapped = map_identifier("f")
        self.assertIn(fn_mapped, scope)
        self.assertIs(scope[fn_mapped](), True)

    def test_typed_parameter_and_order_preservation(self):
        source = (
            "fn test_params(a: Bool, b: XoX) -> Bool:\n"
            "    return a\n"
        )
        ast = parse(tokenize(source))
        sem = analyze(ast)
        lowered = lower_statement(ast.statements[0], sem.result)

        # Check parameter signature
        param_a = map_identifier("a")
        param_b = map_identifier("b")
        fn_name = map_identifier("test_params")
        self.assertEqual(lowered[0], f"def {fn_name}({param_a}, {param_b}):")

        scope = {"XoX": XoX}
        exec("\n".join(lowered), scope)
        self.assertIs(scope[fn_name](True, XoX.UNKNOWN), True)

    def test_direct_xox_return(self):
        source = (
            "fn make_xox() -> XoX:\n"
            "    return True\n"
        )
        ast = parse(tokenize(source))
        sem = analyze(ast)
        lowered = lower_statement(ast.statements[0], sem.result)

        scope = {"XoX": XoX}
        exec("\n".join(lowered), scope)
        fn_name = map_identifier("make_xox")
        self.assertIs(scope[fn_name](), XoX.TRUE)

    def test_equality_return_from_function(self):
        source = (
            "fn is_unknown(t: XoX) -> Bool:\n"
            "    return t == Unknown\n"
        )
        ast = parse(tokenize(source))
        sem = analyze(ast)
        lowered = lower_statement(ast.statements[0], sem.result)

        scope = {"XoX": XoX}
        exec("\n".join(lowered), scope)
        fn_name = map_identifier("is_unknown")
        self.assertIs(scope[fn_name](XoX.UNKNOWN), True)
        self.assertIs(scope[fn_name](XoX.TRUE), False)

    def test_function_with_xox_conditional(self):
        source = (
            "fn classify(t: XoX) -> XoX:\n"
            "    if t:\n"
            "        return True\n"
            "    xen:\n"
            "        return Unknown\n"
            "    else:\n"
            "        return False\n"
        )
        ast = parse(tokenize(source))
        sem = analyze(ast)
        lowered = lower_statement(ast.statements[0], sem.result)

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
        }
        exec("\n".join(lowered), scope)
        fn_name = map_identifier("classify")
        self.assertIs(scope[fn_name](XoX.TRUE), XoX.TRUE)
        self.assertIs(scope[fn_name](XoX.UNKNOWN), XoX.UNKNOWN)
        self.assertIs(scope[fn_name](XoX.FALSE), XoX.FALSE)

    def test_function_with_xen_ignore_fallthrough(self):
        source = (
            "fn fallthrough_func(t: XoX) -> XoX:\n"
            "    if t:\n"
            "        return True\n"
            "    xen:\n"
            "        ignore\n"
            "    else:\n"
            "        return False\n"
            "    return Unknown\n"
        )
        ast = parse(tokenize(source))
        sem = analyze(ast)
        lowered = lower_statement(ast.statements[0], sem.result)

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
        }
        exec("\n".join(lowered), scope)
        fn_name = map_identifier("fallthrough_func")
        self.assertIs(scope[fn_name](XoX.UNKNOWN), XoX.UNKNOWN)

    def test_keyword_and_runtime_shadowing_function_names(self):
        # Function named 'def' with parameter named 'XoX'
        source = (
            "fn def(XoX: Bool) -> Bool:\n"
            "    return XoX\n"
        )
        ast = parse(tokenize(source))
        sem = analyze(ast)
        lowered = lower_statement(ast.statements[0], sem.result)

        scope = {"XoX": XoX}
        exec("\n".join(lowered), scope)
        fn_name = map_identifier("def")
        self.assertIs(scope[fn_name](True), True)
        self.assertIs(scope["XoX"], XoX)  # Runtime XoX is not shadowed!




if __name__ == "__main__":
    unittest.main()
