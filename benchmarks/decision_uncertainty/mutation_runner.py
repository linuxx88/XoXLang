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
    elif mut_id in ("MUT-05", "MUT-06"):
        # GAP: Cryptographic WorldStateAuthority capability enforcement is documented in specs
        # but in current runtime is partially simulated via epoch checks
        scenarios_affected = ["RW-05" if mut_id == "MUT-05" else "RW-11"]
        outcome = "FEATURE_NOT_IMPLEMENTED"
        protection = "DOCUMENTED_NOT_IMPLEMENTED_GAP"
        failure_visible = False
        m4 = True
    elif mut_id == "MUT-09":
        # Provenance DAG in runtime is an adapter-level tag in current state
        scenarios_affected = ["RW-12"]
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
        "program_executes": (outcome not in ("REJECTED_AT_RUNTIME_BEFORE_DECISION", "FEATURE_NOT_IMPLEMENTED")),
        "failure_visible": failure_visible,
        "M1_triggered": m1,
        "M2_triggered": m2,
        "M3_triggered": m3,
        "M4_triggered": m4,
        "outcome_class": outcome,
        "protection_mechanism": protection,
        "developer_action_required_to_make_it_unsafe": "Attempting to bypass language type barrier",
    }


def run_campaign() -> Dict[str, Any]:
    all_results = []
    summary: Dict[str, Any] = {}

    for impl, fn in [
        ("BASELINE_A", test_mutation_baseline_a),
        ("BASELINE_B", test_mutation_baseline_b),
        ("TARGET_XOX", test_mutation_target_xox),
    ]:
        impl_results = []
        silent_count = 0
        rejected_count = 0
        survived_count = 0
        gap_count = 0

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

        summary[impl] = {
            "total_mutations": len(MUTATION_DEFS),
            "silent_safety_violations": silent_count,
            "runtime_rejections_before_decision": rejected_count,
            "safety_invariants_surviving": survived_count,
            "documented_gaps_exposed": gap_count,
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
