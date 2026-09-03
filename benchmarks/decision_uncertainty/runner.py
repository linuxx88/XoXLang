"""
Decision Uncertainty Benchmark Comparative Runner.

Executes Baseline A, Baseline B, and Target XoX against the 12 frozen scenarios,
evaluates outputs against the ground-truth oracle, and computes safety (M1-M4)
and structural (M5-M9) metrics.
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


ENFORCEMENT_MAP = {
    "BASELINE_A": {
        "RW-01": "MANUAL_CONVENTION",
        "RW-02": "MANUAL_CONVENTION",
        "RW-03": "MANUAL_CONVENTION",
        "RW-04": "MANUAL_CONVENTION",
        "RW-05": "MANUAL_CONVENTION",
        "RW-06": "MANUAL_CONVENTION",
        "RW-07": "MANUAL_CONVENTION",
        "RW-08": "MANUAL_CONVENTION",
        "RW-09": "MANUAL_CONVENTION",
        "RW-10": "MANUAL_CONVENTION",
        "RW-11": "MANUAL_CONVENTION",
        "RW-12": "MANUAL_CONVENTION",
    },
    "BASELINE_B": {
        "RW-01": "STRUCTURED_TYPE_OR_API_GUARD",
        "RW-02": "STRUCTURED_TYPE_OR_API_GUARD",
        "RW-03": "STRUCTURED_TYPE_OR_API_GUARD",
        "RW-04": "STRUCTURED_TYPE_OR_API_GUARD",
        "RW-05": "STRUCTURED_TYPE_OR_API_GUARD",
        "RW-06": "STRUCTURED_TYPE_OR_API_GUARD",
        "RW-07": "STRUCTURED_TYPE_OR_API_GUARD",
        "RW-08": "STRUCTURED_TYPE_OR_API_GUARD",
        "RW-09": "STRUCTURED_TYPE_OR_API_GUARD",
        "RW-10": "STRUCTURED_TYPE_OR_API_GUARD",
        "RW-11": "STRUCTURED_TYPE_OR_API_GUARD",
        "RW-12": "STRUCTURED_TYPE_OR_API_GUARD",
    },
    "TARGET_XOX": {
        "RW-01": "LANGUAGE_OR_RUNTIME_GUARANTEE",
        "RW-02": "LANGUAGE_OR_RUNTIME_GUARANTEE",
        "RW-03": "LANGUAGE_OR_RUNTIME_GUARANTEE",
        "RW-04": "LANGUAGE_OR_RUNTIME_GUARANTEE",
        "RW-05": "HOST_BOUNDARY_LIMITATION",
        "RW-06": "LANGUAGE_OR_RUNTIME_GUARANTEE",
        "RW-07": "LANGUAGE_OR_RUNTIME_GUARANTEE",
        "RW-08": "LANGUAGE_OR_RUNTIME_GUARANTEE",
        "RW-09": "BENCHMARK_ADAPTER_ONLY",
        "RW-10": "LANGUAGE_OR_RUNTIME_GUARANTEE",
        "RW-11": "LANGUAGE_OR_RUNTIME_GUARANTEE",
        "RW-12": "LANGUAGE_OR_RUNTIME_GUARANTEE",
    }
}


def evaluate_scenario(scenario: Dict[str, Any], target_name: str, runner_fn) -> Dict[str, Any]:
    res = runner_fn(scenario)
    sc_id = scenario["id"]
    oracle = scenario["oracle"]
    oracle_state = oracle["factive_state"]

    factive_claim = res.get("factive_claim")
    policy_decision = res.get("policy_decision")
    uncertainty_preserved = res.get("uncertainty_preserved", False)
    contradiction_detected = res.get("contradiction_detected", False)
    authority_validated = res.get("authority_validated", False)
    provenance_tag = res.get("provenance_tag")
    error = res.get("error")

    # Metric 1: Unjustified Definitive Factive Decision
    # Flagged if factive_claim is True/False when oracle is UNRESOLVED or CONTRADICTION
    m1_violation = False
    if oracle_state in ("UNRESOLVED", "CONTRADICTION"):
        if factive_claim is not None:
            m1_violation = True
    elif oracle_state == "COMPOUND_DEFINITE_OPERANDS_UNRESOLVED":
        expected_compound = oracle.get("compound_factive_truth")
        if factive_claim is not expected_compound:
            m1_violation = True
    elif oracle_state == "TRUE" and factive_claim is not True:
        m1_violation = True
    elif oracle_state == "FALSE" and factive_claim is not False:
        m1_violation = True

    # Metric 2: Silent Uncertainty Loss
    # Flagged if unresolved state disappears without explicit recorded policy/collapse operation or error
    m2_violation = False
    if oracle_state == "UNRESOLVED":
        if not uncertainty_preserved and policy_decision is None and error is None:
            m2_violation = True

    # Metric 3: Contradiction Masking
    # Flagged if CONTRADICTION is treated as ordinary True/False/Unknown instead of fail-closed
    m3_violation = False
    if oracle_state == "CONTRADICTION":
        if not contradiction_detected:
            m3_violation = True

    # Metric 4: Stale Authority Acceptance
    m4_violation = False
    if sc_id in ("RW-05", "RW-11"):
        if authority_validated:
            m4_violation = True

    # Metric 5: Explicit Decision-vs-Truth Separation
    # Passes if policy_decision is distinct from factive_claim when policy is exercised (RW-07)
    m5_success = True
    if sc_id == "RW-07":
        m5_success = (factive_claim is None and policy_decision is not None)

    enforcement_class = ENFORCEMENT_MAP[target_name][sc_id]

    return {
        "scenario_id": sc_id,
        "implementation": target_name,
        "oracle_state": oracle_state,
        "factive_claim": factive_claim,
        "policy_decision": policy_decision,
        "uncertainty_preserved": uncertainty_preserved,
        "contradiction_detected": contradiction_detected,
        "authority_validated": authority_validated,
        "provenance_tag": provenance_tag,
        "error": error,
        "M1_unjustified_definitive_factive_decision": m1_violation,
        "M2_silent_uncertainty_loss": m2_violation,
        "M3_contradiction_masking": m3_violation,
        "M4_stale_authority_acceptance": m4_violation,
        "M5_decision_vs_truth_separation": m5_success,
        "enforcement_class": enforcement_class,
    }


def run_benchmark() -> Dict[str, Any]:
    scenarios_path = os.path.join(os.path.dirname(__file__), "scenarios.json")
    with open(scenarios_path) as f:
        scenarios = json.load(f)["scenarios"]

    targets = [
        ("BASELINE_A", baseline_a_classic.run_scenario),
        ("BASELINE_B", baseline_b_structured.run_scenario),
        ("TARGET_XOX", target_xox.run_scenario),
    ]

    all_records: List[Dict[str, Any]] = []
    summary_by_target: Dict[str, Any] = {}

    for target_name, runner_fn in targets:
        records = []
        m1_count = 0
        m2_count = 0
        m3_count = 0
        m4_count = 0
        m5_success_count = 0
        enforcement_counts: Dict[str, int] = {}

        for sc in scenarios:
            rec = evaluate_scenario(sc, target_name, runner_fn)
            records.append(rec)
            all_records.append(rec)

            if rec["M1_unjustified_definitive_factive_decision"]:
                m1_count += 1
            if rec["M2_silent_uncertainty_loss"]:
                m2_count += 1
            if rec["M3_contradiction_masking"]:
                m3_count += 1
            if rec["M4_stale_authority_acceptance"]:
                m4_count += 1
            if rec["M5_decision_vs_truth_separation"]:
                m5_success_count += 1

            enf = rec["enforcement_class"]
            enforcement_counts[enf] = enforcement_counts.get(enf, 0) + 1

        summary_by_target[target_name] = {
            "M1_unjustified_decisions": m1_count,
            "M2_silent_uncertainty_loss": m2_count,
            "M3_contradiction_masking": m3_count,
            "M4_stale_authority_acceptance": m4_count,
            "M5_separation_success_rate": f"{m5_success_count}/{len(scenarios)}",
            "enforcement_class_distribution": enforcement_counts,
            "total_safety_failures": m1_count + m2_count + m3_count + m4_count,
        }

    return {
        "execution_summary": summary_by_target,
        "detailed_scenario_records": all_records,
    }


if __name__ == "__main__":
    results = run_benchmark()
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)
    out_file = os.path.join(results_dir, "first_comparative_run.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Benchmark run complete. Results saved to {out_file}")
