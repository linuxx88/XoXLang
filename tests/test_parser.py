"""Unit tests for X-o-X Parser and generic AST construction."""
import unittest
from xoxlang.lexer import tokenize
from xoxlang.tokens import TokenKind
from xoxlang.ast import (
    AssignmentStatement,
    BinaryExpr,
    Block,
    ConditionalStatement,
    ExprStatement,
    FunctionDefinition,
    GroupExpr,
    IdentifierExpr,
    IgnoreStatement,
    InlineConditionalExpr,
    LiteralExpr,
    Parameter,
    PassStatement,
    Program,
    ReturnStatement,
    UnaryExpr,
)
from xoxlang.parser import Parser, ParseError, parse


class TestParser(unittest.TestCase):
    def test_parse_bool_shaped_conditional(self):
        source = (
            "if cond:\n"
            "    pass\n"
            "else:\n"
            "    pass\n"
        )
        tokens = tokenize(source)
        ast = parse(tokens)
        self.assertIsInstance(ast, Program)
        self.assertEqual(len(ast.statements), 1)

        stmt = ast.statements[0]
        self.assertIsInstance(stmt, ConditionalStatement)
        self.assertIsInstance(stmt.condition, IdentifierExpr)
        self.assertEqual(stmt.condition.name, "cond")
        self.assertIsInstance(stmt.true_branch, Block)
        self.assertIsNone(stmt.xen_branch)
        self.assertIsInstance(stmt.else_branch, Block)

    def test_parse_full_xox_conditional(self):
        source = (
            "if my_xox:\n"
            "    action1\n"
            "xen:\n"
            "    action2\n"
            "else:\n"
            "    action3\n"
        )
        tokens = tokenize(source)
        ast = parse(tokens)
        stmt = ast.statements[0]
        self.assertIsInstance(stmt, ConditionalStatement)
        self.assertIsInstance(stmt.true_branch, Block)
        self.assertIsInstance(stmt.xen_branch, Block)
        self.assertIsInstance(stmt.else_branch, Block)

    def test_parse_xen_ignore_dedicated_marker(self):
        source = (
            "if my_xox:\n"
            "    pass\n"
            "xen:\n"
            "    ignore\n"
            "else:\n"
            "    pass\n"
        )
        tokens = tokenize(source)
        ast = parse(tokens)
        stmt = ast.statements[0]
        self.assertIsInstance(stmt, ConditionalStatement)
        self.assertIsInstance(stmt.xen_branch, IgnoreStatement)

    def test_parse_xen_multi_statement_with_pass_and_effective_logic(self):
        source = (
            "if t:\n"
            "    pass\n"
            "xen:\n"
            "    audit\n"
            "    pass\n"
            "else:\n"
            "    pass\n"
        )
        tokens = tokenize(source)
        ast = parse(tokens)
        stmt = ast.statements[0]

        self.assertIsInstance(stmt.xen_branch, Block)
        self.assertEqual(len(stmt.xen_branch.statements), 2)
        self.assertIsInstance(stmt.xen_branch.statements[0], ExprStatement)
        self.assertIsInstance(stmt.xen_branch.statements[1], PassStatement)

    def test_reject_xen_clause_containing_only_pass(self):
        samples = [
            "if t:\n    pass\nxen:\n    pass\nelse:\n    pass\n",
            "if t:\n    pass\nxen:\n    pass\n    pass\nelse:\n    pass\n",
        ]
        for src in samples:
            with self.subTest(src=src):
                tokens = tokenize(src)
                with self.assertRaises(ParseError) as ctx:
                    parse(tokens)
                self.assertIn("only 'pass' is invalid", str(ctx.exception))

    def test_reject_xen_ignore_coexisting_with_other_statements(self):
        samples = [
            "if t:\n    pass\nxen:\n    ignore\n    audit\nelse:\n    pass\n",
            "if t:\n    pass\nxen:\n    audit\n    ignore\nelse:\n    pass\n",
        ]
        for src in samples:
            with self.subTest(src=src):
                tokens = tokenize(src)
                with self.assertRaises(ParseError) as ctx:
                    parse(tokens)
    def test_ctx_xen_inline_01_compact_ignore_ast_equivalence(self):
        src_block = (
            "if my_xox:\n"
            "    pass\n"
            "xen:\n"
            "    ignore\n"
            "else:\n"
            "    pass\n"
        )
        src_compact = (
            "if my_xox:\n"
            "    pass\n"
            "xen: ignore\n"
            "else:\n"
            "    pass\n"
        )
        ast_block = parse(tokenize(src_block))
        ast_compact = parse(tokenize(src_compact))

        stmt_b = ast_block.statements[0]
        stmt_c = ast_compact.statements[0]
        self.assertIsInstance(stmt_b, ConditionalStatement)
        self.assertIsInstance(stmt_c, ConditionalStatement)
        self.assertIsInstance(stmt_b.xen_branch, IgnoreStatement)
        self.assertIsInstance(stmt_c.xen_branch, IgnoreStatement)
        self.assertEqual(type(stmt_b.xen_branch), type(stmt_c.xen_branch))

    def test_ctx_xen_inline_02_reject_arbitrary_inline_statement_under_xen(self):
        samples = [
            "if t:\n    pass\nxen: foo()\nelse:\n    pass\n",
            "if t:\n    pass\nxen: pass\nelse:\n    pass\n",
            "if t:\n    pass\nxen: x = True\nelse:\n    pass\n",
        ]
        for src in samples:
            with self.subTest(src=src):
                tokens = tokenize(src)
                with self.assertRaises(ParseError) as ctx:
                    parse(tokens)
                self.assertIn("Illegal inline statement under 'xen'", str(ctx.exception))

    def test_ctx_xen_inline_03_reject_compound_semicolon_in_compact_xen(self):
        # Compound statements on the same line after ignore are rejected
        samples_parser = [
            "if t:\n    pass\nxen: ignore foo()\nelse:\n    pass\n",
            "if t:\n    pass\nxen: ignore pass\nelse:\n    pass\n",
            "if t:\n    pass\nxen: ignore audit\nelse:\n    pass\n",
        ]
        for src in samples_parser:
            with self.subTest(src=src):
                tokens = tokenize(src)
                with self.assertRaises(ParseError) as ctx:
                    parse(tokens)
                self.assertIn("Non-exclusive 'xen: ignore'", str(ctx.exception))

        # Semicolons are rejected at lexer or parser level
        from xoxlang.lexer import LexerError
        samples_semicolon = [
            "if t:\n    pass\nxen: ignore; foo()\nelse:\n    pass\n",
            "if t:\n    pass\nxen: ignore; pass\nelse:\n    pass\n",
        ]
        for src in samples_semicolon:
            with self.subTest(src=src):
                with self.assertRaises((ParseError, LexerError)):
                    parse(tokenize(src))

    def test_ctx_xen_inline_04_reject_contextual_ignore_outside_xen(self):
        samples = [
            "if cond: ignore\n",
            "else: ignore\n",
        ]
        for src in samples:
            with self.subTest(src=src):
                tokens = tokenize(src)
                with self.assertRaises(ParseError) as ctx:
                    parse(tokens)

    def test_reject_orphan_clauses(self):
        with self.assertRaises(ParseError) as ctx:
            parse(tokenize("xen:\n    pass\n"))
        self.assertIn("Orphan 'xen'", str(ctx.exception))

        with self.assertRaises(ParseError) as ctx:
            parse(tokenize("else:\n    pass\n"))
        self.assertIn("Orphan 'else'", str(ctx.exception))

    def test_reject_elif_construct(self):
        samples = [
            "elif cond:\n    pass\n",
            "if a:\n    pass\nelif b:\n    pass\nelse:\n    pass\n",
        ]
        for src in samples:
            with self.subTest(src=src):
                tokens = tokenize(src)
                with self.assertRaises(ParseError) as ctx:
                    parse(tokens)
                self.assertIn("elif", str(ctx.exception))

    def test_reject_duplicate_and_invalidly_ordered_clauses(self):
        samples = [
            # duplicate xen
            "if a:\n    pass\nxen:\n    ignore\nxen:\n    ignore\nelse:\n    pass\n",
            # duplicate else
            "if a:\n    pass\nelse:\n    pass\nelse:\n    pass\n",
            # invalid order: else before xen
            "if a:\n    pass\nelse:\n    pass\nxen:\n    ignore\n",
        ]
        for src in samples:
            with self.subTest(src=src):
                tokens = tokenize(src)
                with self.assertRaises(ParseError):
                    parse(tokens)

    def test_expression_precedence_hierarchy(self):
        # NOT a == b AND c strictly parses as ((NOT a) == b) AND c
        source = "NOT a == b AND c"
        ast = parse(tokenize(source))
        stmt = ast.statements[0]
        self.assertIsInstance(stmt, ExprStatement)
        expr = stmt.expr
        # Top-level should be AND
        self.assertIsInstance(expr, BinaryExpr)
        self.assertEqual(expr.op, TokenKind.AND)
        self.assertIsInstance(expr.right, IdentifierExpr)
        self.assertEqual(expr.right.name, "c")

        # Left should be ==
        left = expr.left
        self.assertIsInstance(left, BinaryExpr)
        self.assertEqual(left.op, TokenKind.EQ_EQ)
        self.assertIsInstance(left.right, IdentifierExpr)
        self.assertEqual(left.right.name, "b")

        # Left of == should be NOT a
        not_expr = left.left
        self.assertIsInstance(not_expr, UnaryExpr)
        self.assertEqual(not_expr.op, TokenKind.NOT)
        self.assertIsInstance(not_expr.operand, IdentifierExpr)
        self.assertEqual(not_expr.operand.name, "a")

    def test_parentheses_override_precedence(self):
        # NOT (a == b) AND c
        source = "NOT (a == b) AND c"
        ast = parse(tokenize(source))
        expr = ast.statements[0].expr
        self.assertIsInstance(expr, BinaryExpr)
        self.assertEqual(expr.op, TokenKind.AND)

        not_expr = expr.left
        self.assertIsInstance(not_expr, UnaryExpr)
        self.assertEqual(not_expr.op, TokenKind.NOT)
        self.assertIsInstance(not_expr.operand, GroupExpr)
        self.assertIsInstance(not_expr.operand.expr, BinaryExpr)
        self.assertEqual(not_expr.operand.expr.op, TokenKind.EQ_EQ)

    def test_and_or_left_associativity(self):
        # a AND b AND c -> (a AND b) AND c
        source = "a AND b AND c"
        ast = parse(tokenize(source))
        expr = ast.statements[0].expr
        self.assertIsInstance(expr, BinaryExpr)
        self.assertEqual(expr.op, TokenKind.AND)
        self.assertIsInstance(expr.left, BinaryExpr)
        self.assertEqual(expr.left.op, TokenKind.AND)

        # a OR b OR c -> (a OR b) OR c
        source = "a OR b OR c"
        ast = parse(tokenize(source))
        expr = ast.statements[0].expr
        self.assertIsInstance(expr, BinaryExpr)
        self.assertEqual(expr.op, TokenKind.OR)
        self.assertIsInstance(expr.left, BinaryExpr)
        self.assertEqual(expr.left.op, TokenKind.OR)

    def test_reject_chained_comparisons(self):
        samples = [
            "a == b == c",
            "a == b != c",
            "a != b == c",
            "a != b != c",
            "True == Unknown == False",
        ]
        for src in samples:
            with self.subTest(src=src):
                tokens = tokenize(src)
                with self.assertRaises(ParseError) as ctx:
                    parse(tokens)
                self.assertIn("Chained comparisons", str(ctx.exception))

    def test_structural_parsing_of_all_literals_and_operators(self):
        source = "Unknown != False OR True == Unknown AND NOT False"
        ast = parse(tokenize(source))
        self.assertIsInstance(ast.statements[0], ExprStatement)

    def test_source_span_preservation(self):
        source = "if True:\n    pass\n"
        ast = parse(tokenize(source))
        stmt = ast.statements[0]
        self.assertIsNotNone(stmt.span)
        self.assertEqual(stmt.span.start.line, 1)
        self.assertEqual(stmt.span.start.column, 1)
        self.assertIsNotNone(stmt.if_span)

    # Variable Binding and Reassignment Tests
    def test_parse_inferred_assignment(self):
        source = "x = True\n"
        ast = parse(tokenize(source))
        self.assertEqual(len(ast.statements), 1)
        stmt = ast.statements[0]
        self.assertIsInstance(stmt, AssignmentStatement)
        self.assertEqual(stmt.target, "x")
        self.assertIsNone(stmt.annotation)
        self.assertIsInstance(stmt.value, LiteralExpr)
        self.assertEqual(stmt.value.kind, TokenKind.TRUE)

    def test_parse_annotated_assignments(self):
        # status: XoX = Unknown
        ast_xox = parse(tokenize("status: XoX = Unknown\n"))
        stmt_xox = ast_xox.statements[0]
        self.assertIsInstance(stmt_xox, AssignmentStatement)
        self.assertEqual(stmt_xox.target, "status")
        self.assertEqual(stmt_xox.annotation, "XoX")
        self.assertIsInstance(stmt_xox.value, LiteralExpr)
        self.assertEqual(stmt_xox.value.kind, TokenKind.UNKNOWN)

        # flag: Bool = False
        ast_bool = parse(tokenize("flag: Bool = False\n"))
        stmt_bool = ast_bool.statements[0]
        self.assertIsInstance(stmt_bool, AssignmentStatement)
        self.assertEqual(stmt_bool.target, "flag")
        self.assertEqual(stmt_bool.annotation, "Bool")
        self.assertIsInstance(stmt_bool.value, LiteralExpr)
        self.assertEqual(stmt_bool.value.kind, TokenKind.FALSE)

    def test_parse_assignment_with_complex_expression(self):
        ast = parse(tokenize("x = a AND b\n"))
        stmt = ast.statements[0]
        self.assertIsInstance(stmt, AssignmentStatement)
        self.assertIsInstance(stmt.value, BinaryExpr)
        self.assertEqual(stmt.value.op, TokenKind.AND)

        ast_annotated = parse(tokenize("x: XoX = True AND False\n"))
        stmt_ann = ast_annotated.statements[0]
        self.assertIsInstance(stmt_ann, AssignmentStatement)
        self.assertEqual(stmt_ann.annotation, "XoX")
        self.assertIsInstance(stmt_ann.value, BinaryExpr)


    def test_equality_statement_vs_assignment(self):
        ast = parse(tokenize("x == y\n"))
        self.assertEqual(len(ast.statements), 1)
        stmt = ast.statements[0]
        self.assertIsInstance(stmt, ExprStatement)
        self.assertIsInstance(stmt.expr, BinaryExpr)
        self.assertEqual(stmt.expr.op, TokenKind.EQ_EQ)

    def test_reject_invalid_or_unsupported_type_annotations(self):
        invalid_samples = [
            "x: Foo = True\n",
            "x: int = True\n",
            "x: = True\n",
        ]
        for src in invalid_samples:
            with self.subTest(src=src):
                with self.assertRaises(ParseError) as ctx:
                    parse(tokenize(src))
                self.assertIn("unsupported type annotation", str(ctx.exception))

    def test_reject_uninitialized_or_missing_initializers(self):
        uninitialized_samples = [
            "x: XoX\n",
            "x: Bool\n",
        ]
        for src in uninitialized_samples:
            with self.subTest(src=src):
                with self.assertRaises(ParseError) as ctx:
                    parse(tokenize(src))
                self.assertIn("Uninitialized variable declarations", str(ctx.exception))

        missing_samples = [
            "x =\n",
            "x: XoX =\n",
        ]
        for src in missing_samples:
            with self.subTest(src=src):
                with self.assertRaises(ParseError) as ctx:
                    parse(tokenize(src))
                self.assertIn("Missing initializer", str(ctx.exception))

    def test_assignment_source_span_preservation(self):
        source = "status: XoX = Unknown\n"
        ast = parse(tokenize(source))
        stmt = ast.statements[0]
        self.assertIsInstance(stmt, AssignmentStatement)
        self.assertIsNotNone(stmt.span)
        self.assertIsNotNone(stmt.target_span)
        self.assertIsNotNone(stmt.annotation_span)
        self.assertIsNotNone(stmt.assign_span)
        self.assertEqual(stmt.target_span.start.column, 1)

    def test_assignments_inside_conditionals(self):
        source = (
            "if a:\n"
            "    x = True\n"
            "xen:\n"
            "    x: XoX = Unknown\n"
            "else:\n"
            "    x = False\n"
        )
        ast = parse(tokenize(source))
        cond = ast.statements[0]
        self.assertIsInstance(cond, ConditionalStatement)
        self.assertIsInstance(cond.true_branch.statements[0], AssignmentStatement)
        self.assertIsInstance(cond.xen_branch.statements[0], AssignmentStatement)
        self.assertIsInstance(cond.else_branch.statements[0], AssignmentStatement)

    # Function Definition and Return Statement Tests
    def test_parse_simple_function(self):
        source = "fn f():\n    pass\n"
        ast = parse(tokenize(source))
        self.assertEqual(len(ast.statements), 1)
        fn = ast.statements[0]
        self.assertIsInstance(fn, FunctionDefinition)
        self.assertEqual(fn.name, "f")
        self.assertEqual(len(fn.parameters), 0)
        self.assertIsNone(fn.return_annotation)
        self.assertIsInstance(fn.body, Block)

    def test_parse_parameterized_functions(self):
        # Single parameter
        source1 = "fn f(x: Bool):\n    pass\n"
        ast1 = parse(tokenize(source1))
        fn1 = ast1.statements[0]
        self.assertEqual(len(fn1.parameters), 1)
        self.assertEqual(fn1.parameters[0].name, "x")
        self.assertEqual(fn1.parameters[0].type_name, "Bool")

        # Multiple parameters preserving order with canonical XoX
        source2 = "fn f(x: Bool, y: XoX):\n    pass\n"
        ast2 = parse(tokenize(source2))
        fn2 = ast2.statements[0]
        self.assertEqual(len(fn2.parameters), 2)
        self.assertEqual(fn2.parameters[0].name, "x")
        self.assertEqual(fn2.parameters[0].type_name, "Bool")
        self.assertEqual(fn2.parameters[1].name, "y")
        self.assertEqual(fn2.parameters[1].type_name, "XoX")

        # Rejected unsupported parameter type
        with self.assertRaises(ParseError) as ctx:
            parse(tokenize("fn f(x: Bool, y: CustomType):\n    pass\n"))
        self.assertIn("unsupported parameter type", str(ctx.exception).lower())

    def test_parse_functions_with_return_annotations(self):
        # -> Bool
        ast1 = parse(tokenize("fn f() -> Bool:\n    return True\n"))
        fn1 = ast1.statements[0]
        self.assertEqual(fn1.return_annotation, "Bool")
        self.assertIsInstance(fn1.body.statements[0], ReturnStatement)

        # -> XoX (canonical)
        ast_xox = parse(tokenize("fn f(x: XoX) -> XoX:\n    return x\n"))
        fn_xox = ast_xox.statements[0]
        self.assertEqual(fn_xox.return_annotation, "XoX")
        self.assertIsInstance(fn_xox.body.statements[0], ReturnStatement)

        # Rejected unsupported return type
        with self.assertRaises(ParseError) as ctx:
            parse(tokenize("fn f(x: XoX) -> CustomType:\n    return x\n"))
        self.assertIn("unsupported return type", str(ctx.exception).lower())


    def test_parse_return_statements(self):
        # return True
        ast1 = parse(tokenize("return True\n"))
        ret1 = ast1.statements[0]
        self.assertIsInstance(ret1, ReturnStatement)
        self.assertIsInstance(ret1.value, LiteralExpr)
        self.assertEqual(ret1.value.kind, TokenKind.TRUE)

        # return Unknown
        ast2 = parse(tokenize("return Unknown\n"))
        ret2 = ast2.statements[0]
        self.assertIsInstance(ret2, ReturnStatement)
        self.assertEqual(ret2.value.kind, TokenKind.UNKNOWN)

        # return x AND True
        ast3 = parse(tokenize("return x AND True\n"))
        ret3 = ast3.statements[0]
        self.assertIsInstance(ret3, ReturnStatement)
        self.assertIsInstance(ret3.value, BinaryExpr)
        self.assertEqual(ret3.value.op, TokenKind.AND)

    def test_function_body_with_assignments_and_conditionals(self):
        source = (
            "fn process(x: XoX) -> XoX:\n"
            "    res = x\n"
            "    if res:\n"
            "        return True\n"
            "    xen:\n"
            "        return Unknown\n"
            "    else:\n"
            "        return False\n"
        )
        ast = parse(tokenize(source))
        fn = ast.statements[0]
        self.assertIsInstance(fn, FunctionDefinition)
        self.assertEqual(len(fn.body.statements), 2)
        self.assertIsInstance(fn.body.statements[0], AssignmentStatement)
        self.assertIsInstance(fn.body.statements[1], ConditionalStatement)

    def test_reject_invalid_function_syntax(self):
        invalid_samples = [
            # untyped parameter
            ("fn f(x):\n    pass\n", "explicitly typed"),
            # unsupported parameter type
            ("fn f(x: Foo):\n    pass\n", "unsupported parameter type"),
            ("fn f(x: CustomType):\n    pass\n", "unsupported parameter type"),
            # unsupported return type
            ("fn f() -> Foo:\n    pass\n", "unsupported return type"),
            ("fn f() -> CustomType:\n    pass\n", "unsupported return type"),
            # missing parameter type
            ("fn f(x:):\n    pass\n", "unsupported parameter type"),
            # malformed parameter
            ("fn f(: Bool):\n    pass\n", "Expected parameter name"),
            # trailing comma
            ("fn f(x: Bool,):\n    pass\n", "Trailing comma"),
            # missing colon
            ("fn f()\n    pass\n", "Expected ':'"),
            # malformed return annotation
            ("fn f() ->:\n    pass\n", "unsupported return type"),
            # bare return
            ("return\n", "Bare 'return'"),
        ]

        for src, expected_err in invalid_samples:
            with self.subTest(src=src):
                with self.assertRaises(ParseError) as ctx:
                    parse(tokenize(src))
                self.assertIn(expected_err.lower(), str(ctx.exception).lower())

    def test_function_source_span_preservation(self):
        source = "fn f(x: Bool) -> XoX:\n    return True\n"
        ast = parse(tokenize(source))
        fn = ast.statements[0]
        self.assertIsInstance(fn, FunctionDefinition)
        self.assertIsNotNone(fn.span)
        self.assertIsNotNone(fn.fn_span)
        self.assertIsNotNone(fn.name_span)
        self.assertIsNotNone(fn.return_annotation_span)

        param = fn.parameters[0]
        self.assertIsNotNone(param.span)
        self.assertIsNotNone(param.name_span)
        self.assertIsNotNone(param.type_span)

        ret = fn.body.statements[0]
        self.assertIsInstance(ret, ReturnStatement)
        self.assertIsNotNone(ret.span)
        self.assertIsNotNone(ret.return_span)

    def test_parse_inline_conditional_bool_form(self):
        source = "t if c else f\n"
        ast = parse(tokenize(source))
        self.assertEqual(len(ast.statements), 1)
        stmt = ast.statements[0]
        self.assertIsInstance(stmt, ExprStatement)
        expr = stmt.expr
        self.assertIsInstance(expr, InlineConditionalExpr)
        self.assertIsInstance(expr.true_expr, IdentifierExpr)
        self.assertEqual(expr.true_expr.name, "t")
        self.assertIsInstance(expr.condition, IdentifierExpr)
        self.assertEqual(expr.condition.name, "c")
        self.assertIsNone(expr.xen_expr)
        self.assertIsInstance(expr.else_expr, IdentifierExpr)
        self.assertEqual(expr.else_expr.name, "f")
        self.assertIsNotNone(expr.span)
        self.assertEqual(expr.span.start.line, 1)
        self.assertEqual(expr.span.start.column, 1)
        self.assertEqual(expr.span.end.line, 1)
        self.assertEqual(expr.span.end.column, 14)

    def test_parse_inline_conditional_xox_form(self):
        source = "t if c xen u else f\n"
        ast = parse(tokenize(source))
        self.assertEqual(len(ast.statements), 1)
        stmt = ast.statements[0]
        self.assertIsInstance(stmt, ExprStatement)
        expr = stmt.expr
        self.assertIsInstance(expr, InlineConditionalExpr)
        self.assertIsInstance(expr.true_expr, IdentifierExpr)
        self.assertEqual(expr.true_expr.name, "t")
        self.assertIsInstance(expr.condition, IdentifierExpr)
        self.assertEqual(expr.condition.name, "c")
        self.assertIsNotNone(expr.xen_expr)
        self.assertIsInstance(expr.xen_expr, IdentifierExpr)
        self.assertEqual(expr.xen_expr.name, "u")
        self.assertIsInstance(expr.else_expr, IdentifierExpr)
        self.assertEqual(expr.else_expr.name, "f")
        self.assertIsNotNone(expr.span)
        self.assertEqual(expr.span.start.line, 1)
        self.assertEqual(expr.span.start.column, 1)
        self.assertEqual(expr.span.end.line, 1)
        self.assertEqual(expr.span.end.column, 20)

    def test_parse_inline_conditional_precedence_below_or(self):
        source = "a OR b if c else d\n"
        ast = parse(tokenize(source))
        self.assertEqual(len(ast.statements), 1)
        stmt = ast.statements[0]
        self.assertIsInstance(stmt, ExprStatement)
        expr = stmt.expr
        self.assertIsInstance(expr, InlineConditionalExpr)
        self.assertNotIsInstance(expr, BinaryExpr)

        self.assertIsInstance(expr.true_expr, BinaryExpr)
        self.assertEqual(expr.true_expr.op, TokenKind.OR)
        self.assertIsInstance(expr.true_expr.left, IdentifierExpr)
        self.assertEqual(expr.true_expr.left.name, "a")
        self.assertIsInstance(expr.true_expr.right, IdentifierExpr)
        self.assertEqual(expr.true_expr.right.name, "b")

        self.assertIsInstance(expr.condition, IdentifierExpr)
        self.assertEqual(expr.condition.name, "c")
        self.assertIsNone(expr.xen_expr)
        self.assertIsInstance(expr.else_expr, IdentifierExpr)
        self.assertEqual(expr.else_expr.name, "d")

    def test_parse_inline_conditional_right_associativity(self):
        source = "a if c1 else b if c2 else d\n"
        ast = parse(tokenize(source))
        self.assertEqual(len(ast.statements), 1)
        stmt = ast.statements[0]
        self.assertIsInstance(stmt, ExprStatement)
        root = stmt.expr
        self.assertIsInstance(root, InlineConditionalExpr)
        self.assertIsInstance(root.true_expr, IdentifierExpr)
        self.assertEqual(root.true_expr.name, "a")
        self.assertIsInstance(root.condition, IdentifierExpr)
        self.assertEqual(root.condition.name, "c1")
        self.assertIsNone(root.xen_expr)

        nested = root.else_expr
        self.assertIsInstance(nested, InlineConditionalExpr)
        self.assertIsInstance(nested.true_expr, IdentifierExpr)
        self.assertEqual(nested.true_expr.name, "b")
        self.assertIsInstance(nested.condition, IdentifierExpr)
        self.assertEqual(nested.condition.name, "c2")
        self.assertIsNone(nested.xen_expr)
        self.assertIsInstance(nested.else_expr, IdentifierExpr)
        self.assertEqual(nested.else_expr.name, "d")

    def test_parse_inline_conditional_missing_else_fails(self):
        source = "a if c\n"
        with self.assertRaises(ParseError) as ctx:
            parse(tokenize(source))
        self.assertIn("expected 'else'", str(ctx.exception).lower())



if __name__ == "__main__":
    unittest.main()
