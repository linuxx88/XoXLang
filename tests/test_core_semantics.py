"""Tests for the finite-world XoXLang semantic classifier.

Includes both normal suite and adversarial attack suites to verify:
1. Canonical 3-way partition: Inconsistent, Known, Unknown.
2. Absolute priority of the definedness precondition over all classifications.
3. Permutation invariance, scale resistance, structural equivalence, and return type safety.
"""
import unittest
from xoxlang.core_semantics import (
    DefinednessPreconditionError,
    SemanticClassification,
    SemanticOutcome,
    classify_factive_behaviors,
)


class TestCoreSemantics(unittest.TestCase):
    """Verifies standard factive world space classifications."""

    def test_empty_factive_behavior_sequence_is_inconsistent(self):
        """When the factive world space is empty (no admissible realities), the state is Inconsistent."""
        behaviors = []
        result = classify_factive_behaviors(behaviors)
        self.assertEqual(result, SemanticClassification.INCONSISTENT)

    def test_single_defined_behavior_is_known(self):
        """When exactly one reality is admissible and its outcome is defined, the outcome is Known."""
        behaviors = [SemanticOutcome.defined(42)]
        result = classify_factive_behaviors(behaviors)
        self.assertEqual(result, SemanticClassification.KNOWN)

    def test_multiple_identical_defined_behaviors_are_known(self):
        """When all admissible worlds yield observationally identical outcomes, the outcome is Known."""
        behaviors = [
            SemanticOutcome.defined("success"),
            SemanticOutcome.defined("success"),
            SemanticOutcome.defined("success"),
        ]
        result = classify_factive_behaviors(behaviors)
        self.assertEqual(result, SemanticClassification.KNOWN)

    def test_two_distinguishable_defined_behaviors_are_unknown(self):
        """When two admissible worlds yield different outcomes, the outcome is Unknown (distinguishable)."""
        behaviors = [
            SemanticOutcome.defined(True),
            SemanticOutcome.defined(False),
        ]
        result = classify_factive_behaviors(behaviors)
        self.assertEqual(result, SemanticClassification.UNKNOWN)

    def test_multiple_behaviors_containing_distinguishable_outcomes_are_unknown(self):
        """When a multi-world space contains at least one differing outcome, the outcome is Unknown."""
        behaviors = [
            SemanticOutcome.defined(10),
            SemanticOutcome.defined(10),
            SemanticOutcome.defined(20),
        ]
        result = classify_factive_behaviors(behaviors)
        self.assertEqual(result, SemanticClassification.UNKNOWN)

    def test_single_undefined_behavior_raises_precondition_error(self):
        """An expression with undefined behavior fails the classification precondition immediately."""
        behaviors = [SemanticOutcome.undefined()]
        with self.assertRaises(DefinednessPreconditionError) as ctx:
            classify_factive_behaviors(behaviors)
        self.assertIn("precondition failed", str(ctx.exception).lower())

    def test_defined_behaviors_plus_one_undefined_behavior_raises_precondition_error(self):
        """If even one admissible world has undefined semantics, classification is strictly refused."""
        behaviors = [
            SemanticOutcome.defined(42),
            SemanticOutcome.undefined(),
            SemanticOutcome.defined(42),
        ]
        with self.assertRaises(DefinednessPreconditionError) as ctx:
            classify_factive_behaviors(behaviors)
        self.assertIn("precondition failed", str(ctx.exception).lower())

    def test_undefined_behavior_never_returns_classification_enum(self):
        """Undefined behavior must never silently produce INCONSISTENT, KNOWN, or UNKNOWN."""
        behaviors = [SemanticOutcome.undefined()]
        try:
            result = classify_factive_behaviors(behaviors)
            self.fail(f"Expected DefinednessPreconditionError but got classification: {result}")
        except DefinednessPreconditionError:
            pass


class TestCoreSemanticsAdversarial(unittest.TestCase):
    """Adversarial stress tests attacking edge cases, ordering, scaling, and definedness priority."""

    def test_undefined_behavior_at_start_blocks_classification(self):
        """Undefined behavior as the first element must immediately block classification."""
        behaviors = [
            SemanticOutcome.undefined(),
            SemanticOutcome.defined(42),
            SemanticOutcome.defined(42),
        ]
        with self.assertRaises(DefinednessPreconditionError):
            classify_factive_behaviors(behaviors)

    def test_undefined_behavior_at_end_blocks_known_classification(self):
        """Undefined behavior as the last element must prevent falsely concluding Known."""
        behaviors = [
            SemanticOutcome.defined(42),
            SemanticOutcome.defined(42),
            SemanticOutcome.undefined(),
        ]
        with self.assertRaises(DefinednessPreconditionError):
            classify_factive_behaviors(behaviors)

    def test_undefined_behavior_blocks_classification_even_when_distinguishable_behaviors_precede_it(self):
        """Undefined behavior must strictly block UNKNOWN classification even if variance was already observed."""
        behaviors = [
            SemanticOutcome.defined(1),
            SemanticOutcome.defined(2),
            SemanticOutcome.undefined(),
        ]
        with self.assertRaises(DefinednessPreconditionError):
            classify_factive_behaviors(behaviors)

    def test_empty_sequence_is_inconsistent_never_confused_with_undefined_sequence(self):
        """An empty factive space is Inconsistent, whereas an undefined space is a precondition violation."""
        self.assertEqual(classify_factive_behaviors([]), SemanticClassification.INCONSISTENT)
        with self.assertRaises(DefinednessPreconditionError):
            classify_factive_behaviors([SemanticOutcome.undefined()])

    def test_permutation_invariance_on_distinguishable_behaviors(self):
        """Reordering factive worlds must never alter the UNKNOWN classification."""
        b1 = [SemanticOutcome.defined("A"), SemanticOutcome.defined("B"), SemanticOutcome.defined("C")]
        b2 = [SemanticOutcome.defined("C"), SemanticOutcome.defined("A"), SemanticOutcome.defined("B")]
        self.assertEqual(classify_factive_behaviors(b1), SemanticClassification.UNKNOWN)
        self.assertEqual(classify_factive_behaviors(b2), SemanticClassification.UNKNOWN)

    def test_reversing_known_sequence_remains_known(self):
        """Reversing a Known behavior sequence must remain Known."""
        behaviors = [SemanticOutcome.defined(10), SemanticOutcome.defined(10), SemanticOutcome.defined(10)]
        self.assertEqual(classify_factive_behaviors(behaviors[::-1]), SemanticClassification.KNOWN)

    def test_reversing_unknown_sequence_remains_unknown(self):
        """Reversing an Unknown behavior sequence must remain Unknown."""
        behaviors = [SemanticOutcome.defined("left"), SemanticOutcome.defined("right")]
        self.assertEqual(classify_factive_behaviors(behaviors[::-1]), SemanticClassification.UNKNOWN)

    def test_duplicating_equivalent_behaviors_preserves_known(self):
        """Adding duplicate identical worlds to a Known space must preserve Known."""
        behaviors = [SemanticOutcome.defined(42)] * 10
        self.assertEqual(classify_factive_behaviors(behaviors), SemanticClassification.KNOWN)

    def test_duplicating_distinguishable_behavior_preserves_unknown(self):
        """Duplicating worlds in an Unknown space must preserve Unknown."""
        behaviors = [SemanticOutcome.defined("A")] * 5 + [SemanticOutcome.defined("B")] * 5
        self.assertEqual(classify_factive_behaviors(behaviors), SemanticClassification.UNKNOWN)

    def test_large_sequence_of_equivalent_behaviors_is_known(self):
        """A high-scale space of 10,000 identical worlds must remain Known without performance decay."""
        behaviors = [SemanticOutcome.defined(999)] * 10000
        self.assertEqual(classify_factive_behaviors(behaviors), SemanticClassification.KNOWN)

    def test_large_sequence_with_distinguishable_behavior_near_end_is_unknown(self):
        """A space of 10,000 worlds with one differing outcome at the end must be classified as Unknown."""
        behaviors = [SemanticOutcome.defined("same")] * 9999 + [SemanticOutcome.defined("different")]
        self.assertEqual(classify_factive_behaviors(behaviors), SemanticClassification.UNKNOWN)

    def test_large_sequence_with_undefined_behavior_near_end_raises_precondition_error(self):
        """A space of 10,000 worlds with one undefined outcome at the end must raise DefinednessPreconditionError."""
        behaviors = [SemanticOutcome.defined("same")] * 9999 + [SemanticOutcome.undefined()]
        with self.assertRaises(DefinednessPreconditionError):
            classify_factive_behaviors(behaviors)

    def test_structural_equivalence_does_not_fail_on_distinct_object_identities(self):
        """Distinct memory allocations with identical observational value must be classified as Known."""
        obj1 = {"status": "ok", "items": [1, 2, 3]}
        obj2 = {"status": "ok", "items": [1, 2, 3]}
        self.assertIsNot(obj1, obj2)
        behaviors = [SemanticOutcome.defined(obj1), SemanticOutcome.defined(obj2)]
        self.assertEqual(classify_factive_behaviors(behaviors), SemanticClassification.KNOWN)

    def test_distinguishable_types_with_accidental_equality_are_handled_by_custom_equivalence(self):
        """Custom observational equivalence relations (e.g. strict type + value) prevent false Known classifications."""
        # Python int 1 == bool True, but strict observational equivalence can distinguish them
        def strict_observational_equivalence(a, b):
            return type(a) is type(b) and a == b

        behaviors = [SemanticOutcome.defined(1), SemanticOutcome.defined(True)]
        self.assertEqual(
            classify_factive_behaviors(behaviors, equivalence_fn=strict_observational_equivalence),
            SemanticClassification.UNKNOWN,
        )

    def test_all_valid_classifications_strictly_return_semantic_classification_enum(self):
        """Classifier must always return an exact SemanticClassification enum instance, never raw booleans or None."""
        test_inputs = [
            [],
            [SemanticOutcome.defined(1)],
            [SemanticOutcome.defined(1), SemanticOutcome.defined(2)],
        ]
        for inp in test_inputs:
            result = classify_factive_behaviors(inp)
            self.assertIsInstance(result, SemanticClassification)
            self.assertIn(result, (SemanticClassification.INCONSISTENT, SemanticClassification.KNOWN, SemanticClassification.UNKNOWN))


if __name__ == "__main__":
    unittest.main()
