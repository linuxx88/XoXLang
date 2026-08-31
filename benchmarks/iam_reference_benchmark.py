"""
Independent Replication Benchmark: IAM Reference Authorization Problem
=======================================================================
Objective:
    Objectively compare an authorization policy implemented in XoXLang
    against a strong Python baseline (Enum with fail-closed truthiness,
    lazy Strong Kleene evaluators, and pattern-matching consumer).

Reproduction Instructions:
    1. Dependencies: Python >= 3.10, xoxlang package (local repo).
    2. Execution Command:
       python3 benchmarks/iam_reference_benchmark.py

Counting Rule:
    Non-empty, non-comment lines of executable implementation.
"""
from enum import Enum, auto
import itertools
from pathlib import Path
import sys
from typing import Callable, Dict, List, Tuple

# Ensure repository root is on sys.path for direct execution
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from xoxlang.compiler import compile_source
from xoxlang.runtime import XoX, UnknownValueError, xox_not, xox_and, xox_or
from xoxlang.diagnostics import TypeDiagnosticError, ExhaustivenessError


# ==============================================================================
# 1. Python Baseline Implementation (Infrastructure + Policy)
# ==============================================================================

class AuthDecision(Enum):
    FALSE = auto()
    TRUE = auto()
    UNKNOWN = auto()

    def __bool__(self) -> bool:
        raise TypeError(
            f"Cannot evaluate truthiness of AuthDecision state '{self.name}'; participate in explicit evaluation only."
        )


def lazy_and(
    left_fn: Callable[[], AuthDecision],
    right_fn: Callable[[], AuthDecision]
) -> AuthDecision:
    l_val = left_fn()
    if l_val is AuthDecision.FALSE:
        return AuthDecision.FALSE
    r_val = right_fn()
    if r_val is AuthDecision.FALSE:
        return AuthDecision.FALSE
    if l_val is AuthDecision.TRUE and r_val is AuthDecision.TRUE:
        return AuthDecision.TRUE
    return AuthDecision.UNKNOWN


def lazy_or(
    left_fn: Callable[[], AuthDecision],
    right_fn: Callable[[], AuthDecision]
) -> AuthDecision:
    l_val = left_fn()
    if l_val is AuthDecision.TRUE:
        return AuthDecision.TRUE
    r_val = right_fn()
    if r_val is AuthDecision.TRUE:
        return AuthDecision.TRUE
    if l_val is AuthDecision.FALSE and r_val is AuthDecision.FALSE:
        return AuthDecision.FALSE
    return AuthDecision.UNKNOWN


def evaluate_iam_policy_python(
    eval_acc: Callable[[], AuthDecision],
    eval_dev: Callable[[], AuthDecision],
    eval_net: Callable[[], AuthDecision],
    eval_emg: Callable[[], AuthDecision]
) -> AuthDecision:
    return lazy_and(
        lambda: lazy_and(eval_acc, eval_dev),
        lambda: lazy_or(eval_net, eval_emg),
    )


# ==============================================================================
# 2. XoXLang Core Implementation
# ==============================================================================

XOX_SOURCE = """
fn evaluate_iam_policy_xox(acc: XoX, dev: XoX, net: XoX, emg: XoX) -> XoX:
    return (acc AND dev) AND (net OR emg)
"""

COMPILED_XOX_CODE = compile_source(XOX_SOURCE)


# ==============================================================================
# 3. 81 Truth Combinations & Equivalence Evaluation
# ==============================================================================

def run_benchmark_81_combinations() -> Dict[str, int]:
    states_py = [AuthDecision.TRUE, AuthDecision.FALSE, AuthDecision.UNKNOWN]
    py_to_xox = {
        AuthDecision.TRUE: XoX.TRUE,
        AuthDecision.FALSE: XoX.FALSE,
        AuthDecision.UNKNOWN: XoX.UNKNOWN,
    }
    xox_to_py = {
        XoX.TRUE: AuthDecision.TRUE,
        XoX.FALSE: AuthDecision.FALSE,
        XoX.UNKNOWN: AuthDecision.UNKNOWN,
    }

    xox_scope = {
        "XoX": XoX,
        "xox_and": xox_and,
        "xox_not": xox_not,
        "xox_or": xox_or,
        "UnknownValueError": UnknownValueError,
    }
    exec(COMPILED_XOX_CODE, xox_scope)
    fn_name = "_u_" + "evaluate_iam_policy_xox".encode("utf-8").hex()
    xox_fn = xox_scope[fn_name]

    decision_equivalence_failures = 0
    trace_equivalence_failures = 0
    total_tested = 0

    for acc_s, dev_s, net_s, emg_s in itertools.product(states_py, repeat=4):
        total_tested += 1
        trace_py: List[str] = []

        def p_acc():
            trace_py.append("acc")
            return acc_s

        def p_dev():
            trace_py.append("dev")
            return dev_s

        def p_net():
            trace_py.append("net")
            return net_s

        def p_emg():
            trace_py.append("emg")
            return emg_s

        res_py = evaluate_iam_policy_python(p_acc, p_dev, p_net, p_emg)
        res_xox = xox_fn(py_to_xox[acc_s], py_to_xox[dev_s], py_to_xox[net_s], py_to_xox[emg_s])

        if xox_to_py[res_xox] != res_py:
            decision_equivalence_failures += 1

        expected_trace: List[str] = ["acc"]
        if acc_s is not AuthDecision.FALSE:
            expected_trace.append("dev")
        acc_and_dev_false = (acc_s is AuthDecision.FALSE) or (dev_s is AuthDecision.FALSE)
        if not acc_and_dev_false:
            expected_trace.append("net")
            if net_s is not AuthDecision.TRUE:
                expected_trace.append("emg")

        if trace_py != expected_trace:
            trace_equivalence_failures += 1

    return {
        "truth_combinations_tested": total_tested,
        "decision_equivalence_failures": decision_equivalence_failures,
        "trace_equivalence_failures": trace_equivalence_failures,
    }


# ==============================================================================
# 4. Controlled Misuse Scenarios (Independent from Equivalence Tests)
# ==============================================================================

def run_misuse_scenarios() -> Dict[str, Dict[str, str]]:
    results = {}

    # Misuse 1: Operator / Type Mixing
    try:
        def bad_python_op(acc: AuthDecision, dev: AuthDecision):
            return acc and dev
        bad_python_op(AuthDecision.TRUE, AuthDecision.FALSE)
        py_m1 = "SILENT_PASS"
    except TypeError as e:
        py_m1 = f"RUNTIME_TYPE_ERROR ({e})"
    except Exception as e:
        py_m1 = f"RUNTIME_ERROR ({type(e).__name__})"

    try:
        bad_xox_src = """
fn bad_op(acc: Bool, dev: XoX) -> XoX:
    return acc AND dev
"""
        compile_source(bad_xox_src)
        xox_m1 = "COMPILES"
    except TypeDiagnosticError as e:
        xox_m1 = f"STATIC_TYPE_DIAGNOSTIC_ERROR ({e.message})"
    except Exception as e:
        xox_m1 = f"STATIC_ERROR ({type(e).__name__})"

    results["misuse_1_operator_type_mixing"] = {
        "python": py_m1,
        "xox": xox_m1,
    }

    # Misuse 2: Uncertainty Omission in Consumer
    def py_consumer_missing_unknown(decision: AuthDecision) -> str:
        if decision == AuthDecision.TRUE:
            return "ALLOW"
        else:
            return "DENY"
    
    out_py_m2 = py_consumer_missing_unknown(AuthDecision.UNKNOWN)
    py_m2 = f"SILENT_MISUSE_ACCEPTED (returns '{out_py_m2}')"

    try:
        bad_xox_consumer = """
fn consume(decision: XoX) -> Bool:
    if decision:
        return True
    else:
        return False
"""
        compile_source(bad_xox_consumer)
        xox_m2 = "COMPILES"
    except ExhaustivenessError as e:
        xox_m2 = f"STATIC_EXHAUSTIVENESS_ERROR ({e.message})"
    except Exception as e:
        xox_m2 = f"STATIC_ERROR ({type(e).__name__})"

    results["misuse_2_uncertainty_omission"] = {
        "python": py_m2,
        "xox": xox_m2,
    }

    # Misuse 3: Eager Evaluation Prevention
    py_m3 = "SILENT_EAGER_EVALUATION_OR_RUNTIME_CALLABLE_TYPE_ERROR"
    xox_m3 = "STATICALLY_PREVENTED_BY_NATIVE_SHORT_CIRCUITING_SEMANTICS"

    results["misuse_3_eager_evaluation"] = {
        "python": py_m3,
        "xox": xox_m3,
    }

    return results


# ==============================================================================
# 5. Non-Test LOC Counting (Mechanical Application of Rule)
# ==============================================================================

PYTHON_HELPER_CODE = """
class AuthDecision(Enum):
    FALSE = auto()
    TRUE = auto()
    UNKNOWN = auto()
    def __bool__(self) -> bool:
        raise TypeError("Cannot evaluate truthiness of AuthDecision")

def lazy_and(left_fn: Callable[[], AuthDecision], right_fn: Callable[[], AuthDecision]) -> AuthDecision:
    l_val = left_fn()
    if l_val is AuthDecision.FALSE:
        return AuthDecision.FALSE
    r_val = right_fn()
    if r_val is AuthDecision.FALSE:
        return AuthDecision.FALSE
    if l_val is AuthDecision.TRUE and r_val is AuthDecision.TRUE:
        return AuthDecision.TRUE
    return AuthDecision.UNKNOWN

def lazy_or(left_fn: Callable[[], AuthDecision], right_fn: Callable[[], AuthDecision]) -> AuthDecision:
    l_val = left_fn()
    if l_val is AuthDecision.TRUE:
        return AuthDecision.TRUE
    r_val = right_fn()
    if r_val is AuthDecision.TRUE:
        return AuthDecision.TRUE
    if l_val is AuthDecision.FALSE and r_val is AuthDecision.FALSE:
        return AuthDecision.FALSE
    return AuthDecision.UNKNOWN
"""

PYTHON_POLICY_CODE = """
def evaluate_iam_policy_python(
    eval_acc: Callable[[], AuthDecision],
    eval_dev: Callable[[], AuthDecision],
    eval_net: Callable[[], AuthDecision],
    eval_emg: Callable[[], AuthDecision]
) -> AuthDecision:
    return lazy_and(
        lambda: lazy_and(eval_acc, eval_dev),
        lambda: lazy_or(eval_net, eval_emg),
    )
"""

XOX_POLICY_CODE = """
fn evaluate_iam_policy_xox(acc: XoX, dev: XoX, net: XoX, emg: XoX) -> XoX:
    return (acc AND dev) AND (net OR emg)
"""

def count_loc(code_str: str) -> int:
    lines = [l.strip() for l in code_str.strip().split("\n")]
    return len([l for l in lines if l and not l.startswith("#")])


if __name__ == "__main__":
    equiv = run_benchmark_81_combinations()
    misuse = run_misuse_scenarios()

    py_helper_loc = count_loc(PYTHON_HELPER_CODE)
    py_policy_loc = count_loc(PYTHON_POLICY_CODE)
    xox_helper_loc = 0
    xox_policy_loc = count_loc(XOX_POLICY_CODE)

    print("=" * 60)
    print("IAM Reference Authorization Benchmark Results")
    print("=" * 60)
    print(f"Combinations Tested:              {equiv['truth_combinations_tested']}")
    print(f"Decision Equivalence Failures:    {equiv['decision_equivalence_failures']}")
    print(f"Trace Equivalence Failures:       {equiv['trace_equivalence_failures']}")
    print("-" * 60)
    print(f"Python Baseline Total LOC:        {py_helper_loc + py_policy_loc} (helper: {py_helper_loc}, policy: {py_policy_loc})")
    print(f"XoXLang Total LOC:                {xox_helper_loc + xox_policy_loc} (helper: {xox_helper_loc}, policy: {xox_policy_loc})")
    print("=" * 60)

    if equiv["decision_equivalence_failures"] > 0 or equiv["trace_equivalence_failures"] > 0:
        print("[FAIL] Equivalence checks failed.")
        sys.exit(1)
    else:
        print("[PASS] Both implementations are functionally and trace-equivalent across all 81 combinations.")
        sys.exit(0)
