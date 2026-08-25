"""Unit tests for XoX (X-o-X) expression lowering."""
import unittest
from trool.lexer import tokenize
from trool.parser import parse
from trool.semantic import analyze
from trool.lowering import ExpressionLowerer, lower_expression, map_identifier, LoweredExpr
from trool.runtime import XoX, xox_not, xox_and, xox_or


class TestXoXExpressionLowering(unittest.TestCase):
    def test_literal_lowering_bool_and_xox(self):
        # Bool True / False
        ast_b = parse(tokenize("True\n"))
        sem_b = analyze(ast_b)
        lowered_b = lower_expression(ast_b.statements[0].expr, sem_b.result)
        self.assertEqual(lowered_b.expr, "True")

        # XoX True / False / Unknown
        ast_t = parse(tokenize("x: XoX = True\n"))
        sem_t = analyze(ast_t)
        lowered_t = lower_expression(ast_t.statements[0].value, sem_t.result)
        self.assertEqual(lowered_t.expr, "XoX.TRUE")

        ast_u = parse(tokenize("Unknown\n"))
        sem_u = analyze(ast_u)
        lowered_u = lower_expression(ast_u.statements[0].expr, sem_u.result)
        self.assertEqual(lowered_u.expr, "XoX.UNKNOWN")

    def test_not_lowering(self):
        # Bool NOT
        ast_b = parse(tokenize("NOT True\n"))
        sem_b = analyze(ast_b)
        lowered_b = lower_expression(ast_b.statements[0].expr, sem_b.result)
        self.assertEqual(lowered_b.expr, "(not True)")

        # XoX NOT
        ast_t = parse(tokenize("t: XoX = Unknown\nNOT t\n"))
        sem_t = analyze(ast_t)
        lowered_t = lower_expression(ast_t.statements[1].expr, sem_t.result)
        self.assertEqual(lowered_t.expr, f"xox_not({map_identifier('t')})")

    def test_bool_and_or_lowering(self):
        # Simple Bool AND
        ast_and = parse(tokenize("True AND False\n"))
        sem_and = analyze(ast_and)
        lowered_and = lower_expression(ast_and.statements[0].expr, sem_and.result)
        self.assertEqual(lowered_and.expr, "(True and False)")

        # Simple Bool OR
        ast_or = parse(tokenize("True OR False\n"))
        sem_or = analyze(ast_or)
        lowered_or = lower_expression(ast_or.statements[0].expr, sem_or.result)
        self.assertEqual(lowered_or.expr, "(True or False)")

    def test_xox_and_short_circuit_execution(self):
        ast = parse(tokenize("t: XoX = Unknown\nFalse AND t\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[1].expr, sem.result)

        # Build python script to execute and verify side-effect skipping
        code_lines = [
            "evaluated_right = False",
            "def get_right():",
            "    global evaluated_right",
            "    evaluated_right = True",
            "    return XoX.TRUE",
            *lowered.prelude,
        ]
        # Replace right operand with get_right() to trace evaluation
        for i, line in enumerate(code_lines):
            if "xox_and(" in line:
                code_lines[i] = line.replace(f", {map_identifier('t')})", ", get_right())")

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("t"): XoX.UNKNOWN,
        }
        exec("\n".join(code_lines), scope)
        self.assertFalse(scope["evaluated_right"])
        res_val = scope[lowered.expr]
        self.assertIs(res_val, XoX.FALSE)

    def test_xox_or_short_circuit_execution(self):
        ast = parse(tokenize("t: XoX = Unknown\nTrue OR t\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[1].expr, sem.result)

        code_lines = [
            "evaluated_right = False",
            "def get_right():",
            "    global evaluated_right",
            "    evaluated_right = True",
            "    return XoX.FALSE",
            *lowered.prelude,
        ]
        for i, line in enumerate(code_lines):
            if "xox_or(" in line:
                code_lines[i] = line.replace(f", {map_identifier('t')})", ", get_right())")

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("t"): XoX.UNKNOWN,
        }
        exec("\n".join(code_lines), scope)
        self.assertFalse(scope["evaluated_right"])
        res_val = scope[lowered.expr]
        self.assertIs(res_val, XoX.TRUE)

    def test_equality_lowering(self):
        # Bool equality
        ast_b = parse(tokenize("True == False\n"))
        sem_b = analyze(ast_b)
        lowered_b = lower_expression(ast_b.statements[0].expr, sem_b.result)
        self.assertEqual(lowered_b.expr, "(True == False)")

        # XoX equality uses identity 'is'
        ast_t = parse(tokenize("True == Unknown\n"))
        sem_t = analyze(ast_t)
        lowered_t = lower_expression(ast_t.statements[0].expr, sem_t.result)
        self.assertEqual(lowered_t.expr, "(XoX.TRUE is XoX.UNKNOWN)")

        # Execute lowered XoX equality
        scope = {"XoX": XoX}
        res = eval(lowered_t.expr, scope)
        self.assertIs(res, False)

    def test_missing_metadata_fails_explicitly(self):
        ast = parse(tokenize("True\n"))
        # Do not analyze ast
        from trool.semantic import SemanticResult
        empty_sem = SemanticResult()

        with self.assertRaises(KeyError):
            lower_expression(ast.statements[0].expr, empty_sem)



if __name__ == "__main__":
    unittest.main()
