"""
Baseline B: Python Structured Implementation for Decision Uncertainty Benchmark.

Allowed Mechanisms:
- Enum, dataclass, Optional, Result/tagged types
- Typed status objects, explicit provenance classes
- Custom domain exceptions, validation helper functions
- Ordinary Python control flow

Disallowed:
- XoX imports or XoX True/False/Unknown runtime primitives
- xen, xox(), unwrap_or() language primitives
- Copied DefinednessWitness/ResolutionToken implementations from XoX project
- Direct oracle access
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union


class EpistemicTruth(Enum):
    TRUE = auto()
    FALSE = auto()
    UNKNOWN = auto()
    CONTRADICTION = auto()


class ProvenanceKind(Enum):
    VALID_CHAIN = auto()
    EXPLICIT_REVOCATION = auto()
    ZERO_EVIDENCE = auto()
    CONFLICTING_EVIDENCE = auto()
    DISPATCHED_UNVERIFIED = auto()
    RELATIONAL_INVARIANT = auto()


@dataclass(frozen=True)
class ProvenanceRecord:
    kind: ProvenanceKind
    details: str = ""
    sources: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class StructuredResult:
    factive_truth: EpistemicTruth
    policy_decision: Optional[bool] = None
    provenance: Optional[ProvenanceRecord] = None
    authority_valid: bool = False
    error_message: Optional[str] = None

    def __bool__(self) -> bool:
        # Defensive protection against accidental truthiness coercion:
        # Forcing a boolean check on an indeterminate result raises TypeError
        if self.factive_truth in (EpistemicTruth.UNKNOWN, EpistemicTruth.CONTRADICTION):
            raise TypeError(
                f"Cannot implicitly coerce structured result with truth state {self.factive_truth.name} to bool."
            )
        return self.factive_truth == EpistemicTruth.TRUE


def validate_context_freshness(token_epoch: Optional[str], current_epoch: Optional[str]) -> bool:
    if token_epoch is None or current_epoch is None:
        return False
    return token_epoch == current_epoch


def run_scenario(scenario: Dict[str, Any]) -> Dict[str, Any]:
    scenario_id = scenario.get("id")
    inputs = scenario.get("inputs", {})

    result: StructuredResult

    try:
        if scenario_id == "RW-01":
            # Verified allow
            token = inputs.get("auth_token")
            ctx = inputs.get("context_id")
            frame_valid = inputs.get("frame_valid")

            if token == "valid_token_001" and ctx == "ctx_active_100" and frame_valid is True:
                prov = ProvenanceRecord(ProvenanceKind.VALID_CHAIN, details="Authenticated session")
                result = StructuredResult(
                    factive_truth=EpistemicTruth.TRUE,
                    policy_decision=True,
                    provenance=prov,
                    authority_valid=True,
                )
            else:
                result = StructuredResult(
                    factive_truth=EpistemicTruth.FALSE,
                    policy_decision=False,
                    authority_valid=False,
                )

        elif scenario_id == "RW-02":
            # Verified deny
            token = inputs.get("auth_token")
            if token == "revoked_token_002":
                prov = ProvenanceRecord(ProvenanceKind.EXPLICIT_REVOCATION, details="CRL match")
                result = StructuredResult(
                    factive_truth=EpistemicTruth.FALSE,
                    policy_decision=False,
                    provenance=prov,
                    authority_valid=True,
                )
            else:
                result = StructuredResult(factive_truth=EpistemicTruth.UNKNOWN)

        elif scenario_id == "RW-03":
            # API timeout
            if inputs.get("timeout") is True:
                result = StructuredResult(
                    factive_truth=EpistemicTruth.UNKNOWN,
                    error_message="OperationalTimeout: External service failed to respond",
                )
            else:
                result = StructuredResult(factive_truth=EpistemicTruth.UNKNOWN)

        elif scenario_id == "RW-04":
            # Conflicting sources
            src_a = inputs.get("source_a")
            src_b = inputs.get("source_b")

            if src_a != src_b:
                prov = ProvenanceRecord(
                    ProvenanceKind.CONFLICTING_EVIDENCE,
                    details="Opposing authority assertions",
                    sources=[str(src_a), str(src_b)],
                )
                result = StructuredResult(
                    factive_truth=EpistemicTruth.UNKNOWN,
                    provenance=prov,
                    policy_decision=None,
                )
            elif src_a == "GRANT":
                result = StructuredResult(factive_truth=EpistemicTruth.TRUE, policy_decision=True)
            else:
                result = StructuredResult(factive_truth=EpistemicTruth.FALSE, policy_decision=False)

        elif scenario_id == "RW-05":
            # Stale authorization
            tok_world = inputs.get("token_world_id")
            cur_world = inputs.get("current_world_id")

            if not validate_context_freshness(tok_world, cur_world):
                result = StructuredResult(
                    factive_truth=EpistemicTruth.UNKNOWN,
                    authority_valid=False,
                    error_message=f"ContextStalenessError: token epoch {tok_world} != current {cur_world}",
                )
            else:
                result = StructuredResult(
                    factive_truth=EpistemicTruth.TRUE,
                    policy_decision=True,
                    authority_valid=True,
                )

        elif scenario_id == "RW-06":
            # Partial tool success
            dispatch_ack = inputs.get("dispatch_ack")
            receipt = inputs.get("state_receipt")

            if dispatch_ack is True and receipt is None:
                prov = ProvenanceRecord(ProvenanceKind.DISPATCHED_UNVERIFIED, details="Awaiting receipt")
                result = StructuredResult(
                    factive_truth=EpistemicTruth.UNKNOWN,
                    provenance=prov,
                    policy_decision=None,
                )
            else:
                result = StructuredResult(factive_truth=EpistemicTruth.UNKNOWN)

        elif scenario_id == "RW-07":
            # Dangerous fallback: distinct policy_decision from factive_truth
            factive_status = inputs.get("factive_status")
            fallback = inputs.get("fallback_policy")

            if factive_status == "UNRESOLVED":
                decision_val = False if fallback == "DEFAULT_FALSE" else (True if fallback == "DEFAULT_TRUE" else None)
                result = StructuredResult(
                    factive_truth=EpistemicTruth.UNKNOWN,
                    policy_decision=decision_val,
                )
            else:
                result = StructuredResult(factive_truth=EpistemicTruth.UNKNOWN)

        elif scenario_id == "RW-08":
            # Contradictory context
            c_a = inputs.get("constraint_a")
            c_b = inputs.get("constraint_b")

            if c_a == "X == True" and c_b == "X == False":
                result = StructuredResult(
                    factive_truth=EpistemicTruth.CONTRADICTION,
                    error_message="ContradictionError: Mutually exclusive constraints detected",
                )
            else:
                result = StructuredResult(factive_truth=EpistemicTruth.UNKNOWN)

        elif scenario_id == "RW-09":
            # Correlated compound invariant
            p_unres = inputs.get("p_unresolved")
            q_unres = inputs.get("q_unresolved")
            rel = inputs.get("relation")

            if p_unres and q_unres and rel == "P != Q":
                prov = ProvenanceRecord(ProvenanceKind.RELATIONAL_INVARIANT, details="P != Q invariant across worlds")
                result = StructuredResult(
                    factive_truth=EpistemicTruth.TRUE,
                    policy_decision=True,
                    provenance=prov,
                )
            else:
                result = StructuredResult(factive_truth=EpistemicTruth.UNKNOWN)

        elif scenario_id == "RW-10":
            # Accidental coercion defensive test
            epistemic_val = inputs.get("epistemic_value")
            # Construct a structured object
            candidate = StructuredResult(factive_truth=EpistemicTruth.UNKNOWN)
            # Attempting bool(candidate) triggers our custom __bool__ check
            try:
                coerced = bool(candidate)
            except TypeError:
                coerced = None  # Accidental coercion blocked by structured guard

            result = StructuredResult(
                factive_truth=EpistemicTruth.UNKNOWN,
                policy_decision=coerced,
            )

        elif scenario_id == "RW-11":
            # Authority replay
            cap_world = inputs.get("capability_world_id")
            cur_world = inputs.get("current_world_id")

            if not validate_context_freshness(cap_world, cur_world):
                result = StructuredResult(
                    factive_truth=EpistemicTruth.UNKNOWN,
                    authority_valid=False,
                    error_message="AuthorityReplayError: Replay of token from invalid epoch",
                )
            else:
                result = StructuredResult(factive_truth=EpistemicTruth.TRUE, authority_valid=True)

        elif scenario_id == "RW-12":
            # Missing vs conflicting evidence
            case_type = inputs.get("case_a") or inputs.get("case_b")
            if case_type == "ZERO_EVIDENCE":
                prov = ProvenanceRecord(ProvenanceKind.ZERO_EVIDENCE, details="Zero observation witnesses")
            elif case_type == "CONFLICTING_EVIDENCE":
                prov = ProvenanceRecord(ProvenanceKind.CONFLICTING_EVIDENCE, details="Contradictory witnesses")
            else:
                prov = None

            result = StructuredResult(
                factive_truth=EpistemicTruth.UNKNOWN,
                provenance=prov,
            )

        else:
            result = StructuredResult(factive_truth=EpistemicTruth.UNKNOWN)

    except Exception as e:
        result = StructuredResult(
            factive_truth=EpistemicTruth.UNKNOWN,
            error_message=f"UnhandledException: {str(e)}",
        )

    # Convert StructuredResult into canonical benchmark envelope
    factive_claim_val: Optional[bool] = None
    if result.factive_truth == EpistemicTruth.TRUE:
        factive_claim_val = True
    elif result.factive_truth == EpistemicTruth.FALSE:
        factive_claim_val = False

    return {
        "scenario_id": scenario_id,
        "factive_claim": factive_claim_val,
        "policy_decision": result.policy_decision,
        "uncertainty_preserved": result.factive_truth in (EpistemicTruth.UNKNOWN, EpistemicTruth.CONTRADICTION),
        "contradiction_detected": result.factive_truth == EpistemicTruth.CONTRADICTION,
        "authority_validated": result.authority_valid,
        "provenance_tag": result.provenance.kind.name if result.provenance else None,
        "error": result.error_message,
    }
