# Adversarial Counterexample Matrix: Bool-to-XoX Promotion Form (`xox(expr)`)

## Status & Context
- **Status**: `LOCKED_ADVERSARIAL_SPEC`
- **Target**: Bool-to-XoX Promotion Form (`xox(expr)`)
- **Typing Rule**: $\Gamma \vdash e : \text{Bool} \implies \Gamma \vdash \text{xox}(e) : \text{XoX}$
- **Core Invariants**:
  - $\text{xox}(\text{True}) = \text{XoX.True}$
  - $\text{xox}(\text{False}) = \text{XoX.False}$
  - No other rule
  - `xox(expr)` never introduces `Unknown`
  - `xox(expr)` is strictly non-idempotent
  - `XoX` and `Unknown` are never valid operands
  - The typed AST preserves `PromoteBoolToXoX(expr)`
  - `expr` is evaluated exactly once
  - No reordering of the operational trace (strictly condition-first)
  - Parentheses are mandatory

---

## 1. Reference Invariants

| Input Expression | Static / Runtime Result | Invariant Enforced |
| :--- | :--- | :--- |
| `xox(Unknown)` | `TypeError` (Static) | `Unknown` / `XoX` is never a valid operand for `xox(...)` |
| `xox(True)` | `XoX.True` | Direct lossless promotion to truth state `XoX.True` |
| `xox(False)` | `XoX.False` | Direct lossless promotion to false state `XoX.False` |

---

## 2. Adversarial Test Matrix

### CTX-PROMOT-01: Rejected Idempotence
- **Expression**: `xox(xox(flag))`
- **Setup**: `flag: Bool = True`
- **Invariants Tested**: Strict non-idempotence; operand of promotion construct must be statically typed `Bool`.
- **Derivation**:
  1. Inner `xox(flag)` promotes `Bool` to `XoX`.
  2. Outer `xox(...)` receives operand of static type `XoX`.
  3. Promotion expects `Bool`, receives `XoX`.
- **Expected Outcome**: Static `TypeError` (TypeDiagnosticError).
- **Verdict**: `REJECTED_STATIC_TYPE_ERROR`

---

### CTX-PROMOT-02: Rejected XoX Compound
- **Expression**: `xox(xox_a AND xox_b)`
- **Setup**: `xox_a: XoX = True`, `xox_b: XoX = Unknown`
- **Invariants Tested**: Compound XoX expression promotion prohibition; no redundant or nested promotion of XoX domains.
- **Derivation**:
  1. `(xox_a AND xox_b)` evaluates under Strong Kleene logic to static type `XoX`.
  2. Promotion construct `xox(...)` receives `XoX`.
  3. Operand is already `XoX`.
- **Expected Outcome**: Static `TypeError` (TypeDiagnosticError).
- **Verdict**: `REJECTED_STATIC_TYPE_ERROR`

---

### CTX-PROMOT-03: Precedence Without Parentheses
- **Expression**: `xox a == b`
- **Setup**: `a: Bool = True`, `b: Bool = True`
- **Invariants Tested**: Mandatory parentheses invariant for `xox(...)`.
- **Derivation**:
  - `xox(expr)` requires mandatory enclosing parentheses.
  - The unparenthesized sequence `xox a == b` is an ungrammatical token sequence rejected at parse time.
  - No syntactic grouping alternative (such as `(xox a) == b`) or secondary TypeError fallback is permitted.
- **Expected Outcome**: `SyntaxError` / `ParseError` (Mandatory).
- **Verdict**: `REJECTED_SYNTAX_ERROR`

---

### CTX-PROMOT-04: Trace & Single Evaluation
- **Expression**: `xox(side_effect())`
- **Setup**: Function `side_effect() -> Bool` appending invocation record to execution trace list.
- **Invariants Tested**: Single evaluation semantics; side effects must execute exactly once at the exact sequential position without duplicate evaluation or trace reordering.
- **Derivation**:
  1. Call `side_effect()` once.
  2. Return value evaluated to `Bool`.
  3. Promoted to `XoX` without re-evaluating or duplicating call.
  4. Execution trace shows length 1 at exact sequential position.
- **Expected Outcome**: Evaluation returns `XoX.True` (or `XoX.False`); invocation count == 1.
- **Verdict**: `PASS`
