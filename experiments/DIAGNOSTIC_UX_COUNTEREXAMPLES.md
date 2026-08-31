# Adversarial Specification: User-Facing Diagnostic Standard & UX Invariants

## Status & Context
- **Status**: `LOCKED_ADVERSARIAL_SPEC`
- **Target**: User-Facing Compiler and Runtime Diagnostic Messages
- **Governing Standard**: Problem-oriented plain English diagnostics with actionable corrective guidance, adaptive 5W+H reasoning, and zero compiler-internals leakage.
- **5W+H Internal Reasoning Model & Adaptive Rendering**:
  - The 5W+H framework (Who, What, When, Where, Why, How) is the compiler's internal diagnostic reasoning and completeness model, **not** a mandatory six-label user-facing terminal layout.
  - The compiler must be able to internally resolve Who, What, When, Where, Why, and How whenever relevant.
  - Mechanically displaying raw `WHO`, `WHAT`, `WHEN`, `WHERE`, `WHY`, and `HOW` labels for every diagnostic is strictly prohibited.
  - User-facing diagnostics must render adaptively as: `source span/location + concise error + optional semantic context + action`.
  - Diagnostic verbosity and complexity must scale with problem complexity.
  - **WHERE**: Provide exact source span (line, column, source excerpt, and visual caret) when source information is available.
  - **WHAT**: State the concise primary problem statement directly.
  - **WHO**: Convey operand, type, or construct annotations only when they improve clarity.
  - **WHEN & WHY**: Include short contextual notes only when they materially help explain the semantic rule (e.g. `Unknown`, `xen`, `xox(...)`, `.unwrap_or(...)`, or short-circuit semantics).
  - **HOW**: Distinguish deterministic `help` from intent-dependent `alternatives`.
- **Action Policy (`help` vs. `alternatives`)**:
  - **`help`**: Permitted strictly when the compiler knows a single, deterministic, semantics-preserving correction. Never present a single speculative fix as certain when multiple valid alternatives exist.
  - **`alternatives`**: Required when multiple valid corrections exist and the correct choice depends on developer intent or domain policy. The compiler must never guess or select semantic intent on behalf of the developer.
- **Core Invariants**:
  - Internal exception taxonomy (`LexerError`, `ParseError`, `TypeDiagnosticError`, `ExhaustivenessError`, `MissingReturnError`, `TypeError`, `UnknownValueError`) remains technical and strictly preserved.
  - User-facing diagnostic message strings must explain the developer's actual problem in plain language rather than merely asserting parser state or compiler phase failure.
  - Simple syntax errors must remain compact without unnecessary semantic explanations.
  - Type-boundary errors should expose the actual involved types or operands without compiler jargon.
  - XoX semantic invariant errors may briefly teach relevant `Unknown`/`xen`/`xox`/`unwrap_or` rules.
  - Diagnostics must avoid exposing raw compiler internals, including `TokenKind` enum names (e.g. `RPAREN`, `IDENTIFIER`), AST class names (e.g. `Program AST node`, `Statement`), parser phase designations (`Phase 2`, `Phase 3`), or versioning milestones (`in V1`, `in V1 grammar`, `in V1 lexical core`).
  - Diagnostic guidance for domain conversions must exclusively reference canonical language constructs (`xox(expr)` for Bool-to-XoX promotion and `.unwrap_or(default_bool)` for XoX-to-Bool collapse); guidance referencing obsolete runtime helper methods such as `XoX.from_bool` is strictly forbidden.
  - Any code example shown in diagnostic help or alternatives must itself be valid XoXLang under current canonical specifications.
  - Diagnostics must not claim a narrower rule than the type system actually enforces (e.g., claiming `unwrap_or` requires a Bool literal when any valid Bool expression is accepted).
  - All static checks, type safety guarantees, and exhaustiveness rules remain strictly fail-closed; human-friendly phrasing must never weaken or bypass validation invariants.

---

## 1. Diagnostic Policy Matrix

| Diagnostic Category | Internal Exception Class | User-Facing Message Standard | Prohibited Wording | Required Guidance / Action |
| :--- | :--- | :--- | :--- | :--- |
| **Lexer Syntax** | `LexerError` | Clear character and indentation descriptions | "in V1 lexical core", raw byte offsets | Point to invalid character / indentation mismatch |
| **Parser Syntax** | `ParseError` | Plain-English syntactic expectation | Raw `TokenKind` names (`LPAREN`, `EOF`), "in V1 grammar", raw 5W+H labels | State expected keyword or punctuation in context |
| **Type Incompatibility** | `TypeDiagnosticError` | Clear source vs target domain mismatch | Raw AST node names, bare "TypeError: expected X got Y" | Suggest `xox(...)` or `.unwrap_or(...)` where applicable |
| **Mixed Operations** | `TypeDiagnosticError` | Plain statement of domain boundary violation | `(XoX.from_bool)`, implicit coercion suggestions | Suggest explicit `xox(...)` conversion for the Bool operand |
| **Collapse Violation** | `TypeDiagnosticError` | Plain statement of `unwrap_or` contract | "MethodCall", internal projection terminology, claiming literal Bool required | Explain `source: XoX` and `fallback: Bool` expression requirements |
| **Exhaustiveness** | `ExhaustivenessError` | State missing knowledge state (`Unknown` or `False`) | Compiler phase numbers, "Phase 3 failure" | Suggest adding `xen` (or `xen: ignore`) or `else` |
| **Definite Return** | `MissingReturnError` | Identify function and missing return paths | AST CFG node names, "Phase 4 definite return error" | Remind developer to return a value on all branches |

---

## 2. Adversarial Test Matrix

### CTX-DIAG-01: Jargon-Free Syntax & Token Expectations
- **Context**: Parser encounters unexpected token or missing punctuation (e.g. missing colon, invalid parameter name).
- **Invariants Tested**: No raw `TokenKind` enum identifier is presented to the developer; error message uses clear English terms (e.g. "Expected '('" rather than "Expected LPAREN, found IDENTIFIER").
- **Bad Example**: `Expected IDENTIFIER, found RPAREN (')')`
- **Conformant Standard**: `Expected parameter name, found ')'`
- **Verdict**: `LOCKED_CONFORMANCE_RULE`

---

### CTX-DIAG-02: Canonical Promotion Guidance for Mixed Domain Operations
- **Context**: Developer writes mixed binary operations without explicit domain conversion (e.g. `bool_val AND xox_val`).
- **Invariants Tested**: Message identifies mixed-domain violation and suggests canonical `xox(...)` surface syntax; obsolete `XoX.from_bool` is strictly prohibited.
- **Bad Example**: `Mixed logical operation 'AND' between Bool and XoX is forbidden without explicit conversion (XoX.from_bool)`
- **Conformant Standard**: `Cannot combine Bool and XoX with 'AND'. Wrap the Bool operand in 'xox(...)' to perform 3-valued Strong Kleene logic.`
- **Verdict**: `LOCKED_CONFORMANCE_RULE`

---

### CTX-DIAG-03: Actionable Guidance for `unwrap_or` Collapses
- **Context**: Developer invokes `unwrap_or` on a `Bool` expression or passes a non-`Bool` fallback.
- **Invariants Tested**: Error message clearly explains the domain roles of source (`XoX`) and fallback (`Bool`) and offers corrective steps.
- **Bad Example**: `Operator 'unwrap_or' requires a XoX source expression, got Bool`
- **Conformant Standard**: `'unwrap_or(...)' can only be called on an XoX value to collapse it to Bool, but the source expression is already Bool.`
- **Verdict**: `LOCKED_CONFORMANCE_RULE`

---

### CTX-DIAG-04: Actionable Exhaustiveness & `xen: ignore` Guidance
- **Context**: Conditional structure on an `XoX` condition omits the `xen` branch or `else` branch.
- **Invariants Tested**: Error message specifies the unhandled truth state (`Unknown` or `False`) and mentions `xen: ignore` when no action is needed for uncertainty.
- **Bad Example**: `XoX conditional is non-exhaustive; missing 'xen' clause to cover the Unknown state`
- **Conformant Standard**: `XoX conditional does not handle the 'Unknown' state. Add a 'xen' clause (or 'xen: ignore' if no action is needed).`
- **Verdict**: `LOCKED_CONFORMANCE_RULE`

---

### CTX-DIAG-05: Non-Versioning Grammar Diagnostics
- **Context**: Developer attempts to use uninitialized variables, bare returns, or chained comparisons.
- **Invariants Tested**: Error message states the language rule directly without referencing historical versions or implementation milestones (such as "in V1").
- **Bad Example**: `Uninitialized variable declarations are not supported in V1; variables must be initialized immediately with '='`
- **Conformant Standard**: `Variables must be initialized when declared; uninitialized variable declarations are not supported. Use 'name = value' or 'name: Type = value'.`
- **Verdict**: `LOCKED_CONFORMANCE_RULE`

---

### CTX-DIAG-06: Problem-Oriented Function Return Diagnostics
- **Context**: Function annotated with a return type has code paths lacking return statements.
- **Invariants Tested**: Clear, human-understandable message identifying function name, declared return type, and the requirement to return on all control paths.
- **Bad Example**: `Phase 4 DefiniteReturnError on AST FunctionDefinition 'compute'`
- **Conformant Standard**: `Function 'compute' is annotated to return '-> XoX', but does not return a value on every possible execution path.`
- **Verdict**: `LOCKED_CONFORMANCE_RULE`

---

### CTX-DIAG-07: Compact Rendering for Simple Syntax Errors
- **Context**: Developer makes a trivial syntax mistake (e.g. missing colon at the end of an `if` header).
- **Invariants Tested**: Simple syntax errors must not produce an unnecessary 5W+H tutorial or multi-paragraph explanation; concise `WHERE` + `WHAT` + deterministic `HOW` is sufficient.
- **Bad Example**: `WHO: Colon token. WHAT: Expected colon. WHEN: At end of if condition. WHERE: line 1, col 8. WHY: In XoXLang, every compound statement header must terminate with a colon. HOW: Add a ':' character.`
- **Conformant Standard**: `Expected ':' after if condition.`
- **Verdict**: `LOCKED_CONFORMANCE_RULE`

---

### CTX-DIAG-08: Contextual Semantic Explanation for XoX Invariants
- **Context**: Developer writes an `XoX` conditional with a missing `xen` or `else` branch, or attempts an invalid operation on `Unknown`.
- **Invariants Tested**: Semantic XoX errors involving `Unknown` may include short `WHEN`/`WHY` context when needed to understand the rule without verbose filler.
- **Bad Example**: `Non-exhaustive conditional (AST node #42)`
- **Conformant Standard**: `XoX conditional does not handle the 'Unknown' state. XoX conditionals require 3-way branching because expressions may evaluate to Unknown at runtime. Add a 'xen:' branch (or 'xen: ignore' to discard uncertainty).`
- **Verdict**: `LOCKED_CONFORMANCE_RULE`

---

### CTX-DIAG-09: Single Deterministic Correction via `help`
- **Context**: Developer writes an operation with exactly one deterministic, semantics-preserving fix (e.g. Bool condition with an invalid `xen` clause).
- **Invariants Tested**: When exactly one safe correction exists, expose it directly as `help` and never as a speculative list of alternatives.
- **Bad Example**: `Alternatives: 1) Remove the xen clause; 2) Change the condition to XoX; 3) Maybe wrap in xox(...); 4) Convert else branch.`
- **Conformant Standard**: `Cannot use 'xen' with Bool condition 'flag'. Help: Remove the 'xen' clause, or promote 'flag' to XoX using 'xox(flag)' if 3-valued logic is intended.`
- **Verdict**: `LOCKED_CONFORMANCE_RULE`

---

### CTX-DIAG-10: Intent-Dependent Ambiguity via `alternatives`
- **Context**: Developer writes a type boundary mismatch where multiple semantically valid corrections exist depending on developer intent (e.g. passing an `XoX` expression where `Bool` is expected).
- **Invariants Tested**: When multiple semantically valid corrections exist, the compiler must not choose or guess intent on behalf of the developer; present concise alternatives instead.
- **Bad Example**: `Type mismatch: automatically inserting '.unwrap_or(False)' to resolve Bool requirement.`
- **Conformant Standard**: `Expected Bool, found XoX. Alternatives: 1) Collapse to Bool with explicit fallback: 'expr.unwrap_or(False)' or 'expr.unwrap_or(True)'; 2) Update the target parameter/variable type annotation to 'XoX'.`
- **Verdict**: `LOCKED_CONFORMANCE_RULE`

---

### CTX-DIAG-11: Accurate Rule Scope without Artificial Narrowing
- **Context**: Developer misuses a construct with expression-level rules (e.g. `unwrap_or` fallback argument).
- **Invariants Tested**: A diagnostic must not claim a narrower rule than the type system actually enforces, such as claiming `unwrap_or` requires a Bool literal (`True`/`False`) when any valid `Bool` expression is accepted.
- **Bad Example**: `'unwrap_or' only accepts literal 'True' or 'False'.`
- **Conformant Standard**: `'unwrap_or' requires a Bool fallback argument (found 'XoX'). Pass a Bool expression: 'unwrap_or(default_bool)'.`
- **Verdict**: `LOCKED_CONFORMANCE_RULE`

---

### CTX-DIAG-12: Canonical Syntax Validity in Diagnostic Examples
- **Context**: Compiler generates hints, suggested code snippets, or error message examples.
- **Invariants Tested**: Any code example shown in a diagnostic must itself be valid XoXLang under the current canonical specification (e.g., using `xox(expr)`, `xen: ignore`, `unwrap_or(default_bool)`, without obsolete `XoX.from_bool`, `elif`, or invalid syntax).
- **Bad Example**: `Suggested fix: use 'elif cond:' or 'XoX.from_bool(val)'`
- **Conformant Standard**: `Suggested fix: use nested 'else: if cond:' for Bool, 'xen:' for XoX, or 'xox(val)' for Bool promotion.`
- **Verdict**: `LOCKED_CONFORMANCE_RULE`

---

## 3. Implementation Verification & Invariant Boundary

- **Audited Files**: `xoxlang/diagnostics.py`, `xoxlang/parser.py`, `xoxlang/semantic.py`, `xoxlang/control_flow.py`, `xoxlang/lexer.py`, `xoxlang/runtime.py`.
- **Taxonomy Invariant**: `DiagnosticCategory`, `TypeDiagnosticError`, `ExhaustivenessError`, `MissingReturnError`, and `SourceSpan` structures remain invariant.
- **Fail-Closed Boundary**: Enhancing message clarity must strictly maintain static analysis rejection criteria across Phase 1 (lexer), Phase 2 (parser), Phase 3 (semantic/type checking), and Phase 4 (definite return analysis).
