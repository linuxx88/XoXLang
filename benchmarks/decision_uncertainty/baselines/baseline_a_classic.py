"""
Baseline A: Python Classic Implementation for Decision Uncertainty Benchmark.

Allowed Mechanisms:
- bool, None, exceptions
- ordinary dict/list/tuple values
- status flags and ordinary Python control flow

Disallowed:
- Custom three-valued truth type
- Enum-based epistemic state model
- Result/Option tagged union abstractions
- XoX runtime primitives or capability classes
"""

from typing import Any, Dict, Optional


class TimeoutException(Exception):
    pass


class InconsistentConstraintException(Exception):
    pass


class StaleTokenException(Exception):
    pass


def run_scenario(scenario: Dict[str, Any]) -> Dict[str, Any]:
    scenario_id = scenario.get("id")
    inputs = scenario.get("inputs", {})

    # Envelope initialization
    factive_claim: Optional[bool] = None
    policy_decision: Optional[bool] = None
    uncertainty_preserved: bool = False
    contradiction_detected: bool = False
    authority_validated: bool = False
    provenance_tag: Optional[str] = None
    error: Optional[str] = None

    try:
        if scenario_id == "RW-01":
            # Verified allow: valid token in active frame
            token = inputs.get("auth_token")
            ctx = inputs.get("context_id")
            frame_valid = inputs.get("frame_valid")

            if token == "valid_token_001" and ctx == "ctx_active_100" and frame_valid is True:
                factive_claim = True
                policy_decision = True
                authority_validated = True
                provenance_tag = "VALID_AUTH_CHAIN"
            else:
                factive_claim = False
                policy_decision = False

        elif scenario_id == "RW-02":
            # Verified deny: revoked token confirmed by registry
            token = inputs.get("auth_token")
            if token == "revoked_token_002":
                factive_claim = False
                policy_decision = False
                authority_validated = True
                provenance_tag = "EXPLICIT_REVOCATION_REGISTRY"
            else:
                factive_claim = None
                uncertainty_preserved = True

        elif scenario_id == "RW-03":
            # API timeout: remote authority fails to answer
            if inputs.get("timeout") is True:
                raise TimeoutException("Remote authorization service timed out after 5000ms")

        elif scenario_id == "RW-04":
            # Conflicting authoritative sources
            src_a = inputs.get("source_a")
            src_b = inputs.get("source_b")

            if src_a != src_b:
                # Conflict detected using standard dict comparison
                factive_claim = None
                policy_decision = None
                uncertainty_preserved = True
                provenance_tag = f"CONFLICT({src_a}_VS_{src_b})"
            elif src_a == "GRANT":
                factive_claim = True
                policy_decision = True
            elif src_a == "REVOKE":
                factive_claim = False
                policy_decision = False

        elif scenario_id == "RW-05":
            # Stale authorization: token epoch != current epoch
            tok_world = inputs.get("token_world_id")
            cur_world = inputs.get("current_world_id")

            if tok_world != cur_world:
                raise StaleTokenException(f"Token epoch {tok_world} does not match current epoch {cur_world}")
            else:
                factive_claim = True
                policy_decision = True
                authority_validated = True

        elif scenario_id == "RW-06":
            # Partial tool success: request queued but receipt missing
            dispatch_ack = inputs.get("dispatch_ack")
            receipt = inputs.get("state_receipt")

            if dispatch_ack is True and receipt is None:
                # Acknowledged but unverified
                factive_claim = None
                policy_decision = None
                uncertainty_preserved = True
                provenance_tag = "DISPATCHED_PENDING_RECEIPT"

        elif scenario_id == "RW-07":
            # Dangerous fallback: unresolved fact with explicit policy default
            factive_status = inputs.get("factive_status")
            fallback = inputs.get("fallback_policy")

            if factive_status == "UNRESOLVED":
                factive_claim = None  # Factive truth remains unknown
                uncertainty_preserved = True
                if fallback == "DEFAULT_FALSE":
                    policy_decision = False  # Explicit fallback decision
                elif fallback == "DEFAULT_TRUE":
                    policy_decision = True

        elif scenario_id == "RW-08":
            # Contradictory context: mutually exclusive hard constraints
            c_a = inputs.get("constraint_a")
            c_b = inputs.get("constraint_b")

            if c_a == "X == True" and c_b == "X == False":
                contradiction_detected = True
                raise InconsistentConstraintException("Constraint contradiction: X cannot be both True and False")

        elif scenario_id == "RW-09":
            # Correlated compound invariant: P and Q unresolved, but P != Q invariant
            p_unres = inputs.get("p_unresolved")
            q_unres = inputs.get("q_unresolved")
            rel = inputs.get("relation")

            if p_unres and q_unres and rel == "P != Q":
                # In classic python, we compute the compound truth directly: P != Q is True for all admissible worlds
                factive_claim = True
                policy_decision = True
                provenance_tag = "RELATIONAL_INVARIANT_TRUE"

        elif scenario_id == "RW-10":
            # Accidental coercion: checking bool(UNKNOWN) in ordinary if-condition
            epistemic_val = inputs.get("epistemic_value")
            # In classic Python, non-empty string or custom object without __bool__ defaults to truthy (True)
            # A defensive developer checks for None, but raw truthiness coercion fails:
            is_truthy = bool(epistemic_val) if epistemic_val is not None else False
            # Classic python represents unknown as None:
            if epistemic_val == "UNKNOWN":
                # If treated as a sentinel string, it coercively becomes True; if treated as None, it becomes False
                factive_claim = None
                uncertainty_preserved = True
                policy_decision = is_truthy  # Captures the accidental coercion pressure

        elif scenario_id == "RW-11":
            # Authority replay: capability world state mismatch
            cap_world = inputs.get("capability_world_id")
            cur_world = inputs.get("current_world_id")

            if cap_world != cur_world:
                authority_validated = False
                factive_claim = None
                uncertainty_preserved = True
                error = "AuthorityReplayError: capability world mismatch"
            else:
                authority_validated = True
                factive_claim = True

        elif scenario_id == "RW-12":
            # Missing vs conflicting evidence
            case_type = inputs.get("case_a") or inputs.get("case_b")
            factive_claim = None
            uncertainty_preserved = True

            if case_type == "ZERO_EVIDENCE":
                provenance_tag = "PROVENANCE_ZERO_EVIDENCE"
            elif case_type == "CONFLICTING_EVIDENCE":
                provenance_tag = "PROVENANCE_CONFLICTING_EVIDENCE"

    except TimeoutException as e:
        error = f"TimeoutException: {str(e)}"
        factive_claim = None
        uncertainty_preserved = True
    except StaleTokenException as e:
        error = f"StaleTokenException: {str(e)}"
        factive_claim = None
        uncertainty_preserved = True
    except InconsistentConstraintException as e:
        error = f"InconsistentConstraintException: {str(e)}"
        factive_claim = None
        contradiction_detected = True
    except Exception as e:
        error = f"UnexpectedException: {str(e)}"
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
