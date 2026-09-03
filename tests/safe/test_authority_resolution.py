"""Tests for experimental O0/SAFE authority, resolution tokens, and fallback policies."""
import unittest

from experimental.safe import (
    FallbackPolicyIdentity,
    NO_FALLBACK,
    ResolutionToken,
    WorldStateAuthority,
    resolve_unwrap_or,
    resolve_xen_ignore,
)
from xoxlang.core_semantics import DefinednessPreconditionError, SemanticOutcome
from xoxlang.identity import (
    AtomicFact,
    CanonicalPath,
    CompoundFact,
    ConstraintContentIdentity,
    EvaluatorSemanticProfile,
    FactiveTrajectory,
    OntologicalConstraintToken,
    ProvenanceSet,
    SemanticSelector,
    WorldStateID,
    authorize_ontological_constraint,
)


class TestOntologicalConstraintTokenAuthority(unittest.TestCase):
    """Verifies OntologicalConstraintToken issuance with WorldStateAuthority, 5-tuple matching, and staleness."""

    def test_ontological_token_exact_5_tuple_matching(self):
        """An OntologicalConstraintToken matches its exact 5-tuple binding."""
        root = CompoundFact()
        sel = SemanticSelector("balance")
        path = CanonicalPath((sel,))
        profile = EvaluatorSemanticProfile(label="v1_strict")
        constraint = ConstraintContentIdentity(structural_digest="balance_non_negative")
        authority = WorldStateAuthority(authorized_constraints=[constraint])
        ws = authority.create_world_state()
        evaluator = ws.create_evaluator(profile=profile)

        token = authorize_ontological_constraint(evaluator, root, path, constraint)
        self.assertTrue(token.matches(root, path, ws, profile, constraint))
        self.assertEqual(token.root_id, root.identity)
        self.assertEqual(token.semantic_path, path.selectors)
        self.assertEqual(token.world_state_id, ws.state_id)
        self.assertEqual(token.profile_id, profile.profile_id)
        self.assertEqual(token.constraint_id, constraint.constraint_id)

    def test_ontological_token_exact_reuse_is_valid(self):
        """Exact token reuse against the same 5-tuple remains valid within the same WorldStateID."""
        root = CompoundFact()
        sel = SemanticSelector("age")
        path = CanonicalPath((sel,))
        profile = EvaluatorSemanticProfile()
        constraint = ConstraintContentIdentity()
        authority = WorldStateAuthority(authorized_constraints=[constraint])
        ws = authority.create_world_state()
        evaluator = ws.create_evaluator(profile=profile)

        token = authorize_ontological_constraint(evaluator, root, path, constraint)
        token.verify(root, path, ws, profile, constraint)
        token.verify(root, path, ws, profile, constraint)
        self.assertTrue(token.matches(root, path, ws, profile, constraint))

    def test_ontological_token_mismatches_fail_closed(self):
        """Mismatch on any of the 5 axes fails closed with DefinednessPreconditionError."""
        root1 = CompoundFact()
        root2 = CompoundFact()
        path1 = CanonicalPath((SemanticSelector("a"),))
        path2 = CanonicalPath((SemanticSelector("b"),))
        prof1 = EvaluatorSemanticProfile(label="p1")
        prof2 = EvaluatorSemanticProfile(label="p2")
        c1 = ConstraintContentIdentity(structural_digest="c1")
        c2 = ConstraintContentIdentity(structural_digest="c2")
        authority = WorldStateAuthority(authorized_constraints=[c1])
        ws1 = authority.create_world_state()
        ws2 = authority.create_world_state()

        evaluator1 = ws1.create_evaluator(profile=prof1)
        token = authorize_ontological_constraint(evaluator1, root1, path1, c1)

        # Root mismatch
        self.assertFalse(token.matches(root2, path1, ws1, prof1, c1))
        with self.assertRaises(DefinednessPreconditionError):
            token.verify(root2, path1, ws1, prof1, c1)

        # Path mismatch
        self.assertFalse(token.matches(root1, path2, ws1, prof1, c1))
        with self.assertRaises(DefinednessPreconditionError):
            token.verify(root1, path2, ws1, prof1, c1)

        # WorldStateID mismatch (staleness)
        self.assertFalse(token.matches(root1, path1, ws2, prof1, c1))
        with self.assertRaises(DefinednessPreconditionError):
            token.verify(root1, path1, ws2, prof1, c1)

        # Profile mismatch
        self.assertFalse(token.matches(root1, path1, ws1, prof2, c1))
        with self.assertRaises(DefinednessPreconditionError):
            token.verify(root1, path1, ws1, prof2, c1)

        # ConstraintContentIdentity mismatch
        self.assertFalse(token.matches(root1, path1, ws1, prof1, c2))
        with self.assertRaises(DefinednessPreconditionError):
            token.verify(root1, path1, ws1, prof1, c2)


class TestFallbackPolicyIdentity(unittest.TestCase):
    """Test suite for FallbackPolicyIdentity canonical structural semantic identity."""

    def test_fallback_policy_identity_creation(self):
        prof = EvaluatorSemanticProfile()
        ref = AtomicFact()
        pol = FallbackPolicyIdentity("Digest_X", referents=[ref], profile=prof)
        self.assertEqual(pol.structural_digest, "Digest_X")
        self.assertEqual(pol.referents, (ref.identity,))
        self.assertEqual(pol.profile_id, prof.profile_id)

    def test_no_fallback_constant(self):
        self.assertEqual(NO_FALLBACK.structural_digest, "NO_FALLBACK")


class TestResolutionToken(unittest.TestCase):
    """Test suite for ResolutionToken exact 4-tuple binding and verification."""

    def test_authorized_resolution_token_issuance_and_exact_match(self):
        f1 = AtomicFact()
        pset = ProvenanceSet([f1])
        pol = FallbackPolicyIdentity("Fallback_False")
        auth = WorldStateAuthority(authorized_resolutions=[(pset, "unwrap_or", pol)])
        ws = auth.create_world_state()

        token = auth.authorize_resolution(pset, "unwrap_or", ws, pol)
        self.assertEqual(token.provenance_set, pset)
        self.assertEqual(token.operation_type, "unwrap_or")
        self.assertEqual(token.world_state_id, ws.state_id)
        self.assertEqual(token.policy_id, pol.policy_id)

        # Exact match verification
        token.verify(pset, "unwrap_or", ws, pol)

    def test_resolution_token_mismatches_fail_closed(self):
        f1 = AtomicFact()
        f2 = AtomicFact()
        ps1 = ProvenanceSet([f1])
        ps2 = ProvenanceSet([f1, f2])
        pol1 = FallbackPolicyIdentity("Pol1")
        pol2 = FallbackPolicyIdentity("Pol2")

        auth1 = WorldStateAuthority(authorized_resolutions=[(ps1, "unwrap_or", pol1)])
        ws1 = auth1.create_world_state()
        ws2 = WorldStateID()

        token = auth1.authorize_resolution(ps1, "unwrap_or", ws1, pol1)

        # Provenance mismatch
        self.assertFalse(token.matches(ps2, "unwrap_or", ws1, pol1))
        with self.assertRaises(DefinednessPreconditionError):
            token.verify(ps2, "unwrap_or", ws1, pol1)

        # OperationType mismatch
        self.assertFalse(token.matches(ps1, "xen_ignore", ws1, pol1))
        with self.assertRaises(DefinednessPreconditionError):
            token.verify(ps1, "xen_ignore", ws1, pol1)

        # WorldStateID mismatch (staleness)
        self.assertFalse(token.matches(ps1, "unwrap_or", ws2, pol1))
        with self.assertRaises(DefinednessPreconditionError):
            token.verify(ps1, "unwrap_or", ws2, pol1)

        # Policy mismatch
        self.assertFalse(token.matches(ps1, "unwrap_or", ws1, pol2))
        with self.assertRaises(DefinednessPreconditionError):
            token.verify(ps1, "unwrap_or", ws1, pol2)

    def test_direct_resolution_token_construction_prohibited(self):
        with self.assertRaises(PermissionError):
            ResolutionToken()


class TestResolveUnwrapOrAndXenIgnore(unittest.TestCase):
    """Test suite for resolve_unwrap_or and resolve_xen_ignore authority enforcement."""

    def test_resolve_unwrap_or_success_and_lazy_evaluation(self):
        f1 = AtomicFact()
        pset = ProvenanceSet([f1])
        pol = FallbackPolicyIdentity("Fallback_False")
        auth = WorldStateAuthority(authorized_resolutions=[(pset, "unwrap_or", pol)])
        traj1 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj2 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws = auth.create_world_state(trajectories=[traj1, traj2])
        evaluator = ws.create_evaluator()
        token = auth.authorize_resolution(pset, "unwrap_or", ws, pol)

        called = False
        def fallback():
            nonlocal called
            called = True
            return False

        u = evaluator.evaluate_projection(f1)
        res = resolve_unwrap_or(u, fallback, token, ws, pol)
        self.assertIs(res, False)
        self.assertTrue(called)

    def test_resolve_xen_ignore_success(self):
        f1 = AtomicFact()
        pset = ProvenanceSet([f1])
        auth = WorldStateAuthority(authorized_resolutions=[(pset, "xen_ignore", NO_FALLBACK)])
        traj1 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj2 = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws = auth.create_world_state(trajectories=[traj1, traj2])
        evaluator = ws.create_evaluator()
        token = auth.authorize_resolution(pset, "xen_ignore", ws, NO_FALLBACK)

        u = evaluator.evaluate_projection(f1)
        res = resolve_xen_ignore(u, token, ws)
        self.assertTrue(res)


if __name__ == "__main__":
    unittest.main()
