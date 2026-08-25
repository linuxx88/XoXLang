"""Unit tests for Trool V1 lexer."""
import unittest
from trool.tokens import TokenKind, SourceLocation, SourceSpan, Token
from trool.lexer import Lexer, LexerError, tokenize


class TestTroolLexer(unittest.TestCase):
    def test_bootstrap_import(self):
        import trool.tokens
        import trool.lexer
        self.assertTrue(hasattr(trool.tokens, "Token"))
        self.assertTrue(hasattr(trool.lexer, "tokenize"))

    def test_tokenize_bool_conditional(self):
        source = (
            "if True:\n"
            "    pass\n"
            "else:\n"
            "    pass\n"
        )
        tokens = tokenize(source)
        expected_kinds = [
            TokenKind.IF,
            TokenKind.TRUE,
            TokenKind.COLON,
            TokenKind.NEWLINE,
            TokenKind.INDENT,
            TokenKind.PASS,
            TokenKind.NEWLINE,
            TokenKind.DEDENT,
            TokenKind.ELSE,
            TokenKind.COLON,
            TokenKind.NEWLINE,
            TokenKind.INDENT,
            TokenKind.PASS,
            TokenKind.NEWLINE,
            TokenKind.DEDENT,
            TokenKind.EOF,
        ]
        self.assertEqual([t.kind for t in tokens], expected_kinds)

    def test_tokenize_trool_conditional(self):
        source = (
            "if my_trool:\n"
            "    pass\n"
            "xen:\n"
            "    ignore\n"
            "else:\n"
            "    pass\n"
        )
        tokens = tokenize(source)
        expected_kinds = [
            TokenKind.IF,
            TokenKind.IDENTIFIER,
            TokenKind.COLON,
            TokenKind.NEWLINE,
            TokenKind.INDENT,
            TokenKind.PASS,
            TokenKind.NEWLINE,
            TokenKind.DEDENT,
            TokenKind.XEN,
            TokenKind.COLON,
            TokenKind.NEWLINE,
            TokenKind.INDENT,
            TokenKind.IDENTIFIER,  # 'ignore' must lex as IDENTIFIER
            TokenKind.NEWLINE,
            TokenKind.DEDENT,
            TokenKind.ELSE,
            TokenKind.COLON,
            TokenKind.NEWLINE,
            TokenKind.INDENT,
            TokenKind.PASS,
            TokenKind.NEWLINE,
            TokenKind.DEDENT,
            TokenKind.EOF,
        ]
        self.assertEqual([t.kind for t in tokens], expected_kinds)
        self.assertEqual(tokens[12].lexeme, "ignore")
        self.assertEqual(tokens[12].kind, TokenKind.IDENTIFIER)

    def test_tokenize_literals_logical_and_comparisons(self):
        source = "NOT (True == Unknown) AND (False != True) OR NOT False"
        tokens = tokenize(source)
        expected_kinds = [
            TokenKind.NOT,
            TokenKind.LPAREN,
            TokenKind.TRUE,
            TokenKind.EQ_EQ,
            TokenKind.UNKNOWN,
            TokenKind.RPAREN,
            TokenKind.AND,
            TokenKind.LPAREN,
            TokenKind.FALSE,
            TokenKind.EXCL_EQ,
            TokenKind.TRUE,
            TokenKind.RPAREN,
            TokenKind.OR,
            TokenKind.NOT,
            TokenKind.FALSE,
            TokenKind.NEWLINE,
            TokenKind.EOF,
        ]
        self.assertEqual([t.kind for t in tokens], expected_kinds)

    def test_tokenize_assignments_and_type_names(self):
        # x = True
        tokens = tokenize("x = True")
        self.assertEqual(
            [t.kind for t in tokens],
            [TokenKind.IDENTIFIER, TokenKind.ASSIGN, TokenKind.TRUE, TokenKind.NEWLINE, TokenKind.EOF],
        )

        # x: XoX = Unknown (XoX remains IDENTIFIER at lexing time)
        tokens_xox = tokenize("x: XoX = Unknown")
        self.assertEqual(
            [t.kind for t in tokens_xox],
            [
                TokenKind.IDENTIFIER,
                TokenKind.COLON,
                TokenKind.IDENTIFIER,
                TokenKind.ASSIGN,
                TokenKind.UNKNOWN,
                TokenKind.NEWLINE,
                TokenKind.EOF,
            ],
        )
        self.assertEqual(tokens_xox[2].lexeme, "XoX")
        self.assertEqual(tokens_xox[2].kind, TokenKind.IDENTIFIER)

        # x: Trool = Unknown (Trool remains IDENTIFIER at lexing time for backward compatibility)
        tokens_trool = tokenize("x: Trool = Unknown")
        self.assertEqual(
            [t.kind for t in tokens_trool],
            [
                TokenKind.IDENTIFIER,
                TokenKind.COLON,
                TokenKind.IDENTIFIER,
                TokenKind.ASSIGN,
                TokenKind.UNKNOWN,
                TokenKind.NEWLINE,
                TokenKind.EOF,
            ],
        )
        self.assertEqual(tokens_trool[2].lexeme, "Trool")
        self.assertEqual(tokens_trool[2].kind, TokenKind.IDENTIFIER)

        # x: Bool = False (Bool remains IDENTIFIER at lexing time)
        tokens_bool = tokenize("x: Bool = False")
        self.assertEqual(
            [t.kind for t in tokens_bool],
            [
                TokenKind.IDENTIFIER,
                TokenKind.COLON,
                TokenKind.IDENTIFIER,
                TokenKind.ASSIGN,
                TokenKind.FALSE,
                TokenKind.NEWLINE,
                TokenKind.EOF,
            ],
        )
        self.assertEqual(tokens_bool[2].lexeme, "Bool")
        self.assertEqual(tokens_bool[2].kind, TokenKind.IDENTIFIER)


    def test_tokenize_functions_and_returns(self):
        # fn f():
        tokens_fn = tokenize("fn f():")
        self.assertEqual(
            [t.kind for t in tokens_fn],
            [
                TokenKind.FN,
                TokenKind.IDENTIFIER,
                TokenKind.LPAREN,
                TokenKind.RPAREN,
                TokenKind.COLON,
                TokenKind.NEWLINE,
                TokenKind.EOF,
            ],
        )

        # fn f(x: Bool):
        tokens_param = tokenize("fn f(x: Bool):")
        self.assertEqual(
            [t.kind for t in tokens_param],
            [
                TokenKind.FN,
                TokenKind.IDENTIFIER,
                TokenKind.LPAREN,
                TokenKind.IDENTIFIER,
                TokenKind.COLON,
                TokenKind.IDENTIFIER,
                TokenKind.RPAREN,
                TokenKind.COLON,
                TokenKind.NEWLINE,
                TokenKind.EOF,
            ],
        )
        self.assertEqual(tokens_param[5].lexeme, "Bool")

        # fn f(x: Bool, y: XoX) -> XoX:
        tokens_full = tokenize("fn f(x: Bool, y: XoX) -> XoX:")
        self.assertEqual(
            [t.kind for t in tokens_full],
            [
                TokenKind.FN,
                TokenKind.IDENTIFIER,
                TokenKind.LPAREN,
                TokenKind.IDENTIFIER,
                TokenKind.COLON,
                TokenKind.IDENTIFIER,
                TokenKind.COMMA,
                TokenKind.IDENTIFIER,
                TokenKind.COLON,
                TokenKind.IDENTIFIER,
                TokenKind.RPAREN,
                TokenKind.ARROW,
                TokenKind.IDENTIFIER,
                TokenKind.COLON,
                TokenKind.NEWLINE,
                TokenKind.EOF,
            ],
        )
        self.assertEqual(tokens_full[6].kind, TokenKind.COMMA)
        self.assertEqual(tokens_full[11].kind, TokenKind.ARROW)
        self.assertEqual(tokens_full[9].lexeme, "XoX")
        self.assertEqual(tokens_full[12].lexeme, "XoX")


        # return True / return Unknown
        tokens_ret1 = tokenize("return True")
        self.assertEqual(
            [t.kind for t in tokens_ret1],
            [TokenKind.RETURN, TokenKind.TRUE, TokenKind.NEWLINE, TokenKind.EOF],
        )

        tokens_ret2 = tokenize("return Unknown")
        self.assertEqual(
            [t.kind for t in tokens_ret2],
            [TokenKind.RETURN, TokenKind.UNKNOWN, TokenKind.NEWLINE, TokenKind.EOF],
        )

    def test_arrow_and_hyphen_handling(self):
        # '->' emits ARROW
        tokens = tokenize("->")
        self.assertEqual(
            [t.kind for t in tokens],
            [TokenKind.ARROW, TokenKind.NEWLINE, TokenKind.EOF],
        )

        # Standalone '-' fails explicitly
        with self.assertRaises(LexerError):
            tokenize("-")
        with self.assertRaises(LexerError):
            tokenize("--")
        with self.assertRaises(LexerError):
            tokenize("a - b")

    def test_assignment_vs_equality_longest_match(self):
        # a == b -> EQ_EQ
        tokens_eq = tokenize("a == b")
        self.assertEqual(
            [t.kind for t in tokens_eq],
            [TokenKind.IDENTIFIER, TokenKind.EQ_EQ, TokenKind.IDENTIFIER, TokenKind.NEWLINE, TokenKind.EOF],
        )

        # a = b == c -> ASSIGN, then EQ_EQ
        tokens_mixed = tokenize("a = b == c")
        self.assertEqual(
            [t.kind for t in tokens_mixed],
            [
                TokenKind.IDENTIFIER,
                TokenKind.ASSIGN,
                TokenKind.IDENTIFIER,
                TokenKind.EQ_EQ,
                TokenKind.IDENTIFIER,
                TokenKind.NEWLINE,
                TokenKind.EOF,
            ],
        )

    def test_ignore_and_elif_are_identifiers(self):
        source = "ignore elif true false"
        tokens = tokenize(source)
        expected_kinds = [
            TokenKind.IDENTIFIER,
            TokenKind.IDENTIFIER,
            TokenKind.IDENTIFIER,
            TokenKind.IDENTIFIER,
            TokenKind.NEWLINE,
            TokenKind.EOF,
        ]
        self.assertEqual([t.kind for t in tokens], expected_kinds)
        self.assertEqual([t.lexeme for t in tokens[:-2]], ["ignore", "elif", "true", "false"])

    def test_nested_indentation_structure(self):
        source = (
            "if a:\n"
            "    if b:\n"
            "        pass\n"
            "    else:\n"
            "        pass\n"
        )
        tokens = tokenize(source)
        expected_kinds = [
            TokenKind.IF,
            TokenKind.IDENTIFIER,
            TokenKind.COLON,
            TokenKind.NEWLINE,
            TokenKind.INDENT,
            TokenKind.IF,
            TokenKind.IDENTIFIER,
            TokenKind.COLON,
            TokenKind.NEWLINE,
            TokenKind.INDENT,
            TokenKind.PASS,
            TokenKind.NEWLINE,
            TokenKind.DEDENT,
            TokenKind.ELSE,
            TokenKind.COLON,
            TokenKind.NEWLINE,
            TokenKind.INDENT,
            TokenKind.PASS,
            TokenKind.NEWLINE,
            TokenKind.DEDENT,
            TokenKind.DEDENT,
            TokenKind.EOF,
        ]
        self.assertEqual([t.kind for t in tokens], expected_kinds)

    def test_source_spans_and_locations(self):
        source = "if True:\n    pass"
        tokens = tokenize(source)
        # 'if' at line 1 col 1 to 1:3
        self.assertEqual(tokens[0].kind, TokenKind.IF)
        self.assertEqual(tokens[0].span.start, SourceLocation(1, 1))
        self.assertEqual(tokens[0].span.end, SourceLocation(1, 3))

        # 'True' at line 1 col 4 to 1:8
        self.assertEqual(tokens[1].kind, TokenKind.TRUE)
        self.assertEqual(tokens[1].span.start, SourceLocation(1, 4))
        self.assertEqual(tokens[1].span.end, SourceLocation(1, 8))

        # ':' at line 1 col 8 to 1:9
        self.assertEqual(tokens[2].kind, TokenKind.COLON)
        self.assertEqual(tokens[2].span.start, SourceLocation(1, 8))
        self.assertEqual(tokens[2].span.end, SourceLocation(1, 9))

    def test_unsupported_characters_fail_explicitly(self):
        unsupported_samples = [
            "a + b",
            "a & b",
            "a < b",
            "a ! b",
            "@decorator",
            "$dollar",
        ]
        for src in unsupported_samples:
            with self.subTest(src=src):
                with self.assertRaises(LexerError):
                    tokenize(src)

    def test_invalid_unindent_fails_explicitly(self):
        source = (
            "if True:\n"
            "    pass\n"
            "  pass\n"
        )
        with self.assertRaises(LexerError) as ctx:
            tokenize(source)
        self.assertIn("Unindent", str(ctx.exception))

    def test_unmatched_parentheses_fail_explicitly(self):
        with self.assertRaises(LexerError):
            tokenize(")")
        with self.assertRaises(LexerError):
            tokenize("(True AND False")


if __name__ == "__main__":
    unittest.main()
