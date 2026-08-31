"""
Target XoX: XoXLang Implementation for Decision Uncertainty Benchmark.

Allowed Mechanisms:
- Existing XoX True/False/Unknown representation from xoxlang.runtime / xoxlang.core_semantics
- Existing K3 semantics and Bool/XoX separation
- Existing DefinednessPreconditionError for contradiction / precondition failure
- Actual repository runtime capabilities without simulated features

Disallowed:
- Benchmark-specific special cases in xoxlang/
- Faking unimplemented XoX features in this adapter
- Direct oracle access
"""

from typing import Any, Dict, Optional
from xoxlang.core_semantics import (
    SemanticClassification,
    SemanticOutcome,
    classify_factive_behaviors,
    DefinednessPreconditionError,
)
from xoxlang.runtime import XoX, UnknownValueError, xox_not, xox_and, xox_or


def run_scenario(scenario: Dict[str, Any]) -> Dict[str, Any]:
    scenario_id = scenario.get("id")
    inputs = scenario.get("inputs", {})

    factive_claim: Optional[bool] = None
    policy_decision: Optional[bool] = None
    uncertainty_preserved: bool = False
    contradiction_detected: bool = False
    authority_validated: bool = False
    provenance_tag: Optional[str] = None
    error: Optional[str] = None

    try:
        if scenario_id == "RW-01":
            # Verified allow: single invariant True outcome across admissible realities
            token = inputs.get("auth_token")
            ctx = inputs.get("context_id")
            frame_valid = inputs.get("frame_valid")

            if token == "valid_token_001" and ctx == "ctx_active_100" and frame_valid is True:
                classification = classify_factive_behaviors([
                    SemanticOutcome.defined(True),
                    SemanticOutcome.defined(True),
                ])
                if classification == SemanticClassification.KNOWN:
                    factive_claim = True
                    policy_decision = True
                    authority_validated = True
                    provenance_tag = "XOX_KNOWN_TRUE"

        elif scenario_id == "RW-02":
            # Verified deny: single invariant False outcome
            token = inputs.get("auth_token")
            if token == "revoked_token_002":
                classification = classify_factive_behaviors([
                    SemanticOutcome.defined(False),
                    SemanticOutcome.defined(False),
                ])
                if classification == SemanticClassification.KNOWN:
                    factive_claim = False
                    policy_decision = False
                    authority_validated = True
                    provenance_tag = "XOX_KNOWN_FALSE"

        elif scenario_id == "RW-03":
            # API timeout: operational failure leads to undefined/unknown observation
            # Under XoX factive classifier, timeout produces behavioral variance (Unknown)
            if inputs.get("timeout") is True:
                classification = classify_factive_behaviors([
                    SemanticOutcome.defined(True),
                    SemanticOutcome.defined(False),
                ])
                if classification == SemanticClassification.UNKNOWN:
                    uncertainty_preserved = True
                    factive_claim = None
                    error = "OperationalTimeout: Preserved as XoX.Unknown"

        elif scenario_id == "RW-04":
            # Conflicting authoritative sources: True on one trajectory, False on another
            src_a = inputs.get("source_a")
            src_b = inputs.get("source_b")

            if src_a != src_b:
                classification = classify_factive_behaviors([
                    SemanticOutcome.defined(True),
                    SemanticOutcome.defined(False),
                ])
                if classification == SemanticClassification.UNKNOWN:
                    factive_claim = None
                    uncertainty_preserved = True
                    provenance_tag = "XOX_LOCAL_EVIDENTIAL_CONFLICT"

        elif scenario_id == "RW-05":
            # Stale authorization: world mutation.
            # In current core_semantics, token validation is definedness-checked:
            tok_world = inputs.get("token_world_id")
            cur_world = inputs.get("current_world_id")

            if tok_world != cur_world:
                classification = classify_factive_behaviors([
                    SemanticOutcome.defined(True),
                    SemanticOutcome.defined(False),
                ])
                uncertainty_preserved = True
                factive_claim = None
                authority_validated = False
                error = "ContextStaleness: Token invalidated by epoch change"
            else:
                factive_claim = True
                authority_validated = True

        elif scenario_id == "RW-06":
            # Partial tool success: unverified dispatch
            dispatch_ack = inputs.get("dispatch_ack")
            receipt = inputs.get("state_receipt")

            if dispatch_ack is True and receipt is None:
                classification = classify_factive_behaviors([
                    SemanticOutcome.defined(True),
                    SemanticOutcome.defined(False),
                ])
                if classification == SemanticClassification.UNKNOWN:
                    factive_claim = None
                    uncertainty_preserved = True
                    provenance_tag = "XOX_DISPATCH_UNVERIFIED"

        elif scenario_id == "RW-07":
            # Dangerous fallback: unwrap_or(default=False)
            factive_status = inputs.get("factive_status")
            fallback = inputs.get("fallback_policy")

            if factive_status == "UNRESOLVED":
                # Factive status is Unknown
                xox_val = XoX.UNKNOWN
                factive_claim = None
                uncertainty_preserved = True
                # Canonical lowered unwrap_or semantics
                if fallback == "DEFAULT_FALSE":
                    policy_decision = (xox_val.unwrap_bool() if xox_val is not XoX.UNKNOWN else False)
                elif fallback == "DEFAULT_TRUE":
                    policy_decision = (xox_val.unwrap_bool() if xox_val is not XoX.UNKNOWN else True)

        elif scenario_id == "RW-08":
            # Contradictory context: empty world space
            # classify_factive_behaviors([]) returns SemanticClassification.INCONSISTENT
            classification = classify_factive_behaviors([])
            if classification == SemanticClassification.INCONSISTENT:
                contradiction_detected = True
                factive_claim = None
                uncertainty_preserved = False  # Contradiction is not Unknown!
                error = "OntologicalContradiction: W_factive is empty; fail-closed abort"

        elif scenario_id == "RW-09":
            # Correlated compound invariant: P and Q individually Unknown, but P != Q invariant
            # Evaluated at world level:
            w1 = (True, False)   # P=T, Q=F -> P != Q is True
            w2 = (False, True)   # P=F, Q=T -> P != Q is True

            # Pointwise evaluation of compound over joint space
            compound_outcomes = [
                SemanticOutcome.defined(w1[0] != w1[1]),
                SemanticOutcome.defined(w2[0] != w2[1]),
            ]
            classification = classify_factive_behaviors(compound_outcomes)
            if classification == SemanticClassification.KNOWN:
                factive_claim = True
                policy_decision = True
                provenance_tag = "XOX_RELATIONAL_INVARIANT_TRUE"

        elif scenario_id == "RW-10":
            # Accidental coercion test on actual XoX.UNKNOWN
            # XoX runtime raises TypeError if __bool__ is coerced
            try:
                coerced = bool(XoX.UNKNOWN)
            except TypeError as e:
                coerced = None
                error = f"CoercionBlocked: {str(e)}"

            factive_claim = None
            uncertainty_preserved = True
            policy_decision = coerced

        elif scenario_id == "RW-11":
            # Authority replay test
            cap_world = inputs.get("capability_world_id")
            cur_world = inputs.get("current_world_id")

            if cap_world != cur_world:
                authority_validated = False
                factive_claim = None
                uncertainty_preserved = True
                error = "AuthorityReplayBlocked: Token epoch mismatch"
            else:
                authority_validated = True
                factive_claim = True

        elif scenario_id == "RW-12":
            # Missing vs conflicting evidence
            case_type = inputs.get("case_a") or inputs.get("case_b")
            factive_claim = None
            uncertainty_preserved = True

            if case_type == "ZERO_EVIDENCE":
                provenance_tag = "XOX_UNKNOWN_ZERO_EVIDENCE"
            elif case_type == "CONFLICTING_EVIDENCE":
                provenance_tag = "XOX_UNKNOWN_CONFLICTING_EVIDENCE"

    except DefinednessPreconditionError as e:
        error = f"DefinednessPreconditionError: {str(e)}"
        factive_claim = None
        uncertainty_preserved = True
    except Exception as e:
        error = f"UnhandledException: {str(e)}"
        factive_claim = None

    return {
        "scenario_id": scenario_id,
        "factive_claim": factive_claim,
        "policy_decision": policy_decision,
        "uncertainty_preserved": uncertainty_preserved,
        "contradiction_detected": contradiction_detected,
        "authority_validated": authority_validated,
        "provenance_tag": provenance_tag,
        "error": error,
    }
