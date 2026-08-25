"""Bootstrap and architectural structure tests for Trool prototype."""
import importlib
import unittest


class TestSpecStructure(unittest.TestCase):
    def test_prototype_modules_importable_without_side_effects(self):
        modules = [
            "trool",
            "trool.tokens",
            "trool.lexer",
            "trool.ast",
            "trool.parser",
            "trool.types",
            "trool.semantic",
            "trool.control_flow",
            "trool.diagnostics",
            "trool.runtime",
            "trool.lowering",
        ]
        for mod_name in modules:
            with self.subTest(module=mod_name):
                mod = importlib.import_module(mod_name)
                self.assertIsNotNone(mod)

    def test_one_way_architecture_boundaries(self):
        import trool.tokens as tokens
        self.assertFalse(hasattr(tokens, "parse"))
        self.assertFalse(hasattr(tokens, "lower_to_python"))

        import trool.runtime as runtime
        self.assertFalse(hasattr(runtime, "parse"))
        self.assertFalse(hasattr(runtime, "Parser"))

    def test_diagnostic_categories_match_spec_phase_structure(self):
        from trool.diagnostics import DiagnosticCategory
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
