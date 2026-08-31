"""Tests for structured diagnostic representation and adaptive renderer in xoxlang.diagnostics."""
import unittest
from xoxlang.tokens import SourceLocation, SourceSpan
from xoxlang.diagnostics import (
    Diagnostic,
    DiagnosticCategory,
    TypeDiagnosticError,
    ExhaustivenessError,
    MissingReturnError,
    render_diagnostic,
)


class TestStructuredDiagnostics(unittest.TestCase):
    def test_primary_error_renders_alone_without_empty_sections(self):
        diag = Diagnostic(
            category=DiagnosticCategory.SYNTAX_ERROR,
            message="Expected ':' after if condition.",
            primary_error="Expected ':' after if condition.",
        )
        rendered = render_diagnostic(diag)
        self.assertEqual(rendered, "SyntaxError: Expected ':' after if condition.")
        self.assertNotIn("Note:", rendered)
        self.assertNotIn("Help:", rendered)
        self.assertNotIn("Alternatives:", rendered)
        self.assertNotIn("WHO:", rendered)
        self.assertNotIn("WHAT:", rendered)
        self.assertNotIn("WHEN:", rendered)
        self.assertNotIn("WHERE:", rendered)
        self.assertNotIn("WHY:", rendered)
        self.assertNotIn("HOW:", rendered)

    def test_filename_line_and_column_render_from_span(self):
        span = SourceSpan(SourceLocation(3, 5), SourceLocation(3, 12))
        diag = Diagnostic(
            category=DiagnosticCategory.TYPE_ERROR,
            message="Expected Bool, found XoX.",
            span=span,
        )
        rendered = render_diagnostic(diag, filename="test.xox")
        self.assertTrue(rendered.startswith("test.xox:3:5: TypeError: Expected Bool, found XoX."))

    def test_source_excerpt_and_caret_column_alignment(self):
        source = "x = True\nif status:\n    pass\n"
        span = SourceSpan(SourceLocation(2, 4), SourceLocation(2, 10))
        diag = Diagnostic(
            category=DiagnosticCategory.EXHAUSTIVENESS_ERROR,
            message="This XoX condition does not handle Unknown.",
            span=span,
        )
        rendered = render_diagnostic(diag, source_text=source, filename="main.xox")
        lines = rendered.splitlines()
        self.assertEqual(lines[0], "main.xox:2:4: ExhaustivenessError: This XoX condition does not handle Unknown.")
        self.assertEqual(lines[1], "  if status:")
        self.assertEqual(lines[2], "     ^^^^^^")

    def test_same_line_multi_character_caret_range(self):
        source = "res = x.unwrap_or()\n"
        span = SourceSpan(SourceLocation(1, 7), SourceLocation(1, 18))
        diag = Diagnostic(
            category=DiagnosticCategory.SYNTAX_ERROR,
            message="Missing mandatory fallback argument in 'unwrap_or()'",
            span=span,
        )
        rendered = render_diagnostic(diag, source_text=source)
        lines = rendered.splitlines()
        self.assertEqual(lines[0], "1:7: SyntaxError: Missing mandatory fallback argument in 'unwrap_or()'")
        self.assertEqual(lines[1], "  res = x.unwrap_or()")
        self.assertEqual(lines[2], "        ^^^^^^^^^^^")

    def test_multiline_span_degrades_safely_to_first_line(self):
        source = "fn compute(\n    x: Bool,\n) -> XoX:\n    pass\n"
        span = SourceSpan(SourceLocation(1, 1), SourceLocation(4, 9))
        diag = Diagnostic(
            category=DiagnosticCategory.MISSING_RETURN_ERROR,
            message="Function 'compute' does not return a value on every control-flow path.",
            span=span,
        )
        rendered = render_diagnostic(diag, source_text=source, filename="app.xox")
        lines = rendered.splitlines()
        self.assertEqual(lines[0], "app.xox:1:1: MissingReturnError: Function 'compute' does not return a value on every control-flow path.")
        self.assertEqual(lines[1], "  fn compute(")
        self.assertEqual(lines[2], "  ^")

    def test_missing_source_text_renders_location_and_error(self):
        span = SourceSpan(SourceLocation(10, 2), SourceLocation(10, 5))
        diag = Diagnostic(
            category=DiagnosticCategory.TYPE_ERROR,
            message="Cannot combine Bool and XoX.",
            span=span,
        )
        rendered = render_diagnostic(diag, source_text=None, filename="src.xox")
        self.assertEqual(rendered, "src.xox:10:2: TypeError: Cannot combine Bool and XoX.")

    def test_invalid_or_out_of_range_coordinates_degrade_safely(self):
        source = "x = 1\n"
        span = SourceSpan(SourceLocation(99, 10), SourceLocation(99, 20))
        diag = Diagnostic(
            category=DiagnosticCategory.TYPE_ERROR,
            message="Out-of-range span test.",
            span=span,
        )
        rendered = render_diagnostic(diag, source_text=source, filename="file.xox")
        self.assertEqual(rendered, "file.xox:99:10: TypeError: Out-of-range span test.")

    def test_note_renders_only_when_explicitly_supplied(self):
        diag_without_note = Diagnostic(
            category=DiagnosticCategory.TYPE_ERROR,
            message="Type mismatch.",
        )
        self.assertNotIn("Note:", render_diagnostic(diag_without_note))

        diag_with_note = Diagnostic(
            category=DiagnosticCategory.TYPE_ERROR,
            message="Type mismatch.",
            note="XoX conditionals require 3-way branching for Unknown.",
        )
        rendered = render_diagnostic(diag_with_note)
        self.assertIn("Note: XoX conditionals require 3-way branching for Unknown.", rendered)

    def test_help_renders_only_when_explicitly_supplied(self):
        diag_without_help = Diagnostic(
            category=DiagnosticCategory.TYPE_ERROR,
            message="Cannot use xen with Bool.",
        )
        self.assertNotIn("Help:", render_diagnostic(diag_without_help))

        diag_with_help = Diagnostic(
            category=DiagnosticCategory.TYPE_ERROR,
            message="Cannot use xen with Bool.",
            help="Remove the 'xen' clause or promote condition with 'xox(...)'.",
        )
        rendered = render_diagnostic(diag_with_help)
        self.assertIn("Help: Remove the 'xen' clause or promote condition with 'xox(...)'.", rendered)

    def test_alternatives_render_only_when_supplied_and_preserve_order(self):
        diag_without_alts = Diagnostic(
            category=DiagnosticCategory.TYPE_ERROR,
            message="Expected Bool, found XoX.",
        )
        self.assertNotIn("Alternatives:", render_diagnostic(diag_without_alts))

        alts = [
            "Collapse to Bool with explicit fallback: 'expr.unwrap_or(False)'",
            "Update parameter annotation to 'XoX'",
        ]
        diag_with_alts = Diagnostic(
            category=DiagnosticCategory.TYPE_ERROR,
            message="Expected Bool, found XoX.",
            alternatives=alts,
        )
        rendered = render_diagnostic(diag_with_alts)
        self.assertIn("Alternatives:", rendered)
        lines = rendered.splitlines()
        alt_indices = [i for i, l in enumerate(lines) if l.strip().startswith("- ")]
        self.assertEqual(len(alt_indices), 2)
        self.assertIn("Collapse to Bool", lines[alt_indices[0]])
        self.assertIn("Update parameter annotation", lines[alt_indices[1]])

    def test_no_mechanical_5wh_labels_and_no_hallucinated_advice(self):
        diag = Diagnostic(
            category=DiagnosticCategory.SYNTAX_ERROR,
            message="Invalid syntax",
        )
        rendered = render_diagnostic(diag)
        for label in ("WHO:", "WHAT:", "WHEN:", "WHERE:", "WHY:", "HOW:"):
            self.assertNotIn(label, rendered)
        self.assertNotIn("Help:", rendered)
        self.assertNotIn("Alternatives:", rendered)
        self.assertNotIn("Note:", rendered)

    def test_existing_exception_str_compatibility(self):
        span = SourceSpan(SourceLocation(1, 1), SourceLocation(1, 5))
        e1 = TypeDiagnosticError("Cannot combine Bool and XoX", span=span, violated_rule="§7")
        self.assertEqual(str(e1), "TypeError: Cannot combine Bool and XoX")
        self.assertEqual(e1.message, "Cannot combine Bool and XoX")
        self.assertEqual(e1.span, span)
        self.assertEqual(e1.violated_rule, "§7")

        e2 = ExhaustivenessError("Missing 'xen' clause", span=span, violated_rule="§10")
        self.assertEqual(str(e2), "ExhaustivenessError: Missing 'xen' clause")

        e3 = MissingReturnError("Function 'f' missing return", span=span, violated_rule="§11")
        self.assertEqual(str(e3), "MissingReturnError: Function 'f' missing return")

    def test_exception_to_diagnostic_and_renderer(self):
        span = SourceSpan(SourceLocation(2, 5), SourceLocation(2, 9))
        exc = TypeDiagnosticError(
            "Cannot use 'xen' with Bool condition",
            span=span,
            note="Bool conditions only have True and False states.",
            help="Remove 'xen' or wrap condition in 'xox(...)'.",
        )
        rendered = exc.render(source_text="if flag:\n    pass\nxen:\n    pass\n", filename="test.xox")
        self.assertIn("test.xox:2:5: TypeError: Cannot use 'xen' with Bool condition", rendered)
        self.assertIn("Note: Bool conditions only have True and False states.", rendered)
        self.assertIn("Help: Remove 'xen' or wrap condition in 'xox(...)'.", rendered)

    def test_lexer_error_adapter_and_render(self):
        from xoxlang.lexer import LexerError
        err = LexerError("Unsupported character '@'", SourceLocation(1, 4), filename="sample.xox")
        diag = err.to_diagnostic()
        self.assertEqual(diag.category, DiagnosticCategory.SYNTAX_ERROR)
        self.assertEqual(diag.primary_error, "Unsupported character '@'")
        self.assertIsNotNone(diag.span)
        self.assertEqual(diag.span.start, SourceLocation(1, 4))
        rendered = err.render(source_text="fn @():\n    pass\n")
        self.assertIn("sample.xox:1:4: SyntaxError: Unsupported character '@'", rendered)
        self.assertIn("fn @():", rendered)

    def test_parse_error_adapter_and_render(self):
        from xoxlang.parser import ParseError
        err = ParseError("Expected ':' after if condition", SourceLocation(2, 8), filename="test.xox")
        diag = err.to_diagnostic()
        self.assertEqual(diag.category, DiagnosticCategory.SYNTAX_ERROR)
        self.assertEqual(diag.primary_error, "Expected ':' after if condition")
        self.assertEqual(diag.span.start, SourceLocation(2, 8))
        rendered = err.render(source_text="if a\n    pass\n")
        self.assertIn("test.xox:2:8: SyntaxError: Expected ':' after if condition", rendered)

    def test_top_level_package_export(self):
        import xoxlang
        self.assertTrue(hasattr(xoxlang, "render_diagnostic"))
        self.assertTrue(hasattr(xoxlang, "Diagnostic"))
        self.assertTrue(hasattr(xoxlang, "DiagnosticCategory"))
        self.assertTrue(hasattr(xoxlang, "XoX"))
        self.assertTrue(hasattr(xoxlang, "xox_not"))
        self.assertTrue(hasattr(xoxlang, "xox_and"))
        self.assertTrue(hasattr(xoxlang, "xox_or"))
        self.assertTrue(hasattr(xoxlang, "UnknownValueError"))
        self.assertTrue(hasattr(xoxlang, "DefinednessPreconditionError"))

    def test_public_api_all_exports_present_in_package_root(self):
        import xoxlang
        for symbol in xoxlang.__all__:
            self.assertTrue(
                hasattr(xoxlang, symbol),
                f"Symbol '{symbol}' in __all__ must be directly accessible from top-level package namespace"
            )
        self.assertEqual(len(xoxlang.__all__), len(set(xoxlang.__all__)), "__all__ must contain no duplicate entries")

    def test_public_api_runtime_execution_via_root_import(self):
        from xoxlang import XoX, xox_and, xox_not, xox_or
        self.assertIs(xox_not(XoX.UNKNOWN), XoX.UNKNOWN)
        self.assertIs(xox_and(XoX.FALSE, XoX.UNKNOWN), XoX.FALSE)
        self.assertIs(xox_or(XoX.TRUE, XoX.UNKNOWN), XoX.TRUE)
        self.assertTrue(XoX.TRUE.unwrap_bool())
        self.assertFalse(XoX.FALSE.unwrap_bool())

    def test_public_api_exceptions_catchable_from_root(self):
        from xoxlang import DefinednessPreconditionError, UnknownValueError, XoX
        with self.assertRaises(UnknownValueError):
            XoX.UNKNOWN.unwrap_bool()

        with self.assertRaises(DefinednessPreconditionError):
            raise DefinednessPreconditionError("Precondition failure")

    def test_compile_source_raises_raw_exceptions_directly(self):
        from xoxlang import compile_source
        from xoxlang.lexer import LexerError
        from xoxlang.parser import ParseError

        # Lexer error raised directly
        with self.assertRaises(LexerError) as ctx_lex:
            compile_source("fn @():\n    pass\n")
        self.assertIsInstance(ctx_lex.exception, LexerError)
        self.assertIn("LexerError:", str(ctx_lex.exception))

        # Parse error raised directly
        with self.assertRaises(ParseError) as ctx_parse:
            compile_source("fn f():\n    return\n")
        self.assertIsInstance(ctx_parse.exception, ParseError)
        self.assertIn("SyntaxError:", str(ctx_parse.exception))

        # Type error raised directly
        with self.assertRaises(TypeDiagnosticError) as ctx_type:
            compile_source("fn f(x: Bool) -> XoX:\n    if x:\n        return True\n    xen:\n        ignore\n")
        self.assertIsInstance(ctx_type.exception, TypeDiagnosticError)
        self.assertIn("TypeError:", str(ctx_type.exception))

        # Exhaustiveness error raised directly
        with self.assertRaises(ExhaustivenessError) as ctx_exh:
            compile_source("fn f(x: XoX) -> Bool:\n    if x:\n        return True\n    else:\n        return False\n")
        self.assertIsInstance(ctx_exh.exception, ExhaustivenessError)
        self.assertIn("ExhaustivenessError:", str(ctx_exh.exception))

        # Missing return error raised directly
        with self.assertRaises(MissingReturnError) as ctx_ret:
            compile_source("fn f(x: Bool) -> Bool:\n    if x:\n        return True\n")
        self.assertIsInstance(ctx_ret.exception, MissingReturnError)
        self.assertIn("MissingReturnError:", str(ctx_ret.exception))

    def test_all_five_adapters_preserve_primary_error_and_span(self):
        from xoxlang.lexer import LexerError
        from xoxlang.parser import ParseError

        loc = SourceLocation(5, 10)
        span = SourceSpan(SourceLocation(5, 10), SourceLocation(5, 20))

        lex_err = LexerError("Bad token", loc)
        lex_diag = lex_err.to_diagnostic()
        self.assertEqual(lex_diag.primary_error, "Bad token")
        self.assertEqual(lex_diag.span.start, loc)

        parse_err = ParseError("Bad syntax", loc)
        parse_diag = parse_err.to_diagnostic()
        self.assertEqual(parse_diag.primary_error, "Bad syntax")
        self.assertEqual(parse_diag.span.start, loc)

        type_err = TypeDiagnosticError("Bad type", span=span, violated_rule="§7")
        type_diag = type_err.to_diagnostic()
        self.assertEqual(type_diag.primary_error, "Bad type")
        self.assertEqual(type_diag.span, span)
        self.assertEqual(type_diag.violated_rule, "§7")

        exh_err = ExhaustivenessError("Non-exhaustive", span=span, violated_rule="§10")
        exh_diag = exh_err.to_diagnostic()
        self.assertEqual(exh_diag.primary_error, "Non-exhaustive")
        self.assertEqual(exh_diag.span, span)

        ret_err = MissingReturnError("Missing return", span=span, violated_rule="§11")
        ret_diag = ret_err.to_diagnostic()
        self.assertEqual(ret_diag.primary_error, "Missing return")
        self.assertEqual(ret_diag.span, span)

    def test_runtime_unknown_value_error_remains_deferred(self):
        from xoxlang.runtime import UnknownValueError
        err = UnknownValueError("Cannot unwrap")
        self.assertFalse(hasattr(err, "to_diagnostic"))
        self.assertFalse(hasattr(err, "render"))
        self.assertEqual(str(err), "Cannot unwrap")

    def test_ctx_diag_03_non_xox_source_structured_metadata(self):
        from xoxlang import compile_source
        source = "b: Bool = True\nres = b.unwrap_or(False)\n"
        with self.assertRaises(TypeDiagnosticError) as ctx:
            compile_source(source)
        exc = ctx.exception
        self.assertEqual(exc.message, "'unwrap_or(...)' works on an XoX value, but this value is Bool.")
        self.assertEqual(exc.note, "The fallback is only used when an XoX value is Unknown.")
        self.assertIsNone(exc.help)
        self.assertIsNotNone(exc.alternatives)
        self.assertEqual(len(exc.alternatives), 1)
        self.assertIn("xox(...)", exc.alternatives[0])
        self.assertEqual(exc.annotations, {"source_type": "Bool"})
        self.assertEqual(exc.violated_rule, "§3, §19")
        self.assertIsNotNone(exc.span)
        self.assertEqual(str(exc), "TypeError: 'unwrap_or(...)' works on an XoX value, but this value is Bool.")

        diag = exc.to_diagnostic()
        self.assertEqual(diag.primary_error, "'unwrap_or(...)' works on an XoX value, but this value is Bool.")
        self.assertEqual(diag.note, "The fallback is only used when an XoX value is Unknown.")
        self.assertIsNone(diag.help)
        self.assertIsNotNone(diag.alternatives)
        self.assertEqual(diag.alternatives, ["If you intended three-state logic here, convert the Bool with xox(...)."])

        rendered = exc.render(source_text=source, filename="main.xox")
        self.assertIn("main.xox:2:7: TypeError: 'unwrap_or(...)' works on an XoX value, but this value is Bool.", rendered)
        self.assertIn("  res = b.unwrap_or(False)", rendered)
        self.assertIn("  Note: The fallback is only used when an XoX value is Unknown.", rendered)
        self.assertIn("  Alternatives:", rendered)
        self.assertIn("    - If you intended three-state logic here, convert the Bool with xox(...).", rendered)
        self.assertNotIn("Help:", rendered)

    def test_ctx_diag_03_non_bool_fallback_structured_metadata(self):
        from xoxlang import compile_source
        source = "x: XoX = True\nres = x.unwrap_or(Unknown)\n"
        with self.assertRaises(TypeDiagnosticError) as ctx:
            compile_source(source)
        exc = ctx.exception
        self.assertEqual(exc.message, "'unwrap_or(...)' needs a Bool fallback, but this fallback is XoX.")
        self.assertEqual(exc.note, "The fallback is evaluated only when the source is Unknown and must produce the final True or False result.")
        self.assertEqual(exc.help, "Use an expression whose type is Bool as the fallback.")
        self.assertIsNone(exc.alternatives)
        self.assertEqual(exc.annotations, {"fallback_type": "XoX"})
        self.assertEqual(exc.violated_rule, "§3, §19")
        self.assertIsNotNone(exc.span)
        self.assertEqual(str(exc), "TypeError: 'unwrap_or(...)' needs a Bool fallback, but this fallback is XoX.")

        diag = exc.to_diagnostic()
        self.assertEqual(diag.primary_error, "'unwrap_or(...)' needs a Bool fallback, but this fallback is XoX.")
        self.assertEqual(diag.note, "The fallback is evaluated only when the source is Unknown and must produce the final True or False result.")
        self.assertEqual(diag.help, "Use an expression whose type is Bool as the fallback.")
        self.assertIsNone(diag.alternatives)

        rendered = exc.render(source_text=source, filename="main.xox")
        self.assertIn("main.xox:2:19: TypeError: 'unwrap_or(...)' needs a Bool fallback, but this fallback is XoX.", rendered)
        self.assertIn("  res = x.unwrap_or(Unknown)", rendered)
        self.assertIn("  Note: The fallback is evaluated only when the source is Unknown and must produce the final True or False result.", rendered)
        self.assertIn("  Help: Use an expression whose type is Bool as the fallback.", rendered)
        self.assertNotIn("Alternatives:", rendered)
        self.assertNotIn("literal", rendered.lower())

    def test_ctx_diag_03_arbitrary_bool_fallback_expression_accepted(self):
        from xoxlang import compile_source
        source = "t: XoX = Unknown\na: Bool = True\nb: Bool = False\nres = t.unwrap_or(a AND b)\n"
        compiled = compile_source(source)
        self.assertIsInstance(compiled, str)

    def test_ctx_diag_04_missing_xen_structured_metadata(self):
        from xoxlang import compile_source
        source = (
            "status: XoX = Unknown\n"
            "if status:\n"
            "    pass\n"
            "else:\n"
            "    pass\n"
        )
        with self.assertRaises(ExhaustivenessError) as ctx:
            compile_source(source)
        exc = ctx.exception
        self.assertEqual(exc.message, "This XoX condition does not handle Unknown (missing 'xen' clause).")
        self.assertEqual(exc.note, "A 'xen' branch handles the case where an XoX condition evaluates to Unknown.")
        self.assertIsNone(exc.help)
        self.assertIsNotNone(exc.alternatives)
        self.assertEqual(len(exc.alternatives), 2)
        self.assertEqual(exc.alternatives[0], "Add a 'xen' branch to handle Unknown.")
        self.assertEqual(exc.alternatives[1], "Use 'xen: ignore' if intentionally doing nothing for Unknown is correct.")
        self.assertEqual(exc.violated_rule, "§10")
        self.assertIsNotNone(exc.span)
        self.assertEqual(str(exc), "ExhaustivenessError: This XoX condition does not handle Unknown (missing 'xen' clause).")

        diag = exc.to_diagnostic()
        self.assertEqual(diag.primary_error, "This XoX condition does not handle Unknown (missing 'xen' clause).")
        self.assertEqual(diag.note, "A 'xen' branch handles the case where an XoX condition evaluates to Unknown.")
        self.assertIsNone(diag.help)
        self.assertEqual(len(diag.alternatives), 2)

        rendered = exc.render(source_text=source, filename="main.xox")
        self.assertIn("main.xox:2:1: ExhaustivenessError: This XoX condition does not handle Unknown", rendered)
        self.assertIn("  Note: A 'xen' branch handles the case where an XoX condition evaluates to Unknown.", rendered)
        self.assertIn("  Alternatives:", rendered)
        self.assertIn("    - Add a 'xen' branch to handle Unknown.", rendered)
        self.assertIn("    - Use 'xen: ignore' if intentionally doing nothing for Unknown is correct.", rendered)
        self.assertNotIn("Help:", rendered)
        self.assertNotIn("non-exhaustive", rendered.lower())

    def test_ctx_diag_04_missing_else_structured_metadata(self):
        from xoxlang import compile_source
        source = (
            "status: XoX = Unknown\n"
            "if status:\n"
            "    pass\n"
            "xen:\n"
            "    ignore\n"
        )
        with self.assertRaises(ExhaustivenessError) as ctx:
            compile_source(source)
        exc = ctx.exception
        self.assertEqual(exc.message, "This XoX condition does not handle False (missing 'else' clause).")
        self.assertEqual(exc.note, "An 'else' branch handles the False case.")
        self.assertEqual(exc.help, "Add an 'else' branch to handle False.")
        self.assertIsNone(exc.alternatives)
        self.assertEqual(exc.violated_rule, "§10")
        self.assertIsNotNone(exc.span)
        self.assertEqual(str(exc), "ExhaustivenessError: This XoX condition does not handle False (missing 'else' clause).")

        diag = exc.to_diagnostic()
        self.assertEqual(diag.primary_error, "This XoX condition does not handle False (missing 'else' clause).")
        self.assertEqual(diag.note, "An 'else' branch handles the False case.")
        self.assertEqual(diag.help, "Add an 'else' branch to handle False.")
        self.assertIsNone(diag.alternatives)

        rendered = exc.render(source_text=source, filename="main.xox")
        self.assertIn("main.xox:2:1: ExhaustivenessError: This XoX condition does not handle False", rendered)
        self.assertIn("  Note: An 'else' branch handles the False case.", rendered)
        self.assertIn("  Help: Add an 'else' branch to handle False.", rendered)
        self.assertNotIn("Alternatives:", rendered)
        self.assertNotIn("non-exhaustive", rendered.lower())

    def test_ctx_diag_04_missing_both_structured_metadata(self):
        from xoxlang import compile_source
        source = (
            "status: XoX = Unknown\n"
            "if status:\n"
            "    pass\n"
        )
        with self.assertRaises(ExhaustivenessError) as ctx:
            compile_source(source)
        exc = ctx.exception
        self.assertEqual(exc.message, "This XoX condition does not handle Unknown or False (missing both 'xen' and 'else' clauses).")
        self.assertEqual(exc.note, "XoX conditions can be True, False, or Unknown.")
        self.assertEqual(exc.help, "Add an 'else' branch to handle False.")
        self.assertIsNotNone(exc.alternatives)
        self.assertEqual(len(exc.alternatives), 2)
        self.assertEqual(exc.violated_rule, "§10")
        self.assertIsNotNone(exc.span)

        rendered = exc.render(source_text=source, filename="main.xox")
        self.assertIn("main.xox:2:1: ExhaustivenessError: This XoX condition does not handle Unknown or False", rendered)
        self.assertIn("  Note: XoX conditions can be True, False, or Unknown.", rendered)
        self.assertIn("  Help: Add an 'else' branch to handle False.", rendered)
        self.assertIn("  Alternatives:", rendered)
        self.assertIn("    - Add a 'xen' branch to handle Unknown.", rendered)
        self.assertIn("    - Use 'xen: ignore' if intentionally doing nothing for Unknown is correct.", rendered)

    def test_ctx_diag_04_inline_missing_xen_structured_metadata(self):
        from xoxlang import compile_source
        source = "status: XoX = Unknown\nres = True if status else False\n"
        with self.assertRaises(ExhaustivenessError) as ctx:
            compile_source(source)
        exc = ctx.exception
        self.assertEqual(exc.message, "This inline XoX conditional has no result for Unknown (missing 'xen' branch).")
        self.assertEqual(exc.note, "The 'xen' branch supplies the result when the condition is Unknown.")
        self.assertEqual(exc.help, "Add a 'xen' result for the Unknown case.")
        self.assertIsNone(exc.alternatives)
        self.assertEqual(exc.violated_rule, "§5, §10")
        self.assertIsNotNone(exc.span)

        rendered = exc.render(source_text=source, filename="main.xox")
        self.assertIn("main.xox:2:7: ExhaustivenessError: This inline XoX conditional has no result for Unknown", rendered)
        self.assertIn("  Note: The 'xen' branch supplies the result when the condition is Unknown.", rendered)
        self.assertIn("  Help: Add a 'xen' result for the Unknown case.", rendered)
        self.assertNotIn("Alternatives:", rendered)

    def test_ctx_diag_02_mixed_and_structured_metadata(self):
        from xoxlang import compile_source
        source = "b: Bool = True\nx: XoX = Unknown\nres = b AND x\n"
        with self.assertRaises(TypeDiagnosticError) as ctx:
            compile_source(source)
        exc = ctx.exception
        self.assertEqual(exc.message, "Cannot combine Bool and XoX with logical operator 'AND'.")
        self.assertEqual(exc.annotations, {"left_type": "Bool", "right_type": "XoX"})
        self.assertEqual(exc.note, "Bool has only True and False, while XoX can also be Unknown. XoXLang does not combine those domains implicitly.")
        self.assertIsNone(exc.help)
        self.assertIsNotNone(exc.alternatives)
        self.assertEqual(len(exc.alternatives), 2)
        self.assertEqual(exc.alternatives[0], "If three-state logic is intended, convert the Bool operand with xox(...).")
        self.assertEqual(exc.alternatives[1], "If two-state Bool logic is intended, keep both operands in the Bool domain instead.")
        self.assertEqual(exc.violated_rule, "§7, §19")
        self.assertIsNotNone(exc.span)

        rendered = exc.render(source_text=source, filename="main.xox")
        self.assertIn("main.xox:3:7: TypeError: Cannot combine Bool and XoX with logical operator 'AND'.", rendered)
        self.assertIn("  res = b AND x", rendered)
        self.assertIn("  Note: Bool has only True and False, while XoX can also be Unknown.", rendered)
        self.assertIn("  Alternatives:", rendered)
        self.assertIn("    - If three-state logic is intended, convert the Bool operand with xox(...).", rendered)
        self.assertIn("    - If two-state Bool logic is intended, keep both operands in the Bool domain instead.", rendered)
        self.assertNotIn("Help:", rendered)
        self.assertNotIn("XoX.from_bool", rendered)
        self.assertNotIn("implicit mixing", rendered)
        self.assertNotIn("homogeneous types", rendered)

    def test_ctx_diag_02_mixed_or_structured_metadata(self):
        from xoxlang import compile_source
        source = "x: XoX = Unknown\nb: Bool = False\nres = x OR b\n"
        with self.assertRaises(TypeDiagnosticError) as ctx:
            compile_source(source)
        exc = ctx.exception
        self.assertEqual(exc.message, "Cannot combine XoX and Bool with logical operator 'OR'.")
        self.assertEqual(exc.annotations, {"left_type": "XoX", "right_type": "Bool"})
        self.assertIsNone(exc.help)
        self.assertEqual(len(exc.alternatives), 2)

        rendered = exc.render(source_text=source, filename="main.xox")
        self.assertIn("TypeError: Cannot combine XoX and Bool with logical operator 'OR'.", rendered)
        self.assertIn("  Alternatives:", rendered)

    def test_ctx_diag_02_mixed_equality_structured_metadata(self):
        from xoxlang import compile_source
        source = "b: Bool = True\nx: XoX = Unknown\nres = b == x\n"
        with self.assertRaises(TypeDiagnosticError) as ctx:
            compile_source(source)
        exc = ctx.exception
        self.assertEqual(exc.message, "Cannot compare Bool and XoX with equality operator '=='.")
        self.assertEqual(exc.annotations, {"left_type": "Bool", "right_type": "XoX"})
        self.assertEqual(exc.note, "Bool and XoX are different semantic domains, so equality requires both operands to use the same domain.")
        self.assertIsNone(exc.help)
        self.assertIsNotNone(exc.alternatives)
        self.assertEqual(len(exc.alternatives), 2)
        self.assertEqual(exc.alternatives[0], "If you want to compare in three-state logic, convert the Bool operand with xox(...).")
        self.assertEqual(exc.alternatives[1], "If the comparison should remain two-state, keep both values as Bool.")
        self.assertEqual(exc.violated_rule, "§8, §19")
        self.assertIsNotNone(exc.span)

        rendered = exc.render(source_text=source, filename="main.xox")
        self.assertIn("main.xox:3:7: TypeError: Cannot compare Bool and XoX with equality operator '=='.", rendered)
        self.assertIn("  res = b == x", rendered)
        self.assertIn("  Note: Bool and XoX are different semantic domains", rendered)
        self.assertIn("  Alternatives:", rendered)
        self.assertIn("    - If you want to compare in three-state logic, convert the Bool operand with xox(...).", rendered)
        self.assertIn("    - If the comparison should remain two-state, keep both values as Bool.", rendered)
        self.assertNotIn("Help:", rendered)
        self.assertNotIn("XoX.from_bool", rendered)
        self.assertNotIn("homogeneous types", rendered)

    def test_ctx_diag_02_mixed_inequality_structured_metadata(self):
        from xoxlang import compile_source
        source = "x: XoX = Unknown\nb: Bool = True\nres = x != b\n"
        with self.assertRaises(TypeDiagnosticError) as ctx:
            compile_source(source)
        exc = ctx.exception
        self.assertEqual(exc.message, "Cannot compare XoX and Bool with equality operator '!='.")
        self.assertEqual(exc.annotations, {"left_type": "XoX", "right_type": "Bool"})
        self.assertIsNone(exc.help)
        self.assertEqual(len(exc.alternatives), 2)

        rendered = exc.render(source_text=source, filename="main.xox")
        self.assertIn("TypeError: Cannot compare XoX and Bool with equality operator '!='.", rendered)
        self.assertIn("  Alternatives:", rendered)

    def test_ctx_diag_06_missing_return_structured_metadata(self):
        from xoxlang import compile_source
        source = (
            "fn compute(flag: Bool) -> XoX:\n"
            "    if flag:\n"
            "        return True\n"
        )
        with self.assertRaises(MissingReturnError) as ctx:
            compile_source(source)
        exc = ctx.exception
        self.assertIn("Function 'compute' can finish without returning a value", exc.message)
        self.assertEqual(exc.annotations, {"function_name": "compute", "return_type": "XoX"})
        self.assertEqual(exc.note, "The function is declared to return XoX, so every possible execution path must return a XoX value.")
        self.assertEqual(exc.help, "Make sure every possible path returns a XoX value.")
        self.assertIsNone(exc.alternatives)
        self.assertEqual(exc.violated_rule, "§11, §19")
        self.assertIsNotNone(exc.span)
        self.assertIn("MissingReturnError: Function 'compute' can finish without returning a value", str(exc))

        diag = exc.to_diagnostic()
        self.assertIn("Function 'compute' can finish without returning a value", diag.primary_error)
        self.assertEqual(diag.note, "The function is declared to return XoX, so every possible execution path must return a XoX value.")
        self.assertEqual(diag.help, "Make sure every possible path returns a XoX value.")
        self.assertIsNone(diag.alternatives)
        self.assertEqual(diag.annotations, {"function_name": "compute", "return_type": "XoX"})

        rendered = exc.render(source_text=source, filename="app.xox")
        self.assertIn("app.xox:1:24: MissingReturnError: Function 'compute' can finish without returning a value", rendered)
        self.assertIn("fn compute(flag: Bool) -> XoX:", rendered)
        self.assertIn("  Note: The function is declared to return XoX, so every possible execution path must return a XoX value.", rendered)
        self.assertIn("  Help: Make sure every possible path returns a XoX value.", rendered)
        self.assertNotIn("Alternatives:", rendered)
        self.assertNotIn("CFG", rendered)
    def test_lexer_error_structured_metadata_support(self):
        from xoxlang.lexer import LexerError
        loc = SourceLocation(3, 5)

        # Legacy constructor check
        legacy_err = LexerError("Invalid byte", loc, "foo.xox")
        self.assertEqual(str(legacy_err), "foo.xox:3:5: LexerError: Invalid byte")
        self.assertIsNone(legacy_err.note)
        self.assertIsNone(legacy_err.help)
        self.assertIsNone(legacy_err.alternatives)
        self.assertIsNone(legacy_err.annotations)
        legacy_diag = legacy_err.to_diagnostic()
        self.assertIsNone(legacy_diag.note)
        self.assertIsNone(legacy_diag.help)
        self.assertIsNone(legacy_diag.alternatives)
        self.assertIsNone(legacy_diag.annotations)

        # Structured constructor check
        rich_err = LexerError(
            "Unsupported character '$'",
            loc,
            "foo.xox",
            note="XoXLang source files use UTF-8 characters without currency symbols.",
            help="Remove the '$' symbol.",
            alternatives=["Use a valid identifier.", "Remove the character."],
            annotations={"char": "$"},
        )
        self.assertEqual(str(rich_err), "foo.xox:3:5: LexerError: Unsupported character '$'")
        self.assertEqual(rich_err.note, "XoXLang source files use UTF-8 characters without currency symbols.")
        self.assertEqual(rich_err.help, "Remove the '$' symbol.")
        self.assertEqual(rich_err.alternatives, ["Use a valid identifier.", "Remove the character."])
        self.assertEqual(rich_err.annotations, {"char": "$"})

        rich_diag = rich_err.to_diagnostic()
        self.assertEqual(rich_diag.category, DiagnosticCategory.SYNTAX_ERROR)
        self.assertEqual(rich_diag.primary_error, "Unsupported character '$'")
        self.assertEqual(rich_diag.note, "XoXLang source files use UTF-8 characters without currency symbols.")
        self.assertEqual(rich_diag.help, "Remove the '$' symbol.")
        self.assertEqual(rich_diag.alternatives, ["Use a valid identifier.", "Remove the character."])
        self.assertEqual(rich_diag.annotations, {"char": "$"})

        rendered = rich_err.render(source_text="x = 1\ny = 2\nz = $ + 3\n")
        self.assertIn("foo.xox:3:5: SyntaxError: Unsupported character '$'", rendered)
        self.assertIn("  z = $ + 3", rendered)
        self.assertIn("  Note: XoXLang source files use UTF-8 characters without currency symbols.", rendered)
        self.assertIn("  Help: Remove the '$' symbol.", rendered)
        self.assertIn("  Alternatives:", rendered)
        self.assertIn("    - Use a valid identifier.", rendered)
        self.assertIn("    - Remove the character.", rendered)

    def test_parse_error_structured_metadata_support(self):
        from xoxlang.parser import ParseError
        loc = SourceLocation(2, 5)

        # Legacy constructor check
        legacy_err = ParseError("Unexpected token", loc, "bar.xox")
        self.assertEqual(str(legacy_err), "bar.xox:2:5: SyntaxError: Unexpected token")
        self.assertIsNone(legacy_err.note)
        self.assertIsNone(legacy_err.help)
        self.assertIsNone(legacy_err.alternatives)
        self.assertIsNone(legacy_err.annotations)
        legacy_diag = legacy_err.to_diagnostic()
        self.assertIsNone(legacy_diag.note)
        self.assertIsNone(legacy_diag.help)
        self.assertIsNone(legacy_diag.alternatives)
        self.assertIsNone(legacy_diag.annotations)

        # Structured constructor check
        rich_err = ParseError(
            "Expected ':' after if condition",
            loc,
            "bar.xox",
            note="Conditional statements require a colon before the indented block.",
            help="Add ':' at the end of the if header.",
            alternatives=["Add ':' after condition.", "Check expression syntax."],
            annotations={"expected": ":"},
        )
        self.assertEqual(str(rich_err), "bar.xox:2:5: SyntaxError: Expected ':' after if condition")
        self.assertEqual(rich_err.note, "Conditional statements require a colon before the indented block.")
        self.assertEqual(rich_err.help, "Add ':' at the end of the if header.")
        self.assertEqual(rich_err.alternatives, ["Add ':' after condition.", "Check expression syntax."])
        self.assertEqual(rich_err.annotations, {"expected": ":"})

        rich_diag = rich_err.to_diagnostic()
        self.assertEqual(rich_diag.category, DiagnosticCategory.SYNTAX_ERROR)
        self.assertEqual(rich_diag.primary_error, "Expected ':' after if condition")
        self.assertEqual(rich_diag.note, "Conditional statements require a colon before the indented block.")
        self.assertEqual(rich_diag.help, "Add ':' at the end of the if header.")
        self.assertEqual(rich_diag.alternatives, ["Add ':' after condition.", "Check expression syntax."])
        self.assertEqual(rich_diag.annotations, {"expected": ":"})

        rendered = rich_err.render(source_text="x = 1\nif x\n    pass\n")
        self.assertIn("bar.xox:2:5: SyntaxError: Expected ':' after if condition", rendered)
        self.assertIn("  if x", rendered)
        self.assertIn("  Note: Conditional statements require a colon before the indented block.", rendered)
        self.assertIn("  Help: Add ':' at the end of the if header.", rendered)
        self.assertIn("  Alternatives:", rendered)
        self.assertIn("    - Add ':' after condition.", rendered)
        self.assertIn("    - Check expression syntax.", rendered)



class TestDiagnosticConformanceFixes(unittest.TestCase):
    """Adversarial and conformance tests verifying zero leakage of AST/TokenKind names and peer-level UX."""

    def test_unbound_identifier_diagnostic(self):
        from xoxlang.lexer import tokenize
        from xoxlang.parser import parse
        from xoxlang.semantic import analyze

        source = "x = missing_var\n"
        with self.assertRaises(TypeDiagnosticError) as ctx:
            analyze(parse(tokenize(source)))
        err = ctx.exception
        self.assertIn("Variable 'missing_var' is not defined.", err.message)
        self.assertIn("Define and initialize 'missing_var' before using it.", err.help)
        self.assertNotIn("Unbound identifier", err.message)
        self.assertNotIn("TokenKind.", err.message)
        self.assertNotIn("AST", err.message)

    def test_unsupported_statement_diagnostic(self):
        from xoxlang.ast import Statement
        from xoxlang.semantic import SemanticAnalyzer

        class DummyCustomStatement(Statement):
            pass

        analyzer = SemanticAnalyzer()
        with self.assertRaises(TypeDiagnosticError) as ctx:
            analyzer.check_statement(DummyCustomStatement())
        err = ctx.exception
        self.assertEqual(err.message, "Unsupported statement syntax.")
        self.assertIn("Supported statements are variable assignments", err.help)
        self.assertNotIn("DummyCustomStatement", err.message)
        self.assertNotIn("AST", err.message)

    def test_unsupported_expression_ast_diagnostic(self):
        from xoxlang.ast import Expression
        from xoxlang.semantic import SemanticAnalyzer

        class DummyCustomExpr(Expression):
            pass

        analyzer = SemanticAnalyzer()
        with self.assertRaises(TypeDiagnosticError) as ctx:
            analyzer.check_expression(DummyCustomExpr())
        err = ctx.exception
        self.assertEqual(err.message, "Unsupported expression syntax.")
        self.assertIn("Use supported literals, identifiers", err.help)
        self.assertNotIn("DummyCustomExpr", err.message)
        self.assertNotIn("AST node", err.message)

    def test_unsupported_unary_operator_diagnostic(self):
        from xoxlang.ast import LiteralExpr, UnaryExpr
        from xoxlang.semantic import SemanticAnalyzer
        from xoxlang.tokens import TokenKind

        # Construct UnaryExpr with unsupported operator
        expr = UnaryExpr(op=TokenKind.ARROW, operand=LiteralExpr(kind=TokenKind.TRUE))
        analyzer = SemanticAnalyzer()
        with self.assertRaises(TypeDiagnosticError) as ctx:
            analyzer.check_expression(expr)
        err = ctx.exception
        self.assertIn("Unsupported unary operator '->'.", err.message)
        self.assertIn("Only 'NOT' is supported for logical unary negation.", err.help)
        self.assertNotIn("TokenKind.", err.message)

    def test_unsupported_binary_operator_diagnostic(self):
        from xoxlang.ast import BinaryExpr, LiteralExpr
        from xoxlang.semantic import SemanticAnalyzer
        from xoxlang.tokens import TokenKind

        # Construct BinaryExpr with unsupported operator
        expr = BinaryExpr(
            left=LiteralExpr(kind=TokenKind.TRUE),
            op=TokenKind.ARROW,
            right=LiteralExpr(kind=TokenKind.FALSE),
        )
        analyzer = SemanticAnalyzer()
        with self.assertRaises(TypeDiagnosticError) as ctx:
            analyzer.check_expression(expr)
        err = ctx.exception
        self.assertIn("Unsupported binary operator '->'.", err.message)
        self.assertIn("Supported binary operators are 'AND', 'OR', '==', and '!='.", err.help)
        self.assertNotIn("TokenKind.", err.message)

    def test_unknown_literal_kind_diagnostic(self):
        from xoxlang.ast import LiteralExpr
        from xoxlang.semantic import SemanticAnalyzer
        from xoxlang.tokens import TokenKind

        expr = LiteralExpr(kind=TokenKind.ARROW)
        analyzer = SemanticAnalyzer()
        with self.assertRaises(TypeDiagnosticError) as ctx:
            analyzer.check_expression(expr)
        err = ctx.exception
        self.assertIn("Unsupported literal value '->'.", err.message)
        self.assertIn("Supported truth literals are 'True', 'False', and 'Unknown'.", err.help)
        self.assertNotIn("TokenKind.", err.message)

    def test_invalid_not_operand_diagnostic(self):
        from xoxlang.ast import IdentifierExpr, UnaryExpr
        from xoxlang.semantic import SemanticAnalyzer, TypeEnv
        from xoxlang.tokens import TokenKind

        analyzer = SemanticAnalyzer(env=TypeEnv({"num": "Int"}))  # type: ignore
        expr = UnaryExpr(op=TokenKind.NOT, operand=IdentifierExpr(name="num"))
        with self.assertRaises(TypeDiagnosticError) as ctx:
            analyzer.check_expression(expr)
        err = ctx.exception
        self.assertIn("Operator 'NOT' cannot be applied to type 'Int'.", err.message)
        self.assertIn("Logical NOT operates exclusively on truth-typed expressions.", err.note)
        self.assertIn("Ensure the operand evaluates to a Bool or XoX value.", err.help)
        self.assertNotIn("TokenKind.", err.message)


if __name__ == "__main__":
    unittest.main()
