"""Bootstrap and architectural structure tests for X-o-X reference compiler."""
import importlib
import unittest


class TestSpecStructure(unittest.TestCase):
    def test_prototype_modules_importable_without_side_effects(self):
        modules = [
            "xoxlang",
            "xoxlang.tokens",
            "xoxlang.lexer",
            "xoxlang.ast",
            "xoxlang.parser",
            "xoxlang.types",
            "xoxlang.semantic",
            "xoxlang.control_flow",
            "xoxlang.diagnostics",
            "xoxlang.runtime",
            "xoxlang.lowering",
        ]
        for mod_name in modules:
            with self.subTest(module=mod_name):
                mod = importlib.import_module(mod_name)
                self.assertIsNotNone(mod)

    def test_one_way_architecture_boundaries(self):
        import xoxlang.tokens as tokens
        self.assertFalse(hasattr(tokens, "parse"))
        self.assertFalse(hasattr(tokens, "lower_to_python"))

        import xoxlang.runtime as runtime
        self.assertFalse(hasattr(runtime, "parse"))
        self.assertFalse(hasattr(runtime, "Parser"))

    def test_diagnostic_categories_match_spec_phase_structure(self):
        from xoxlang.diagnostics import DiagnosticCategory
        categories = {c.name for c in DiagnosticCategory}
        expected = {
            "SYNTAX_ERROR",
            "TYPE_ERROR",
            "EXHAUSTIVENESS_ERROR",
            "MISSING_RETURN_ERROR",
        }
        self.assertEqual(categories, expected)


if __name__ == "__main__":
    unittest.main()
