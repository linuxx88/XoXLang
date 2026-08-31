"""Unit tests for XoX (X-o-X) V2 runtime representation, anti-truthiness, conversion, and Strong Kleene semantics."""
import unittest
from enum import Enum, IntEnum
from xoxlang.runtime import XoX, UnknownValueError, xox_not, xox_and, xox_or


class TestXoXRuntime(unittest.TestCase):
    def test_enum_representation_and_member_count(self):
        self.assertTrue(issubclass(XoX, Enum))
        self.assertFalse(issubclass(XoX, IntEnum))
        members = list(XoX)
        self.assertEqual(len(members), 3)
        self.assertEqual({m.name for m in members}, {"FALSE", "TRUE", "UNKNOWN"})

    def test_singleton_identity(self):
        t1 = XoX.TRUE
        t2 = XoX.TRUE
        self.assertIs(t1, t2)

        f1 = XoX.FALSE
        f2 = XoX.FALSE
        self.assertIs(f1, f2)

        u1 = XoX.UNKNOWN
        u2 = XoX.UNKNOWN
        self.assertIs(u1, u2)

        self.assertIsNot(XoX.TRUE, XoX.FALSE)
        self.assertIsNot(XoX.TRUE, XoX.UNKNOWN)
        self.assertIsNot(XoX.FALSE, XoX.UNKNOWN)

    def test_anti_truthiness_protection(self):
        for state in (XoX.TRUE, XoX.FALSE, XoX.UNKNOWN):
            with self.subTest(state=state):
                with self.assertRaises(TypeError) as ctx:
                    bool(state)
                self.assertIn("implicit Boolean truthiness", str(ctx.exception))

    def test_explicit_from_bool_conversion(self):
        self.assertIs(XoX.from_bool(True), XoX.TRUE)
        self.assertIs(XoX.from_bool(False), XoX.FALSE)

        # Rejection of non-bool inputs, especially ints 0 and 1
        invalid_inputs = [0, 1, 2, None, "True", "False", [], {}, ()]
        for val in invalid_inputs:
            with self.subTest(val=val):
                with self.assertRaises(TypeError):
                    XoX.from_bool(val)

    def test_explicit_unwrap_bool_extraction(self):
        self.assertIs(XoX.TRUE.unwrap_bool(), True)
        self.assertIs(XoX.FALSE.unwrap_bool(), False)

        with self.assertRaises(UnknownValueError):
            XoX.UNKNOWN.unwrap_bool()

    def test_no_fallback_extraction_api(self):
        self.assertFalse(hasattr(XoX, "to_bool"))

    def test_strong_kleene_not(self):
        self.assertIs(xox_not(XoX.TRUE), XoX.FALSE)
        self.assertIs(xox_not(XoX.FALSE), XoX.TRUE)
        self.assertIs(xox_not(XoX.UNKNOWN), XoX.UNKNOWN)

    def test_strong_kleene_and_all_nine_pairs(self):
        table = [
            (XoX.TRUE, XoX.TRUE, XoX.TRUE),
            (XoX.TRUE, XoX.UNKNOWN, XoX.UNKNOWN),
            (XoX.TRUE, XoX.FALSE, XoX.FALSE),
            (XoX.UNKNOWN, XoX.TRUE, XoX.UNKNOWN),
            (XoX.UNKNOWN, XoX.UNKNOWN, XoX.UNKNOWN),
            (XoX.UNKNOWN, XoX.FALSE, XoX.FALSE),
            (XoX.FALSE, XoX.TRUE, XoX.FALSE),
            (XoX.FALSE, XoX.UNKNOWN, XoX.FALSE),
            (XoX.FALSE, XoX.FALSE, XoX.FALSE),
        ]
        for left, right, expected in table:
            with self.subTest(left=left, right=right):
                self.assertIs(xox_and(left, right), expected)

    def test_strong_kleene_or_all_nine_pairs(self):
        table = [
            (XoX.TRUE, XoX.TRUE, XoX.TRUE),
            (XoX.TRUE, XoX.UNKNOWN, XoX.TRUE),
            (XoX.TRUE, XoX.FALSE, XoX.TRUE),
            (XoX.UNKNOWN, XoX.TRUE, XoX.TRUE),
            (XoX.UNKNOWN, XoX.UNKNOWN, XoX.UNKNOWN),
            (XoX.UNKNOWN, XoX.FALSE, XoX.UNKNOWN),
            (XoX.FALSE, XoX.TRUE, XoX.TRUE),
            (XoX.FALSE, XoX.UNKNOWN, XoX.UNKNOWN),
            (XoX.FALSE, XoX.FALSE, XoX.FALSE),
        ]
        for left, right, expected in table:
            with self.subTest(left=left, right=right):
                self.assertIs(xox_or(left, right), expected)


    def test_invalid_operands_to_strong_kleene_helpers(self):
        with self.assertRaises(TypeError):
            xox_not(True)  # type: ignore

        with self.assertRaises(TypeError):
            xox_and(XoX.TRUE, True)  # type: ignore

        with self.assertRaises(TypeError):
            xox_or(False, XoX.FALSE)  # type: ignore

    def test_numeric_bitwise_and_ordering_isolation(self):
        # Arithmetic
        with self.assertRaises(TypeError):
            _ = XoX.TRUE + 1  # type: ignore
        with self.assertRaises(TypeError):
            _ = XoX.FALSE * 2  # type: ignore

        # Bitwise integer operations
        with self.assertRaises(TypeError):
            _ = XoX.TRUE & XoX.FALSE  # type: ignore
        with self.assertRaises(TypeError):
            _ = XoX.TRUE | XoX.UNKNOWN  # type: ignore

        # Ordering
        with self.assertRaises(TypeError):
            _ = XoX.UNKNOWN < XoX.TRUE  # type: ignore
        with self.assertRaises(TypeError):
            _ = XoX.FALSE >= XoX.TRUE  # type: ignore

    def test_runtime_all_export_surface(self):
        import xoxlang.runtime as runtime_mod
        expected_exports = {
            "UnknownValueError",
            "XoX",
            "xox_and",
            "xox_not",
            "xox_or",
        }
        self.assertTrue(hasattr(runtime_mod, "__all__"))
        self.assertEqual(set(runtime_mod.__all__), expected_exports)
        self.assertEqual(len(runtime_mod.__all__), len(expected_exports))

        # Ensure internal symbols are not in __all__
        for internal in ("Enum", "auto"):
            self.assertNotIn(internal, runtime_mod.__all__)

        # Ensure every exported symbol exists and is resolvable on the module
        for sym in runtime_mod.__all__:
            self.assertTrue(hasattr(runtime_mod, sym))


if __name__ == "__main__":
    unittest.main()

