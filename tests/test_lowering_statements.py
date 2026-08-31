"""Unit tests for XoX (X-o-X) simple statement lowering."""
import unittest
from xoxlang.lexer import tokenize
from xoxlang.parser import parse
from xoxlang.semantic import analyze
from xoxlang.lowering import StatementLowerer, lower_statement, map_identifier
from xoxlang.runtime import XoX, xox_not, xox_and, xox_or


class TestXoXLoweringStatements(unittest.TestCase):
    def test_inferred_and_annotated_assignments(self):
        # Inferred Bool
        ast_b = parse(tokenize("x = True\n"))
        sem_b = analyze(ast_b)
        lowered_b = lower_statement(ast_b.statements[0], sem_b.result)
        self.assertEqual(lowered_b, [f"{map_identifier('x')} = True"])

        # Annotated XoX -> lowered to XoX.TRUE
        ast_t = parse(tokenize("x: XoX = True\n"))
        sem_t = analyze(ast_t)
        lowered_t = lower_statement(ast_t.statements[0], sem_t.result)
        self.assertEqual(lowered_t, [f"{map_identifier('x')} = XoX.TRUE"])

    def test_reassignment_same_target(self):
        ast = parse(tokenize("x = True\nx = False\n"))
        sem = analyze(ast)
        lowered1 = lower_statement(ast.statements[0], sem.result)
        lowered2 = lower_statement(ast.statements[1], sem.result)
        self.assertEqual(lowered1, [f"{map_identifier('x')} = True"])
        self.assertEqual(lowered2, [f"{map_identifier('x')} = False"])

    def test_assignment_with_xox_logical_preludes(self):
        ast = parse(tokenize("t: XoX = Unknown\nx: XoX = False AND t\n"))
        sem = analyze(ast)
        lowered = lower_statement(ast.statements[1], sem.result)

        # Check execution of assignment statement
        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("t"): XoX.UNKNOWN,
        }
        exec("\n".join(lowered), scope)
        self.assertIs(scope[map_identifier("x")], XoX.FALSE)

    def test_expr_statement_lowering(self):
        ast = parse(tokenize("t: XoX = Unknown\nNOT t\n"))
        sem = analyze(ast)
        lowered = lower_statement(ast.statements[1], sem.result)
        self.assertEqual(lowered, [f"xox_not({map_identifier('t')})"])

    def test_pass_and_ignore_statements(self):
        ast_pass = parse(tokenize("pass\n"))
        sem_pass = analyze(ast_pass)
        self.assertEqual(lower_statement(ast_pass.statements[0], sem_pass.result), ["pass"])

        # IgnoreStatement
        from xoxlang.ast import IgnoreStatement
        ignore_stmt = IgnoreStatement()
        self.assertEqual(lower_statement(ignore_stmt, sem_pass.result), ["pass"])

    def test_return_statement_bool_and_xox(self):
        # Return Bool
        source_b = "fn f() -> Bool:\n    return True\n"
        ast_b = parse(tokenize(source_b))
        sem_b = analyze(ast_b)
        ret_b = ast_b.statements[0].body.statements[0]
        self.assertEqual(lower_statement(ret_b, sem_b.result), ["return True"])

        # Return XoX -> lowered to XoX.TRUE
        source_t = "fn f() -> XoX:\n    return True\n"
        ast_t = parse(tokenize(source_t))
        sem_t = analyze(ast_t)
        ret_t = ast_t.statements[0].body.statements[0]
        self.assertEqual(lower_statement(ret_t, sem_t.result), ["return XoX.TRUE"])

    def test_return_statement_with_logical_preludes(self):
        source = (
            "fn f(t: XoX) -> XoX:\n"
            "    return True OR t\n"
        )
        ast = parse(tokenize(source))
        sem = analyze(ast)
        ret_stmt = ast.statements[0].body.statements[0]
        lowered = lower_statement(ret_stmt, sem.result)

        # Wrap in python function and execute
        func_lines = ["def test_fn():", *[f"    {line}" for line in lowered]]
        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("t"): XoX.UNKNOWN,
        }
        exec("\n".join(func_lines), scope)
        result = scope["test_fn"]()
        self.assertIs(result, XoX.TRUE)

    def test_keyword_and_runtime_shadowing_targets(self):
        # Target named 'class'
        ast_kw = parse(tokenize("class: Bool = True\n"))
        sem_kw = analyze(ast_kw)
        lowered_kw = lower_statement(ast_kw.statements[0], sem_kw.result)
        self.assertEqual(lowered_kw, [f"{map_identifier('class')} = True"])
        exec("\n".join(lowered_kw), {})

        # Target named 'XoX'
        ast_rt = parse(tokenize("XoX: Bool = True\n"))
        sem_rt = analyze(ast_rt)
        lowered_rt = lower_statement(ast_rt.statements[0], sem_rt.result)
        self.assertEqual(lowered_rt, [f"{map_identifier('XoX')} = True"])
        scope = {"XoX": XoX}
        exec("\n".join(lowered_rt), scope)
        self.assertIs(scope["XoX"], XoX)  # Runtime XoX is not shadowed!




if __name__ == "__main__":
    unittest.main()
