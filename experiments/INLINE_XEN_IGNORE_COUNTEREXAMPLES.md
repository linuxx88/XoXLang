# Adversarial Counterexample Matrix: Compact `xen: ignore` Syntax

## Status & Context
- **Status**: `LOCKED_ADVERSARIAL_SPEC`
- **Target**: Compact Single-Line `xen: ignore` Clause
- **Grammar Production**: `XenIgnoreClause ::= 'xen' ':' 'ignore'` (Strict: no other inline suite or general `xen: <statement>` is permitted)
- **AST Normalization Target**: Normalizes directly to existing canonical AST representation (identical to block form `xen:\n    ignore`), introducing zero new semantic AST nodes.
- **Core Invariants**:
  - `xen: ignore` is pure and strict syntactic sugar
  - Zero distinct new semantic AST nodes are introduced
  - Compact form and block form normalize to the identical AST
  - `ignore` remains exclusive and contextual to the `xen` clause
  - No general inline form `xen: <statement>` is permitted
  - No modification to `if`/`xen`/`else` semantics
  - No relaxation of Phase 3 static exhaustiveness
  - No new dangling `else` or dangling `xen` issues
  - Complete preservation of operational trace and evaluation order

---

## 1. Reference Invariants

| Syntax Form | Parse / Validation Result | Invariant Enforced |
| :--- | :--- | :--- |
| `xen: ignore` | Valid (Normalized to block AST) | Pure syntactic sugar for `xen:\n    ignore` |
| `xen: foo()` | `SyntaxError` (Static) | No general inline statement suite under `xen` |
| `xen: ignore; foo()` | `SyntaxError` (Static) | Compound or semicolon-separated inline statements strictly forbidden |
| `ignore` (alone / expression) | `SyntaxError` (Static) | `ignore` is not an expression or general keyword |
| `if c:\n    A()\nxen: ignore\nelse:\n    B()` | Identical AST / Phase 3 behavior | Strict semantic equivalence to multi-line block form |

---

## 2. Adversarial Test Matrix

### CTX-XEN-INLINE-01: Strict AST Equivalence and Phase 3 Exhaustiveness
- **Snippet**:
  ```xox
  if condition:
      A()
  xen: ignore
  else:
      B()
  ```
- **Invariants Tested**: Strict AST equivalence, Phase 3 exhaustiveness validation, identical semantic lowering and runtime dispatch to block form `xen:\n    ignore`.
- **Derivation**:
  1. Parser identifies compact `xen: ignore` production.
  2. Normalizes directly into standard `XenBranch` with `ignore` / no-op body.
  3. AST is identical to block-form AST.
  4. Phase 3 type checker verifies full exhaustiveness over `XoX` condition.
  5. Lowering and runtime dispatch behavior are strictly identical.
- **Expected Outcome**: AST identity matches block form; Phase 3 exhaustiveness satisfied; identical operational trace.
- **Verdict**: `PASS`

---

### CTX-XEN-INLINE-02: Rejection of Arbitrary Inline Statement (`xen: foo()`)
- **Snippet**:
  ```xox
  if condition:
      A()
  xen: foo()
  else:
      B()
  ```
- **Invariants Tested**: Prohibition of general inline statement suites under `xen`; only literal `ignore` is permitted inline.
- **Derivation**:
  1. Parser encounters `xen` followed by `:` and non-`ignore` token `foo`.
  2. Grammar strictly restricts inline `xen` to `XenIgnoreClause ::= 'xen' ':' 'ignore'`.
  3. General inline statement form `xen: <stmt>` is invalid.
- **Expected Outcome**: Static `SyntaxError` / `ParseError`.
- **Verdict**: `REJECTED_SYNTAX_ERROR`

---

### CTX-XEN-INLINE-03: Rejection of Compound or Multiple Statements (`xen: ignore; foo()`)
- **Snippet**:
  ```xox
  if condition:
      A()
  xen: ignore; foo()
  else:
      B()
  ```
- **Invariants Tested**: Semicolon chaining and compound statement prohibition in compact `xen` clause.
- **Derivation**:
  1. Parser encounters `xen: ignore` followed by `;`.
  2. `XenIgnoreClause` must terminate with newline / end of clause.
  3. Semicolon chaining is strictly forbidden in compact `xen` syntax.
- **Expected Outcome**: Static `SyntaxError` / `ParseError`.
- **Verdict**: `REJECTED_SYNTAX_ERROR`

---

### CTX-XEN-INLINE-04: Rejection of `ignore` Outside `xen` Context
- **Snippet**:
  ```xox
  let x = ignore
  if ignore:
      pass
  ```
- **Invariants Tested**: Contextual exclusivity of `ignore`; `ignore` is never a value, expression, or general keyword.
- **Derivation**:
  1. Parser analyzes expressions containing `ignore`.
  2. `ignore` is not an identifier, expression node, or standalone statement.
  3. `ignore` is exclusively recognized as a terminal token within `XenIgnoreClause` or `xen` block clause.
- **Expected Outcome**: Static `SyntaxError` / `ParseError`.
- **Verdict**: `REJECTED_SYNTAX_ERROR`

---

### CTX-XEN-INLINE-05: Operational Trace Preservation, Else Attachment, and Exhaustiveness Rules
- **Snippet**:
  ```xox
  if trace_cond():
      trace_then()
  xen: ignore
  else:
      trace_else()
  ```
- **Invariants Tested**: Operational trace preservation (condition evaluated first, no-op when Unknown), unambiguous `else` attachment, zero semantic drift.
- **Derivation**:
  1. `trace_cond()` evaluates condition expression.
  2. If condition == `XoX.Unknown`, execution enters `xen: ignore` branch: 0 side effects, execution continues without error.
  3. `else` clause binds unambiguously to the outer `if/xen` structure without dangling ambiguity.
  4. Trace matches block form byte-for-byte across all executions (`True`, `False`, `Unknown`).
- **Expected Outcome**: Execution trace and branch attachment identical to block form across all domain states.
- **Verdict**: `PASS`

---

## 3. Implementation & Verification Audit

- **Audit Status**: `VERIFIED_CONFORMANT`
- **Parser Implementation**: Minimal delta implemented in `xoxlang/parser.py:parse_xen_block()`.
- **AST Normalization**: Compact `xen: ignore` and block `xen:\n    ignore` normalize to the identical `IgnoreStatement` node in `ConditionalStatement.xen_branch`. Zero AST changes or new node classes introduced.
- **Semantic Model & Pipeline**: Zero modifications required to `xoxlang/semantic.py`, `xoxlang/control_flow.py`, lowering, or runtime. Phase 3 exhaustiveness, branch attachment, and operational traces are strictly invariant.
- **Adversarial Safety**: All cases `CTX-XEN-INLINE-01` through `CTX-XEN-INLINE-05` pass. General inline suites `xen: <statement>` and compound `xen: ignore; <statement>` remain strictly rejected (`SyntaxError` / `ParseError`).
- **Test Baseline**: Full test suite passing with 0 failures (`python3 -m unittest discover tests`).

