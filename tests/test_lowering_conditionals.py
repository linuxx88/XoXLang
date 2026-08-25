"""Unit tests for XoX (X-o-X) conditional statement lowering."""
import unittest
from trool.lexer import tokenize
from trool.parser import parse
from trool.semantic import analyze
from trool.lowering import lower_statement, map_identifier
from trool.runtime import XoX, xox_not, xox_and, xox_or


class TestXoXLoweringConditionals(unittest.TestCase):
    def test_bool_conditional_execution(self):
        # Bool if-only (True condition)
        src_true = "if True:\n    x = True\n"
        ast_t = parse(tokenize(src_true))
        sem_t = analyze(ast_t)
        lowered_t = lower_statement(ast_t.statements[0], sem_t.result)
        scope_t = {}
        exec("\n".join(lowered_t), scope_t)
        self.assertIs(scope_t[map_identifier("x")], True)

        # Bool if-only (False condition)
        src_false = "if False:\n    x = True\n"
        ast_f = parse(tokenize(src_false))
        sem_f = analyze(ast_f)
        lowered_f = lower_statement(ast_f.statements[0], sem_f.result)
        scope_f = {}
        exec("\n".join(lowered_f), scope_f)
        self.assertNotIn(map_identifier("x"), scope_f)

        # Bool if/else
        src_ifelse = "if False:\n    x = True\nelse:\n    x = False\n"
        ast_ie = parse(tokenize(src_ifelse))
        sem_ie = analyze(ast_ie)
        lowered_ie = lower_statement(ast_ie.statements[0], sem_ie.result)
        scope_ie = {}
        exec("\n".join(lowered_ie), scope_ie)
        self.assertIs(scope_ie[map_identifier("x")], False)

    def test_xox_conditional_three_way_dispatch(self):
        src = (
            "status: XoX = Unknown\n"
            "if status:\n"
            "    res = True\n"
            "xen:\n"
            "    res = False\n"
            "    status\n"
            "else:\n"
            "    res = False\n"
        )
        ast = parse(tokenize(src))
        sem = analyze(ast)
        cond_stmt = ast.statements[1]
        lowered = lower_statement(cond_stmt, sem.result)

        for state, expected_branch in [
            (XoX.TRUE, "true"),
            (XoX.UNKNOWN, "xen"),
            (XoX.FALSE, "else"),
        ]:
            with self.subTest(state=state):
                scope = {
                    "XoX": XoX,
                    "xox_and": xox_and,
                    "xox_not": xox_not,
                    "xox_or": xox_or,
                    map_identifier("status"): state,
                    "selected": None,
                }
                # Track which branch ran by inserting markers
                test_lines = []
                for line in lowered:
                    test_lines.append(line)
                    if "is XoX.TRUE:" in line:
                        test_lines.append("    selected = 'true'")
                    elif "is XoX.UNKNOWN:" in line:
                        test_lines.append("    selected = 'xen'")
                    elif "is XoX.FALSE:" in line:
                        test_lines.append("    selected = 'else'")
                exec("\n".join(test_lines), scope)
                self.assertEqual(scope["selected"], expected_branch)

    def test_xox_xen_ignore_execution(self):
        src = (
            "status: XoX = Unknown\n"
            "if status:\n"
            "    res = True\n"
            "xen:\n"
            "    ignore\n"
            "else:\n"
            "    res = False\n"
        )
        ast = parse(tokenize(src))
        sem = analyze(ast)
        cond_stmt = ast.statements[1]
        lowered = lower_statement(cond_stmt, sem.result)

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("status"): XoX.UNKNOWN,
        }
        exec("\n".join(lowered), scope)
        # res was not set because xen: ignore executed as no-op
        self.assertNotIn(map_identifier("res"), scope)

    def test_nested_conditionals_execution(self):
        src = (
            "a: Bool = True\n"
            "b: XoX = Unknown\n"
            "if a:\n"
            "    if b:\n"
            "        x = True\n"
            "    xen:\n"
            "        x = False\n"
            "    else:\n"
            "        x = False\n"
            "else:\n"
            "    x = False\n"
        )
        ast = parse(tokenize(src))
        sem = analyze(ast)
        cond_stmt = ast.statements[2]
        lowered = lower_statement(cond_stmt, sem.result)

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("a"): True,
            map_identifier("b"): XoX.UNKNOWN,
        }
        exec("\n".join(lowered), scope)
        self.assertIs(scope[map_identifier("x")], False)

    def test_invalid_runtime_condition_state_fails(self):
        src = (
            "status: XoX = Unknown\n"
            "if status:\n"
            "    pass\n"
            "xen:\n"
            "    ignore\n"
            "else:\n"
            "    pass\n"
        )
        ast = parse(tokenize(src))
        sem = analyze(ast)
        cond_stmt = ast.statements[1]
        lowered = lower_statement(cond_stmt, sem.result)

        # Execute with an invalid (non-XoX) state
        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("status"): "invalid_state",
        }
        with self.assertRaises(TypeError):
            exec("\n".join(lowered), scope)

    def test_missing_conditional_kind_fails_explicitly(self):
        from trool.ast import ConditionalStatement, LiteralExpr
        from trool.semantic import SemanticResult
        dummy = ConditionalStatement()
        empty_sem = SemanticResult()

        with self.assertRaises(KeyError):
            lower_statement(dummy, empty_sem)



if __name__ == "__main__":
    unittest.main()
