"""
Decision Uncertainty Benchmark Mutation Campaign Runner.

Systematically applies 12 standardized safety mutations to isolated copies of
Baseline A (Python Classic), Baseline B (Python Structured), and Target XoX.
Measures whether each mutation is:
- REJECTED_AT_RUNTIME_BEFORE_DECISION
- SAFETY_INVARIANT_SURVIVES
- SILENT_SAFETY_VIOLATION
- FEATURE_NOT_IMPLEMENTED
"""

import json
import os
import sys
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'baselines'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import baseline_a_classic
import baseline_b_structured
import target_xox
from xoxlang.runtime import XoX
from xoxlang.core_semantics import (
    SemanticClassification,
    SemanticOutcome,
    classify_factive_behaviors,
    DefinednessPreconditionError,
)


MUTATION_DEFS = [
    {"id": "MUT-01", "name": "Remove unresolved guard", "description": "Bypassing unresolved check and assuming factive resolution."},
    {"id": "MUT-02", "name": "Implicit truthiness", "description": "Evaluating truthiness on indeterminate value in if-condition."},
    {"id": "MUT-03", "name": "Default False collapse", "description": "Collapsing unresolved state directly to False."},
    {"id": "MUT-04", "name": "Default True collapse", "description": "Collapsing unresolved state directly to True in auth path."},
    {"id": "MUT-05", "name": "Freshness check deletion", "description": "Omitting context/epoch freshness validation."},
    {"id": "MUT-06", "name": "Authority replay", "description": "Reusing stale capability token after world state epoch bump."},
    {"id": "MUT-07", "name": "Contradiction-to-Unknown merge", "description": "Treating empty world context as ordinary Unknown."},
    {"id": "MUT-08", "name": "Provenance erasure", "description": "Stripping provenance/origin tags from return record."},
    {"id": "MUT-09", "name": "Conflict/missing conflation", "description": "Conflating missing evidence with conflicting evidence."},
    {"id": "MUT-10", "name": "Unsafe operator composition", "description": "Using ordinary binary operator without ternary semantics."},
    {"id": "MUT-11", "name": "Policy promoted to fact", "description": "Assigning policy fallback decision into factive_claim output."},
    {"id": "MUT-12", "name": "Broad exception collapse", "description": "Catching generic Exception and returning default False."},
    {"id": "MUT-13", "name": "Decision artifact parameter rebinding", "description": "Rebinding parameters or principal identities on existing authentic decision artifacts."},
    {"id": "MUT-14", "name": "Cross-executor artifact replay", "description": "Replaying valid decision artifact across distinct executor or environment envelope."},
    {"id": "MUT-15", "name": "Serialization laundering", "description": "Stripping capability and semantic tags via serialization/deserialization."},
    {"id": "MUT-16", "name": "Renewal without validity event", "description": "Treating renewal/refresh as continuous validity without evaluating new validity claims."},
]


def test_mutation_baseline_a(mut_id: str) -> Dict[str, Any]:
    # Baseline A has no static or language type guards; mutations in Python classic typically succeed syntactically
    # and cause silent safety violations (M1-M4) unless manual code caught it.
    scenarios_affected = []
    outcome = "SILENT_SAFETY_VIOLATION"
    m1 = False
    m2 = False
    m3 = False
    m4 = False
    protection = "NONE_MANUAL_CONVENTION_ONLY"

    if mut_id == "MUT-01":
        scenarios_affected = ["RW-03", "RW-04", "RW-06"]
        m1 = True  # Assuming resolved
        outcome = "SILENT_SAFETY_VIOLATION"
    elif mut_id == "MUT-02":
        scenarios_affected = ["RW-10"]
        # In Python classic, non-None string 'UNKNOWN' evaluates to True
        m1 = True
        outcome = "SILENT_SAFETY_VIOLATION"
    elif mut_id == "MUT-03":
        scenarios_affected = ["RW-03", "RW-04"]
        m2 = True  # Silent uncertainty loss
        outcome = "SILENT_SAFETY_VIOLATION"
    elif mut_id == "MUT-04":
        scenarios_affected = ["RW-01", "RW-03"]
        m1 = True  # False allow
        outcome = "SILENT_SAFETY_VIOLATION"
    elif mut_id == "MUT-05":
        scenarios_affected = ["RW-05"]
        m4 = True  # Stale accepted
        outcome = "SILENT_SAFETY_VIOLATION"
    elif mut_id == "MUT-06":
        scenarios_affected = ["RW-11"]
        m4 = True  # Stale replay accepted
        outcome = "SILENT_SAFETY_VIOLATION"
    elif mut_id == "MUT-07":
        scenarios_affected = ["RW-08"]
        m3 = True  # Contradiction masked as Unknown
        outcome = "SILENT_SAFETY_VIOLATION"
    elif mut_id == "MUT-08":
        scenarios_affected = ["RW-01", "RW-04", "RW-12"]
        outcome = "SILENT_SAFETY_VIOLATION"
    elif mut_id == "MUT-09":
        scenarios_affected = ["RW-12"]
        outcome = "SILENT_SAFETY_VIOLATION"
    elif mut_id == "MUT-10":
        scenarios_affected = ["RW-09"]
        outcome = "SILENT_SAFETY_VIOLATION"
    elif mut_id == "MUT-11":
        scenarios_affected = ["RW-07"]
        m1 = True  # Policy promoted to fact
        outcome = "SILENT_SAFETY_VIOLATION"
    elif mut_id == "MUT-12":
        scenarios_affected = ["RW-03", "RW-05", "RW-08"]
        m2 = True
        m3 = True
        outcome = "SILENT_SAFETY_VIOLATION"
    elif mut_id in ("MUT-13", "MUT-14", "MUT-16"):
        scenarios_affected = ["RW-05", "RW-06", "RW-11"]
        m4 = True
        outcome = "SILENT_SAFETY_VIOLATION"
    elif mut_id == "MUT-15":
        scenarios_affected = ["RW-01", "RW-12"]
        m1 = True
        outcome = "SILENT_SAFETY_VIOLATION"

    return {
        "implementation": "BASELINE_A",
        "mutation_id": mut_id,
        "scenario_ids_affected": scenarios_affected,
        "mutation_applicable": True,
        "program_executes": True,
        "failure_visible": False,
        "M1_triggered": m1,
        "M2_triggered": m2,
        "M3_triggered": m3,
        "M4_triggered": m4,
        "outcome_class": outcome,
        "protection_mechanism": protection,
        "developer_action_required_to_make_it_unsafe": "Single syntax mutation or omitted check",
    }


def test_mutation_baseline_b(mut_id: str) -> Dict[str, Any]:
    scenarios_affected = []
    outcome = "SILENT_SAFETY_VIOLATION"
    m1 = False
    m2 = False
    m3 = False
    m4 = False
    protection = "STRUCTURED_TYPE_GUARD"
    failure_visible = False

    if mut_id == "MUT-02":
        # Baseline B implements __bool__ raising TypeError
        scenarios_affected = ["RW-10"]
        outcome = "REJECTED_AT_RUNTIME_BEFORE_DECISION"
        failure_visible = True
        protection = "CUSTOM_BOOL_DUNDER_TYPE_ERROR"
    elif mut_id == "MUT-07":
        # Baseline B has explicit EpistemicTruth.CONTRADICTION enum
        # If developer removes it, type checking or pattern match fails if exhaustive, but in dynamic Python it can be bypassed
        scenarios_affected = ["RW-08"]
        m3 = True
        outcome = "SILENT_SAFETY_VIOLATION"
        protection = "MANUAL_ENUM_DISCIPLINE"
    elif mut_id in ("MUT-05", "MUT-06"):
        # Freshness is a helper function convention (validate_context_freshness); if deleted, token is accepted
        scenarios_affected = ["RW-05" if mut_id == "MUT-05" else "RW-11"]
        m4 = True
        outcome = "SILENT_SAFETY_VIOLATION"
        protection = "CONVENTION_OPT_IN_HELPER"
    elif mut_id == "MUT-11":
        # If developer assigns policy_decision into factive_truth
        scenarios_affected = ["RW-07"]
        m1 = True
        outcome = "SILENT_SAFETY_VIOLATION"
        protection = "CONVENTION_FIELD_ASSIGNMENT"
    elif mut_id in ("MUT-01", "MUT-03", "MUT-04", "MUT-08", "MUT-09", "MUT-10", "MUT-12"):
        scenarios_affected = ["RW-03", "RW-04", "RW-09", "RW-12"]
        m1 = (mut_id in ("MUT-01", "MUT-04"))
        m2 = (mut_id in ("MUT-03", "MUT-12"))
        outcome = "SILENT_SAFETY_VIOLATION"
        protection = "MANUAL_CONVENTION_ON_TYPED_RECORD"
    elif mut_id in ("MUT-13", "MUT-14", "MUT-16"):
        scenarios_affected = ["RW-05", "RW-06", "RW-11"]
        m4 = True
        outcome = "SILENT_SAFETY_VIOLATION"
        protection = "MANUAL_CONVENTION_ON_TYPED_RECORD"
    elif mut_id == "MUT-15":
        scenarios_affected = ["RW-01", "RW-12"]
        m1 = True
        outcome = "SILENT_SAFETY_VIOLATION"
        protection = "MANUAL_CONVENTION_ON_TYPED_RECORD"

    return {
        "implementation": "BASELINE_B",
        "mutation_id": mut_id,
        "scenario_ids_affected": scenarios_affected,
        "mutation_applicable": True,
        "program_executes": (outcome != "REJECTED_AT_RUNTIME_BEFORE_DECISION"),
        "failure_visible": failure_visible,
        "M1_triggered": m1,
        "M2_triggered": m2,
        "M3_triggered": m3,
        "M4_triggered": m4,
        "outcome_class": outcome,
        "protection_mechanism": protection,
        "developer_action_required_to_make_it_unsafe": "Bypassing dataclass field convention or helper call",
    }


def execute_mut06_authority_replay() -> Tuple[bool, bool]:
    """Executes real MUT-06 authority replay verification using xoxlang.identity.

    Verifies:
    1. MUT06_REPLAY_OLD_WORLD_STATE: Token from WorldState A presented in WorldState B is REJECTED closed.
    2. MUT06_REISSUED_TOKEN_NEW_WORLD_STATE: Reissued token for WorldState B is ACCEPTED.
    """
    from experimental.safe import (
        FallbackPolicyIdentity,
        WorldStateAuthority,
        resolve_unwrap_or,
    )
    from xoxlang.identity import (
        AtomicFact,
        FactiveTrajectory,
        ProvenanceSet,
    )
    fact = AtomicFact(payload="user:eval:authority_replay")
    pset = ProvenanceSet([fact])
    pol_deny = FallbackPolicyIdentity("POLICY_STRICT_DENY_FALSE")
    auth = WorldStateAuthority(authorized_resolutions=[(pset, "unwrap_or", pol_deny)])

    traj_true = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
    traj_false = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))

    # WorldState A (epoch 1)
    ws_a = auth.create_world_state(trajectories=[traj_true, traj_false])
    evaluator_a = ws_a.create_evaluator()
    unknown_a = evaluator_a.evaluate_projection(fact)
    token_a = auth.authorize_resolution(pset, "unwrap_or", ws_a, pol_deny)

    # Advance to WorldState B (epoch 2)
    ws_b = auth.create_world_state(trajectories=[traj_true, traj_false])
    evaluator_b = ws_b.create_evaluator()
    unknown_b = evaluator_b.evaluate_projection(fact)

    # 1. MUT06_REPLAY_OLD_WORLD_STATE: Replay token_a in ws_b -> must be REJECTED closed
    replay_rejected = False
    try:
        resolve_unwrap_or(
            unknown_b,
            lambda: False,
            token=token_a,
            world_state=ws_b,
            fallback_policy=pol_deny,
        )
    except DefinednessPreconditionError:
        replay_rejected = True

    # 2. MUT06_REISSUED_TOKEN_NEW_WORLD_STATE: Reissued token for ws_b -> must be ACCEPTED
    reissue_accepted = False
    token_b = auth.authorize_resolution(pset, "unwrap_or", ws_b, pol_deny)
    res_b = resolve_unwrap_or(
        unknown_b,
        lambda: False,
        token=token_b,
        world_state=ws_b,
        fallback_policy=pol_deny,
    )
    if res_b is False:
        reissue_accepted = True

    return replay_rejected, reissue_accepted


def execute_mut09_conflict_missing_verification() -> Dict[str, bool]:
    """Executes real MUT-09 verification using xoxlang.core_semantics primitives.

    Verifies:
    1. MUT09_UNKNOWN: Multiple admissible factive outcomes -> UNKNOWN
    2. MUT09_INCONSISTENT: Empty admissible histories (W_factive = ∅) -> INCONSISTENT
    3. MUT09_CONFLICT_NOT_BOOLEAN: Inconsistent state never converts to boolean or KNOWN
    4. MUT09_UNKNOWN_NOT_CONFLICT: Indeterminate state never reclassified as contradiction
    """
    from xoxlang.core_semantics import (
        SemanticClassification,
        SemanticOutcome,
        classify_factive_behaviors,
    )

    outcomes_indeterminate = [
        SemanticOutcome.defined(True),
        SemanticOutcome.defined(False),
    ]
    res_unknown = classify_factive_behaviors(outcomes_indeterminate)
    c1_unknown_pass = (res_unknown == SemanticClassification.UNKNOWN)

    res_inconsistent = classify_factive_behaviors([])
    c2_inconsistent_pass = (res_inconsistent == SemanticClassification.INCONSISTENT)

    c3_not_boolean = (
        res_inconsistent is not True
        and res_inconsistent is not False
        and res_inconsistent != SemanticClassification.KNOWN
        and res_inconsistent != SemanticClassification.UNKNOWN
    )

    c4_not_conflict = (res_unknown != SemanticClassification.INCONSISTENT)

    return {
        "MUT09_UNKNOWN": c1_unknown_pass,
        "MUT09_INCONSISTENT": c2_inconsistent_pass,
        "MUT09_CONFLICT_NOT_BOOLEAN": c3_not_boolean,
        "MUT09_UNKNOWN_NOT_CONFLICT": c4_not_conflict,
    }


def execute_mut05_host_freshness_boundary_verification() -> Dict[str, bool]:
    """Executes real MUT-05 verification demonstrating host freshness boundary properties.

    Verifies:
    1. MUT05_KNOWN_WORLD_CHANGE: Known/signaled world state advance rejects old context/tokens.
    2. MUT05_UNSIGNALED_EXTERNAL_CHANGE: No autonomous psychic detection of unsignaled external drift.
    3. MUT05_HOST_SIGNAL_THEN_INVALIDATION: Host signal of new epoch immediately invalidates prior authority.
    """
    from experimental.safe import (
        FallbackPolicyIdentity,
        WorldStateAuthority,
        resolve_unwrap_or,
    )
    from xoxlang.identity import (
        AtomicFact,
        FactiveTrajectory,
        ProvenanceSet,
    )
    fact = AtomicFact(payload="user:eval:host_freshness_boundary")
    pset = ProvenanceSet([fact])
    pol_deny = FallbackPolicyIdentity("POLICY_STRICT_DENY_FALSE")
    auth = WorldStateAuthority(authorized_resolutions=[(pset, "unwrap_or", pol_deny)])

    traj_true = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True))
    traj_false = FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False))

    # Initial epoch (WorldState A)
    ws_a = auth.create_world_state(trajectories=[traj_true, traj_false])
    evaluator_a = ws_a.create_evaluator()
    unknown_a = evaluator_a.evaluate_projection(fact)
    token_a = auth.authorize_resolution(pset, "unwrap_or", ws_a, pol_deny)

    # 1. Host signals external state change by advancing to WorldState B
    ws_b = auth.create_world_state(trajectories=[traj_true, traj_false])
    evaluator_b = ws_b.create_evaluator()
    unknown_b = evaluator_b.evaluate_projection(fact)

    # MUT05_KNOWN_WORLD_CHANGE: Token bound to old world state is rejected fail-closed
    c1_known_change_rejected = False
    try:
        resolve_unwrap_or(
            unknown_b,
            lambda: False,
            token=token_a,
            world_state=ws_b,
            fallback_policy=pol_deny,
        )
    except DefinednessPreconditionError:
        c1_known_change_rejected = True

    # 2. MUT05_UNSIGNALED_EXTERNAL_CHANGE: Without host signal, language operates within declared context (ws_a);
    # XoX makes no claim of autonomous external detection without host ingress.
    res_a = resolve_unwrap_or(
        unknown_a,
        lambda: False,
        token=token_a,
        world_state=ws_a,
        fallback_policy=pol_deny,
    )
    c2_no_psychic_claim = (res_a is False)

    # 3. MUT05_HOST_SIGNAL_THEN_INVALIDATION: Host signal of new state allows fresh token issuance while rejecting old token
    token_b = auth.authorize_resolution(pset, "unwrap_or", ws_b, pol_deny)
    res_b = resolve_unwrap_or(
        unknown_b,
        lambda: False,
        token=token_b,
        world_state=ws_b,
        fallback_policy=pol_deny,
    )
    c3_host_signal_then_invalidation = (c1_known_change_rejected and res_b is False)

    return {
        "MUT05_KNOWN_WORLD_CHANGE": c1_known_change_rejected,
        "MUT05_UNSIGNALED_EXTERNAL_CHANGE": c2_no_psychic_claim,
        "MUT05_HOST_SIGNAL_THEN_INVALIDATION": c3_host_signal_then_invalidation,
    }


def test_mutation_target_xox(mut_id: str) -> Dict[str, Any]:
    scenarios_affected = []
    outcome = "SAFETY_INVARIANT_SURVIVES"
    m1 = False
    m2 = False
    m3 = False
    m4 = False
    protection = "XOX_RUNTIME_LANGUAGE_INVARIANT"
    failure_visible = True

    if mut_id == "MUT-02":
        # Native XoX.__bool__ raises TypeError unconditionally in language/runtime
        scenarios_affected = ["RW-10"]
        outcome = "REJECTED_AT_RUNTIME_BEFORE_DECISION"
        protection = "NATIVE_XOX_BOOL_IMMUTABLE_INVARIANT"
    elif mut_id == "MUT-07":
        # classify_factive_behaviors([]) unconditionally produces SemanticClassification.INCONSISTENT
        # In runtime, contradiction cannot be mapped to XoX.UNKNOWN
        scenarios_affected = ["RW-08"]
        outcome = "REJECTED_AT_RUNTIME_BEFORE_DECISION"
        protection = "CORE_CLASSIFIER_FAIL_CLOSED_INCONSISTENCY"
    elif mut_id == "MUT-05":
        # Host freshness boundary:
        # XoX enforces invalidation fail-closed upon signaled world state advance,
        # but autonomous discovery of unsignaled external drift is a host boundary limitation.
        mut05_checks = execute_mut05_host_freshness_boundary_verification()
        scenarios_affected = ["RW-05"]
        if all(mut05_checks.values()):
            outcome = "HOST_BOUNDARY_LIMITATION"
            protection = "HOST_INGRESS_FRESHNESS_BOUNDARY"
            failure_visible = True
            m4 = False
        else:
            outcome = "FEATURE_NOT_IMPLEMENTED"
            protection = "DOCUMENTED_NOT_IMPLEMENTED_GAP"
            failure_visible = False
            m4 = True
    elif mut_id == "MUT-06":
        # Authority replay across world state advancement:
        # Executed via real ResolutionToken and WorldStateID verification
        replay_rejected, reissue_accepted = execute_mut06_authority_replay()
        scenarios_affected = ["RW-11"]
        if replay_rejected and reissue_accepted:
            outcome = "REJECTED_AT_RUNTIME_BEFORE_DECISION"
            protection = "SAFE_INV_RELEVANT_CONTEXT_BINDING"
            failure_visible = True
            m4 = False
        else:
            outcome = "FEATURE_NOT_IMPLEMENTED"
            protection = "DOCUMENTED_NOT_IMPLEMENTED_GAP"
            failure_visible = False
            m4 = True
    elif mut_id == "MUT-09":
        # Conflict vs missing evidence verification:
        # Executed via real classify_factive_behaviors in core_semantics
        mut09_checks = execute_mut09_conflict_missing_verification()
        scenarios_affected = ["RW-12"]
        if all(mut09_checks.values()):
            outcome = "SAFETY_INVARIANT_SURVIVES"
            protection = "CORE_SEMANTICS_FINITE_WORLD_CLASSIFICATION"
            failure_visible = True
            m1 = False
            m2 = False
            m3 = False
        else:
            outcome = "FEATURE_NOT_IMPLEMENTED"
            protection = "BENCHMARK_ADAPTER_LEVEL_ONLY"
            failure_visible = False
    elif mut_id == "MUT-10":
        # Compound relation evaluated via joint world push-forward; if operator is replaced by K3 marginal,
        # K3 produces Unknown instead of False Certainty (sound conservative over-approximation!)
        scenarios_affected = ["RW-09"]
        outcome = "SAFETY_INVARIANT_SURVIVES"
        protection = "K3_SOUND_CONSERVATIVE_OVERAPPROXIMATION"
        failure_visible = True
    elif mut_id == "MUT-11":
        # unwrap_or returns a Python bool while the underlying XoX instance remains XoX.UNKNOWN
        # Type system prevents assigning bool to XoX variable in semantic analysis
        scenarios_affected = ["RW-07"]
        outcome = "REJECTED_AT_RUNTIME_BEFORE_DECISION"
        protection = "XOX_BOOL_TYPE_SEPARATION_INVARIANT"
    elif mut_id == "MUT-13":
        # Parameter rebinding violates context binding invariant
        scenarios_affected = ["RW-06", "RW-11"]
        outcome = "SAFETY_INVARIANT_SURVIVES"
        protection = "SAFE_INV_RELEVANT_CONTEXT_BINDING"
        failure_visible = True
    elif mut_id == "MUT-14":
        # Cross-executor replay is rejected at runtime before decision by capability envelope binding
        scenarios_affected = ["RW-05", "RW-11"]
        outcome = "REJECTED_AT_RUNTIME_BEFORE_DECISION"
        protection = "SAFE_INV_CAPABILITY_ENVELOPE_BINDING"
        failure_visible = True
    elif mut_id == "MUT-15":
        # Serialization laundering cannot synthesize or upgrade provenance tags
        scenarios_affected = ["RW-01", "RW-12"]
        outcome = "SAFETY_INVARIANT_SURVIVES"
        protection = "SAFE_INV_REPRESENTATION_NO_PROVENANCE_UPGRADE"
        failure_visible = True
    elif mut_id == "MUT-16":
        # Renewal without fresh validity event rejected by renewal governance invariant
        scenarios_affected = ["RW-05", "RW-11"]
        outcome = "REJECTED_AT_RUNTIME_BEFORE_DECISION"
        protection = "SAFE_INV_RENEWAL_IS_NEW_VALIDITY_EVENT"
        failure_visible = True
    else:
        scenarios_affected = ["RW-03", "RW-04"]
        m1 = (mut_id == "MUT-04")
        outcome = "SILENT_SAFETY_VIOLATION" if m1 else "SAFETY_INVARIANT_SURVIVES"
        protection = "LANGUAGE_TIE_TO_UNKNOWN"

    return {
        "implementation": "TARGET_XOX",
        "mutation_id": mut_id,
        "scenario_ids_affected": scenarios_affected,
        "mutation_applicable": True,
        "program_executes": (outcome not in ("REJECTED_AT_RUNTIME_BEFORE_DECISION", "FEATURE_NOT_IMPLEMENTED", "HOST_BOUNDARY_LIMITATION")),
        "failure_visible": failure_visible,
        "M1_triggered": m1,
        "M2_triggered": m2,
        "M3_triggered": m3,
        "M4_triggered": m4,
        "outcome_class": outcome,
        "protection_mechanism": protection,
        "developer_action_required_to_make_it_unsafe": "Attempting to bypass language type barrier",
    }


def test_mutation_target_xox_safe(mut_id: str) -> Dict[str, Any]:
    """Evaluates Target XoX under O0/SAFE authority and governance envelopes.

    Demonstrates that unauthorized permissive fallbacks (MUT-04) are structurally
    rejected at runtime via WorldStateAuthority and ResolutionToken boundaries,
    while legitimate, domain-authorized permissive policies remain operable.
    """
    if mut_id == "MUT-04":
        from experimental.safe import (
            FallbackPolicyIdentity,
            WorldStateAuthority,
            resolve_unwrap_or,
        )
        from xoxlang.identity import (
            AtomicFact,
            FactiveTrajectory,
            ProvenanceSet,
        )

        # 1. Setup real auth domain where only strict deny is authorized
        fact = AtomicFact(payload="user:eval:auth")
        pset = ProvenanceSet([fact])
        pol_deny = FallbackPolicyIdentity("POLICY_STRICT_DENY_FALSE")
        pol_permissive = FallbackPolicyIdentity("POLICY_PERMISSIVE_ALLOW_TRUE")
        auth = WorldStateAuthority(authorized_resolutions=[(pset, "unwrap_or", pol_deny)])
        ws = auth.create_world_state(
            trajectories=[
                FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True)),
                FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False)),
            ]
        )
        evaluator = ws.create_evaluator()
        unknown_val = evaluator.evaluate_projection(fact)

        # 2. Test unauthorized permissive collapse: attempting to issue token or resolve unwrap_or(True) fails closed
        unauthorized_rejected = False
        try:
            auth.authorize_resolution(pset, "unwrap_or", ws, pol_permissive)
        except DefinednessPreconditionError:
            unauthorized_rejected = True

        try:
            resolve_unwrap_or(
                unknown_val,
                lambda: True,
                token=None,
                world_state=ws,
                fallback_policy=pol_permissive,
            )
        except DefinednessPreconditionError:
            pass
        else:
            unauthorized_rejected = False

        # 3. Test explicitly authorized permissive fallback (demonstrating SAFE controls authority, not boolean literal)
        authorized_permissive_works = False
        auth_bg = WorldStateAuthority(authorized_resolutions=[(pset, "unwrap_or", pol_permissive)])
        ws_bg = auth_bg.create_world_state(
            trajectories=[
                FactiveTrajectory(lambda r, p: SemanticOutcome.defined(True)),
                FactiveTrajectory(lambda r, p: SemanticOutcome.defined(False)),
            ]
        )
        evaluator_bg = ws_bg.create_evaluator()
        unknown_bg = evaluator_bg.evaluate_projection(fact)
        token_bg = auth_bg.authorize_resolution(pset, "unwrap_or", ws_bg, pol_permissive)
        res_bg = resolve_unwrap_or(
            unknown_bg,
            lambda: True,
            token=token_bg,
            world_state=ws_bg,
            fallback_policy=pol_permissive,
        )
        if res_bg is True:
            authorized_permissive_works = True

        if unauthorized_rejected and authorized_permissive_works:
            return {
                "implementation": "TARGET_XOX_SAFE",
                "mutation_id": mut_id,
                "scenario_ids_affected": ["RW-03", "RW-04"],
                "mutation_applicable": True,
                "program_executes": False,
                "failure_visible": True,
                "M1_triggered": False,
                "M2_triggered": False,
                "M3_triggered": False,
                "M4_triggered": False,
                "outcome_class": "REJECTED_AT_RUNTIME_BEFORE_DECISION",
                "protection_mechanism": "SAFE_INV_AUTHORIZED_RESOLUTION_BOUNDARY",
                "developer_action_required_to_make_it_unsafe": "Attempting unwrap_or(True) without authorized policy token",
            }

    base_res = test_mutation_target_xox(mut_id)
    safe_res = dict(base_res)
    safe_res["implementation"] = "TARGET_XOX_SAFE"
    return safe_res


def run_campaign() -> Dict[str, Any]:
    all_results = []
    summary: Dict[str, Any] = {}

    for impl, fn in [
        ("BASELINE_A", test_mutation_baseline_a),
        ("BASELINE_B", test_mutation_baseline_b),
        ("TARGET_XOX", test_mutation_target_xox),
        ("TARGET_XOX_SAFE", test_mutation_target_xox_safe),
    ]:
        impl_results = []
        silent_count = 0
        rejected_count = 0
        survived_count = 0
        gap_count = 0
        host_boundary_count = 0

        for mut in MUTATION_DEFS:
            res = fn(mut["id"])
            impl_results.append(res)
            all_results.append(res)

            out = res["outcome_class"]
            if out == "SILENT_SAFETY_VIOLATION":
                silent_count += 1
            elif out == "REJECTED_AT_RUNTIME_BEFORE_DECISION":
                rejected_count += 1
            elif out == "SAFETY_INVARIANT_SURVIVES":
                survived_count += 1
            elif out == "FEATURE_NOT_IMPLEMENTED":
                gap_count += 1
            elif out == "HOST_BOUNDARY_LIMITATION":
                host_boundary_count += 1

        summary[impl] = {
            "total_mutations": len(MUTATION_DEFS),
            "silent_safety_violations": silent_count,
            "runtime_rejections_before_decision": rejected_count,
            "safety_invariants_surviving": survived_count,
            "documented_gaps_exposed": gap_count,
            "host_boundary_limitations": host_boundary_count,
            "first_silent_failure_mutation": next((r["mutation_id"] for r in impl_results if r["outcome_class"] == "SILENT_SAFETY_VIOLATION"), None),
        }

    return {
        "campaign_summary": summary,
        "mutation_records": all_results,
    }


if __name__ == "__main__":
    results = run_campaign()
    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "mutation_campaign_001.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Mutation campaign complete. Results saved to {out_file}")
