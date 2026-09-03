"""O0/SAFE enforcement tests for permissive fallback (MUT-04) detection and containment.

Validates that existing O0/SAFE governance invariants:
- INV_STAGE_CATEGORY_NON_SUBSTITUTION
- INV_AUTHORIZED_RESOLUTION_BOUNDARY
- INV_POLICY_APPLICABILITY_AUTHORITY
- INV_RELEVANT_CONTEXT_BINDING
- INV_CAPABILITY_ENVELOPE_BINDING

structurally detect and reject unauthorized permissive collapses (such as unwrap_or(True))
in authorization contexts without altering S1 language semantics or the unwrap_or primitive.
"""

import unittest
from xoxlang.core_semantics import DefinednessPreconditionError, SemanticOutcome
from xoxlang.runtime import XoX
from experimental.safe import (
    FallbackPolicyIdentity,
    NO_FALLBACK,
    WorldStateAuthority,
    resolve_unwrap_or,
)
from xoxlang.identity import (
    AtomicFact,
    FactiveTrajectory,
    ProvenanceSet,
)


class TestSafePermissiveFallbackEnforcement(unittest.TestCase):
    """Verifies that O0/SAFE authority envelopes prevent unauthorized permissive fallbacks."""

    def setUp(self):
        self.fact_auth = AtomicFact(payload="user:bob:action:read_secret")
        self.pset_auth = ProvenanceSet([self.fact_auth])

        self.pol_strict_deny = FallbackPolicyIdentity("POLICY_STRICT_DENY_FALSE")
        self.pol_permissive_allow = FallbackPolicyIdentity("POLICY_PERMISSIVE_ALLOW_TRUE")

        # Authority authorizes ONLY strict deny policy for unwrap_or on this provenance set
        self.authority = WorldStateAuthority(
            authorized_resolutions=[(self.pset_auth, "unwrap_or", self.pol_strict_deny)]
        )

        # Factive trajectories creating indeterminate/Unknown outcome
        traj_true = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj_false = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))

        self.ws = self.authority.create_world_state(trajectories=[traj_true, traj_false])
        self.evaluator = self.ws.create_evaluator()
        self.unknown_auth = self.evaluator.evaluate_projection(self.fact_auth)

    def test_case_1_unknown_unwrap_true_without_policy_authority_rejected(self):
        """Case 1: UNKNOWN + unwrap_or(True) without policy authority -> REJECT.

        Violates INV_AUTHORIZED_RESOLUTION_BOUNDARY and INV_POLICY_APPLICABILITY_AUTHORITY.
        """
        # 1a. Attempting to issue a token for permissive allow when not in authorized resolutions fails
        with self.assertRaises(DefinednessPreconditionError) as ctx:
            self.authority.authorize_resolution(
                self.pset_auth, "unwrap_or", self.ws, self.pol_permissive_allow
            )
        self.assertIn("not authorized", str(ctx.exception))

        # 1b. Attempting to invoke resolve_unwrap_or without a valid ResolutionToken fails closed
        with self.assertRaises(DefinednessPreconditionError) as ctx:
            resolve_unwrap_or(
                self.unknown_auth,
                lambda: True,
                token=None,
                world_state=self.ws,
                fallback_policy=self.pol_permissive_allow,
            )
        self.assertIn("Cannot unwrap Unknown with provenance without a valid ResolutionToken", str(ctx.exception))

        # 1c. Attempting to invoke unwrap_or(True) using the strict-deny token causes FallbackPolicyIdentity mismatch
        valid_deny_token = self.authority.authorize_resolution(
            self.pset_auth, "unwrap_or", self.ws, self.pol_strict_deny
        )
        with self.assertRaises(DefinednessPreconditionError) as ctx:
            resolve_unwrap_or(
                self.unknown_auth,
                lambda: True,
                token=valid_deny_token,
                world_state=self.ws,
                fallback_policy=self.pol_permissive_allow,
            )
        self.assertIn("FallbackPolicyIdentity", str(ctx.exception))

    def test_case_2_unknown_unwrap_false_under_applicable_policy_accepted(self):
        """Case 2: UNKNOWN + unwrap_or(False) under applicable authorized policy -> ACCEPT.

        Conforms to INV_AUTHORIZED_RESOLUTION_BOUNDARY and INV_CAPABILITY_ENVELOPE_BINDING.
        """
        valid_deny_token = self.authority.authorize_resolution(
            self.pset_auth, "unwrap_or", self.ws, self.pol_strict_deny
        )
        called = False

        def fallback_deny():
            nonlocal called
            called = True
            return False

        result = resolve_unwrap_or(
            self.unknown_auth,
            fallback_deny,
            token=valid_deny_token,
            world_state=self.ws,
            fallback_policy=self.pol_strict_deny,
        )
        self.assertIs(result, False)
        self.assertTrue(called)

    def test_case_3_unknown_fallback_explicitly_authorized_accepted(self):
        """Case 3: UNKNOWN + fallback explicitly authorized -> ACCEPT.

        When a domain explicitly authorizes a permissive fallback under valid governance,
        the capability envelope permits the resolution.
        """
        pol_breakglass = FallbackPolicyIdentity("POLICY_EMERGENCY_BREAKGLASS_TRUE")
        breakglass_authority = WorldStateAuthority(
            authorized_resolutions=[(self.pset_auth, "unwrap_or", pol_breakglass)]
        )
        traj_true = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj_false = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))

        ws_bg = breakglass_authority.create_world_state(trajectories=[traj_true, traj_false])
        evaluator_bg = ws_bg.create_evaluator()
        unknown_bg = evaluator_bg.evaluate_projection(self.fact_auth)

        token_bg = breakglass_authority.authorize_resolution(
            self.pset_auth, "unwrap_or", ws_bg, pol_breakglass
        )

        called = False

        def fallback_allow():
            nonlocal called
            called = True
            return True

        result = resolve_unwrap_or(
            unknown_bg,
            fallback_allow,
            token=token_bg,
            world_state=ws_bg,
            fallback_policy=pol_breakglass,
        )
        self.assertIs(result, True)
        self.assertTrue(called)

    def test_case_4_policy_token_out_of_context_rejected(self):
        """Case 4: policy token out of context -> REJECT.

        Violates INV_RELEVANT_CONTEXT_BINDING.
        A token authorized in WorldState A cannot be replayed in WorldState B (epoch/state drift).
        """
        valid_deny_token = self.authority.authorize_resolution(
            self.pset_auth, "unwrap_or", self.ws, self.pol_strict_deny
        )

        # Create a second, distinct world state under the same authority (simulating state advance / epoch bump)
        traj_true = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj_false = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws2 = self.authority.create_world_state(trajectories=[traj_true, traj_false])
        evaluator2 = ws2.create_evaluator()
        unknown_ws2 = evaluator2.evaluate_projection(self.fact_auth)

        # Using token from ws1 in ws2 fails closed
        with self.assertRaises(DefinednessPreconditionError) as ctx:
            resolve_unwrap_or(
                unknown_ws2,
                lambda: False,
                token=valid_deny_token,
                world_state=ws2,
                fallback_policy=self.pol_strict_deny,
            )
        self.assertIn("WorldStateID", str(ctx.exception))

    def test_case_5_policy_replay_cross_action_or_cross_resource_rejected(self):
        """Case 5: policy replay cross-action or cross-resource -> REJECT.

        Violates INV_CAPABILITY_ENVELOPE_BINDING.
        """
        # 5a. Cross-resource replay: token for resource 1 used on resource 2
        fact_other = AtomicFact(payload="user:bob:action:write_admin")
        pset_other = ProvenanceSet([fact_other])
        unknown_other = self.evaluator.evaluate_projection(fact_other)

        valid_deny_token_auth = self.authority.authorize_resolution(
            self.pset_auth, "unwrap_or", self.ws, self.pol_strict_deny
        )

        with self.assertRaises(DefinednessPreconditionError) as ctx:
            resolve_unwrap_or(
                unknown_other,
                lambda: False,
                token=valid_deny_token_auth,
                world_state=self.ws,
                fallback_policy=self.pol_strict_deny,
            )
        self.assertIn("ProvenanceSet", str(ctx.exception))

        # 5b. Cross-action replay: token for xen_ignore replayed on unwrap_or
        authority_multiaction = WorldStateAuthority(
            authorized_resolutions=[
                (self.pset_auth, "xen_ignore", NO_FALLBACK),
                (self.pset_auth, "unwrap_or", self.pol_strict_deny),
            ]
        )
        ws_multi = authority_multiaction.create_world_state(
            trajectories=[
                FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True)),
                FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False)),
            ]
        )
        evaluator_multi = ws_multi.create_evaluator()
        unknown_multi = evaluator_multi.evaluate_projection(self.fact_auth)

        token_xen_ignore = authority_multiaction.authorize_resolution(
            self.pset_auth, "xen_ignore", ws_multi, NO_FALLBACK
        )

        with self.assertRaises(DefinednessPreconditionError) as ctx:
            resolve_unwrap_or(
                unknown_multi,
                lambda: False,
                token=token_xen_ignore,
                world_state=ws_multi,
                fallback_policy=self.pol_strict_deny,
            )
        self.assertIn("OperationType", str(ctx.exception))

    def test_case_6_mut05_host_freshness_boundary(self):
        """Case 6: MUT-05 host freshness boundary verification.

        Demonstrates:
        1. MUT05_KNOWN_WORLD_CHANGE: Known/signaled world state advance rejects old context/tokens.
        2. MUT05_UNSIGNALED_EXTERNAL_CHANGE: Within declared context, evaluation proceeds without autonomous polling.
        3. MUT05_HOST_SIGNAL_THEN_INVALIDATION: Host-signaled state advance invalidates prior authority while new token is accepted.
        """
        valid_token_a = self.authority.authorize_resolution(
            self.pset_auth, "unwrap_or", self.ws, self.pol_strict_deny
        )

        # 1. MUT05_KNOWN_WORLD_CHANGE: Advance to WorldState B
        traj_true = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
        traj_false = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))
        ws_b = self.authority.create_world_state(trajectories=[traj_true, traj_false])
        evaluator_b = ws_b.create_evaluator()
        unknown_b = evaluator_b.evaluate_projection(self.fact_auth)

        with self.assertRaises(DefinednessPreconditionError) as ctx:
            resolve_unwrap_or(
                unknown_b,
                lambda: False,
                token=valid_token_a,
                world_state=ws_b,
                fallback_policy=self.pol_strict_deny,
            )
        self.assertIn("WorldStateID", str(ctx.exception))

        # 2. MUT05_UNSIGNALED_EXTERNAL_CHANGE: In ws_a (no host advance), token_a evaluates normally
        res_a = resolve_unwrap_or(
            self.unknown_auth,
            lambda: False,
            token=valid_token_a,
            world_state=self.ws,
            fallback_policy=self.pol_strict_deny,
        )
        self.assertIs(res_a, False)

        # 3. MUT05_HOST_SIGNAL_THEN_INVALIDATION: New token in ws_b evaluates cleanly
        token_b = self.authority.authorize_resolution(
            self.pset_auth, "unwrap_or", ws_b, self.pol_strict_deny
        )
        res_b = resolve_unwrap_or(
            unknown_b,
            lambda: False,
            token=token_b,
            world_state=ws_b,
            fallback_policy=self.pol_strict_deny,
        )
        self.assertIs(res_b, False)


if __name__ == "__main__":
    unittest.main()
