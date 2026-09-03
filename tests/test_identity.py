"""Normal test suite for validated XoXLang atomic fact identity semantics.

Verifies:
1. Distinct semantic identity across independent fact occurrences.
2. Orthogonality of fact identity and value/payload equality.
3. Reference identity preservation.
4. Separation of mutable storage identity from immutable fact identity.
5. Invariant preservation across valid and rejected rebinding operations.
6. Post-construction immutability of protected identities and bindings.
"""
import unittest
from typing import Any, Optional, Sequence, Tuple
from xoxlang.core_semantics import DefinednessPreconditionError, SemanticOutcome

from xoxlang.runtime import XoX
from xoxlang.identity import (
    AtomicFact,
    CanonicalPath,
    CompoundFact,
    ConstraintContentIdentity,
    DefinednessWitness,
    DerivedProjectionFact,
    EvaluatorSemanticProfile,
    FactiveEvaluator,
    FactiveTrajectory,
    FactReference,
    OntologicalConstraintToken,
    ProvenanceSet,
    SemanticSelector,
    StorageLocation,
    UnknownValue,
    WorldStateID,
    authorize_ontological_constraint,
    certify_factive_definedness,
    k3_and_with_provenance,
    k3_not_with_provenance,
    k3_or_with_provenance,
)






class TestAtomicFactIdentity(unittest.TestCase):
    """Verifies atomic fact identity generation, equality, and immutability."""

    def test_two_independently_created_atomic_facts_have_distinct_identities(self):
        """Two independently instantiated atomic facts must receive distinct semantic identities."""
        f1 = AtomicFact()
        f2 = AtomicFact()
        self.assertNotEqual(f1.identity, f2.identity)
        self.assertNotEqual(f1, f2)

    def test_two_atomic_facts_with_equal_payloads_remain_distinct_facts(self):
        """Equal payloads or representations must never merge distinct atomic fact identities."""
        f1 = AtomicFact(payload="data")
        f2 = AtomicFact(payload="data")
        self.assertEqual(f1.payload, f2.payload)
        self.assertNotEqual(f1.identity, f2.identity)
        self.assertNotEqual(f1, f2)

    def test_an_atomic_fact_identity_remains_stable_across_repeated_reads(self):
        """Reading an atomic fact's identity multiple times must return the exact same identifier."""
        f = AtomicFact(payload=42)
        first_id = f.identity
        second_id = f.identity
        self.assertEqual(first_id, second_id)

    def test_direct_atomic_fact_identity_reassignment_is_rejected(self):
        """Direct assignment to an atomic fact's identity must be rejected post-construction."""
        f = AtomicFact()
        original_id = f.identity
        with self.assertRaises(AttributeError):
            f._identity = 999
        self.assertEqual(f.identity, original_id)


class TestFactReference(unittest.TestCase):
    """Verifies fact reference identity preservation, resolution, and immutability."""

    def test_two_fact_references_targeting_the_same_fact_expose_the_same_identity(self):
        """Multiple references to the same atomic fact preserve and expose the same fact identity."""
        fact = AtomicFact()
        ref1 = FactReference(fact)
        ref2 = FactReference(fact)
        self.assertIs(ref1.resolve(), fact)
        self.assertIs(ref2.resolve(), fact)
        self.assertEqual(ref1.identity, ref2.identity)

    def test_fact_reference_construction_rejects_a_non_atomic_fact(self):
        """Constructing a FactReference with a non-AtomicFact must raise TypeError."""
        with self.assertRaises(TypeError) as ctx:
            FactReference("not_a_fact")  # type: ignore[arg-type]
        self.assertIn("AtomicFact", str(ctx.exception))

    def test_direct_fact_reference_target_reassignment_is_rejected(self):
        """Direct assignment to a fact reference's target must be rejected."""
        f1 = AtomicFact()
        f2 = AtomicFact()
        ref = FactReference(f1)
        with self.assertRaises(AttributeError):
            ref._target = f2
        self.assertIs(ref.resolve(), f1)


class TestStorageLocationIdentity(unittest.TestCase):
    """Verifies storage location identity persistence, rebinding, and protection."""

    def test_storage_location_identity_persists_across_rebinding(self):
        """Storage location identity remains strictly invariant across rebinding operations."""
        f1 = AtomicFact()
        f2 = AtomicFact()
        loc = StorageLocation(f1)
        initial_storage_id = loc.storage_id

        self.assertIs(loc.read(), f1)
        old_fact = loc.rebind(f2)

        self.assertIs(old_fact, f1)
        self.assertIs(loc.read(), f2)
        self.assertEqual(loc.storage_id, initial_storage_id)

    def test_storage_location_identity_is_distinct_from_fact_identity(self):
        """Storage location identity and atomic fact identity are strictly distinct and non-comparable."""
        fact = AtomicFact()
        loc = StorageLocation(fact)
        self.assertNotEqual(loc.storage_id, fact.identity)

    def test_two_storage_locations_bound_to_the_same_fact_have_distinct_storage_identities(self):
        """Two distinct storage locations bound to the same fact remain separate storage identities."""
        shared_fact = AtomicFact()
        loc1 = StorageLocation(shared_fact)
        loc2 = StorageLocation(shared_fact)
        self.assertNotEqual(loc1.storage_id, loc2.storage_id)
        self.assertIs(loc1.read(), shared_fact)
        self.assertIs(loc2.read(), shared_fact)

    def test_storage_location_construction_rejects_a_non_atomic_fact(self):
        """Constructing a StorageLocation with a non-AtomicFact must raise TypeError."""
        with self.assertRaises(TypeError) as ctx:
            StorageLocation("not_a_fact")  # type: ignore[arg-type]
        self.assertIn("AtomicFact", str(ctx.exception))

    def test_storage_location_rebind_rejects_a_non_atomic_fact_and_preserves_state(self):
        """Attempting to rebind with a non-AtomicFact must fail and preserve current storage state."""
        fact = AtomicFact()
        loc = StorageLocation(fact)
        initial_sid = loc.storage_id

        with self.assertRaises(TypeError) as ctx:
            loc.rebind(123)  # type: ignore[arg-type]

        self.assertIn("AtomicFact", str(ctx.exception))
        self.assertIs(loc.read(), fact)
        self.assertEqual(loc.storage_id, initial_sid)

    def test_direct_storage_location_storage_identity_reassignment_is_rejected(self):
        """Direct assignment to a storage location's storage_id must be rejected."""
        fact = AtomicFact()
        loc = StorageLocation(fact)
        initial_sid = loc.storage_id
        with self.assertRaises(AttributeError):
            loc._storage_id = 999
        self.assertEqual(loc.storage_id, initial_sid)

    def test_direct_storage_location_fact_binding_reassignment_is_rejected(self):
        """Direct assignment to a storage location's _bound_fact must be rejected."""
        f1 = AtomicFact()
        f2 = AtomicFact()
        loc = StorageLocation(f1)
        with self.assertRaises(AttributeError):
            loc._bound_fact = f2
        self.assertIs(loc.read(), f1)


class TestDefinednessWitness(unittest.TestCase):
    """Verifies DefinednessWitness issuance, 3-tuple exact matching, and non-forgeability."""

    def test_definedness_witness_exact_matching(self):
        """A witness matches its exact (RootID, SemanticPath, WorldStateID) binding."""
        root = CompoundFact()
        sel = SemanticSelector("age")
        path = CanonicalPath((sel,))
        ws = WorldStateID()
        evaluator = ws.create_evaluator()

        witness = certify_factive_definedness(evaluator, root, path)
        self.assertTrue(witness.matches(root, path, ws))
        self.assertEqual(witness.root_id, root.identity)
        self.assertEqual(witness.semantic_path, path.selectors)
        self.assertEqual(witness.world_state_id, ws.state_id)

    def test_definedness_witness_mismatch_and_staleness_fails_closed(self):
        """Mismatched root, path, or stale world state fails verification."""
        root1 = CompoundFact()
        root2 = CompoundFact()
        sel1 = SemanticSelector("a")
        sel2 = SemanticSelector("b")
        path1 = CanonicalPath((sel1,))
        path2 = CanonicalPath((sel2,))
        ws1 = WorldStateID()
        ws2 = WorldStateID()
        evaluator1 = ws1.create_evaluator()

        witness = certify_factive_definedness(evaluator1, root1, path1)

        # Root mismatch
        self.assertFalse(witness.matches(root2, path1, ws1))
        with self.assertRaises(DefinednessPreconditionError):
            witness.verify(root2, path1, ws1)

        # Path mismatch
        self.assertFalse(witness.matches(root1, path2, ws1))
        with self.assertRaises(DefinednessPreconditionError):
            witness.verify(root1, path2, ws1)

        # Stale WorldStateID
        self.assertFalse(witness.matches(root1, path1, ws2))
        with self.assertRaises(DefinednessPreconditionError):
            witness.verify(root1, path1, ws2)

    def test_direct_construction_without_authorization_is_prohibited(self):
        """Direct construction of DefinednessWitness raises PermissionError."""
        root = CompoundFact()
        sel = SemanticSelector("x")
        path = CanonicalPath((sel,))
        ws = WorldStateID()

        with self.assertRaises(PermissionError):
            DefinednessWitness(root, path, ws)

    def test_derived_projection_fact_validates_witness(self):
        """DerivedProjectionFact validates successfully with a matching witness."""
        root = CompoundFact()
        sel = SemanticSelector("name")
        path = CanonicalPath((sel,))
        ws = WorldStateID()
        evaluator = ws.create_evaluator()
        witness = certify_factive_definedness(evaluator, root, path)


        proj = DerivedProjectionFact(root, path, witness=witness, world_state_id=ws)
        self.assertEqual(proj.root_fact, root)
        self.assertEqual(proj.path, path)


class TestOntologicalConstraintToken(unittest.TestCase):
    """Verifies OntologicalConstraintToken non-forgeability and type separation."""

    def test_direct_ontological_token_construction_is_prohibited(self):
        """Direct construction of OntologicalConstraintToken raises PermissionError."""
        root = CompoundFact()
        path = CanonicalPath((SemanticSelector("x"),))
        ws = WorldStateID()
        prof = EvaluatorSemanticProfile()
        c = ConstraintContentIdentity()

        with self.assertRaises(PermissionError):
            OntologicalConstraintToken(root, path, ws, prof, c)

    def test_definedness_witness_cannot_substitute_for_ontological_token(self):
        """DefinednessWitness has zero authority as an OntologicalConstraintToken."""
        root = CompoundFact()
        path = CanonicalPath((SemanticSelector("k"),))
        ws = WorldStateID()
        evaluator = ws.create_evaluator()
        witness = certify_factive_definedness(evaluator, root, path)

        # DefinednessWitness does not have token properties and fails isinstance checks
        self.assertNotIsInstance(witness, OntologicalConstraintToken)
        self.assertFalse(hasattr(witness, "profile_id"))
        self.assertFalse(hasattr(witness, "constraint_id"))


class TestProvenanceSet(unittest.TestCase):
    """Test suite for ProvenanceSet immutable container and operations."""

    def test_provenance_set_creation_and_canonical_sorting(self):
        f1 = AtomicFact()
        f2 = AtomicFact()
        pset = ProvenanceSet([f2.identity, f1.identity, f1.identity])
        self.assertEqual(pset.facts, tuple(sorted({f1.identity, f2.identity})))
        self.assertEqual(len(pset), 2)
        self.assertIn(f1, pset)
        self.assertIn(f2.identity, pset)

    def test_empty_provenance_set_rejected(self):
        with self.assertRaises(ValueError):
            ProvenanceSet([])

    def test_provenance_set_union(self):
        f1 = AtomicFact()
        f2 = AtomicFact()
        f3 = AtomicFact()
        ps1 = ProvenanceSet([f1])
        ps2 = ProvenanceSet([f2, f3])
        union_ps = ps1 | ps2
        self.assertEqual(union_ps.facts, tuple(sorted({f1.identity, f2.identity, f3.identity})))

    def test_provenance_set_immutability(self):
        ps = ProvenanceSet([AtomicFact()])
        with self.assertRaises(AttributeError):
            ps.facts = (1, 2)  # type: ignore


class TestUnknownProvenancePropagation(unittest.TestCase):
    """Test suite for Unknown provenance propagation and K3 reduction."""

    def _create_authentic_unknown(self, fact: Optional[AtomicFact] = None) -> Tuple[WorldStateID, FactiveEvaluator, AtomicFact, UnknownValue]:
        traj1 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj2 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws = WorldStateID(trajectories=[traj1, traj2])
        evaluator = ws.create_evaluator()
        f = fact if fact is not None else AtomicFact()
        u = evaluator.evaluate_projection(f)
        return ws, evaluator, f, u

    def test_direct_unknown_value_construction_prohibited(self):
        """Direct construction of UnknownValue raises PermissionError."""
        f1 = AtomicFact()
        with self.assertRaises(PermissionError):
            UnknownValue(ProvenanceSet([f1]))

    def test_k3_not_preserves_provenance(self):
        _, _, f1, u = self._create_authentic_unknown()
        res = k3_not_with_provenance(u)
        self.assertIsInstance(res, UnknownValue)
        self.assertEqual(res.provenance_set.facts, (f1.identity,))

    def test_k3_and_or_union_provenance(self):
        traj1 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj2 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws = WorldStateID(trajectories=[traj1, traj2])
        evaluator = ws.create_evaluator()

        f1 = AtomicFact()
        f2 = AtomicFact()
        u1 = evaluator.evaluate_projection(f1)
        u2 = evaluator.evaluate_projection(f2)

        and_res = k3_and_with_provenance(u1, lambda: u2)
        self.assertIsInstance(and_res, UnknownValue)
        self.assertEqual(and_res.provenance_set.facts, tuple(sorted({f1.identity, f2.identity})))

        or_res = k3_or_with_provenance(u1, lambda: u2)
        self.assertIsInstance(or_res, UnknownValue)
        self.assertEqual(or_res.provenance_set.facts, tuple(sorted({f1.identity, f2.identity})))

    def test_k3_short_circuit_zero_provenance(self):
        effect_called = False
        def effect():
            nonlocal effect_called
            effect_called = True
            _, _, _, u = self._create_authentic_unknown()
            return u

        res = k3_and_with_provenance(False, effect)
        self.assertIs(res, XoX.FALSE)
        self.assertFalse(effect_called)

    def test_k3_dominance_eliminates_provenance(self):
        _, _, _, u1 = self._create_authentic_unknown()
        res = k3_and_with_provenance(u1, lambda: False)
        self.assertIs(res, XoX.FALSE)


if __name__ == "__main__":
    unittest.main()






