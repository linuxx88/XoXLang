# Adversarial Counterexample Matrix: XoX-to-Bool Collapse Primitive (`unwrap_or(default_bool)`)

## Status & Context
- **Status**: `LOCKED_ADVERSARIAL_SPEC`
- **Target**: XoX-to-Bool Collapse Flow Control Primitive (`source.unwrap_or(fallback)`)
- **Semantic AST Representation**: `CollapseXoXToBoolWithDefault(source, fallback)` (strictly distinct from generic `MethodCall`)
- **Typing Rule**: $\Gamma \vdash x : \text{XoX} \land \Gamma \vdash d : \text{Bool} \implies \Gamma \vdash x.\text{unwrap\_or}(d) : \text{Bool}$
- **Core Semantic Rules & Invariants**:
  - `True` returns `Bool.True` without evaluating `fallback` ($\text{XoX.True}.\text{unwrap\_or}(d) = \text{Bool.True}$)
  - `False` returns `Bool.False` without evaluating `fallback` ($\text{XoX.False}.\text{unwrap\_or}(d) = \text{Bool.False}$)
  - `Unknown` evaluates `fallback` exactly once and returns its `Bool` ($\text{XoX.Unknown}.\text{unwrap\_or}(d) = d$)
  - `source` is always evaluated exactly once prior to any decision
  - `fallback` is evaluated only if `source == XoX.Unknown`
  - `fallback` is evaluated at most once
  - `True` and `False` never evaluate `fallback` (strict short-circuit)
  - `unwrap_or` is a special lazy flow-control form (short-circuit) and not an ordinary runtime `MethodCall`
  - `unwrap_or` is explicitly an information-losing boundary
  - The canonical semantic AST node is `CollapseXoXToBoolWithDefault(source, fallback)`
  - No truthiness
  - No implicit coercion
  - No implicit fallback (mandatory argument)
  - A source-visible fallback expression demonstrates selected intent, but does not by itself establish authority to define or validate the legitimacy of the fallback policy
  - No XoX -> Bool conversion outside an explicitly permitted boundary
  - The typed AST preserves `CollapseXoXToBoolWithDefault(source, fallback)` and forbids any desugaring into an ordinary `MethodCall`

---

## 1. Reference Invariants

| Input Expression | Fallback Expression | Static / Runtime Result | Invariant Enforced |
| :--- | :--- | :--- | :--- |
| `XoX.True.unwrap_or(d)` | `d: Bool` | `Bool.True` | Short-circuit; fallback `d` not evaluated |
| `XoX.False.unwrap_or(d)` | `d: Bool` | `Bool.False` | Short-circuit; fallback `d` not evaluated |
| `XoX.Unknown.unwrap_or(d)` | `d: Bool` | `d` (Bool) | Fallback `d` evaluated exactly once |
| `xox_val.unwrap_or(Unknown)` | `Unknown` (XoX) | `TypeError` (Static) | Static type of fallback must be `Bool` |
| `bool_val.unwrap_or(False)` | `False` (Bool) | `TypeError` (Static) | Static type of source must be `XoX` |
| `xox_val.unwrap_or()` | *Absent* | `ParseError` / `StaticError` | Mandatory fallback argument; no implicit default |

---

## 2. Adversarial Test Matrix

### CTX-COLLAPSE-01: True Short-Circuit & No Fallback Evaluation
- **Expression**: `XoX.True.unwrap_or(trace_effect())`
- **Setup**: Function `trace_effect() -> Bool` appending invocation record to execution trace list.
- **Invariants Tested**: Short-circuit execution; source evaluated exactly 1 time; fallback side effect never invoked when source is `XoX.True`.
- **Derivation**:
  1. Evaluate `source` -> `XoX.True`.
  2. Short-circuit condition met (`source` is definite `True`).
  3. `trace_effect()` is not called (0 invocations).
  4. Return `Bool.True`.
- **Expected Outcome**: Evaluation returns `Bool.True`; `trace_effect` call count == 0; source call count == 1.
- **Verdict**: `PASS`

---

### CTX-COLLAPSE-02: False Short-Circuit & No Fallback Evaluation
- **Expression**: `XoX.False.unwrap_or(trace_effect())`
- **Setup**: Function `trace_effect() -> Bool` appending invocation record to execution trace list.
- **Invariants Tested**: Short-circuit execution; source evaluated exactly 1 time; fallback side effect never invoked when source is `XoX.False`.
- **Derivation**:
  1. Evaluate `source` -> `XoX.False`.
  2. Short-circuit condition met (`source` is definite `False`).
  3. `trace_effect()` is not called (0 invocations).
  4. Return `Bool.False`.
- **Expected Outcome**: Evaluation returns `Bool.False`; `trace_effect` call count == 0; source call count == 1.
- **Verdict**: `PASS`

---

### CTX-COLLAPSE-03: Unknown Exact Single Fallback Evaluation
- **Expression**: `XoX.Unknown.unwrap_or(trace_effect())`
- **Setup**: Function `trace_effect() -> Bool` returning `Bool.True` (or `Bool.False`) and recording call trace.
- **Invariants Tested**: Source evaluated exactly once; fallback evaluated exactly once if and only after `Unknown` is determined; result is Bool.
- **Derivation**:
  1. Evaluate `source` -> `XoX.Unknown` (evaluation count == 1).
  2. Unknown branch taken -> evaluate `trace_effect()` strictly after source determination.
  3. `trace_effect()` executes exactly once and yields `Bool` result.
  4. Return value is the `Bool` outcome of `trace_effect()`.
- **Expected Outcome**: Evaluation returns `trace_effect()` Bool result; `trace_effect` call count == 1; source call count == 1; sequential order `[source, fallback]`.
- **Verdict**: `PASS`

---

### CTX-COLLAPSE-04: Non-Bool Fallback Statically Rejected
- **Expression**: `xox_val.unwrap_or(Unknown)`
- **Setup**: `xox_val: XoX = True` (or `Unknown`)
- **Invariants Tested**: Static typing rule $\Gamma \vdash d : \text{Bool}$; fallback expression must be statically typed `Bool` regardless of runtime source reachability.
- **Derivation**:
  1. Type checker analyzes `source` -> `XoX`.
  2. Type checker analyzes `fallback` -> `XoX` (`Unknown`).
  3. Collapse requires $\Gamma \vdash \text{fallback} : \text{Bool}$.
  4. Static type violation detected at compile time.
- **Expected Outcome**: Static `TypeError` (TypeDiagnosticError).
- **Verdict**: `REJECTED_STATIC_TYPE_ERROR`

---

### CTX-COLLAPSE-05: Non-XoX Source Statically Rejected
- **Expression**: `bool_val.unwrap_or(False)`
- **Setup**: `bool_val: Bool = True`
- **Invariants Tested**: Static typing rule $\Gamma \vdash x : \text{XoX}$; source expression must be statically typed `XoX`; `Bool` expressions cannot invoke `unwrap_or`.
- **Derivation**:
  1. Type checker analyzes `source` -> `Bool`.
  2. Collapse requires $\Gamma \vdash \text{source} : \text{XoX}$.
  3. `Bool` type does not support `unwrap_or` primitive.
  4. Static type violation detected at compile time.
- **Expected Outcome**: Static `TypeError` (TypeDiagnosticError).
- **Verdict**: `REJECTED_STATIC_TYPE_ERROR`

---

### CTX-COLLAPSE-06: Absent Fallback Statically Rejected
- **Expression**: `xox_val.unwrap_or()`
- **Setup**: `xox_val: XoX = True`
- **Invariants Tested**: Mandatory fallback argument; no implicit default value (`False` or `True`) is assumed.
- **Derivation**:
  1. Parser / static validator encounters `unwrap_or` without argument.
  2. No implicit default exists in XoX language semantics.
  3. Call syntax rejected statically.
- **Expected Outcome**: `SyntaxError` / `ParseError` / `StaticError` (Mandatory).
- **Verdict**: `REJECTED_STATIC_ERROR`

---

## 3. Implementation & Verification Audit

- **Audit Status**: `VERIFIED_CONFORMANT`
- **Specification & Governance Alignment**: Fully audited against `XOX_SPEC.md` (§3, §5.2, §7.1, §12, §13, §14, §18, §19) and `.agents/rules/xen-source-of-truth.md`.
- **AST Canonical Form**: Canonical semantic representation is `CollapseXoXToBoolWithDefault(source, fallback, span)`. Zero generic `MethodCall` or `PropertyAccess` nodes or mechanisms introduced.
- **Lexical & Parser Scoping**: `TokenKind.DOT` is strictly scoped in `parse_postfix()` to `unwrap_or(default_bool)`. All arbitrary methods and attributes remain rejected.
- **Static Typing**: Statically enforced $\Gamma \vdash x : \text{XoX} \land \Gamma \vdash d : \text{Bool} \implies \Gamma \vdash x.\text{unwrap\_or}(d) : \text{Bool}$. Fallback is strictly validated as `Bool` regardless of runtime reachability.
- **Observable Trace Proofs**: Formally proved via observable execution traces (`tests/test_collapse_adversarial.py`):
  - `XoX.True`: `trace = ['eval_source']`, `source_count = 1`, `fallback_count = 0`, `result = Bool.True`.
  - `XoX.False`: `trace = ['eval_source']`, `source_count = 1`, `fallback_count = 0`, `result = Bool.False`.
  - `XoX.Unknown`: `trace = ['eval_source', 'eval_fallback']`, `source_count = 1`, `fallback_count = 1`, `order = [source, fallback]`, `result = fallback_value`.
- **Anti-Coercion & Syntax Integrity**: Zero implicit truthiness or `XoX -> Bool` coercions. No alternative `??` syntax exists.
- **Test Baseline**: Full test suite passing with 0 failures (`python3 -m unittest discover tests`).

