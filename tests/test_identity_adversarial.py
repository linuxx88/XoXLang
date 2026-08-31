"""Adversarial test suite attacking the XoXLang atomic fact identity implementation.

Attacks:
1. Object duplication via copy, deepcopy, and pickle.
2. Mutable payload corruption of hashing and equality.
3. Attribute deletion and dynamic slot-bypassing attempts.
4. Storage identity duplication across rebinds.
5. Invalidation across multi-type invalid rebinds.
6. Subclassing integrity.
"""
import copy
import pickle
from typing import Any, Optional, Sequence, Tuple
import unittest

from xoxlang.core_semantics import DefinednessPreconditionError, SemanticOutcome

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
    FallbackPolicyIdentity,
    NO_FALLBACK,
    OntologicalConstraintToken,
    ProvenanceSet,
    ResolutionToken,
    SemanticSelector,
    StorageLocation,
    UnknownValue,
    WorldStateAuthority,
    WorldStateID,
    authorize_ontological_constraint,
    certify_factive_definedness,
    k3_and_with_provenance,
    k3_not_with_provenance,
    k3_or_with_provenance,
    resolve_unwrap_or,
    resolve_xen_ignore,
)








class TestAdversarialIdentityAttacks(unittest.TestCase):
    """Adversarial stress tests for atomic identity semantics."""

    def test_copy_atomic_fact_must_not_duplicate_identity_into_distinct_occurrence(self):
        """copy.copy on AtomicFact must not create a distinct Python instance sharing the same identity."""
        f = AtomicFact(payload="data")
        f_copy = copy.copy(f)
        # If copy creates a distinct object with the same semantic identity, identity nonforgeability is breached
        self.assertIs(f_copy, f, "copy.copy(AtomicFact) created a distinct Python object carrying the same semantic identity")

    def test_deepcopy_atomic_fact_must_not_duplicate_identity_into_distinct_occurrence(self):
        """copy.deepcopy on AtomicFact must not create a distinct Python instance sharing the same identity."""
        f = AtomicFact(payload="data")
        f_deep = copy.deepcopy(f)
        self.assertIs(f_deep, f, "copy.deepcopy(AtomicFact) created a distinct Python object carrying the same semantic identity")

    def test_pickle_roundtrip_must_not_create_distinct_duplicate_identity(self):
        """pickle serialization on AtomicFact must fail closed because persistent identity semantics are undefined."""
        f = AtomicFact(payload="data")
        with self.assertRaises(TypeError) as ctx:
            pickle.dumps(f)
        self.assertIn("persistent or cross-process semantic identity is not defined", str(ctx.exception))

    def test_pickle_serialization_of_fact_reference_is_rejected(self):
        """pickle serialization on FactReference must fail closed because persistent identity semantics are undefined."""
        f = AtomicFact(payload="data")
        ref = FactReference(f)
        with self.assertRaises(TypeError) as ctx:
            pickle.dumps(ref)
        self.assertIn("persistent or cross-process semantic identity is not defined", str(ctx.exception))

    def test_pickle_serialization_of_storage_location_is_rejected(self):
        """pickle serialization on StorageLocation must fail closed because persistent identity semantics are undefined."""
        loc = StorageLocation(AtomicFact())
        with self.assertRaises(TypeError) as ctx:
            pickle.dumps(loc)
        self.assertIn("persistent or cross-process semantic identity is not defined", str(ctx.exception))

    def test_copy_fact_reference_preserves_target_reference_identity(self):
        """copy.copy on FactReference must preserve designation of the exact target AtomicFact."""
        f = AtomicFact()
        ref = FactReference(f)
        ref_copy = copy.copy(ref)
        self.assertIs(ref_copy.target, f)
        self.assertEqual(ref_copy.identity, f.identity)

    def test_deepcopy_fact_reference_must_not_clone_target_into_second_fact_with_same_identity(self):
        """copy.deepcopy on FactReference must not clone the target into a distinct fact object."""
        f = AtomicFact()
        ref = FactReference(f)
        ref_deep = copy.deepcopy(ref)
        self.assertIs(ref_deep.target, f, "copy.deepcopy(FactReference) cloned target fact into a distinct duplicate object")

    def test_copy_storage_location_must_not_duplicate_storage_identity(self):
        """copy.copy on StorageLocation must fail closed because mutable storage identity cannot be duplicated."""
        loc = StorageLocation(AtomicFact())
        with self.assertRaises(TypeError) as ctx:
            copy.copy(loc)
        self.assertIn("mutable storage identity is unique and non-copyable", str(ctx.exception))

    def test_deepcopy_storage_location_must_not_duplicate_storage_identity(self):
        """copy.deepcopy on StorageLocation must fail closed because mutable storage identity cannot be duplicated."""
        loc = StorageLocation(AtomicFact())
        with self.assertRaises(TypeError) as ctx:
            copy.deepcopy(loc)
        self.assertIn("mutable storage identity is unique and non-copyable", str(ctx.exception))

    def test_two_equal_payload_facts_remain_unequal_with_independently_stable_hashes(self):
        """Equal mutable or immutable payloads must produce unequal facts with distinct identities."""
        f1 = AtomicFact(payload={"a": [1, 2, 3]})
        f2 = AtomicFact(payload={"a": [1, 2, 3]})
        self.assertNotEqual(f1, f2)
        self.assertNotEqual(f1.identity, f2.identity)

    def test_mutating_mutable_payload_does_not_change_equality_or_hash(self):
        """Mutating a mutable payload in-place must not affect the AtomicFact's hash or identity equality."""
        payload = {"items": [1, 2]}
        f = AtomicFact(payload=payload)
        initial_hash = hash(f)
        payload["items"].append(3)
        self.assertEqual(hash(f), initial_hash)

    def test_atomic_fact_remains_findable_in_set_after_payload_mutation(self):
        """An AtomicFact inside a set remains findable after in-place mutation of its payload."""
        payload = [1, 2]
        f = AtomicFact(payload=payload)
        s = {f}
        payload.append(3)
        self.assertIn(f, s)

    def test_fact_reference_target_remains_unchanged_after_failed_direct_mutation_attempts(self):
        """FactReference target remains unchanged after rejected mutation attempts."""
        f1 = AtomicFact()
        f2 = AtomicFact()
        ref = FactReference(f1)
        with self.assertRaises(AttributeError):
            ref._target = f2
        self.assertIs(ref.target, f1)

    def test_storage_location_binding_remains_unchanged_after_invalid_rebind_attempts(self):
        """StorageLocation binding remains invariant across multiple invalid type rebind attempts."""
        f = AtomicFact()
        loc = StorageLocation(f)
        sid = loc.storage_id
        for invalid in [None, 123, "str", [1], {"k": "v"}, True, object()]:
            with self.assertRaises(TypeError):
                loc.rebind(invalid)  # type: ignore[arg-type]
            self.assertIs(loc.read(), f)
            self.assertEqual(loc.storage_id, sid)

    def test_rebind_to_same_atomic_fact_preserves_storage_identity_and_does_not_create_new_fact(self):
        """Rebinding a storage location to its already-bound fact preserves identity without creating new facts."""
        f = AtomicFact()
        loc = StorageLocation(f)
        sid = loc.storage_id
        prev = loc.rebind(f)
        self.assertIs(prev, f)
        self.assertIs(loc.read(), f)
        self.assertEqual(loc.storage_id, sid)

    def test_rebind_repeatedly_across_several_facts_preserves_one_storage_identity(self):
        """Repeatedly rebinding across distinct facts maintains the exact same storage identity."""
        facts = [AtomicFact() for _ in range(5)]
        loc = StorageLocation(facts[0])
        initial_sid = loc.storage_id
        for fact in facts[1:]:
            loc.rebind(fact)
            self.assertEqual(loc.storage_id, initial_sid)
            self.assertIs(loc.read(), fact)

    def test_previously_returned_facts_from_rebind_remain_valid_and_unchanged(self):
        """Historical facts returned from rebind remain valid and immutable."""
        f1 = AtomicFact(payload="f1")
        f2 = AtomicFact(payload="f2")
        f3 = AtomicFact(payload="f3")
        loc = StorageLocation(f1)
        old1 = loc.rebind(f2)
        old2 = loc.rebind(f3)
        self.assertIs(old1, f1)
        self.assertIs(old2, f2)
        self.assertEqual(old1.payload, "f1")
        self.assertEqual(old2.payload, "f2")

    def test_attempting_attribute_deletion_on_atomic_fact_protected_fields_is_rejected(self):
        """Deleting _identity or _payload from AtomicFact must be rejected."""
        f = AtomicFact()
        with self.assertRaises(AttributeError):
            del f._identity
        with self.assertRaises(AttributeError):
            del f._payload

    def test_attempting_attribute_deletion_on_fact_reference_protected_target_is_rejected(self):
        """Deleting _target from FactReference must be rejected."""
        ref = FactReference(AtomicFact())
        with self.assertRaises(AttributeError):
            del ref._target

    def test_attempting_attribute_deletion_on_storage_location_identity_or_bound_fact_is_rejected(self):
        """Deleting _storage_id or _bound_fact from StorageLocation must be rejected."""
        loc = StorageLocation(AtomicFact())
        with self.assertRaises(AttributeError):
            del loc._storage_id
        with self.assertRaises(AttributeError):
            del loc._bound_fact

    def test_unknown_new_attribute_assignment_is_rejected_by_slots(self):
        """Assigning arbitrary new attributes must be rejected by slots and immutability guards."""
        f = AtomicFact()
        loc = StorageLocation(f)
        ref = FactReference(f)
        with self.assertRaises(AttributeError):
            f.extra_attr = "val"
        with self.assertRaises(AttributeError):
            loc.extra_attr = "val"
        with self.assertRaises(AttributeError):
            ref.extra_attr = "val"

    def test_subclassing_atomic_fact_cannot_bypass_isinstance_guards_in_fact_reference_or_storage_location(self):
        """Subclassing AtomicFact preserves instance validity under closed-domain type checks."""
        class CustomFact(AtomicFact):
            pass
        cf = CustomFact(payload="custom")
        ref = FactReference(cf)
        loc = StorageLocation(cf)
        self.assertIs(ref.resolve(), cf)
        self.assertIs(loc.read(), cf)

    def test_subclassing_storage_location_preserves_attribute_protection(self):
        """Subclasses of StorageLocation inherit immutability protection for storage_id."""
        class CustomStorage(StorageLocation):
            pass
        cs = CustomStorage(AtomicFact())
        initial_sid = cs.storage_id
        with self.assertRaises(AttributeError):
            cs._storage_id = 999
        self.assertEqual(cs.storage_id, initial_sid)


class TestAdversarialDefinednessWitnessAttacks(unittest.TestCase):
    """Adversarial attacks on DefinednessWitness non-forgeability and binding enforcement."""

    def test_dw_adv_01_direct_issue_without_evaluation_is_prohibited(self):
        """DW-ADV-01: Direct invocation of internal _issue_from_evaluator without evaluator capability is prohibited."""
        root = CompoundFact()
        sel = SemanticSelector("k")
        path = CanonicalPath((sel,))
        ws = WorldStateID()
        with self.assertRaises(PermissionError):
            DefinednessWitness._issue_from_evaluator(root, path, ws)

    def test_dw_adv_02_constructor_with_guessed_token_is_prohibited(self):
        """DW-ADV-02: Direct constructor call with guessed or invalid token is prohibited."""
        root = CompoundFact()
        sel = SemanticSelector("k")
        path = CanonicalPath((sel,))
        ws = WorldStateID()
        with self.assertRaises(PermissionError):
            DefinednessWitness(root, path, ws, _internal_token="guessed_token")
        with self.assertRaises(PermissionError):
            DefinednessWitness(root, path, ws, _internal_token=object())

    def test_dw_adv_03_root_replay_attack_fails_closed(self):
        """DW-ADV-03: Replaying a valid witness for Root_A against Root_B fails closed."""
        root_a = CompoundFact()
        root_b = CompoundFact()
        sel = SemanticSelector("f")
        path = CanonicalPath((sel,))
        ws = WorldStateID()
        evaluator = ws.create_evaluator()
        witness = certify_factive_definedness(evaluator, root_a, path)

        self.assertFalse(witness.matches(root_b, path, ws))
        with self.assertRaises(DefinednessPreconditionError):
            witness.verify(root_b, path, ws)
        with self.assertRaises(DefinednessPreconditionError):
            DerivedProjectionFact(root_b, path, witness=witness, world_state_id=ws)

    def test_dw_adv_04_path_name_collision_replay_attack_fails_closed(self):
        """DW-ADV-04: Replaying a valid witness against a path with identical name but different selector identity fails closed."""
        root = CompoundFact()
        sel_a = SemanticSelector("score")
        sel_b = SemanticSelector("score")
        path_a = CanonicalPath((sel_a,))
        path_b = CanonicalPath((sel_b,))
        ws = WorldStateID()
        evaluator = ws.create_evaluator()
        witness = certify_factive_definedness(evaluator, root, path_a)

        self.assertFalse(witness.matches(root, path_b, ws))
        with self.assertRaises(DefinednessPreconditionError):
            witness.verify(root, path_b, ws)
        with self.assertRaises(DefinednessPreconditionError):
            DerivedProjectionFact(root, path_b, witness=witness, world_state_id=ws)

    def test_dw_adv_05_state_mutation_replay_attack_fails_closed(self):
        """DW-ADV-05: Replaying a valid witness from WorldState_1 in WorldState_2 fails closed."""
        root = CompoundFact()
        sel = SemanticSelector("val")
        path = CanonicalPath((sel,))
        ws_1 = WorldStateID()
        ws_2 = WorldStateID()
        evaluator_1 = ws_1.create_evaluator()
        witness = certify_factive_definedness(evaluator_1, root, path)

        self.assertFalse(witness.matches(root, path, ws_2))
        with self.assertRaises(DefinednessPreconditionError):
            witness.verify(root, path, ws_2)
        with self.assertRaises(DefinednessPreconditionError):
            DerivedProjectionFact(root, path, witness=witness, world_state_id=ws_2)

    def test_dw_adv_06_serialization_and_attribute_immutability(self):
        """DW-ADV-06: Copying preserves identity, serialization fails, attribute mutation fails."""
        root = CompoundFact()
        sel = SemanticSelector("attr")
        path = CanonicalPath((sel,))
        ws = WorldStateID()
        evaluator = ws.create_evaluator()
        witness = certify_factive_definedness(evaluator, root, path)

        # Immutability
        self.assertIs(copy.copy(witness), witness)
        self.assertIs(copy.deepcopy(witness), witness)
        with self.assertRaises(TypeError):
            pickle.dumps(witness)
        with self.assertRaises(AttributeError):
            witness._root_id = 9999
        with self.assertRaises(AttributeError):
            witness._world_state_id = 9999

    def test_dw_adv_07_substituting_boolean_for_witness_is_rejected(self):
        """DW-ADV-07: Supplying a boolean where witness capability is required raises TypeError."""
        root = CompoundFact()
        sel = SemanticSelector("x")
        path = CanonicalPath((sel,))
        ws = WorldStateID()
        with self.assertRaises(TypeError):
            DerivedProjectionFact(root, path, witness=True, world_state_id=ws)  # type: ignore[arg-type]

    def test_dw_adv_08_empty_or_undefined_world_space_refuses_issuance(self):
        """DW-ADV-08: Certifying definedness over empty world space or undefined trajectory fails closed."""
        root = CompoundFact()
        sel = SemanticSelector("x")
        path = CanonicalPath((sel,))

        # Empty world space fails closed
        empty_ws = WorldStateID(trajectories=[])
        empty_evaluator = empty_ws.create_evaluator()
        with self.assertRaises(DefinednessPreconditionError) as ctx_empty:
            certify_factive_definedness(empty_evaluator, root, path)
        self.assertIn("vacuous truth has zero epistemic authority", str(ctx_empty.exception))

        # Undefined trajectory fails closed
        undef_ws = WorldStateID(
            trajectories=[
                lambda r, p: SemanticOutcome.defined(1),
                lambda r, p: SemanticOutcome.undefined(),
            ]
        )
        undef_evaluator = undef_ws.create_evaluator()
        with self.assertRaises(DefinednessPreconditionError) as ctx_undef:
            certify_factive_definedness(undef_evaluator, root, path)
        self.assertIn("undefined semantic behavior", str(ctx_undef.exception))


class TestAdversarialDefinednessCertificationAuthority(unittest.TestCase):
    """Adversarial attacks on certify_factive_definedness authority and trajectory provenance."""

    def test_dw_cert_01_direct_call_with_fabricated_behavior_list_is_rejected(self):
        """DW-CERT-01: Direct invocation of certify_factive_definedness with caller-fabricated behavior list raises TypeError."""
        root = CompoundFact()
        sel = SemanticSelector("x")
        path = CanonicalPath((sel,))
        with self.assertRaises(TypeError) as ctx:
            certify_factive_definedness([SemanticOutcome.defined(1)], root, path)  # type: ignore[arg-type]
        self.assertIn("FactiveEvaluator", str(ctx.exception))

    def test_dw_cert_02_caller_cannot_omit_undefined_trajectory_from_evaluator(self):
        """DW-CERT-02: Evaluator executes all trajectories in the world state; caller cannot filter out failing ones."""
        root = CompoundFact()
        sel = SemanticSelector("f")
        path = CanonicalPath((sel,))
        ws = WorldStateID(
            trajectories=[
                lambda r, p: SemanticOutcome.defined(10),
                lambda r, p: SemanticOutcome.undefined(),
            ]
        )
        evaluator = ws.create_evaluator()
        with self.assertRaises(DefinednessPreconditionError):
            certify_factive_definedness(evaluator, root, path)

    def test_dw_cert_03_reusing_evaluation_across_roots_is_rejected(self):
        """DW-CERT-03: Trajectory evaluation is bound to target root; witness for Root_A fails for Root_B."""
        root_a = CompoundFact()
        root_b = CompoundFact()
        sel = SemanticSelector("field")
        path = CanonicalPath((sel,))
        ws = WorldStateID()
        evaluator = ws.create_evaluator()

        witness_a = certify_factive_definedness(evaluator, root_a, path)
        self.assertFalse(witness_a.matches(root_b, path, ws))
        with self.assertRaises(DefinednessPreconditionError):
            witness_a.verify(root_b, path, ws)

    def test_dw_cert_04_reusing_trajectories_across_world_states_fails(self):
        """DW-CERT-04: Evaluator is bound to its WorldStateID; witness cannot be verified under distinct WorldStateID."""
        root = CompoundFact()
        sel = SemanticSelector("k")
        path = CanonicalPath((sel,))
        ws_1 = WorldStateID()
        ws_2 = WorldStateID()
        evaluator_1 = ws_1.create_evaluator()

        witness_1 = certify_factive_definedness(evaluator_1, root, path)
        self.assertFalse(witness_1.matches(root, path, ws_2))
        with self.assertRaises(DefinednessPreconditionError):
            witness_1.verify(root, path, ws_2)

    def test_dw_cert_05_caller_mutation_of_evaluator_trajectories_is_prevented(self):
        """DW-CERT-05: Evaluator trajectories are stored in an immutable tuple."""
        ws = WorldStateID()
        evaluator = ws.create_evaluator()
        with self.assertRaises(AttributeError):
            evaluator.trajectories = ()  # type: ignore[misc]

    def test_dw_cert_06_evaluator_processes_all_trajectories_without_intermediate_interception(self):
        """DW-CERT-06: Evaluator executes all trajectories sequentially and aborts fail-closed on first undefined."""
        trace = []

        def traj_1(r: Any, p: Any) -> SemanticOutcome:
            trace.append("t1")
            return SemanticOutcome.defined(1)

        def traj_2(r: Any, p: Any) -> SemanticOutcome:
            trace.append("t2")
            return SemanticOutcome.undefined()

        def traj_3(r: Any, p: Any) -> SemanticOutcome:
            trace.append("t3")
            return SemanticOutcome.defined(3)

        ws = WorldStateID(trajectories=[traj_1, traj_2, traj_3])
        evaluator = ws.create_evaluator()
        root = CompoundFact()
        sel = SemanticSelector("a")
        path = CanonicalPath((sel,))

        with self.assertRaises(DefinednessPreconditionError):
            evaluator.certify_definedness(root, path)

        # Traced execution stopped at traj_2 failure
        self.assertEqual(trace, ["t1", "t2"])

    def test_dw_cert_07_evaluator_with_empty_trajectories_fails_closed(self):
        """DW-CERT-07: Evaluator with empty trajectories space fails closed."""
        ws = WorldStateID(trajectories=[])
        evaluator = ws.create_evaluator()
        root = CompoundFact()
        sel = SemanticSelector("a")
        path = CanonicalPath((sel,))
        with self.assertRaises(DefinednessPreconditionError) as ctx:
            evaluator.certify_definedness(root, path)
        self.assertIn("vacuous truth has zero epistemic authority", str(ctx.exception))

    def test_dw_cert_08_replaying_witness_after_state_mutation_fails(self):
        """DW-CERT-08: Stale witness fails closed when verified against updated world state."""
        root = CompoundFact()
        sel = SemanticSelector("field")
        path = CanonicalPath((sel,))
        ws_initial = WorldStateID()
        ws_mutated = WorldStateID()
        evaluator = ws_initial.create_evaluator()

        witness = evaluator.certify_definedness(root, path)
        self.assertTrue(witness.matches(root, path, ws_initial))
        self.assertFalse(witness.matches(root, path, ws_mutated))
        with self.assertRaises(DefinednessPreconditionError):
            witness.verify(root, path, ws_mutated)


class TestAdversarialFactiveEvaluatorAuthority(unittest.TestCase):
    """Adversarial attacks on FactiveEvaluator authority, trajectory universe, and construction integrity."""

    def test_fe_adv_01_direct_factive_evaluator_construction_is_prohibited(self):
        """FE-ADV-01: Direct caller construction of FactiveEvaluator without authorization capability is prohibited."""
        ws = WorldStateID()
        with self.assertRaises(PermissionError):
            FactiveEvaluator(world_state=ws)

    def test_fe_adv_02_caller_constructed_factive_trajectory_cannot_be_injected(self):
        """FE-ADV-02: Evaluator cannot be constructed with external trajectory overrides for an existing WorldStateID."""
        ws = WorldStateID()
        evaluator = ws.create_evaluator()
        # Trajectories come strictly from the WorldStateID
        self.assertEqual(evaluator.trajectories, ws.trajectories)

    def test_fe_adv_03_caller_cannot_omit_undefined_trajectory_for_existing_world_state(self):
        """FE-ADV-03: Trajectories are permanently sealed into WorldStateID at creation time."""
        ws = WorldStateID(
            trajectories=[
                lambda r, p: SemanticOutcome.defined(1),
                lambda r, p: SemanticOutcome.undefined(),
            ]
        )
        evaluator = ws.create_evaluator()
        root = CompoundFact()
        sel = SemanticSelector("attr")
        path = CanonicalPath((sel,))
        with self.assertRaises(DefinednessPreconditionError):
            evaluator.certify_definedness(root, path)

    def test_fe_adv_04_multiple_evaluators_for_same_world_state_have_identical_trajectories(self):
        """FE-ADV-04: Multiple evaluators for the same WorldStateID share the exact same sealed trajectory universe."""
        ws = WorldStateID()
        eval1 = ws.create_evaluator()
        eval2 = ws.create_evaluator()
        self.assertEqual(eval1.trajectories, eval2.trajectories)
        self.assertIs(eval1.world_state, eval2.world_state)

    def test_fe_adv_05_reusing_evaluator_across_targets_evaluates_target_specifically(self):
        """FE-ADV-05: Evaluator tests target projection directly; passing an undefined target fails closed."""
        root_defined = CompoundFact()
        root_undefined = CompoundFact()
        sel = SemanticSelector("k")
        path = CanonicalPath((sel,))

        def dynamic_resolver(r: Any, p: Any) -> SemanticOutcome:
            if r == root_defined:
                return SemanticOutcome.defined("OK")
            return SemanticOutcome.undefined()


        ws = WorldStateID(trajectories=[dynamic_resolver])
        evaluator = ws.create_evaluator()

        # Succeeds for root_defined
        witness = evaluator.certify_definedness(root_defined, path)
        self.assertTrue(witness.matches(root_defined, path, ws))

        # Fails closed for root_undefined
        with self.assertRaises(DefinednessPreconditionError):
            evaluator.certify_definedness(root_undefined, path)

    def test_fe_adv_06_mock_or_subclassed_evaluator_cannot_forge_witness(self):
        """FE-ADV-06: Mock/subclass of FactiveEvaluator lacking _ISSUANCE_TOKEN cannot construct or forge DefinednessWitness."""
        class MockEvaluator:
            def __init__(self, ws: WorldStateID):
                self._world_state = ws

            def certify_definedness(self, root: Any, path: Any) -> Any:
                # Attempt to forge DefinednessWitness
                return DefinednessWitness(root, path, self._world_state)

        mock = MockEvaluator(WorldStateID())
        root = CompoundFact()
        sel = SemanticSelector("x")
        path = CanonicalPath((sel,))

        # Passing mock to certify_factive_definedness is rejected with TypeError
        with self.assertRaises(TypeError):
            certify_factive_definedness(mock, root, path)  # type: ignore[arg-type]

        # Calling mock method directly raises PermissionError when trying to construct DefinednessWitness
        with self.assertRaises(PermissionError):
            mock.certify_definedness(root, path)

    def test_fe_adv_07_world_state_trajectories_attribute_is_immutable(self):
        """FE-ADV-07: Direct assignment or deletion of WorldStateID._trajectories is rejected."""
        ws = WorldStateID()
        with self.assertRaises(AttributeError):
            ws._trajectories = ()
        with self.assertRaises(AttributeError):
            del ws._trajectories

    def test_fe_adv_08_stale_evaluator_witness_fails_under_new_world_state(self):
        """FE-ADV-08: Stale evaluator created under ws_1 produces witness that fails verification under ws_2."""
        ws_1 = WorldStateID()
        ws_2 = WorldStateID()
        evaluator_1 = ws_1.create_evaluator()
        root = CompoundFact()
        sel = SemanticSelector("f")
        path = CanonicalPath((sel,))

        witness = evaluator_1.certify_definedness(root, path)
        self.assertTrue(witness.matches(root, path, ws_1))
        self.assertFalse(witness.matches(root, path, ws_2))
        with self.assertRaises(DefinednessPreconditionError):
            witness.verify(root, path, ws_2)


class TestAdversarialOntologicalConstraintTokenAttacks(unittest.TestCase):
    """Adversarial attacks on OntologicalConstraintToken non-forgeability, immutability, and 5-tuple verification."""

    def test_oct_adv_01_direct_issue_without_evaluation_is_prohibited(self):
        """OCT-ADV-01: Direct invocation of internal _issue_from_evaluator without evaluator capability is prohibited."""
        root = CompoundFact()
        sel = SemanticSelector("k")
        path = CanonicalPath((sel,))
        ws = WorldStateID()
        prof = EvaluatorSemanticProfile()
        c = ConstraintContentIdentity()
        with self.assertRaises(PermissionError):
            OntologicalConstraintToken._issue_from_evaluator(root, path, ws, prof, c)

    def test_oct_adv_02_constructor_with_guessed_token_is_prohibited(self):
        """OCT-ADV-02: Direct constructor call with guessed or invalid token is prohibited."""
        root = CompoundFact()
        sel = SemanticSelector("k")
        path = CanonicalPath((sel,))
        ws = WorldStateID()
        prof = EvaluatorSemanticProfile()
        c = ConstraintContentIdentity()
        with self.assertRaises(PermissionError):
            OntologicalConstraintToken(root, path, ws, prof, c, _internal_token="guessed_token")
        with self.assertRaises(PermissionError):
            OntologicalConstraintToken(root, path, ws, prof, c, _internal_token=object())

    def test_oct_adv_03_serialization_and_attribute_immutability(self):
        """OCT-ADV-03: Copying preserves identity, serialization fails, attribute mutation fails."""
        root = CompoundFact()
        sel = SemanticSelector("attr")
        path = CanonicalPath((sel,))
        prof = EvaluatorSemanticProfile()
        c = ConstraintContentIdentity()
        auth = WorldStateAuthority(authorized_constraints=[c])
        ws = auth.create_world_state()
        evaluator = ws.create_evaluator(profile=prof)
        token = authorize_ontological_constraint(evaluator, root, path, c)

        # Immutability
        self.assertIs(copy.copy(token), token)
        self.assertIs(copy.deepcopy(token), token)
        with self.assertRaises(TypeError):
            pickle.dumps(token)
        with self.assertRaises(AttributeError):
            token._root_id = 9999
        with self.assertRaises(AttributeError):
            token._world_state_id = 9999
        with self.assertRaises(AttributeError):
            token._profile_id = 9999
        with self.assertRaises(AttributeError):
            token._constraint_id = 9999

    def test_oct_adv_04_profile_and_constraint_identity_immutability(self):
        """OCT-ADV-04: EvaluatorSemanticProfile and ConstraintContentIdentity attributes are immutable and non-serializable."""
        prof = EvaluatorSemanticProfile(label="p")
        c = ConstraintContentIdentity(structural_digest="d")

        self.assertIs(copy.copy(prof), prof)
        self.assertIs(copy.deepcopy(prof), prof)
        with self.assertRaises(TypeError):
            pickle.dumps(prof)
        with self.assertRaises(AttributeError):
            prof._profile_id = 9999

        self.assertIs(copy.copy(c), c)
        self.assertIs(copy.deepcopy(c), c)
        with self.assertRaises(TypeError):
            pickle.dumps(c)
        with self.assertRaises(AttributeError):
            c._constraint_id = 9999

    def test_oct_adv_05_substituting_boolean_or_witness_for_token_is_rejected(self):
        """OCT-ADV-05: Supplying a boolean or DefinednessWitness where OntologicalConstraintToken is required is rejected."""
        root = CompoundFact()
        sel = SemanticSelector("x")
        path = CanonicalPath((sel,))
        c = ConstraintContentIdentity()
        auth = WorldStateAuthority(authorized_constraints=[c])
        ws = auth.create_world_state()
        prof = EvaluatorSemanticProfile()
        evaluator = ws.create_evaluator(profile=prof)
        witness = certify_factive_definedness(evaluator, root, path)

        # Passing witness or bool to authorize_ontological_constraint helper is rejected
        with self.assertRaises(TypeError):
            authorize_ontological_constraint(witness, root, path, c)  # type: ignore[arg-type]

    def test_oct_adv_06_mock_or_subclassed_token_cannot_forge_authority(self):
        """OCT-ADV-06: Mock/subclass lacking valid internal structure cannot forge token verification."""
        class MockToken:
            def __init__(self, root: Any, path: Any, ws: Any, prof: Any, c: Any):
                self.root_id = getattr(root, "identity", root)
                self.semantic_path = getattr(path, "selectors", path)
                self.world_state_id = getattr(ws, "state_id", ws)
                self.profile_id = getattr(prof, "profile_id", prof)
                self.constraint_id = getattr(c, "constraint_id", c)

        mock = MockToken(CompoundFact(), CanonicalPath((SemanticSelector("k"),)), WorldStateID(), EvaluatorSemanticProfile(), ConstraintContentIdentity())
        self.assertNotIsInstance(mock, OntologicalConstraintToken)

    def test_oct_adv_07_stale_token_after_world_state_mutation_fails_closed(self):
        """OCT-ADV-07: Token issued under WorldState_1 fails closed when verified under WorldState_2."""
        root = CompoundFact()
        sel = SemanticSelector("amount")
        path = CanonicalPath((sel,))
        c = ConstraintContentIdentity()
        auth = WorldStateAuthority(authorized_constraints=[c])
        ws_1 = auth.create_world_state()
        ws_2 = auth.create_world_state()
        prof = EvaluatorSemanticProfile()
        evaluator_1 = ws_1.create_evaluator(profile=prof)

        token = authorize_ontological_constraint(evaluator_1, root, path, c)
        self.assertTrue(token.matches(root, path, ws_1, prof, c))
        self.assertFalse(token.matches(root, path, ws_2, prof, c))
        with self.assertRaises(DefinednessPreconditionError) as ctx:
            token.verify(root, path, ws_2, prof, c)
        self.assertIn("WorldStateID", str(ctx.exception))

    def test_oct_adv_08_constraint_substitution_fails_closed(self):
        """OCT-ADV-08: Token issued for Constraint_A fails closed when verified against Constraint_B even with same label."""
        root = CompoundFact()
        sel = SemanticSelector("score")
        path = CanonicalPath((sel,))
        prof = EvaluatorSemanticProfile()
        c_a = ConstraintContentIdentity(structural_digest="score >= 0")
        c_b = ConstraintContentIdentity(structural_digest="score >= 0")  # distinct instance with distinct constraint_id
        auth = WorldStateAuthority(authorized_constraints=[c_a, c_b])
        ws = auth.create_world_state()
        evaluator = ws.create_evaluator(profile=prof)

        token = authorize_ontological_constraint(evaluator, root, path, c_a)
        self.assertTrue(token.matches(root, path, ws, prof, c_a))
        self.assertFalse(token.matches(root, path, ws, prof, c_b))
        with self.assertRaises(DefinednessPreconditionError) as ctx:
            token.verify(root, path, ws, prof, c_b)
        self.assertIn("ConstraintContentIdentity", str(ctx.exception))


class TestAdversarialOntologicalAuthorityBoundary(unittest.TestCase):
    """Adversarial attacks on ontological constraint authorization boundaries and profile consistency."""

    def setUp(self):
        self.authority = WorldStateAuthority()

    def test_oct_auth_01_profile_construction_does_not_grant_issuance_authority(self):
        """OCT-AUTH-01: Merely instantiating an EvaluatorSemanticProfile does not grant authority to issue tokens."""
        prof = EvaluatorSemanticProfile(label="malicious_profile")
        root = CompoundFact()
        path = CanonicalPath((SemanticSelector("f"),))
        c = ConstraintContentIdentity()
        ws = WorldStateID()
        with self.assertRaises(PermissionError):
            OntologicalConstraintToken(root, path, ws, prof, c)

    def test_oct_auth_02_constraint_construction_does_not_grant_issuance_authority(self):
        """OCT-AUTH-02: Merely instantiating a ConstraintContentIdentity does not authorize restricting W_factive."""
        c = ConstraintContentIdentity(structural_digest="admin == True")
        root = CompoundFact()
        path = CanonicalPath((SemanticSelector("f"),))
        ws = WorldStateID()
        prof = EvaluatorSemanticProfile()
        with self.assertRaises(PermissionError):
            OntologicalConstraintToken(root, path, ws, prof, c)

    def test_oct_auth_03_authorizing_unsealed_constraint_fails_closed(self):
        """OCT-AUTH-03: Attempting to authorize a constraint not sealed in WorldStateID is rejected."""
        root = CompoundFact()
        path = CanonicalPath((SemanticSelector("val"),))
        c_sealed = ConstraintContentIdentity(structural_digest="sealed")
        c_unsealed = ConstraintContentIdentity(structural_digest="unsealed")
        auth = WorldStateAuthority(authorized_constraints=[c_sealed])
        ws = auth.create_world_state()
        evaluator = ws.create_evaluator()

        # Sealed succeeds
        token = authorize_ontological_constraint(evaluator, root, path, c_sealed)
        self.assertTrue(token.matches(root, path, ws, evaluator.profile, c_sealed))

        # Unsealed fails closed
        with self.assertRaises(DefinednessPreconditionError) as ctx:
            authorize_ontological_constraint(evaluator, root, path, c_unsealed)
        self.assertIn("not authorized in WorldStateID", str(ctx.exception))

    def test_oct_auth_04_constraint_with_matching_digest_but_distinct_id_fails_closed(self):
        """OCT-AUTH-04: Constructing a separate constraint with identical digest does not match sealed authority."""
        c_original = ConstraintContentIdentity(structural_digest="balance >= 0")
        c_clone = ConstraintContentIdentity(structural_digest="balance >= 0")
        auth = WorldStateAuthority(authorized_constraints=[c_original])
        ws = auth.create_world_state()
        evaluator = ws.create_evaluator()

        with self.assertRaises(DefinednessPreconditionError):
            authorize_ontological_constraint(evaluator, CompoundFact(), CanonicalPath((SemanticSelector("x"),)), c_clone)

    def test_oct_auth_05_reusing_profile_with_unsealed_constraint_fails(self):
        """OCT-AUTH-05: Caller cannot use an authentic profile to authorize an unsealed constraint."""
        prof = EvaluatorSemanticProfile(label="authentic")
        ws = WorldStateID()
        evaluator = ws.create_evaluator(profile=prof)
        c_attacker = ConstraintContentIdentity()

        with self.assertRaises(DefinednessPreconditionError):
            authorize_ontological_constraint(evaluator, CompoundFact(), CanonicalPath((SemanticSelector("a"),)), c_attacker)

    def test_oct_auth_06_profile_override_mismatch_fails_closed(self):
        """OCT-AUTH-06: Passing a foreign profile override to evaluator.authorize_ontological_constraint is rejected."""
        prof_evaluator = EvaluatorSemanticProfile(label="bound_profile")
        prof_foreign = EvaluatorSemanticProfile(label="foreign_profile")
        c = ConstraintContentIdentity()
        auth = WorldStateAuthority(authorized_constraints=[c])
        ws = auth.create_world_state()
        evaluator = ws.create_evaluator(profile=prof_evaluator)

        with self.assertRaises(DefinednessPreconditionError) as ctx:
            evaluator.authorize_ontological_constraint(
                CompoundFact(), CanonicalPath((SemanticSelector("a"),)), c, profile=prof_foreign
            )
        self.assertIn("mismatched profile", str(ctx.exception))

    def test_oct_auth_07_definedness_evidence_cannot_act_as_constraint_identity(self):
        """OCT-AUTH-07: Definedness evidence or outcomes cannot be supplied as constraint identities."""
        c_bad = SemanticOutcome.defined(True)
        ws = WorldStateID()
        evaluator = ws.create_evaluator()
        with self.assertRaises((TypeError, DefinednessPreconditionError)):
            authorize_ontological_constraint(evaluator, CompoundFact(), CanonicalPath((SemanticSelector("k"),)), c_bad)  # type: ignore[arg-type]

    def test_oct_auth_08_multiple_evaluators_for_same_world_state_share_authorized_constraints(self):
        """OCT-AUTH-08: All evaluators for a WorldStateID observe the exact same sealed authorized constraints."""
        c = ConstraintContentIdentity()
        auth = WorldStateAuthority(authorized_constraints=[c])
        ws = auth.create_world_state()
        eval1 = ws.create_evaluator()
        eval2 = ws.create_evaluator()
        self.assertEqual(eval1.world_state.authorized_constraints, eval2.world_state.authorized_constraints)

    def test_oct_auth_09_token_construction_with_private_field_inspection_is_rejected(self):
        """OCT-AUTH-09: Direct construction of OntologicalConstraintToken even with all valid fields raises PermissionError."""
        root = CompoundFact()
        path = CanonicalPath((SemanticSelector("x"),))
        c = ConstraintContentIdentity()
        auth = WorldStateAuthority(authorized_constraints=[c])
        ws = auth.create_world_state()
        prof = EvaluatorSemanticProfile()

        with self.assertRaises(PermissionError):
            OntologicalConstraintToken(root.identity, path, ws.state_id, prof.profile_id, c.constraint_id)

    def test_oct_auth_10_world_state_authorized_constraints_attribute_is_immutable(self):
        """OCT-AUTH-10: WorldStateID._authorized_constraints cannot be mutated or deleted post-construction."""
        ws = WorldStateID()
        with self.assertRaises(AttributeError):
            ws._authorized_constraints = (1, 2)  # type: ignore[misc]
        with self.assertRaises(AttributeError):
            del ws._authorized_constraints  # type: ignore[misc]


class TestAdversarialWorldStateOntologicalAuthority(unittest.TestCase):
    """Adversarial attacks on WorldStateID creation authority and constraint sealing."""

    def test_ws_auth_01_caller_direct_construction_with_authorized_constraints_is_prohibited(self):
        """WS-AUTH-01: Direct caller instantiation of WorldStateID with authorized_constraints raises PermissionError."""
        c = ConstraintContentIdentity(structural_digest="bypass")
        with self.assertRaises(PermissionError):
            WorldStateID(authorized_constraints=[c])

    def test_ws_auth_02_caller_cloning_trajectories_with_unauthorized_constraint_is_prohibited(self):
        """WS-AUTH-02: Caller cloning legitimate trajectories but adding an unauthorized constraint raises PermissionError."""
        auth = WorldStateAuthority()
        legitimate_ws = auth.create_world_state()
        c_unauthorized = ConstraintContentIdentity()
        with self.assertRaises(PermissionError):
            WorldStateID(trajectories=legitimate_ws.trajectories, authorized_constraints=[c_unauthorized])

    def test_ws_auth_03_caller_removing_constraint_creates_distinct_world_state(self):
        """WS-AUTH-03: Removing a constraint by creating a new WorldStateID generates a new state ID, making prior tokens stale."""
        c = ConstraintContentIdentity()
        auth = WorldStateAuthority(authorized_constraints=[c])
        ws_with_c = auth.create_world_state()
        evaluator = ws_with_c.create_evaluator()
        root = CompoundFact()
        path = CanonicalPath((SemanticSelector("f"),))
        token = authorize_ontological_constraint(evaluator, root, path, c)

        ws_without_c = WorldStateID(trajectories=ws_with_c.trajectories)
        self.assertNotEqual(ws_with_c.state_id, ws_without_c.state_id)
        self.assertEqual(ws_without_c.authorized_constraints, ())
        with self.assertRaises(DefinednessPreconditionError):
            token.verify(root, path, ws_without_c, evaluator.profile, c)

    def test_ws_auth_04_caller_created_world_states_default_to_empty_constraints(self):
        """WS-AUTH-04: Multiple caller-created WorldStateID instances have empty authorized constraints."""
        ws1 = WorldStateID()
        ws2 = WorldStateID()
        self.assertEqual(ws1.authorized_constraints, ())
        self.assertEqual(ws2.authorized_constraints, ())

    def test_ws_auth_05_caller_inserting_observational_evidence_into_authorized_constraints_is_prohibited(self):
        """WS-AUTH-05: Direct insertion of observational evidence or non-constraint types is rejected."""
        with self.assertRaises(PermissionError):
            WorldStateID(authorized_constraints=[SemanticOutcome.defined(True)])  # type: ignore[list-item]

    def test_ws_auth_06_copying_constraint_set_to_new_caller_state_is_prohibited(self):
        """WS-AUTH-06: Copying an authentic authorized constraint set into a new caller-created WorldStateID is rejected."""
        c = ConstraintContentIdentity()
        auth = WorldStateAuthority(authorized_constraints=[c])
        ws_orig = auth.create_world_state()
        with self.assertRaises(PermissionError):
            WorldStateID(authorized_constraints=ws_orig.authorized_constraints)

    def test_ws_auth_07_rebuilding_world_state_with_revoked_constraint_without_authority_is_prohibited(self):
        """WS-AUTH-07: Rebuilding a WorldStateID post-revocation with a revoked constraint identity raises PermissionError."""
        c_revoked = ConstraintContentIdentity()
        with self.assertRaises(PermissionError):
            WorldStateID(authorized_constraints=[c_revoked])

    def test_ws_auth_08_reconstructing_world_state_from_visible_fields_without_authority_is_prohibited(self):
        """WS-AUTH-08: Direct invocation of WorldStateID.create_authorized_state without authority capability is rejected."""
        c = ConstraintContentIdentity()
        with self.assertRaises(PermissionError):
            WorldStateID.create_authorized_state(authorized_constraints=[c])
        with self.assertRaises(PermissionError):
            WorldStateID.create_authorized_state(authorized_constraints=[c], _internal_token="fake_token")

    def test_ws_auth_09_mutable_collection_passed_to_authority_is_defensively_copied(self):
        """WS-AUTH-09: Mutating the input list after creating an authorized world state does not mutate sealed constraints."""
        c1 = ConstraintContentIdentity()
        c2 = ConstraintContentIdentity()
        constraint_list = [c1]
        auth = WorldStateAuthority(authorized_constraints=constraint_list)
        ws = auth.create_world_state()
        self.assertEqual(ws.authorized_constraints, (c1.constraint_id,))

        # Mutate the caller's list
        constraint_list.append(c2)
        self.assertEqual(ws.authorized_constraints, (c1.constraint_id,))

    def test_ws_auth_10_witness_or_evaluator_cannot_inject_constraints_into_world_state(self):
        """WS-AUTH-10: DefinednessWitness or FactiveEvaluator cannot inject authorized constraints into WorldStateID."""
        ws = WorldStateID()
        evaluator = ws.create_evaluator()
        root = CompoundFact()
        path = CanonicalPath((SemanticSelector("x"),))
        witness = certify_factive_definedness(evaluator, root, path)

        self.assertFalse(hasattr(witness, "add_constraint"))
        self.assertFalse(hasattr(evaluator, "add_constraint"))
        self.assertEqual(ws.authorized_constraints, ())


class TestAdversarialWorldStateAuthorityHardening(unittest.TestCase):
    """Adversarial attacks on WorldStateAuthority non-forgeability, scoping, and revocation."""

    def test_wsa_adv_01_caller_direct_construction_is_prohibited(self):
        """WSA-ADV-01: Direct caller instantiation of WorldStateAuthority with non-collection fails cleanly."""
        with self.assertRaises(TypeError):
            WorldStateAuthority(authorized_constraints=12345)  # type: ignore[arg-type]

    def test_wsa_adv_02_sealing_unauthorized_constraint_into_world_state_fails_closed(self):
        """WSA-ADV-02: Asking an authentic WorldStateAuthority to seal an arbitrary unheld constraint fails closed."""
        c_held = ConstraintContentIdentity(structural_digest="held")
        c_unheld = ConstraintContentIdentity(structural_digest="unheld")
        auth = WorldStateAuthority(authorized_constraints=[c_held])

        with self.assertRaises(DefinednessPreconditionError) as ctx:
            auth.create_world_state(authorized_constraints=[c_unheld])
        self.assertIn("not permitted by WorldStateAuthority", str(ctx.exception))

    def test_wsa_adv_03_authority_immutability_and_non_serializability(self):
        """WSA-ADV-03: WorldStateAuthority cannot be mutated, copied to fresh instance, or serialized."""
        c = ConstraintContentIdentity()
        auth = WorldStateAuthority(authorized_constraints=[c])

        self.assertIs(copy.copy(auth), auth)
        self.assertIs(copy.deepcopy(auth), auth)
        with self.assertRaises(TypeError):
            pickle.dumps(auth)
        with self.assertRaises(AttributeError):
            auth._authority_id = 9999
        with self.assertRaises(AttributeError):
            auth._authorized_constraints = ()
        with self.assertRaises(AttributeError):
            del auth._authorized_constraints

    def test_wsa_adv_04_divergent_authorities_produce_distinct_world_states(self):
        """WSA-ADV-04: Two distinct authorities seal distinct constraint sets into distinct world states."""
        c1 = ConstraintContentIdentity(structural_digest="c1")
        c2 = ConstraintContentIdentity(structural_digest="c2")
        auth1 = WorldStateAuthority(authorized_constraints=[c1])
        auth2 = WorldStateAuthority(authorized_constraints=[c2])

        ws1 = auth1.create_world_state()
        ws2 = auth2.create_world_state()
        self.assertEqual(ws1.authorized_constraints, (c1.constraint_id,))
        self.assertEqual(ws2.authorized_constraints, (c2.constraint_id,))

        eval1 = ws1.create_evaluator()
        token1 = authorize_ontological_constraint(eval1, CompoundFact(), CanonicalPath((SemanticSelector("x"),)), c1)
        self.assertFalse(token1.matches(CompoundFact(), CanonicalPath((SemanticSelector("x"),)), ws2, eval1.profile, c1))

    def test_wsa_adv_05_authority_does_not_override_exact_root_path_binding(self):
        """WSA-ADV-05: Authority-sealed constraints remain strictly bound to exact RootID and SemanticPath."""
        c = ConstraintContentIdentity()
        auth = WorldStateAuthority(authorized_constraints=[c])
        ws = auth.create_world_state()
        evaluator = ws.create_evaluator()

        root_a = CompoundFact()
        root_b = CompoundFact()
        path_a = CanonicalPath((SemanticSelector("a"),))
        path_b = CanonicalPath((SemanticSelector("b"),))

        token = authorize_ontological_constraint(evaluator, root_a, path_a, c)
        self.assertTrue(token.matches(root_a, path_a, ws, evaluator.profile, c))
        self.assertFalse(token.matches(root_b, path_a, ws, evaluator.profile, c))
        self.assertFalse(token.matches(root_a, path_b, ws, evaluator.profile, c))

    def test_wsa_adv_06_authority_cannot_bypass_evaluator_profile_binding(self):
        """WSA-ADV-06: Tokens issued from authority-created states fail closed on EvaluatorSemanticProfile mismatch."""
        c = ConstraintContentIdentity()
        auth = WorldStateAuthority(authorized_constraints=[c])
        ws = auth.create_world_state()
        prof_a = EvaluatorSemanticProfile(label="A")
        prof_b = EvaluatorSemanticProfile(label="B")
        evaluator = ws.create_evaluator(profile=prof_a)

        token = authorize_ontological_constraint(evaluator, CompoundFact(), CanonicalPath((SemanticSelector("x"),)), c)
        self.assertFalse(token.matches(CompoundFact(), CanonicalPath((SemanticSelector("x"),)), ws, prof_b, c))

    def test_wsa_adv_07_evaluator_cannot_extend_authority_constraint_set(self):
        """WSA-ADV-07: FactiveEvaluator cannot add constraints to its WorldStateAuthority."""
        auth = WorldStateAuthority()
        ws = auth.create_world_state()
        evaluator = ws.create_evaluator()
        self.assertFalse(hasattr(evaluator, "authorized_constraints"))
        self.assertFalse(hasattr(evaluator, "register_constraint"))

    def test_wsa_adv_08_revoked_authority_cannot_create_world_states(self):
        """WSA-ADV-08: Revoking an authority immediately blocks subsequent create_world_state calls."""
        c = ConstraintContentIdentity()
        auth = WorldStateAuthority(authorized_constraints=[c])
        self.assertFalse(auth.is_revoked)

        # Valid before revocation
        ws_valid = auth.create_world_state()
        self.assertEqual(ws_valid.authorized_constraints, (c.constraint_id,))

        # Revoke
        auth.revoke()
        self.assertTrue(auth.is_revoked)

        # Blocked after revocation
        with self.assertRaises(PermissionError) as ctx:
            auth.create_world_state()
        self.assertIn("revoked WorldStateAuthority", str(ctx.exception))

    def test_wsa_adv_09_mutable_input_to_host_authority_is_defensively_copied(self):
        """WSA-ADV-09: Mutating input list passed to WorldStateAuthority does not alter authority's constraints."""
        c1 = ConstraintContentIdentity()
        c2 = ConstraintContentIdentity()
        c_list = [c1]
        auth = WorldStateAuthority(authorized_constraints=c_list)
        self.assertEqual(auth.authorized_constraints, (c1.constraint_id,))

        c_list.append(c2)
        self.assertEqual(auth.authorized_constraints, (c1.constraint_id,))

    def test_wsa_adv_10_reconstructed_authority_lookalike_fails_internal_token_check(self):
        """WSA-ADV-10: Subclass or lookalike authority cannot forge internal capability to WorldStateID."""
        class MockAuthority:
            def __init__(self):
                self.authorized_constraints = (12345,)
            def create_world_state(self):
                return WorldStateID(authorized_constraints=self.authorized_constraints)

        mock = MockAuthority()
        with self.assertRaises(PermissionError):
            mock.create_world_state()


class TestAdversarialRootIssuanceCapability(unittest.TestCase):
    """ROOT-CAP: Adversarial attacks on the root capability and authority segregation."""

    def test_root_cap_01_import_issuance_token_fails(self):
        """ROOT-CAP-01: Module has no _ISSUANCE_TOKEN attribute and cannot be directly imported."""
        import xoxlang.identity as id_mod
        self.assertFalse(hasattr(id_mod, "_ISSUANCE_TOKEN"))

    def test_root_cap_02_getattr_issuance_token_fails(self):
        """ROOT-CAP-02: getattr on xoxlang.identity for _ISSUANCE_TOKEN returns default or raises."""
        import xoxlang.identity as id_mod
        self.assertIsNone(getattr(id_mod, "_ISSUANCE_TOKEN", None))

    def test_root_cap_03_no_universal_capability_in_module_globals(self):
        """ROOT-CAP-03: No universal issuance capability exists in module globals."""
        import xoxlang.identity as id_mod
        self.assertNotIn("_ISSUANCE_TOKEN", id_mod.__dict__)

    def test_root_cap_04_direct_witness_issuance_without_evaluator_fails(self):
        """ROOT-CAP-04: Direct invocation of DefinednessWitness._issue_from_evaluator without capability raises PermissionError."""
        root = CompoundFact()
        path = CanonicalPath((SemanticSelector("x"),))
        ws = WorldStateID()
        with self.assertRaises(PermissionError):
            DefinednessWitness._issue_from_evaluator(root, path, ws)
        with self.assertRaises(PermissionError):
            DefinednessWitness._issue_from_evaluator(root, path, ws, _internal_token="forged")

    def test_root_cap_05_direct_evaluator_creation_without_world_state_fails(self):
        """ROOT-CAP-05: Direct creation of FactiveEvaluator._create_from_world_state without capability raises PermissionError."""
        ws = WorldStateID()
        with self.assertRaises(PermissionError):
            FactiveEvaluator._create_from_world_state(ws)
        with self.assertRaises(PermissionError):
            FactiveEvaluator._create_from_world_state(ws, _internal_token="forged")

    def test_root_cap_06_authority_cannot_seal_arbitrary_unheld_constraint(self):
        """ROOT-CAP-06: WorldStateAuthority only seals held constraints; unheld constraints fail closed."""
        c_held = ConstraintContentIdentity(structural_digest="held")
        c_attacker = ConstraintContentIdentity(structural_digest="attacker")
        auth = WorldStateAuthority(authorized_constraints=[c_held])
        with self.assertRaises(DefinednessPreconditionError):
            auth.create_world_state(authorized_constraints=[c_attacker])

    def test_root_cap_07_direct_token_issuance_without_evaluator_fails(self):
        """ROOT-CAP-07: Direct invocation of OntologicalConstraintToken._issue_from_evaluator without capability raises PermissionError."""
        root = CompoundFact()
        path = CanonicalPath((SemanticSelector("x"),))
        ws = WorldStateID()
        prof = EvaluatorSemanticProfile()
        c = ConstraintContentIdentity()
        with self.assertRaises(PermissionError):
            OntologicalConstraintToken._issue_from_evaluator(root, path, ws, prof, c)
        with self.assertRaises(PermissionError):
            OntologicalConstraintToken._issue_from_evaluator(root, path, ws, prof, c, _internal_token="forged")

    def test_root_cap_08_cross_capability_escalation_is_prevented(self):
        """ROOT-CAP-08: Using arbitrary objects as capability tokens fails across all protected boundaries."""
        root = CompoundFact()
        path = CanonicalPath((SemanticSelector("x"),))
        ws = WorldStateID()
        prof = EvaluatorSemanticProfile()
        c = ConstraintContentIdentity()
        fake_token = object()

        with self.assertRaises(PermissionError):
            DefinednessWitness(root, path, ws, _internal_token=fake_token)
        with self.assertRaises(PermissionError):
            OntologicalConstraintToken(root, path, ws, prof, c, _internal_token=fake_token)
        with self.assertRaises(PermissionError):
            FactiveEvaluator(ws, _internal_token=fake_token)
        with self.assertRaises(PermissionError):
            WorldStateID(authorized_constraints=[c], _internal_token=fake_token)

    def test_root_cap_09_subclass_cannot_synthesize_authority_capabilities(self):
        """ROOT-CAP-09: Subclasses cannot synthesize internal capability tokens."""
        class MaliciousEvaluator(FactiveEvaluator):
            def __init__(self, ws):
                # Cannot call super().__init__ without valid token
                super().__init__(ws)

        ws = WorldStateID()
        with self.assertRaises(PermissionError):
            MaliciousEvaluator(ws)

    def test_root_cap_10_module_level_boundary_is_structurally_enforced(self):
        """ROOT-CAP-10: Structural object boundaries enforce authority without relying on polite underscore conventions."""
        import xoxlang as xox
        self.assertFalse(hasattr(xox, "_ISSUANCE_TOKEN"))
        self.assertFalse(hasattr(xox, "_CAP_WITNESS_ISSUANCE"))
        self.assertFalse(hasattr(xox, "_CAP_ONTOLOGICAL_ISSUANCE"))


class TestAdversarialDomainCapabilityExfiltration(unittest.TestCase):
    """CAP-EXFIL: Adversarial attacks attempting to exfiltrate and reuse domain capabilities."""

    def test_cap_exfil_01_evaluator_creation_capability_not_in_globals_or_class_dict(self):
        """CAP-EXFIL-01: No evaluator-creation capability token exists in globals or class __dict__."""
        import xoxlang.identity as id_mod
        self.assertNotIn("_CAP_EVALUATOR_CREATION", id_mod.__dict__)
        self.assertNotIn("_CAP_EVALUATOR_CREATION", FactiveEvaluator.__dict__)
        self.assertNotIn("_internal_token", FactiveEvaluator.__dict__)

    def test_cap_exfil_02_witness_issuance_capability_not_in_globals_or_class_dict(self):
        """CAP-EXFIL-02: No witness-issuance capability token exists in globals or class __dict__."""
        import xoxlang.identity as id_mod
        self.assertNotIn("_CAP_WITNESS_ISSUANCE", id_mod.__dict__)
        self.assertNotIn("_CAP_WITNESS_ISSUANCE", DefinednessWitness.__dict__)
        self.assertNotIn("_internal_token", DefinednessWitness.__dict__)

    def test_cap_exfil_03_ontological_issuance_capability_not_in_globals_or_class_dict(self):
        """CAP-EXFIL-03: No ontological constraint issuance capability token exists in globals or class __dict__."""
        import xoxlang.identity as id_mod
        self.assertNotIn("_CAP_ONTOLOGICAL_ISSUANCE", id_mod.__dict__)
        self.assertNotIn("_CAP_ONTOLOGICAL_ISSUANCE", OntologicalConstraintToken.__dict__)
        self.assertNotIn("_internal_token", OntologicalConstraintToken.__dict__)

    def test_cap_exfil_04_world_state_sealing_capability_not_in_globals_or_class_dict(self):
        """CAP-EXFIL-04: No world-state sealing capability token exists in globals or class __dict__."""
        import xoxlang.identity as id_mod
        self.assertNotIn("_CAP_WORLD_STATE_SEALING", id_mod.__dict__)
        self.assertNotIn("_CAP_WORLD_STATE_SEALING", WorldStateID.__dict__)
        self.assertNotIn("_CAP_WORLD_STATE_SEALING", WorldStateAuthority.__dict__)

    def test_cap_exfil_05_method_introspection_yields_no_reusable_capability(self):
        """CAP-EXFIL-05: Inspecting function __defaults__, __kwdefaults__, __closure__, and annotations reveals no tokens."""
        for fn in [
            DefinednessWitness.__init__,
            DefinednessWitness._issue_from_evaluator,
            OntologicalConstraintToken.__init__,
            OntologicalConstraintToken._issue_from_evaluator,
            FactiveEvaluator.__init__,
            FactiveEvaluator._create_from_world_state,
            WorldStateID.__init__,
            WorldStateID.create_authorized_state,
        ]:
            if fn.__defaults__ is not None:
                self.assertTrue(all(d is None for d in fn.__defaults__))
            self.assertIsNone(fn.__kwdefaults__)
            self.assertIsNone(fn.__closure__)


    def test_cap_exfil_06_direct_constructor_invocation_fails_regardless_of_arguments(self):
        """CAP-EXFIL-06: Direct invocation of protected constructors unconditionally raises PermissionError."""
        with self.assertRaises(PermissionError):
            DefinednessWitness(CompoundFact(), CanonicalPath((SemanticSelector("x"),)), WorldStateID())
        with self.assertRaises(PermissionError):
            OntologicalConstraintToken(CompoundFact(), CanonicalPath((SemanticSelector("x"),)), WorldStateID(), EvaluatorSemanticProfile(), ConstraintContentIdentity())
        with self.assertRaises(PermissionError):
            FactiveEvaluator()
        with self.assertRaises(PermissionError):
            WorldStateID(authorized_constraints=[ConstraintContentIdentity()])

    def test_cap_exfil_07_cross_domain_escalation_impossible(self):
        """CAP-EXFIL-07: Domain segregation is absolute; no tokens exist to cross-escalate across boundaries."""
        ws = WorldStateID()
        evaluator = ws.create_evaluator()
        root = CompoundFact()
        path = CanonicalPath((SemanticSelector("x"),))
        witness = evaluator.certify_definedness(root, path)

        # A witness cannot be used to create evaluators or authorize constraints
        with self.assertRaises(TypeError):
            authorize_ontological_constraint(witness, root, path, ConstraintContentIdentity())  # type: ignore[arg-type]

    def test_cap_exfil_08_live_instances_contain_no_capability_references(self):
        """CAP-EXFIL-08: Live authority and token instances contain only public/normative properties in slots."""
        c = ConstraintContentIdentity()
        root = CompoundFact()
        path = CanonicalPath((SemanticSelector("x"),))
        auth = WorldStateAuthority(
            authorized_constraints=[c],
            authorized_resolutions=[(ProvenanceSet([root]), "unwrap_or", 999)],
        )
        ws = auth.create_world_state()
        evaluator = ws.create_evaluator()
        witness = evaluator.certify_definedness(root, path)
        token = evaluator.authorize_ontological_constraint(root, path, c)

        traj1 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj2 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws_var = auth.create_world_state(
            trajectories=[traj1, traj2],
            authorized_resolutions=[(ProvenanceSet([root]), "unwrap_or", 999)],
        )
        eval_var = ws_var.create_evaluator()
        unknown = eval_var.evaluate_projection(root)
        res_token = auth.authorize_resolution(ProvenanceSet([root]), "unwrap_or", ws_var, 999)


        for obj, allowed_slots in [
            (auth, {"_authority_id", "_authorized_constraints", "_authorized_resolutions", "_is_revoked"}),
            (ws, {"_state_id", "_trajectories", "_authorized_constraints", "_authorized_resolutions"}),
            (evaluator, {"_world_state", "_profile"}),
            (witness, {"_root_id", "_semantic_path", "_world_state_id", "_witness_id"}),
            (token, {"_root_id", "_semantic_path", "_world_state_id", "_profile_id", "_constraint_id", "_token_id"}),
            (unknown, {"_provenance_set", "_world_state_id"}),
            (res_token, {"_provenance_set", "_operation_type", "_world_state_id", "_policy_id", "_token_id"}),
        ]:
            actual_slots = set(getattr(obj, "__slots__", ()))
            self.assertEqual(actual_slots, allowed_slots)
            self.assertFalse(hasattr(obj, "__dict__"))


    def test_cap_exfil_09_bound_methods_retain_no_hidden_capability_state(self):
        """CAP-EXFIL-09: Bound methods on instances carry no hidden capability objects."""
        ws = WorldStateID()
        evaluator = ws.create_evaluator()
        method = evaluator.certify_definedness
        self.assertIs(method.__self__, evaluator)
        self.assertIsNone(method.__func__.__closure__)

    def test_cap_exfil_10_structural_enforcement_prevents_replay(self):
        """CAP-EXFIL-10: Replay is impossible because issuance requires executing the actual evaluation lifecycle."""
        # Definedness witness cannot be issued without actual defined evaluation
        bad_traj = FactiveTrajectory(lambda r, p: SemanticOutcome.undefined())
        ws_undefined = WorldStateID(trajectories=[bad_traj])
        evaluator_bad = ws_undefined.create_evaluator()
        with self.assertRaises(DefinednessPreconditionError):
            evaluator_bad.certify_definedness(CompoundFact(), CanonicalPath((SemanticSelector("x"),)))


class TestAdversarialUnknownProvenanceAndResolution(unittest.TestCase):
    """ADV-RES: Adversarial stress tests attacking Unknown provenance and ResolutionToken boundaries."""

    def _create_authentic_unknown(self, auth: WorldStateAuthority, facts: Sequence[AtomicFact], op: str, pol: FallbackPolicyIdentity):
        traj1 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj2 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        pset = ProvenanceSet(facts)
        ws = auth.create_world_state(trajectories=[traj1, traj2])
        evaluator = ws.create_evaluator()
        token = auth.authorize_resolution(pset, op, ws, pol)
        # Produce authentic unknown for fact
        u = evaluator.evaluate_projection(facts[0])
        return ws, evaluator, token, u

    def test_adv_res_01_caller_cannot_construct_resolution_token(self):
        """ADV-RES-01: Direct construction of ResolutionToken unconditionally raises PermissionError."""
        with self.assertRaises(PermissionError):
            ResolutionToken()

    def test_adv_res_02_partial_token_cannot_resolve_unknown(self):
        """ADV-RES-02: Token covering {p1} fails closed against Unknown[{p1, p2}]."""
        f1 = AtomicFact()
        f2 = AtomicFact()
        ps1 = ProvenanceSet([f1])
        ps12 = ProvenanceSet([f1, f2])
        pol = FallbackPolicyIdentity("Fallback_False")

        auth = WorldStateAuthority(authorized_resolutions=[(ps1, "unwrap_or", pol)])
        traj1 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj2 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws = auth.create_world_state(trajectories=[traj1, traj2])
        evaluator = ws.create_evaluator()
        token = auth.authorize_resolution(ps1, "unwrap_or", ws, pol)

        u1 = evaluator.evaluate_projection(f1)
        u2 = evaluator.evaluate_projection(f2)
        u12 = k3_and_with_provenance(u1, lambda: u2)

        with self.assertRaises(DefinednessPreconditionError):
            resolve_unwrap_or(u12, lambda: False, token, ws, pol)

    def test_adv_res_03_token_cannot_resolve_subset(self):
        """ADV-RES-03: Token covering {p1, p2} fails closed against Unknown[{p1}]."""
        f1 = AtomicFact()
        f2 = AtomicFact()
        ps12 = ProvenanceSet([f1, f2])
        pol = FallbackPolicyIdentity("Fallback_False")

        auth = WorldStateAuthority(authorized_resolutions=[(ps12, "unwrap_or", pol)])
        traj1 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj2 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws = auth.create_world_state(trajectories=[traj1, traj2])
        evaluator = ws.create_evaluator()
        token = auth.authorize_resolution(ps12, "unwrap_or", ws, pol)

        u1 = evaluator.evaluate_projection(f1)
        with self.assertRaises(DefinednessPreconditionError):
            resolve_unwrap_or(u1, lambda: False, token, ws, pol)

    def test_adv_res_04_caller_cannot_compose_tokens(self):
        """ADV-RES-04: Presenting an iterable or combination of partial tokens fails closed."""
        f1 = AtomicFact()
        f2 = AtomicFact()
        ps1 = ProvenanceSet([f1])
        ps2 = ProvenanceSet([f2])
        pol = FallbackPolicyIdentity("Fallback_False")

        auth = WorldStateAuthority(authorized_resolutions=[(ps1, "unwrap_or", pol), (ps2, "unwrap_or", pol)])
        traj1 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj2 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws = auth.create_world_state(trajectories=[traj1, traj2])
        evaluator = ws.create_evaluator()
        t1 = auth.authorize_resolution(ps1, "unwrap_or", ws, pol)
        t2 = auth.authorize_resolution(ps2, "unwrap_or", ws, pol)

        u1 = evaluator.evaluate_projection(f1)
        u2 = evaluator.evaluate_projection(f2)
        u12 = k3_and_with_provenance(u1, lambda: u2)

        with self.assertRaises(DefinednessPreconditionError):
            resolve_unwrap_or(u12, lambda: False, [t1, t2], ws, pol)  # type: ignore[arg-type]

    def test_adv_res_05_operation_type_isolation(self):
        """ADV-RES-05: Token for xen_ignore cannot authorize unwrap_or, and vice versa."""
        f1 = AtomicFact()
        ps1 = ProvenanceSet([f1])
        pol = FallbackPolicyIdentity("Fallback_False")

        auth = WorldStateAuthority(authorized_resolutions=[
            (ps1, "xen_ignore", NO_FALLBACK),
            (ps1, "unwrap_or", pol),
        ])
        traj1 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj2 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws = auth.create_world_state(trajectories=[traj1, traj2])
        evaluator = ws.create_evaluator()
        t_ignore = auth.authorize_resolution(ps1, "xen_ignore", ws, NO_FALLBACK)
        t_unwrap = auth.authorize_resolution(ps1, "unwrap_or", ws, pol)

        u = evaluator.evaluate_projection(f1)
        # Attempt to use xen_ignore token in unwrap_or
        with self.assertRaises(DefinednessPreconditionError):
            resolve_unwrap_or(u, lambda: False, t_ignore, ws, pol)

        # Attempt to use unwrap_or token in xen_ignore
        with self.assertRaises(DefinednessPreconditionError):
            resolve_xen_ignore(u, t_unwrap, ws)

    def test_adv_res_06_policy_isolation(self):
        """ADV-RES-06: Token authorized for one fallback policy fails closed against a distinct fallback policy."""
        f1 = AtomicFact()
        ps1 = ProvenanceSet([f1])
        pol_a = FallbackPolicyIdentity("Fallback_A")
        pol_b = FallbackPolicyIdentity("Fallback_B")

        auth = WorldStateAuthority(authorized_resolutions=[(ps1, "unwrap_or", pol_a)])
        traj1 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj2 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws = auth.create_world_state(trajectories=[traj1, traj2])
        evaluator = ws.create_evaluator()
        token = auth.authorize_resolution(ps1, "unwrap_or", ws, pol_a)

        u = evaluator.evaluate_projection(f1)
        with self.assertRaises(DefinednessPreconditionError):
            resolve_unwrap_or(u, lambda: False, token, ws, pol_b)

    def test_adv_res_07_staleness_invalidation(self):
        """ADV-RES-07: Token issued for WorldStateID_1 fails closed when evaluated in WorldStateID_2."""
        f1 = AtomicFact()
        ps1 = ProvenanceSet([f1])
        pol = FallbackPolicyIdentity("Fallback_False")

        auth = WorldStateAuthority(authorized_resolutions=[(ps1, "unwrap_or", pol)])
        traj1 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj2 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws1 = auth.create_world_state(trajectories=[traj1, traj2])
        ws2 = auth.create_world_state(trajectories=[traj1, traj2])
        evaluator1 = ws1.create_evaluator()
        token = auth.authorize_resolution(ps1, "unwrap_or", ws1, pol)

        u = evaluator1.evaluate_projection(f1)
        with self.assertRaises(DefinednessPreconditionError):
            resolve_unwrap_or(u, lambda: False, token, ws2, pol)

    def test_adv_res_08_definedness_witness_cannot_substitute_for_resolution_token(self):
        """ADV-RES-08: DefinednessWitness has zero authority as a ResolutionToken."""
        root = CompoundFact()
        path = CanonicalPath((SemanticSelector("x"),))
        traj1 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj2 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws = WorldStateID(trajectories=[traj1, traj2])
        evaluator = ws.create_evaluator()
        witness = evaluator.certify_definedness(root, path)

        u = evaluator.evaluate_projection(root)
        pol = FallbackPolicyIdentity("Fallback_False")
        with self.assertRaises(DefinednessPreconditionError):
            resolve_unwrap_or(u, lambda: False, witness, ws, pol)  # type: ignore[arg-type]

    def test_adv_res_09_ontological_token_cannot_substitute_for_resolution_token(self):
        """ADV-RES-09: OntologicalConstraintToken has zero authority as a ResolutionToken."""
        root = CompoundFact()
        path = CanonicalPath((SemanticSelector("x"),))
        c = ConstraintContentIdentity()
        auth = WorldStateAuthority(authorized_constraints=[c])
        traj1 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj2 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws = auth.create_world_state(trajectories=[traj1, traj2])
        evaluator = ws.create_evaluator()
        token = evaluator.authorize_ontological_constraint(root, path, c)

        u = evaluator.evaluate_projection(root)
        pol = FallbackPolicyIdentity("Fallback_False")
        with self.assertRaises(DefinednessPreconditionError):
            resolve_unwrap_or(u, lambda: False, token, ws, pol)  # type: ignore[arg-type]

    def test_adv_res_10_world_state_authority_cannot_mint_unsealed_resolutions(self):
        """ADV-RES-10: WorldStateAuthority rejects issuance for policies not sealed at initialization."""
        f1 = AtomicFact()
        f2 = AtomicFact()
        ps1 = ProvenanceSet([f1])
        ps2 = ProvenanceSet([f2])
        pol = FallbackPolicyIdentity("Fallback_False")

        auth = WorldStateAuthority(authorized_resolutions=[(ps1, "unwrap_or", pol)])
        ws = auth.create_world_state()

        # Cannot issue token for unsealed ps2
        with self.assertRaises(DefinednessPreconditionError):
            auth.authorize_resolution(ps2, "unwrap_or", ws, pol)


class TestAdversarialProvenanceOriginAudit(unittest.TestCase):
    """PROV-ORIGIN: Adversarial stress tests attacking Unknown[Pi] origin authority."""

    def test_prov_origin_01_caller_cannot_construct_unknown_value_from_known_fact(self):
        """PROV-ORIGIN-01: Caller takes identity of known AtomicFact, tries to construct UnknownValue."""
        f = AtomicFact()
        pset = ProvenanceSet([f])
        with self.assertRaises(PermissionError):
            UnknownValue(pset)

    def test_prov_origin_02_caller_cannot_combine_resolved_fact_ids_into_unknown(self):
        """PROV-ORIGIN-02: Caller combines two genuine FactIDs into ProvenanceSet, tries to construct UnknownValue."""
        f1 = AtomicFact()
        f2 = AtomicFact()
        pset = ProvenanceSet([f1, f2])
        with self.assertRaises(PermissionError):
            UnknownValue(pset)

    def test_prov_origin_03_caller_cannot_fabricate_unknown_with_mixed_provenance(self):
        """PROV-ORIGIN-03: Caller uses one unresolved fact + one resolved fact to fabricate Unknown."""
        f_unresolved = AtomicFact()
        f_resolved = AtomicFact()
        pset = ProvenanceSet([f_unresolved, f_resolved])
        with self.assertRaises(PermissionError):
            UnknownValue(pset)

    def test_prov_origin_04_caller_cannot_bypass_evaluator_to_construct_unknown(self):
        """PROV-ORIGIN-04: Caller directly constructs UnknownValue from a genuine ProvenanceSet without factive evaluation."""
        f = AtomicFact()
        pset = ProvenanceSet([f])
        with self.assertRaises(PermissionError):
            UnknownValue(facts=[f.identity])

    def test_prov_origin_05_cross_world_state_unknown_injection_fails_closed(self):
        """PROV-ORIGIN-05: Authentic Unknown from WorldStateID_1 fails closed when used in WorldStateID_2."""
        f = AtomicFact()
        pset = ProvenanceSet([f])
        pol = FallbackPolicyIdentity("Fallback_False")
        auth = WorldStateAuthority(authorized_resolutions=[(pset, "unwrap_or", pol)])

        traj1 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj2 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws1 = auth.create_world_state(trajectories=[traj1, traj2])
        ws2 = auth.create_world_state(trajectories=[traj1, traj2])

        evaluator1 = ws1.create_evaluator()
        token2 = auth.authorize_resolution(pset, "unwrap_or", ws2, pol)
        u1 = evaluator1.evaluate_projection(f)

        # Attempt to resolve u1 (bound to ws1) in ws2
        with self.assertRaises(DefinednessPreconditionError):
            resolve_unwrap_or(u1, lambda: False, token2, ws2, pol)

    def test_prov_origin_06_known_fact_cannot_be_labeled_unknown_to_force_xen(self):
        """PROV-ORIGIN-06: Known authorization fact evaluates deterministically; caller cannot label it Unknown."""
        f = AtomicFact()
        # Single trajectory: fact is deterministically True in W_factive
        traj = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        ws = WorldStateID(trajectories=[traj])
        evaluator = ws.create_evaluator()
        outcome = evaluator.evaluate_projection(f)

        # Result is determinate True, NOT UnknownValue
        self.assertIs(outcome, True)
        self.assertNotIsInstance(outcome, UnknownValue)

    def test_prov_origin_07_known_false_fact_cannot_be_labeled_unknown_to_trigger_unwrap(self):
        """PROV-ORIGIN-07: Known False fact evaluates to False, bypassing unwrap_or fallback."""
        f = AtomicFact()
        traj = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws = WorldStateID(trajectories=[traj])
        evaluator = ws.create_evaluator()
        outcome = evaluator.evaluate_projection(f)

        called = False
        def fallback():
            nonlocal called
            called = True
            return True

        # resolve_unwrap_or on deterministic False returns False directly without invoking fallback
        res = resolve_unwrap_or(outcome, fallback)
        self.assertIs(res, False)
        self.assertFalse(called)

    def test_prov_origin_08_derived_projection_fact_requires_factive_evaluation(self):
        """PROV-ORIGIN-08: DerivedProjectionFact without factive evaluation cannot be wrapped in UnknownValue."""
        root = CompoundFact()
        path = CanonicalPath((SemanticSelector("y"),))
        # 1. Uncertified projection cannot form DerivedProjectionFact
        with self.assertRaises(DefinednessPreconditionError):
            DerivedProjectionFact(root, path)

        # 2. Certified projection fact cannot be directly wrapped in UnknownValue by caller
        traj = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        ws = WorldStateID(trajectories=[traj])
        evaluator = ws.create_evaluator()
        witness = evaluator.certify_definedness(root, path)
        dp = DerivedProjectionFact(root, path, witness=witness, world_state_id=ws)

        with self.assertRaises(PermissionError):
            UnknownValue(ProvenanceSet([dp]))



    def test_prov_origin_09_caller_cannot_reconstruct_unknown_from_public_provenance_facts(self):
        """PROV-ORIGIN-09: Caller extracts facts from authentic Unknown and tries to manufacture fresh UnknownValue."""
        traj1 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj2 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws = WorldStateID(trajectories=[traj1, traj2])
        evaluator = ws.create_evaluator()
        f = AtomicFact()
        u = evaluator.evaluate_projection(f)

        # Facts are public/inspectable
        public_facts = u.provenance_set.facts
        reconstructed_pset = ProvenanceSet(public_facts)

        # But caller cannot mint a fresh UnknownValue
        with self.assertRaises(PermissionError):
            UnknownValue(reconstructed_pset)

    def test_prov_origin_10_contradiction_cannot_be_wrapped_as_unknown(self):
        """PROV-ORIGIN-10: Evaluated contradiction fails definedness evaluation; cannot be wrapped in UnknownValue."""
        f = AtomicFact()
        bad_traj = FactiveTrajectory(lambda r, p: SemanticOutcome.undefined())
        ws = WorldStateID(trajectories=[bad_traj])
        evaluator = ws.create_evaluator()

        # Factive evaluation fails closed on undefinedness/contradiction
        with self.assertRaises(DefinednessPreconditionError):
            evaluator.evaluate_projection(f)


class TestAdversarialResolutionAuthorityOrigin(unittest.TestCase):
    """RES-AUTH: Adversarial stress tests attacking ResolutionToken issuance authority."""

    def test_res_auth_01_caller_cannot_mint_arbitrary_fallback_policy(self):
        """RES-AUTH-01: Caller obtains authentic Unknown[Pi] and asks authority for unsealed attacker fallback."""
        f = AtomicFact()
        pol_authorized = FallbackPolicyIdentity("Fallback_False")
        pol_attacker = FallbackPolicyIdentity("Attacker_True")
        auth = WorldStateAuthority(authorized_resolutions=[(ProvenanceSet([f]), "unwrap_or", pol_authorized)])

        traj1 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj2 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws = auth.create_world_state(trajectories=[traj1, traj2])
        evaluator = ws.create_evaluator()
        u = evaluator.evaluate_projection(f)

        # Authority refuses to mint resolution for attacker-selected policy
        with self.assertRaises(DefinednessPreconditionError):
            auth.authorize_resolution(u.provenance_set, "unwrap_or", ws, pol_attacker)

    def test_res_auth_02_caller_cannot_mint_resolution_for_unsealed_provenance(self):
        """RES-AUTH-02: Caller asks authority to mint token for genuine ProvenanceSet not in its catalog."""
        f_in_catalog = AtomicFact()
        f_not_in_catalog = AtomicFact()
        pol = FallbackPolicyIdentity("Fallback_False")
        auth = WorldStateAuthority(authorized_resolutions=[(ProvenanceSet([f_in_catalog]), "unwrap_or", pol)])
        ws = auth.create_world_state()

        with self.assertRaises(DefinednessPreconditionError):
            auth.authorize_resolution(ProvenanceSet([f_not_in_catalog]), "unwrap_or", ws, pol)

    def test_res_auth_03_operation_substitution_fails_closed(self):
        """RES-AUTH-03: Caller reuses authorized ProvenanceSet but substitutes xen_ignore on unwrap_or-only policy."""
        f = AtomicFact()
        pol = FallbackPolicyIdentity("Fallback_False")
        auth = WorldStateAuthority(authorized_resolutions=[(ProvenanceSet([f]), "unwrap_or", pol)])
        ws = auth.create_world_state()

        with self.assertRaises(DefinednessPreconditionError):
            auth.authorize_resolution(ProvenanceSet([f]), "xen_ignore", ws, NO_FALLBACK)

    def test_res_auth_04_fallback_policy_substitution_fails_closed(self):
        """RES-AUTH-04: Caller reuses authorized provenance and operation but substitutes a different policy."""
        f = AtomicFact()
        pol1 = FallbackPolicyIdentity("Policy_1")
        pol2 = FallbackPolicyIdentity("Policy_2")
        auth = WorldStateAuthority(authorized_resolutions=[(ProvenanceSet([f]), "unwrap_or", pol1)])
        ws = auth.create_world_state()

        with self.assertRaises(DefinednessPreconditionError):
            auth.authorize_resolution(ProvenanceSet([f]), "unwrap_or", ws, pol2)

    def test_res_auth_05_attacker_created_equivalent_bool_policy_fails_closed(self):
        """RES-AUTH-05: Attacker creates policy with identical boolean intent but distinct identity."""
        f = AtomicFact()
        pol_legit = FallbackPolicyIdentity("Policy_Legit")
        pol_spoof = FallbackPolicyIdentity("Policy_Spoof")
        auth = WorldStateAuthority(authorized_resolutions=[(ProvenanceSet([f]), "unwrap_or", pol_legit)])
        ws = auth.create_world_state()

        with self.assertRaises(DefinednessPreconditionError):
            auth.authorize_resolution(ProvenanceSet([f]), "unwrap_or", ws, pol_spoof)

    def test_res_auth_06_caller_cannot_mutate_authority_policy_catalog(self):
        """RES-AUTH-06: Caller cannot add a new resolution policy after WorldStateAuthority creation."""
        f = AtomicFact()
        pol = FallbackPolicyIdentity("Policy_New")
        auth = WorldStateAuthority()

        with self.assertRaises(AttributeError):
            auth.authorized_resolutions = ((ProvenanceSet([f]), "unwrap_or", pol.policy_id),)  # type: ignore

    def test_res_auth_07_evaluator_cannot_mint_resolution_authority(self):
        """RES-AUTH-07: FactiveEvaluator cannot mint resolution authority."""
        traj1 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj2 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws = WorldStateID(trajectories=[traj1, traj2])
        evaluator = ws.create_evaluator()
        f = AtomicFact()
        u = evaluator.evaluate_projection(f)

        self.assertFalse(hasattr(evaluator, "authorize_resolution"))

    def test_res_auth_08_witness_or_ontological_token_cannot_substitute_for_resolution_authority(self):
        """RES-AUTH-08: DefinednessWitness or OntologicalConstraintToken has zero resolution authority."""
        root = CompoundFact()
        path = CanonicalPath((SemanticSelector("x"),))
        c = ConstraintContentIdentity()
        auth = WorldStateAuthority(authorized_constraints=[c])
        traj1 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj2 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws = auth.create_world_state(trajectories=[traj1, traj2])
        evaluator = ws.create_evaluator()
        witness = evaluator.certify_definedness(root, path)
        ont_token = evaluator.authorize_ontological_constraint(root, path, c)

        u = evaluator.evaluate_projection(root)
        pol = FallbackPolicyIdentity("Fallback_False")
        with self.assertRaises(DefinednessPreconditionError):
            resolve_unwrap_or(u, lambda: False, witness, ws, pol)  # type: ignore[arg-type]

        with self.assertRaises(DefinednessPreconditionError):
            resolve_unwrap_or(u, lambda: False, ont_token, ws, pol)  # type: ignore[arg-type]


    def test_res_auth_09_policy_revoked_in_world_state_cannot_be_minted(self):
        """RES-AUTH-09: Policy present in authority catalog but excluded in a specific WorldStateID fails closed."""
        f = AtomicFact()
        pol = FallbackPolicyIdentity("Fallback_False")
        pset = ProvenanceSet([f])
        auth = WorldStateAuthority(authorized_resolutions=[(pset, "unwrap_or", pol)])

        # Create world state with explicitly empty authorized_resolutions (policy revoked for this state)
        ws_restricted = auth.create_world_state(authorized_resolutions=[])

        with self.assertRaises(DefinednessPreconditionError):
            auth.authorize_resolution(pset, "unwrap_or", ws_restricted, pol)

    def test_res_auth_10_multiple_evaluators_cannot_diverge_resolution_authority(self):
        """RES-AUTH-10: Two evaluators bound to same WorldStateID derive identical outcomes from same Unknown."""
        f = AtomicFact()
        pol = FallbackPolicyIdentity("Fallback_False")
        pset = ProvenanceSet([f])
        auth = WorldStateAuthority(authorized_resolutions=[(pset, "unwrap_or", pol)])

        traj1 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj2 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws = auth.create_world_state(trajectories=[traj1, traj2])

        evaluator1 = ws.create_evaluator()
        evaluator2 = ws.create_evaluator()

        u1 = evaluator1.evaluate_projection(f)
        u2 = evaluator2.evaluate_projection(f)

        self.assertEqual(u1, u2)
        # Resolution token verified identically for both
        token = auth.authorize_resolution(pset, "unwrap_or", ws, pol)
        res1 = resolve_unwrap_or(u1, lambda: False, token, ws, pol)
        res2 = resolve_unwrap_or(u2, lambda: False, token, ws, pol)
        self.assertIs(res1, res2)


if __name__ == "__main__":
    unittest.main()



