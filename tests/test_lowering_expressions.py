"""Unit tests for XoX (X-o-X) expression lowering."""
import unittest
from xoxlang.lexer import tokenize
from xoxlang.parser import parse
from xoxlang.semantic import analyze
from xoxlang.lowering import ExpressionLowerer, lower_expression, map_identifier, LoweredExpr
from xoxlang.runtime import XoX, xox_not, xox_and, xox_or


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

    def test_trace_preservation_and_left_operand_executes_once(self):
        ast = parse(tokenize("t: XoX = Unknown\nt AND False\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[1].expr, sem.result)

        code_lines = [
            "trace = []",
            "def eval_left():",
            "    trace.append('left_eval')",
            "    return XoX.UNKNOWN",
            *lowered.prelude,
        ]
        for i, line in enumerate(code_lines):
            if f"= {map_identifier('t')}" in line:
                code_lines[i] = line.replace(f"= {map_identifier('t')}", "= eval_left()")

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("t"): XoX.UNKNOWN,
        }
        exec("\n".join(code_lines), scope)

        self.assertEqual(scope["trace"], ["left_eval"])
        res_val = scope[lowered.expr]
        self.assertIs(res_val, XoX.FALSE)

    def test_trace_preservation_or_left_operand_executes_once(self):
        ast = parse(tokenize("t: XoX = Unknown\nt OR True\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[1].expr, sem.result)

        code_lines = [
            "trace = []",
            "def eval_left():",
            "    trace.append('left_eval')",
            "    return XoX.UNKNOWN",
            *lowered.prelude,
        ]
        for i, line in enumerate(code_lines):
            if f"= {map_identifier('t')}" in line:
                code_lines[i] = line.replace(f"= {map_identifier('t')}", "= eval_left()")

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("t"): XoX.UNKNOWN,
        }
        exec("\n".join(code_lines), scope)

        self.assertEqual(scope["trace"], ["left_eval"])
        res_val = scope[lowered.expr]
        self.assertIs(res_val, XoX.TRUE)

    def test_left_to_right_evaluation_order_and(self):
        ast = parse(tokenize("a: XoX = True\nb: XoX = Unknown\na AND b\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[2].expr, sem.result)

        code_lines = [
            "trace = []",
            "def eval_A():",
            "    trace.append('eval_A')",
            "    return XoX.TRUE",
            "def eval_B():",
            "    trace.append('eval_B')",
            "    return XoX.UNKNOWN",
            *lowered.prelude,
        ]
        for i, line in enumerate(code_lines):
            if f"= {map_identifier('a')}" in line:
                code_lines[i] = line.replace(f"= {map_identifier('a')}", "= eval_A()")
            if f", {map_identifier('b')})" in line:
                code_lines[i] = line.replace(f", {map_identifier('b')})", ", eval_B())")

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("a"): XoX.TRUE,
            map_identifier("b"): XoX.UNKNOWN,
        }
        exec("\n".join(code_lines), scope)

        self.assertEqual(scope["trace"], ["eval_A", "eval_B"])
        res_val = scope[lowered.expr]
        self.assertIs(res_val, XoX.UNKNOWN)

    def test_left_to_right_evaluation_order_or(self):
        ast = parse(tokenize("a: XoX = False\nb: XoX = Unknown\na OR b\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[2].expr, sem.result)

        code_lines = [
            "trace = []",
            "def eval_A():",
            "    trace.append('eval_A')",
            "    return XoX.FALSE",
            "def eval_B():",
            "    trace.append('eval_B')",
            "    return XoX.UNKNOWN",
            *lowered.prelude,
        ]
        for i, line in enumerate(code_lines):
            if f"= {map_identifier('a')}" in line:
                code_lines[i] = line.replace(f"= {map_identifier('a')}", "= eval_A()")
            if f", {map_identifier('b')})" in line:
                code_lines[i] = line.replace(f", {map_identifier('b')})", ", eval_B())")

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("a"): XoX.FALSE,
            map_identifier("b"): XoX.UNKNOWN,
        }
        exec("\n".join(code_lines), scope)

        self.assertEqual(scope["trace"], ["eval_A", "eval_B"])
        res_val = scope[lowered.expr]
        self.assertIs(res_val, XoX.UNKNOWN)

    def test_short_circuit_and_masks_right_operand_exception(self):
        ast = parse(tokenize("t: XoX = Unknown\nFalse AND t\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[1].expr, sem.result)

        code_lines = [
            "right_call_count = 0",
            "def raising_expr():",
            "    global right_call_count",
            "    right_call_count += 1",
            "    raise RuntimeError('Right operand executed unexpectedly')",
            *lowered.prelude,
        ]
        for i, line in enumerate(code_lines):
            if f", {map_identifier('t')})" in line:
                code_lines[i] = line.replace(f", {map_identifier('t')})", ", raising_expr())")

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            "RuntimeError": RuntimeError,
            map_identifier("t"): XoX.UNKNOWN,
        }
        exec("\n".join(code_lines), scope)

        self.assertEqual(scope["right_call_count"], 0)
        res_val = scope[lowered.expr]
        self.assertIs(res_val, XoX.FALSE)

    def test_short_circuit_or_masks_right_operand_exception(self):
        ast = parse(tokenize("t: XoX = Unknown\nTrue OR t\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[1].expr, sem.result)

        code_lines = [
            "right_call_count = 0",
            "def raising_expr():",
            "    global right_call_count",
            "    right_call_count += 1",
            "    raise RuntimeError('Right operand executed unexpectedly')",
            *lowered.prelude,
        ]
        for i, line in enumerate(code_lines):
            if f", {map_identifier('t')})" in line:
                code_lines[i] = line.replace(f", {map_identifier('t')})", ", raising_expr())")

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            "RuntimeError": RuntimeError,
            map_identifier("t"): XoX.UNKNOWN,
        }
        exec("\n".join(code_lines), scope)

        self.assertEqual(scope["right_call_count"], 0)
        res_val = scope[lowered.expr]
        self.assertIs(res_val, XoX.TRUE)

    def test_chained_and_evaluates_each_reached_operand_exactly_once(self):
        ast = parse(tokenize("a: XoX = True\nb: XoX = True\nc: XoX = Unknown\na AND b AND c\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[3].expr, sem.result)

        code_lines = [
            "trace = []",
            "def eval_A():",
            "    trace.append('eval_A')",
            "    return XoX.TRUE",
            "def eval_B():",
            "    trace.append('eval_B')",
            "    return XoX.TRUE",
            "def eval_C():",
            "    trace.append('eval_C')",
            "    return XoX.UNKNOWN",
            *lowered.prelude,
        ]
        for i, line in enumerate(code_lines):
            if f"= {map_identifier('a')}" in line:
                code_lines[i] = line.replace(f"= {map_identifier('a')}", "= eval_A()")
            if f", {map_identifier('b')})" in line:
                code_lines[i] = line.replace(f", {map_identifier('b')})", ", eval_B())")
            if f", {map_identifier('c')})" in line:
                code_lines[i] = line.replace(f", {map_identifier('c')})", ", eval_C())")

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("a"): XoX.TRUE,
            map_identifier("b"): XoX.TRUE,
            map_identifier("c"): XoX.UNKNOWN,
        }
        exec("\n".join(code_lines), scope)

        self.assertEqual(scope["trace"], ["eval_A", "eval_B", "eval_C"])
        self.assertEqual(scope["trace"].count("eval_A"), 1)
        self.assertEqual(scope["trace"].count("eval_B"), 1)
        self.assertEqual(scope["trace"].count("eval_C"), 1)
        res_val = scope[lowered.expr]
        self.assertIs(res_val, XoX.UNKNOWN)

    def test_chained_or_evaluates_each_reached_operand_exactly_once(self):
        ast = parse(tokenize("a: XoX = False\nb: XoX = False\nc: XoX = Unknown\na OR b OR c\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[3].expr, sem.result)

        code_lines = [
            "trace = []",
            "def eval_A():",
            "    trace.append('eval_A')",
            "    return XoX.FALSE",
            "def eval_B():",
            "    trace.append('eval_B')",
            "    return XoX.FALSE",
            "def eval_C():",
            "    trace.append('eval_C')",
            "    return XoX.UNKNOWN",
            *lowered.prelude,
        ]
        for i, line in enumerate(code_lines):
            if f"= {map_identifier('a')}" in line:
                code_lines[i] = line.replace(f"= {map_identifier('a')}", "= eval_A()")
            if f", {map_identifier('b')})" in line:
                code_lines[i] = line.replace(f", {map_identifier('b')})", ", eval_B())")
            if f", {map_identifier('c')})" in line:
                code_lines[i] = line.replace(f", {map_identifier('c')})", ", eval_C())")

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("a"): XoX.FALSE,
            map_identifier("b"): XoX.FALSE,
            map_identifier("c"): XoX.UNKNOWN,
        }
        exec("\n".join(code_lines), scope)

        self.assertEqual(scope["trace"], ["eval_A", "eval_B", "eval_C"])
        self.assertEqual(scope["trace"].count("eval_A"), 1)
        self.assertEqual(scope["trace"].count("eval_B"), 1)
        self.assertEqual(scope["trace"].count("eval_C"), 1)
        res_val = scope[lowered.expr]
        self.assertIs(res_val, XoX.UNKNOWN)

    def test_left_operand_exception_aborts_and_skips_right(self):
        ast = parse(tokenize("a: XoX = Unknown\nb: XoX = Unknown\na AND b\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[2].expr, sem.result)

        code_lines = [
            "right_call_count = 0",
            "class LeftOperandError(Exception): pass",
            "def raising_left():",
            "    raise LeftOperandError('Left evaluation failed')",
            "def effect_right():",
            "    global right_call_count",
            "    right_call_count += 1",
            "    return XoX.TRUE",
            *lowered.prelude,
        ]
        for i, line in enumerate(code_lines):
            if f"= {map_identifier('a')}" in line:
                code_lines[i] = line.replace(f"= {map_identifier('a')}", "= raising_left()")
            if f", {map_identifier('b')})" in line:
                code_lines[i] = line.replace(f", {map_identifier('b')})", ", effect_right())")

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("a"): XoX.UNKNOWN,
            map_identifier("b"): XoX.UNKNOWN,
        }
        with self.assertRaises(Exception) as ctx:
            exec("\n".join(code_lines), scope)

        self.assertEqual(type(ctx.exception).__name__, "LeftOperandError")
        self.assertEqual(str(ctx.exception), "Left evaluation failed")
        self.assertEqual(scope["right_call_count"], 0)

    def test_left_operand_exception_aborts_and_skips_right_or(self):
        ast = parse(tokenize("a: XoX = Unknown\nb: XoX = Unknown\na OR b\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[2].expr, sem.result)

        code_lines = [
            "right_call_count = 0",
            "class LeftOperandError(Exception): pass",
            "def raising_left():",
            "    raise LeftOperandError('Left evaluation failed in OR')",
            "def effect_right():",
            "    global right_call_count",
            "    right_call_count += 1",
            "    return XoX.FALSE",
            *lowered.prelude,
        ]
        for i, line in enumerate(code_lines):
            if f"= {map_identifier('a')}" in line:
                code_lines[i] = line.replace(f"= {map_identifier('a')}", "= raising_left()")
            if f", {map_identifier('b')})" in line:
                code_lines[i] = line.replace(f", {map_identifier('b')})", ", effect_right())")

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("a"): XoX.UNKNOWN,
            map_identifier("b"): XoX.UNKNOWN,
        }
        with self.assertRaises(Exception) as ctx:
            exec("\n".join(code_lines), scope)

        self.assertEqual(type(ctx.exception).__name__, "LeftOperandError")
        self.assertEqual(str(ctx.exception), "Left evaluation failed in OR")
        self.assertEqual(scope["right_call_count"], 0)

    def test_non_commutative_observable_equivalence_and(self):
        # Expression A: t AND False (left operand t executes)
        ast_a = parse(tokenize("t: XoX = Unknown\nt AND False\n"))
        sem_a = analyze(ast_a)
        lowered_a = lower_expression(ast_a.statements[1].expr, sem_a.result)

        code_lines_a = [
            "trace_a = []",
            "def eval_t_a():",
            "    trace_a.append('effect_t')",
            "    return XoX.UNKNOWN",
            *lowered_a.prelude,
        ]
        for i, line in enumerate(code_lines_a):
            if f"= {map_identifier('t')}" in line:
                code_lines_a[i] = line.replace(f"= {map_identifier('t')}", "= eval_t_a()")

        scope_a = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("t"): XoX.UNKNOWN,
        }
        exec("\n".join(code_lines_a), scope_a)
        res_a = scope_a[lowered_a.expr]
        trace_a = scope_a["trace_a"]

        # Expression B: False AND t (left operand False short-circuits, skipping t)
        ast_b = parse(tokenize("t: XoX = Unknown\nFalse AND t\n"))
        sem_b = analyze(ast_b)
        lowered_b = lower_expression(ast_b.statements[1].expr, sem_b.result)

        code_lines_b = [
            "trace_b = []",
            "def eval_t_b():",
            "    trace_b.append('effect_t')",
            "    return XoX.UNKNOWN",
            *lowered_b.prelude,
        ]
        for i, line in enumerate(code_lines_b):
            if f", {map_identifier('t')})" in line:
                code_lines_b[i] = line.replace(f", {map_identifier('t')})", ", eval_t_b())")

        scope_b = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("t"): XoX.UNKNOWN,
        }
        exec("\n".join(code_lines_b), scope_b)
        res_b = scope_b[lowered_b.expr]
        trace_b = scope_b["trace_b"]

        # Assert K3 value equivalence
        self.assertIs(res_a, XoX.FALSE)
        self.assertIs(res_b, XoX.FALSE)

        # Assert observable trace non-equivalence
        self.assertEqual(trace_a, ["effect_t"])
        self.assertEqual(trace_b, [])
        self.assertNotEqual(trace_a, trace_b)

    def test_non_commutative_observable_equivalence_or(self):
        # Expression A: t OR True (left operand t executes)
        ast_a = parse(tokenize("t: XoX = Unknown\nt OR True\n"))
        sem_a = analyze(ast_a)
        lowered_a = lower_expression(ast_a.statements[1].expr, sem_a.result)

        code_lines_a = [
            "trace_a = []",
            "def eval_t_a():",
            "    trace_a.append('effect_t')",
            "    return XoX.UNKNOWN",
            *lowered_a.prelude,
        ]
        for i, line in enumerate(code_lines_a):
            if f"= {map_identifier('t')}" in line:
                code_lines_a[i] = line.replace(f"= {map_identifier('t')}", "= eval_t_a()")

        scope_a = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("t"): XoX.UNKNOWN,
        }
        exec("\n".join(code_lines_a), scope_a)
        res_a = scope_a[lowered_a.expr]
        trace_a = scope_a["trace_a"]

        # Expression B: True OR t (left operand True short-circuits, skipping t)
        ast_b = parse(tokenize("t: XoX = Unknown\nTrue OR t\n"))
        sem_b = analyze(ast_b)
        lowered_b = lower_expression(ast_b.statements[1].expr, sem_b.result)

        code_lines_b = [
            "trace_b = []",
            "def eval_t_b():",
            "    trace_b.append('effect_t')",
            "    return XoX.UNKNOWN",
            *lowered_b.prelude,
        ]
        for i, line in enumerate(code_lines_b):
            if f", {map_identifier('t')})" in line:
                code_lines_b[i] = line.replace(f", {map_identifier('t')})", ", eval_t_b())")

        scope_b = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("t"): XoX.UNKNOWN,
        }
        exec("\n".join(code_lines_b), scope_b)
        res_b = scope_b[lowered_b.expr]
        trace_b = scope_b["trace_b"]

        # Assert K3 value equivalence
        self.assertIs(res_a, XoX.TRUE)
        self.assertIs(res_b, XoX.TRUE)

        # Assert observable trace non-equivalence
        self.assertEqual(trace_a, ["effect_t"])
        self.assertEqual(trace_b, [])
        self.assertNotEqual(trace_a, trace_b)

    def test_mixed_operator_nesting_trace_preservation(self):
        ast = parse(tokenize("a: XoX = Unknown\nb: XoX = Unknown\n(False AND a) OR b\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[2].expr, sem.result)

        code_lines = [
            "trace = []",
            "def eval_A():",
            "    trace.append('effect_A')",
            "    return XoX.UNKNOWN",
            "def eval_B():",
            "    trace.append('effect_B')",
            "    return XoX.UNKNOWN",
            *lowered.prelude,
        ]
        for i, line in enumerate(code_lines):
            if f", {map_identifier('a')})" in line:
                code_lines[i] = line.replace(f", {map_identifier('a')})", ", eval_A())")
            if f", {map_identifier('b')})" in line:
                code_lines[i] = line.replace(f", {map_identifier('b')})", ", eval_B())")

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("a"): XoX.UNKNOWN,
            map_identifier("b"): XoX.UNKNOWN,
        }
        exec("\n".join(code_lines), scope)

        self.assertEqual(scope["trace"], ["effect_B"])
        self.assertEqual(scope["trace"].count("effect_A"), 0)
        self.assertEqual(scope["trace"].count("effect_B"), 1)
        res_val = scope[lowered.expr]
        self.assertIs(res_val, XoX.UNKNOWN)

    def test_missing_metadata_fails_explicitly(self):
        ast = parse(tokenize("True\n"))
        # Do not analyze ast
        from xoxlang.semantic import SemanticResult
        empty_sem = SemanticResult()

        with self.assertRaises(KeyError):
            lower_expression(ast.statements[0].expr, empty_sem)

    def test_inline_bool_conditional_true_and_false_runtime_execution(self):
        from xoxlang.compiler import compile_source
        source = (
            "c_true: Bool = True\n"
            "c_false: Bool = False\n"
            "res_t: Bool = True if c_true else False\n"
            "res_f: Bool = True if c_false else False\n"
        )
        code = compile_source(source)
        scope = {}
        exec(code, scope)
        self.assertIs(scope[map_identifier("res_t")], True)
        self.assertIs(scope[map_identifier("res_f")], False)

    def test_inline_xox_conditional_three_way_runtime_execution(self):
        from xoxlang.compiler import compile_source
        source = (
            "t: XoX = True\n"
            "u: XoX = Unknown\n"
            "f: XoX = False\n"
            "res_t: XoX = True if t xen Unknown else False\n"
            "res_u: XoX = True if u xen Unknown else False\n"
            "res_f: XoX = True if f xen Unknown else False\n"
            "res_b_t: Bool = True if t xen False else False\n"
            "res_b_u: Bool = True if u xen False else False\n"
            "res_b_f: Bool = True if f xen False else False\n"
        )
        code = compile_source(source)
        scope = {}
        exec(code, scope)
        self.assertIs(scope[map_identifier("res_t")], XoX.TRUE)
        self.assertIs(scope[map_identifier("res_u")], XoX.UNKNOWN)
        self.assertIs(scope[map_identifier("res_f")], XoX.FALSE)
        self.assertIs(scope[map_identifier("res_b_t")], True)
        self.assertIs(scope[map_identifier("res_b_u")], False)
        self.assertIs(scope[map_identifier("res_b_f")], False)

    def test_inline_conditional_condition_evaluated_exactly_once(self):
        ast = parse(tokenize("cond: XoX = Unknown\nres: XoX = True if cond xen Unknown else False\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[1].value, sem.result)

        code_lines = [
            "trace = []",
            "def eval_cond():",
            "    trace.append('cond_eval')",
            "    return XoX.UNKNOWN",
            *lowered.prelude,
        ]
        for i, line in enumerate(code_lines):
            if f"= {map_identifier('cond')}" in line:
                code_lines[i] = line.replace(f"= {map_identifier('cond')}", "= eval_cond()")

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("cond"): XoX.UNKNOWN,
        }
        exec("\n".join(code_lines), scope)
        self.assertEqual(scope["trace"], ["cond_eval"])
        self.assertIs(scope[lowered.expr], XoX.UNKNOWN)

    def test_inline_conditional_unselected_branch_side_effects_skipped(self):
        # Compile XoX inline conditional where condition is True
        ast = parse(tokenize("cond: XoX = True\nres: XoX = True if cond xen Unknown else False\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[1].value, sem.result)

        code_lines = [
            "trace = []",
            "def eval_true():",
            "    trace.append('branch_true')",
            "    return XoX.TRUE",
            "def eval_xen():",
            "    trace.append('branch_xen')",
            "    return XoX.UNKNOWN",
            "def eval_else():",
            "    trace.append('branch_else')",
            "    return XoX.FALSE",
            *lowered.prelude,
        ]
        for i, line in enumerate(code_lines):
            if "= XoX.TRUE" in line:
                code_lines[i] = line.replace("= XoX.TRUE", "= eval_true()")
            elif "= XoX.UNKNOWN" in line:
                code_lines[i] = line.replace("= XoX.UNKNOWN", "= eval_xen()")
            elif "= XoX.FALSE" in line:
                code_lines[i] = line.replace("= XoX.FALSE", "= eval_else()")

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("cond"): XoX.TRUE,
        }
        exec("\n".join(code_lines), scope)
        self.assertEqual(scope["trace"], ["branch_true"])
        self.assertNotIn("branch_xen", scope["trace"])
        self.assertNotIn("branch_else", scope["trace"])
        self.assertIs(scope[lowered.expr], XoX.TRUE)

    def test_inline_conditional_unselected_branch_exceptions_skipped(self):
        # Unselected branches contain division by zero / exception raising helpers
        ast = parse(tokenize("cond: XoX = Unknown\nres: XoX = True if cond xen Unknown else False\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[1].value, sem.result)

        code_lines = [
            "def fail_true():",
            "    raise RuntimeError('Should not execute true branch')",
            "def fail_else():",
            "    raise RuntimeError('Should not execute else branch')",
            *lowered.prelude,
        ]
        for i, line in enumerate(code_lines):
            if "= XoX.TRUE" in line:
                code_lines[i] = line.replace("= XoX.TRUE", "= fail_true()")
            elif "= XoX.FALSE" in line:
                code_lines[i] = line.replace("= XoX.FALSE", "= fail_else()")

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("cond"): XoX.UNKNOWN,
        }
        # Must not raise RuntimeError
        exec("\n".join(code_lines), scope)
        self.assertIs(scope[lowered.expr], XoX.UNKNOWN)

    def test_inline_conditional_selected_branch_evaluated_exactly_once(self):
        ast = parse(tokenize("cond: XoX = False\nres: XoX = True if cond xen Unknown else False\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[1].value, sem.result)

        code_lines = [
            "eval_count = 0",
            "def eval_selected():",
            "    global eval_count",
            "    eval_count += 1",
            "    return XoX.FALSE",
            *lowered.prelude,
        ]
        for i, line in enumerate(code_lines):
            if "= XoX.FALSE" in line:
                code_lines[i] = line.replace("= XoX.FALSE", "= eval_selected()")

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("cond"): XoX.FALSE,
        }
        exec("\n".join(code_lines), scope)
        self.assertEqual(scope["eval_count"], 1)
        self.assertIs(scope[lowered.expr], XoX.FALSE)

    def test_inline_conditional_xox_anti_truthiness_preserved(self):
        from xoxlang.compiler import compile_source
        source = (
            "c: XoX = Unknown\n"
            "res: XoX = True if c xen Unknown else False\n"
        )
        code = compile_source(source)
        # Ensure code does not trigger TypeError from bool(Unknown)
        scope = {}
        exec(code, scope)
        self.assertIs(scope[map_identifier("res")], XoX.UNKNOWN)

    def test_inline_conditional_nested_right_associativity_execution(self):
        from xoxlang.compiler import compile_source
        # a if c1 else b if c2 else d
        source = (
            "c1_f: Bool = False\n"
            "c2_t: Bool = True\n"
            "c2_f: Bool = False\n"
            "res_middle: Bool = True if c1_f else True if c2_t else False\n"
            "res_final: Bool = True if c1_f else True if c2_f else False\n"
        )
        code = compile_source(source)
        scope = {}
        exec(code, scope)
        self.assertIs(scope[map_identifier("res_middle")], True)
        self.assertIs(scope[map_identifier("res_final")], False)

    def test_inline_conditional_composed_with_short_circuit_and_collapse(self):
        from xoxlang.compiler import compile_source
        source = (
            "c: XoX = Unknown\n"
            "collapsed: Bool = (True if c xen Unknown else False).unwrap_or(False)\n"
            "short_circuit_and: XoX = False AND (True if c xen Unknown else False)\n"
            "short_circuit_or: XoX = True OR (True if c xen Unknown else False)\n"
        )
        code = compile_source(source)
        scope = {}
        exec(code, scope)
        self.assertIs(scope[map_identifier("collapsed")], False)
        self.assertIs(scope[map_identifier("short_circuit_and")], XoX.FALSE)
        self.assertIs(scope[map_identifier("short_circuit_or")], XoX.TRUE)

    def test_inline_conditional_invalid_runtime_state_raises_type_error(self):
        ast = parse(tokenize("cond: XoX = True\nres: XoX = True if cond xen Unknown else False\n"))
        sem = analyze(ast)
        lowered = lower_expression(ast.statements[1].value, sem.result)

        scope = {
            "XoX": XoX,
            "xox_and": xox_and,
            "xox_not": xox_not,
            "xox_or": xox_or,
            map_identifier("cond"): "corrupt_runtime_value",
        }
        with self.assertRaises(TypeError):
            exec("\n".join(lowered.prelude), scope)

    def test_inline_conditional_domain_independence_bool_condition_xox_result(self):
        from xoxlang.compiler import compile_source
        source = (
            "c_t: Bool = True\n"
            "c_f: Bool = False\n"
            "res_t: XoX = Unknown if c_t else False\n"
            "res_f: XoX = Unknown if c_f else False\n"
        )
        code = compile_source(source)
        scope = {}
        exec(code, scope)
        self.assertIs(scope[map_identifier("res_t")], XoX.UNKNOWN)
        self.assertIs(scope[map_identifier("res_f")], XoX.FALSE)

    def test_inline_conditional_domain_independence_xox_condition_bool_result(self):
        from xoxlang.compiler import compile_source
        source = (
            "c_t: XoX = True\n"
            "c_u: XoX = Unknown\n"
            "c_f: XoX = False\n"
            "res_t: Bool = True if c_t xen False else False\n"
            "res_u: Bool = False if c_u xen True else False\n"
            "res_f: Bool = False if c_f xen False else True\n"
        )
        code = compile_source(source)
        scope = {}
        exec(code, scope)
        self.assertIs(scope[map_identifier("res_t")], True)
        self.assertIs(scope[map_identifier("res_u")], True)
        self.assertIs(scope[map_identifier("res_f")], True)


if __name__ == "__main__":
    unittest.main()
