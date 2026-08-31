# X-o-X Language Specification: Semantic Core (V2)

## Provenance & Status
- **Specification Version**: V2 (Active Source of Truth)
- **Conceptual / Display Name**: X-o-X
- **Source-Code Primitive Type**: `XoX`
- **Supersedes**: `docs/historical/trool-v1/TROOL_SPEC.md` (Historical V1 Specification)
- **Historical Baseline Integrity**: `docs/historical/trool-v1/TROOL_SPEC.md` and `docs/historical/trool-v1/TROOL_V1_BASELINE.json` remain immutable sealed historical V1 artifacts.
- **Semantic Invariant Preservation**: All core semantics—including the three-valued truth domain (`True`, `False`, `Unknown`), Strong Kleene logic ($K_3$), state-identity equality returning `Bool`, and canonical `if`/`xen`/`else` control flow—are strictly preserved without modification.

## 1. Purpose
Defines the initial immutable semantic core of the XoX (X-o-X) type and the `xen` control flow construct.

## 2. Design Principles
- **Small**
- **Explicit**
- **Deterministic**
- **Human-readable**
- **No silent loss of information**
- **Simple compiler diagnostics**

## 3. Type System
- **Bool**: Exactly two values: `True` and `False`.
- **XoX** (conceptual name: **X-o-X**): Exactly three values: `True`, `False`, and `Unknown`.
- **Non-Numeric Logical Types**: `Bool` and `XoX` are non-numeric logical types with no numeric subtyping, integer arithmetic, bitwise operations, or ordering relations (§19).
- **Distinctness**: `Bool` and `XoX` are distinct types.
- **Coercion**: No implicit XoX-to-Bool or Bool-to-XoX coercion exists.
- **No Fourth Truth Value**: Contradiction ($W_{\text{factive}} = \emptyset$) is not a fourth $K_3$ truth value; it represents an ontological precondition failure that aborts evaluation fail-closed.
- **Explicit Conversion Boundaries**:
  - `Bool` $\rightarrow$ `XoX`: Explicit lossless promotion via `xox(expr)` (§19).
  - `XoX` $\rightarrow$ `Bool`: Explicit information-losing collapse via short-circuit primitive `x.unwrap_or(default_bool)` (§19).

## 4. Meaning of Unknown
- `Unknown` denotes insufficient information to establish `True` or `False` across non-empty admissible execution realities ($|W_{\text{factive}}| \ge 2$).
- `Unknown` does not mean half-true.
- `Unknown` is fundamentally distinct from Contradiction ($W_{\text{factive}} = \emptyset$). Vacuous truth over an empty world space has zero epistemic authority and cannot produce `Known`.

## 5. Control Flow Semantics
- **Conventional Catch-All Semantics**: The keyword `else` retains its conventional catch-all role covering the only remaining unhandled state. The language does not redefine `else` as a specialized `False` keyword.
- **Bool Conditional**:
  - `if` maps to `True`.
  - `else` catches the only remaining state: `False`.
- **XoX Conditional**:
  - `if` maps to `True`.
  - `xen` maps to `Unknown`.
  - `else` catches the only remaining state: `False`.
- **Xen Scope & Contradiction Isolation**: `xen` handles `Unknown` only; `xen` cannot capture or suppress an evaluated Contradiction.
- **Statement-Level Ignore Syntaxes**: The explicit ignore branch for `Unknown` supports two strictly equivalent syntaxes:
  - Multi-line block form: `xen:\n    ignore`
  - Compact single-line form: `xen: ignore`
  - Both forms are purely statement-level syntactic sugar with identical semantics, normalizing to the exact same AST representation.
- **Exhaustiveness**: A XoX conditional must explicitly handle `Unknown` (via a statement block, `xen:\n    ignore`, or compact `xen: ignore`).

### 5.1 Inline Conditional Expressions
- **Syntax and Dual Forms**:
  - **Bool Inline Conditional**: `true_expr if cond_expr else false_expr`
  - **XoX Inline Conditional**: `true_expr if cond_expr xen unk_expr else false_expr`
- **Grammar & Precedence**:
  - Inline conditionals have the **lowest operator precedence** (below `OR`).
  - Inline conditionals are **right-associative**: `a if c1 else b if c2 else d` parses as `a if c1 else (b if c2 else d)`.
- **Exhaustiveness and Syntax Integrity**:
  - For a `XoX`-typed condition, the `xen` branch is **mandatory**; omitting `xen` produces a static `ExhaustivenessError`.
  - For a `Bool`-typed condition, the `xen` branch is **strictly forbidden**; including `xen` produces a static `TypeError`.
  - `xen: ignore` is a statement-level construct only and is **invalid in expressions**; all branches of an inline conditional must be concrete value-producing expressions.
- **Typing and Contextual Domain Resolution**:
  - **Homogeneous Branch Typing**: All branches (`true_expr`, `xen_expr`, `else_expr`) must resolve to the same static type (`Bool` or `XoX`). Heterogeneous branch types produce a static `TypeError`.
  - **Independence of Condition and Result Domain**: The result type of an inline conditional is determined entirely by its branch expressions and is independent from the condition domain (e.g. an `XoX` condition may evaluate to a `Bool` result, and a `Bool` condition may evaluate to a `XoX` result).
  - **Contextual Domain Anchoring (§18)**: If any branch expression contains `XoX` or an `Unknown` literal, uncommitted `True` or `False` literals in other branches resolve contextually to `XoX`. If all branches are uncommitted literals (or `Bool`), they resolve to `Bool`.
- **Operational Trace & Evaluation Requirements (§7.1)**:
  - Evaluation is strictly **condition-first**: `cond_expr` is evaluated first and exactly once.
  - Branch evaluation is **lazy**: only the branch selected by the runtime condition state is evaluated; unselected branches are skipped completely (no side effects executed), strictly preserving the Operational Trace Preservation Invariant (§7.1).

### 5.2 Explicit XoX Collapse Primitive (`unwrap_or`)
- **Flow Control Boundary**: `x.unwrap_or(default_bool)` is a dedicated, special flow-control primitive projecting `XoX` onto `Bool`.
- **Semantic AST Representation**: Evaluated and represented semantically as `CollapseXoXToBoolWithDefault(source, fallback)`, never as an ordinary `MethodCall`.
- **Short-Circuit & Condition-First Evaluation**:
  - `source` is evaluated **exactly once** prior to any decision.
  - If `source == XoX.True`, returns `Bool.True` without evaluating `fallback`.
  - If `source == XoX.False`, returns `Bool.False` without evaluating `fallback`.
  - If `source == XoX.Unknown`, evaluates `fallback` **exactly once** and returns its `Bool` result.
- **Strict Lazy Fallback**: `fallback` is strictly short-circuited when `source` is `True` or `False` (0 side-effect evaluations).
- **Contradiction Isolation**: `unwrap_or` handles `Unknown` only; `unwrap_or` cannot collapse or mask an evaluated Contradiction.
- **Resolution Authority**: In factive evaluation environments, collapsing `Unknown[\Pi]` requires an authoritative `ResolutionToken` matching exact $\Pi$, `OperationType=unwrap_or`, active `WorldStateID`, and the exact `FallbackPolicyIdentity`. Mismatch fails closed before fallback evaluation.
- **Information-Losing Projection**: `unwrap_or` is an explicitly permitted information-reducing boundary, with no truthiness, no implicit coercion, and no implicit fallback.


## 6. Semantic Invariants
- **State Cardinality**: `Bool` has exactly 2 states; `XoX` has exactly 3 states.
- **Mutual Exclusivity**: `True`, `False`, and `Unknown` are strictly mutually exclusive `XoX` states.
- **Information Preservation**: `Unknown` cannot be silently treated as `True` or `False`.
- **Contradiction Isolation**: Contradiction ($W_{\text{factive}} = \emptyset$) is not a 4th truth value; an evaluated Contradiction propagates immediately fail-closed and cannot be captured by `xen` or collapsed by `unwrap_or`.
- **Short-Circuit Immunity**: An operand skipped by legitimate left-to-right short-circuiting is not evaluated and produces no value, effect, exception, or Contradiction (§7, §7.1).
- **Branch Selection**: Every executed `XoX` conditional selects exactly one branch among `if`, `xen`, or `else`.
- **Branch Mapping**: In a `XoX` conditional, `if` corresponds only to `True`, `xen` only to `Unknown`, and `else` only to `False`.
- **Mandatory Handling**: A `XoX` conditional cannot silently omit the `Unknown` path.
- **Binary Isolation**: `Bool` control flow remains strictly binary and does not use `xen`.
- **Operational Trace Preservation**: Evaluation order, short-circuit skipping, and observable side-effect traces must be strictly preserved under all compilation and optimization passes (§7.1).

## 7. XoX Logical Operators
`XoX` logical operators follow **Strong Kleene 3-valued logic ($K_3$)**.
- **Information Preservation**: Operators preserve `Unknown` when the result cannot be determined from known information.
- **Short-Circuit Dominance**: `False` dominates `AND` (i.e. `False AND Unknown = False`); `True` dominates `OR` (i.e. `True OR Unknown = True`).

### Truth Tables

#### NOT
| A | NOT A |
|---|---|
| True | False |
| False | True |
| Unknown | Unknown |

#### AND
| A | B | A AND B |
|---|---|---|
| True | True | True |
| True | False | False |
| True | Unknown | Unknown |
| False | True | False |
| False | False | False |
| False | Unknown | False |
| Unknown | True | Unknown |
| Unknown | False | False |
| Unknown | Unknown | Unknown |

#### OR
| A | B | A OR B |
|---|---|---|
| True | True | True |
| True | False | True |
| True | Unknown | True |
| False | True | True |
| False | False | False |
| False | Unknown | Unknown |
| Unknown | True | True |
| Unknown | False | Unknown |
| Unknown | Unknown | Unknown |

### Evaluation Order and Short-Circuit Semantics
- **Evaluation Order**: Logical expressions evaluate operands strictly from **left to right**.
- **Truth Tables vs Evaluation**: Truth tables describe the mathematical result values; these rules define operational operand evaluation behavior.
- **AND Short-Circuiting**: If the left operand evaluates to `False`, the right operand is **not evaluated** (skipping all potential side effects), because `False` dominates `AND`.
- **OR Short-Circuiting**: If the left operand evaluates to `True`, the right operand is **not evaluated** (skipping all potential side effects), because `True` dominates `OR`.
- **Unknown Left Operand**: If the left operand evaluates to `Unknown`, the right operand **must be evaluated**, as a dominant right operand (`False` for `AND`, `True` for `OR`) can still fully determine the final result.
- **Side Effect Guarantee**: Side effects in a skipped (short-circuited) right operand expression do not occur.

### 7.1 Operational Trace Preservation & Optimization Invariants
- **Strict Operational Trace Preservation Invariant**: Compiler transformations, lowering passes, and target code generation must strictly preserve the canonical observable execution trace (evaluation order, observable side effects, and exceptions) defined by left-to-right operational reduction with short-circuit dominance.
- **Observable Equivalence**: Two expression forms or compiled lowerings are equivalent if and only if they yield identical Strong Kleene $K_3$ values and produce an identical canonical observable effect/exception trace under left-to-right evaluation.
- **Algebraic Equivalence Limitation**: Mathematical $K_3$ algebraic equivalence (e.g. commutativity or annihilation) alone never authorizes runtime reordering or omission of unevaluated expressions.
- **Forbidden Transformations**:
  - Commutative operand swapping (e.g. rewriting `A AND B` $\rightarrow$ `B AND A` or `A OR B` $\rightarrow$ `B OR A`) unless operands are statically proven pure.
  - Unsafe annihilation without prefix evaluation (e.g. rewriting `expr AND False` directly to `False` or `expr OR True` directly to `True` without evaluating `expr`).
  - Speculative, parallel, or out-of-order operand evaluation that triggers right-hand effects prior to left-hand resolution.
  - Duplication of effectful subexpressions across short-circuit boundaries.
- **Permitted Transformations**: Compiler transformations (such as constant folding, algebraic simplification, or dead-code elimination) are permitted only when they preserve canonical left-to-right operational behavior or when all eliminated/reordered subexpressions are statically proven pure.
- **Collapse Primitive (`unwrap_or`) Trace Invariants**:
  - `source` is strictly evaluated first and **exactly once**.
  - `fallback` is evaluated if and only if `source` evaluates to `XoX.Unknown`.
  - If `source` evaluates to `XoX.True` or `XoX.False`, `fallback` is never evaluated (0 side-effect executions).
  - No speculation, reordering, or duplication of `source` or `fallback`.

## 8. XoX Equality

### State Identity Semantics
- **Exact State Identity**: `XoX` equality (`==`) evaluates exact state identity.
- **Return Type**: `XoX` equality and inequality always return `Bool`, never `XoX`.
- **Strict Result-Type Barrier**: `==` and `!=` form a strict result-type barrier that always and exclusively returns `Bool`. An outer expected `XoX` context must never cause the result of `==` or `!=` to become `XoX`.
- **Identity Evaluation**:
  - `True == True` $\rightarrow$ `Bool True`
  - `False == False` $\rightarrow$ `Bool True`
  - `Unknown == Unknown` $\rightarrow$ `Bool True`
- **State Mismatch**: Any comparison between different `XoX` states evaluates to `Bool False` (e.g. `XoX.True == XoX.Unknown` $\rightarrow$ `Bool False`; `XoX.False == XoX.Unknown` $\rightarrow$ `Bool False`).
- **Inequality**: `XoX` inequality (`!=`) is the exact logical negation of `XoX` equality (e.g. `XoX.True != XoX.Unknown` $\rightarrow$ `Bool True`).
- **Deliberate Strong Kleene Deviation**: While logical operators (`NOT`, `AND`, `OR`) strictly follow Strong Kleene 3-valued logic ($K_3$), `XoX` equality intentionally does not. Equality compares exact state identity and always evaluates to `Bool`.
- **Operand Type Homogeneity**: Equality and inequality require homogeneous operand types (`Bool == Bool` or `XoX == XoX`). Comparing already-typed `Bool` and `XoX` expressions without explicit conversion is a `TypeError` (§19). Direct comparisons with uncommitted literals resolve via contextual literal typing (§18).

### Distinction from SQL NULL
- **Not SQL NULL**: `XoX.Unknown` is not `SQL NULL`.
- **SQL Equality (`=`) Contrast**: In standard SQL three-valued logic, equality comparison using `=` does not treat `NULL = NULL` as `True`; instead, it evaluates to `UNKNOWN` (or `NULL`).
- **Exact State Identity**: `XoX` equality (`==`) instead compares exact `XoX` state identity. `Unknown == Unknown` therefore evaluates to `Bool True`.
- **Pedagogical Analogy (`IS NOT DISTINCT FROM`)**: The state-identity behavior of `XoX` equality is conceptually analogous to SQL's `IS NOT DISTINCT FROM` operator rather than SQL's `=` operator. This comparison serves strictly as a pedagogical analogy for state-identity equivalence, not as a claim that `XoX.Unknown` and `SQL NULL` have equivalent semantics.
- **Epistemic vs Real-World Facts**: Two `Unknown` `XoX` values comparing equal means only that both operands reside in the `Unknown` state. It does not establish equality, identity, or knowledge of any underlying real-world facts represented by those `Unknown` states.
- **Pragmatic Strong Kleene Deviation**: While logical operators (`NOT`, `AND`, `OR`) strictly adhere to Strong Kleene 3-valued logic ($K_3$), the deviation of `XoX` equality to state-identity comparison returning binary `Bool` is a deliberate, pragmatic design decision to guarantee a total equivalence relation.

### Strictly Binary Comparison Invariant
- **Strictly Binary Operators**: Comparison operators (`==`, `!=`) are strictly binary operators in the initial specification. Chained comparison syntax (such as `a == b == c` or `a == b != c`) is not supported in the initial language specification and produces a `SyntaxError`.
- **No Implicit Associativity or Desugaring**: A construct such as `a == b == c` must not be interpreted as left-associative nesting `(a == b) == c` nor as implicit Boolean conjunction `(a == b) AND (b == c)`.
- **Explicit Conjunction Requirement**: Developers must write multiple comparisons explicitly using logical operators and grouping, for example: `(a == b) AND (b == c)`.

### Operator Precedence and Associativity
- **Deliberate Language Precedence**: Operator precedence and associativity are formal, deliberate XoX language design decisions and must not be inferred from Python or any other host language.
- **Precedence Hierarchy (Highest to Lowest)**:
  1. **Parentheses**: `(...)` (always overrides default precedence)
  2. **Unary NOT**: `NOT` (unary prefix operator)
  3. **Equality Operators**: `==`, `!=` (strictly binary comparison operators, non-chaining)
  4. **Conjunction**: `AND` (binary logical operator, left-associative)
  5. **Disjunction**: `OR` (binary logical operator, left-associative)
- **Canonical Precedence Table**:

| Precedence | Operator | Arity / Position | Associativity | Description |
|---|---|---|---|---|
| 1 (Highest) | `(...)` | Enclosure | Non-associative | Explicit sub-expression grouping |
| 2 | `NOT` | Unary Prefix | Right-to-left (prefix) | Logical negation (§7) |
| 3 | `==`, `!=` | Binary Infix | Non-associative (strictly binary) | State-identity equality & inequality (§8) |
| 4 | `AND` | Binary Infix | Left-to-right (left-associative) | Logical conjunction with short-circuiting (§7) |
| 5 (Lowest) | `OR` | Binary Infix | Left-to-right (left-associative) | Logical disjunction with short-circuiting (§7) |

- **Parsing Invariants**:
  - Because unary `NOT` binds tighter than `==`, and `==` binds tighter than `AND`, an expression such as `NOT a == b AND c` parses strictly as `((NOT a) == b) AND c`.
  - Parentheses explicitly override default precedence (e.g. `NOT (a == b) AND c` or `(NOT a) == (b AND c)`).
- **Semantics and Evaluation Order**: Precedence strictly governs syntactic expression tree construction (grouping) and does not alter the left-to-right evaluation order and short-circuit semantics established in §7 and §8.
- **No Additional Operators**: The initial language specification defines no arithmetic, integer bitwise, or relational ordering operators (§19).

## 9. Canonical Conditional Syntax

### Bool Conditional Syntax
`Bool` conditions use standard binary branching:
```text
if <Bool-expression>:
    <True-block>
else:
    <False-block>
```
- The `else` branch is optional for `Bool` conditions.

### XoX Conditional Syntax
`XoX` conditions follow the canonical three-way order: `if`, `xen`, `else`.
```text
if <XoX-expression>:
    <True-block>
xen:
    <Unknown-block>
else:
    <False-block>
```
- **Branch Mapping**: `if` executes on `True`, `xen` executes on `Unknown`, and `else` executes on `False`.
- **Validity Scope**: `xen` is valid only for `XoX` conditions.
- **Dependency**: `xen` cannot appear without a preceding `if`.
- **No `elif` for Unknown**: A `XoX` conditional must not use `elif` to represent `Unknown`.
- **Nesting**: Nested conditionals remain structurally independent.

## 10. Conditional Exhaustiveness
- **Bool Conditionals**: May use `if` alone (implicit no-op for `False`) or `if` with an explicit `else`.
- **XoX Conditionals**: Must fully account for all three states (`True`, `Unknown`, and `False`).
- **Structural `if` Presence**: Because every parsed `ConditionalStatement` structurally begins with `if`, a valid parsed conditional inherently possesses its `True` branch. Standalone `xen` or `else` clauses without an `if` are orphan clauses (`SyntaxError`).
- **Missing Unknown Path (`xen`)**: Omitting the `Unknown` path without an explicit ignore mechanism (`xen:` block or compact `xen: ignore`) is an `ExhaustivenessError`.
- **Missing False Path (`else`)**: Omitting the `False` branch (`else`) on a `XoX` conditional is an `ExhaustivenessError`.
- **No Duplicate Branches**: Duplicated semantic branches (e.g. multiple `xen` or multiple `else` blocks for the same conditional) are invalid (`SyntaxError`).
- **Canonical Ordering**: The branch order for a `XoX` conditional is canonically `if`, `xen`, `else`.
- **Exhaustiveness Satisfaction**: Using explicit ignore (`xen:\n    ignore` or compact `xen: ignore`) satisfies the exhaustiveness requirement for `XoX`.

### 10.1 Direct XoX Control vs. Derived Bool Control

XoXLang distinguishes between direct tripartite control flow and binary control flow derived from explicit state observations or policy collapses:

1. **Direct XoX Control (`DIRECT_XOX_CONTROL`)**:
   - **Condition Domain**: The condition expression is typed directly as `XoX`.
   - **Compiler Guarantee**: Static tripartite exhaustiveness is enforced at compile time. Omission of `xen` or `else` produces a static `ExhaustivenessError`.
   - **Safe Direct Example**:
     ```python
     if status:
         grant_access()
     xen:
         challenge_mfa()
     else:
         deny_access()
     ```

2. **Derived Bool Control (`DERIVED_BOOL_CONTROL`)**:
   - **Condition Domain**: The condition expression is typed as `Bool`, produced by an explicit source-level operation on a `XoX` value.
   - **Explicit State Partitioning (`==`, `!=`)**: Comparing state identity (`x == True`) produces a `Bool`. In a binary `if/else`, this explicitly partitions state space:
     ```python
     if x == True:
         grant_access()
     else:
         # Explicit partition: False and Unknown are merged into this branch
         deny_access()
     ```
     State observation tests metadata identity; it does not resolve the underlying proposition.
   - **Explicit Policy Collapse (`unwrap_or`)**: Calling `x.unwrap_or(default_bool)` explicitly collapses `Unknown` to `default_bool` by declared policy.
   - **Manual Equality Reconstruction Limit**: A manual chain of binary equality checks (`if x == True: ... else: if x == Unknown: ... else: ...`) can functionally mirror tripartite runtime dispatch, but loses compiler-enforced exhaustiveness (omitting `Unknown` is accepted silently without compiler errors).

> **Core Guarantee Boundary**: XoXLang prevents implicit loss of `Unknown` and guarantees exhaustive handling strictly under direct `XoX` control (`if`/`xen`/`else`). Derived `Bool` control is fully valid for explicit binary partitioning, but its logical exhaustiveness is governed by developer-authored structure.

## 11. Explicit Unknown Ignore Mechanism

### Contextual Keyword Status & Disambiguation Precedence
- **Soft / Contextual Keyword**: `ignore` is a contextual (soft) keyword, not a globally reserved keyword.
- **Syntactic Disambiguation Precedence**: An isolated standalone identifier token spelled `ignore`, when it appears as the direct and sole body statement of a `xen` clause (either in block form or in compact single-line form `xen: ignore`), is **always** parsed and interpreted as the contextual `IgnoreStatement`.
- **Precedence over Identifier Resolution**: This contextual interpretation strictly takes precedence over resolving a variable or expression-statement named `ignore`. `xen: ignore` cannot be used to evaluate an in-scope variable named `ignore` as a standalone expression.
- **Ordinary Identifier Status Everywhere Else**: A variable, function, parameter, attribute, or member named `ignore` remains completely valid everywhere else. Syntactic uses such as `print(ignore)`, `value = ignore`, `object.ignore`, and `ignore()` are parsed as ordinary identifier references according to standard expression syntax.
- **Deterministic Symbol-Table-Free Parsing**: Distinguishing `IgnoreStatement` from an ordinary identifier requires zero symbol-table lookup or scope awareness; it is determined purely by the local syntactic position in a `xen` clause (`xen:\n    ignore` or `xen: ignore`).
- **Lexer Independence**: The lexer does not need to emit a globally reserved `IGNORE` token.

### Dual Syntactic Forms & Semantic Equivalence
The explicit ignore mechanism for `Unknown` provides two strictly equivalent syntactic forms:
1. **Multi-Line Block Form**:
   ```text
   if <XoX-expression>:
       <True-block>
   xen:
       ignore
   else:
       <False-block>
   ```
2. **Compact Single-Line Form**:
   ```text
   if <XoX-expression>:
       <True-block>
   xen: ignore
   else:
       <False-block>
   ```
- **Strict Syntactic Sugar**: The compact single-line form `xen: ignore` is purely syntactic sugar for the block form `xen:\n    ignore`.
- **Identical AST Normalization**: Both syntactic forms parse and normalize directly to the exact same AST representation: a `ConditionalStatement` with `xen_branch` containing `IgnoreStatement`. Zero new AST node types are introduced.
- **Strict Grammar Restriction**: The production `XenIgnoreClause ::= 'xen' ':' 'ignore'` is the sole authorized compact inline form under `xen:`. Any other inline statement or sequence (e.g. `xen: foo()`, `xen: ignore; foo()`, `xen: pass`) is strictly forbidden and rejected at parse time with `SyntaxError` (CTX-XEN-INLINE-02, CTX-XEN-INLINE-03).
- **Contextual Exclusivity**: `ignore` used outside the `xen:` context is invalid as a standalone keyword/statement (CTX-XEN-INLINE-04).
- **Operational Trace & Attachment Invariance**: The compact form preserves byte-for-byte the operational trace, lazy evaluation, `else` attachment, and static Phase 3 exhaustiveness rules of the block form (CTX-XEN-INLINE-01, CTX-XEN-INLINE-05).
- **Exclusive Atomic Form**: `xen: ignore` is an exclusive atomic form representing an explicitly acknowledged `Unknown` branch with no user action.
- **Sole Statement Invariant**: When `ignore` is used as the `xen` branch body, it must be the sole and exclusive statement in that `xen` clause.
- **Prohibition of Coexistence (SyntaxError)**: A `xen` clause containing `ignore` alongside any additional statement (e.g. `ignore` followed or preceded by another statement, or `xen: ignore; stmt`) is structurally invalid and must produce a `SyntaxError`.
- **Exhaustiveness Satisfaction**: Using `xen: ignore` satisfies the exhaustiveness requirement for `XoX`.
- **No Coercion / Mutation**: `ignore` does not convert `Unknown` to `True` or `False`, nor does it mutate the underlying `XoX` value.
- **Not Else**: `ignore` is not equivalent to `else`.
- **Mandatory Clause**: Omission of `xen` remains strictly invalid for `XoX` conditionals; the `xen:` clause must be written explicitly.
- **Scope Restriction**: The contextual `ignore` construct is conceptually restricted to the `Unknown` (`xen:`) branch context.

### Semantic Distinction: pass vs ignore
- **Canonical Exclusive No-Op**: `xen: ignore` is the only canonical explicit no-op form for acknowledging `Unknown` without executing user action. `xen: ignore` is an exclusive atomic construct and cannot coexist with other statements.
- **Validity of Ordinary `pass`**: Ordinary `pass` remains a normal no-op statement inside standard statement blocks throughout the language, including within multi-statement `xen` blocks.
- **Prohibition of All-`pass` `xen` Clauses (SyntaxError)**: A `xen` branch containing only one or more `pass` statements (with no effective non-pass statement) is invalid and must use `xen: ignore` instead. Attempting to use `xen: pass` or repeated `pass` statements as the sole body of a `xen` clause produces a `SyntaxError`.
- **Multi-Statement `xen` Blocks with Effective Action**: A `xen` block containing at least one effective (non-pass) statement may freely contain `pass` statements without error. For example, both `audit(); pass` and `pass; audit()` are completely valid `xen` blocks when `audit()` represents an effective statement.
- **Language-Level Semantic Meaning**: While `pass` and `ignore` share equivalent runtime no-op execution behavior, they intentionally carry distinct language-level meanings:
  - `ignore` records an explicit, deliberate architectural decision to acknowledge the `Unknown` state and consciously leave it without action.
  - `pass` is a generic syntactical placeholder for empty blocks and cannot silently serve as an alias for `ignore`.

### Definite-Return Semantics & Value-Returning Functions
- **No Synthesized Return Values**: `xen: ignore` performs no user action and does not synthesize, infer, or return any value (no implicit `None`, zero, false, or default values).
- **Separation of Exhaustiveness and Definite Return**: `XoX` branch exhaustiveness and function return-path completeness are distinct, independent semantic properties:
  - Satisfying branch exhaustiveness via `xen: ignore` does not satisfy value-return completeness for a function.
- **Reachability and Non-Terminal Behavior**: `xen: ignore` is not a terminal control-flow statement. Execution falls through past the `xen:` clause to subsequent statements in the enclosing block.
- **Definite-Return Analysis**: A function with a declared return type must return a compatible value on every reachable terminal execution path, evaluated via control-flow reachability analysis rather than branch syntax inspection alone.
- **Static Invalidation (MissingReturnError)**: If an `Unknown` path executes `xen: ignore` and can reach the end of a value-returning function without an explicit return statement (or terminal statement), the function is statically invalid and raises a `MissingReturnError`.
- **Subsequent Returns**: A return statement placed after the `if` / `xen` / `else` construct validly satisfies the return requirement for the `Unknown` path following `xen: ignore`.

## 12. Program and Conditional Grammar

### Concrete Parser Grammar (EBNF)
The concrete parser grammar recognizes function definitions, statement-level constructs, simple statements (including variable bindings, value returns, and reassignment), and generic conditional structures parameterized by a generic `Expression` non-terminal, without evaluating or requiring type information during parsing:
```ebnf
Statement            ::= FunctionDefinition | ConditionalStatement | SimpleStatement ;

FunctionDefinition   ::= "fn" Identifier "(" ParameterList? ")" ReturnAnnotation? ":" Block ;
ParameterList        ::= Parameter ( "," Parameter )* ;
Parameter            ::= Identifier ":" TypeName ;
ReturnAnnotation     ::= "->" TypeName ;

SimpleStatement      ::= AssignmentStatement | ReturnStatement | ExpressionStatement | PassStatement ;

AssignmentStatement  ::= Identifier "=" Expression
                       | Identifier ":" TypeName "=" Expression ;

ReturnStatement      ::= "return" Expression ;

TypeName             ::= "Bool" | "XoX" ;

ExpressionStatement  ::= Expression ;
PassStatement        ::= "pass" ;

ConditionalStatement ::= "if" Expression ":" Block
                         ( "xen" ":" XenBlock )?
                         ( "else" ":" Block )? ;

XenBlock             ::= Block | XenIgnoreClause ;
XenIgnoreClause      ::= "ignore" ;

Expression           ::= InlineConditional ;
InlineConditional    ::= LogicalOr ( "if" LogicalOr ( "xen" LogicalOr "else" | "else" ) InlineConditional )? ;
LogicalOr            ::= LogicalAnd ( "OR" LogicalAnd )* ;
LogicalAnd           ::= EqualityExpr ( "AND" EqualityExpr )* ;
EqualityExpr         ::= UnaryExpr ( ( "==" | "!=" ) UnaryExpr )? ;
UnaryExpr            ::= "NOT" UnaryExpr | PostfixExpr ;
PostfixExpr          ::= PrimaryExpr ( "." "unwrap_or" "(" Expression ")" )* ;
PrimaryExpr          ::= Identifier | Literal | "(" Expression ")" | "xox" "(" Expression ")" ;
Literal              ::= "True" | "False" | "Unknown" ;
```

### Parser Invariants
- **Type-Agnostic Parsing**: The parser processes expressions and conditions solely as generic `Expression` nodes and does not determine whether an expression evaluates to `Bool`, `XoX`, or any other type.
- **Single Production**: There are no separate grammar productions for Bool versus XoX conditionals at parse time.
- **Compact and Block `xen: ignore` Syntax**:
  - `xen: ignore` is parsed either directly on the same line (`xen: ignore`) or as an indented block (`xen:\n    ignore`).
  - Both forms normalize directly to the same `IgnoreStatement` node assigned to `ConditionalStatement.xen_branch`.
  - The grammar strictly restricts compact inline `xen` clauses to `XenIgnoreClause ::= 'xen' ':' 'ignore'`. Any other inline statement suite under `xen:` (such as `xen: foo()` or `xen: ignore; foo()`) is strictly prohibited and produces a `SyntaxError` at parse time (CTX-XEN-INLINE-02, CTX-XEN-INLINE-03).
- **Explicit Collapse Syntax (`x.unwrap_or(default_expr)`)**:
  - The parser recognizes `.unwrap_or(default_expr)` postfix invocation on primary expressions.
  - The fallback argument is **mandatory**; omitting the argument (`x.unwrap_or()`) is a static `SyntaxError` / `ParseError` (CTX-COLLAPSE-06).
  - General method invocation (`x.method()`) or arbitrary attribute accesses are not part of the language grammar; `unwrap_or` is recognized exclusively as the flow-control collapse primitive.
  - No alternative `??` or coalesce operator syntax is permitted.
- **Function Definition and Parameter Syntax**:
  - `fn` introduces function definitions (`FunctionDefinition ::= "fn" Identifier "(" ParameterList? ")" ReturnAnnotation? ":" Block`).
  - **Explicitly Typed Parameters**: In V1, all function parameters must be explicitly typed (`Identifier ":" TypeName`) using the closed truth-type set `Bool` or `XoX`. Untyped parameters are not supported in V1.
  - **Syntactically Optional Return Annotation**: The return annotation `-> TypeName` is syntactically optional in the grammar and restricted to `Bool` or `XoX`. Semantic analysis enforces that any function returning `XoX` must explicitly declare `-> XoX` (§19).
  - **Value-Return Statements**: `ReturnStatement ::= "return" Expression`. Bare `return` without an expression is not supported in this initial truth-type prototype.
  - **Scope and Function Limitations in V1**: Function-call syntax, recursion, closures, default parameters, variadic parameters, keyword arguments, generics, overloads, higher-order functions, and nested functions are not defined or supported in the initial V1 prototype grammar.
- **Variable Binding and Reassignment Syntax**:
  - Inferred binding: `Identifier "=" Expression` (e.g. `flag = True`).
  - Annotated initialized binding: `Identifier ":" TypeName "=" Expression` (e.g. `status: XoX = True`).
  - Reassignment: uses the identical `Identifier "=" Expression` syntax when the identifier is already bound in the static environment.
  - **Declaration vs Reassignment**: Distinguishing a new variable declaration from a reassignment is performed strictly during semantic analysis via symbol-table lookup, not during parsing or lexing.
  - **Prohibition of Uninitialized Declarations (SyntaxError)**: Variable declarations without an explicit initializer (such as `x: XoX` or `x: Bool`) are not supported in V1 and produce a `SyntaxError`. Requiring immediate initialization guarantees that uninitialized variable states and complex definite-assignment analysis are not introduced into the initial prototype.
- **Structural Ordering**: When present, conditional clauses must appear in strict canonical sequence: `if`, then `xen`, then `else`. `xen` cannot precede `if`, and `else` cannot precede `xen`.
- **No Duplicate Clauses**: Duplicate `if`, `xen`, or `else` clauses within the same conditional construct are syntactically invalid (`SyntaxError`).
- **Exclusive Atomic Unknown Body**: `xen: ignore` is parsed as an exclusive atomic `XenBlock` via contextual soft-keyword matching without symbol-table lookup. `ignore` cannot coexist with other statements in the same `xen` block (`SyntaxError`).
- **No `pass`-Only `xen` Blocks**: A `xen` clause containing only one or more `pass` statements without effective logic cannot silently alias `ignore` and is invalid (`SyntaxError`). Multi-statement `xen` blocks containing effective statements may contain `pass`.
- **No `elif` in Initial Grammar (SyntaxError)**: `elif` is not supported in the initial language grammar for either `Bool` or `XoX` conditionals. Any appearance of `elif` produces a `SyntaxError`.
- **Multi-Branch Bool Control Flow**: Multi-branch `Bool` branching must be expressed explicitly using nested `if` statements inside `else` blocks (`if ...: ... else: if ...: ...`).
- **XoX Ternary Invariant**: `XoX` conditionals remain strictly ternary using `if` / `xen` / `else`. `elif` must never be used to represent the `Unknown` state.
- **Independent Nesting**: Nested conditionals are parsed independently under the same generic production.

### Post-Type Semantic Classification
- **Post-Parsing Type Resolution**: The `condition` expression is type-checked and resolved during semantic analysis following AST construction.
- **Semantic Classifications**: `BoolConditional` and `XoXConditional` are post-type semantic classifications, not concrete grammar productions:
  - **`BoolConditional`**: A `ConditionalStatement` whose condition resolves to type `Bool`. Semantic validation enforces that `xen` is absent (presence of `xen` emits `TypeError`).
  - **`XoXConditional`**: A `ConditionalStatement` whose condition resolves to type `XoX`. A `XoX` condition is fully valid; semantic validation enforces exhaustiveness (both `xen`—or `xen: ignore`—and `else` must be present; omission emits `ExhaustivenessError`).
- **Diagnostic Precedence Alignment**: This separation guarantees that syntax errors are identified in Phase 1 without type checking, type admissibility is validated in Phase 2, and exhaustiveness coverage is verified in Phase 3.

## 13. Static Diagnostic Requirements

### Diagnostic Resolution Precedence
Diagnostics are resolved through a deterministic four-phase pipeline:
1. **Phase 1: SyntaxError (Structural Validity)**
   - Emitted when source code violates grammar or structural invariants (e.g. duplicate branch declarations, invalid clause ordering, orphan `xen` or `else` without `if`, non-exclusive `xen: ignore`, illegal inline xen statements like `xen: foo()`, compound inline statements like `xen: ignore; foo()`, all-`pass` `xen` blocks, use of `elif`, or an attempted contextual `ignore` construct outside `xen:`).
2. **Phase 2: TypeError (Type Admissibility)**
   - Emitted after condition type resolution when an inadmissible type or incompatible keyword is used.
   - If the condition resolves to `Bool` and a `xen` clause is present $\rightarrow$ `TypeError` (`xen` is invalid for binary `Bool` conditions).
   - If an expression is neither `Bool` nor `XoX`, or if implicit coercion is attempted $\rightarrow$ `TypeError`.
3. **Phase 3: ExhaustivenessError (Exhaustive Semantic Coverage)**
   - Emitted when a syntactically valid conditional with an admissible condition type fails to account for all required semantic states.
   - If the condition resolves to `XoX` and lacks a `xen` clause (via statement block, `xen:\n    ignore`, or compact `xen: ignore`), or lacks an `else` clause $\rightarrow$ `ExhaustivenessError` (never `TypeError`). Both block and compact ignore forms satisfy Phase 3 exhaustiveness identically.
4. **Phase 4: MissingReturnError (Definite-Return Completeness)**
   - Emitted when control-flow reachability analysis determines that a function with a declared return type has reachable terminal paths (e.g. falling through `xen: ignore` or `xen:\n    ignore`) that fail to return a compatible value.

### Diagnostic Structure & 5W+H Reasoning Contract
The 5W+H (Who, What, When, Where, Why, How) framework serves as the compiler's internal diagnostic reasoning and completeness model, **not** a mandatory six-label user-facing terminal layout. Every diagnostic must be rooted in this internal contract:
1. **WHO**: Identify the exact construct, operand, branch, variable, function, or value involved.
2. **WHAT**: Identify the concrete rule or contract violation (concise primary problem statement).
3. **WHEN**: Identify when the relevant semantic rule or execution condition matters (e.g. at runtime evaluation, branch dispatch, or short-circuit evaluation).
4. **WHERE**: Identify the exact source span, providing file, line, column, source excerpt, and visual caret annotation when available.
5. **WHY**: Explain the relevant XoXLang semantic rule in plain English when that explanation materially helps.
6. **HOW**: Determine safe corrective actions without guessing developer intent.

### Adaptive User-Facing Diagnostic Rendering
User-facing diagnostics must render adaptively as `source span/location + concise error + optional semantic context + action`. Diagnostic complexity must scale with problem complexity, ensuring that the compiler understands the full problem, explains only what is useful, and never chooses semantics on the developer's behalf:
- **`WHERE` $\rightarrow$ Source Span**: Line, column, source excerpt, and caret indicator when source-span information is available.
- **`WHAT` $\rightarrow$ Primary Error**: Concise, direct problem statement.
- **`WHO` $\rightarrow$ Operand/Type Context**: Concrete operand, type, or construct annotations included only when they improve clarity.
- **`WHY` & `WHEN` $\rightarrow$ Semantic Context**: Short contextual notes included only when they materially help explain XoX semantics (e.g. `Unknown`, `xen`, `xox(...)`, `.unwrap_or(...)`, or short-circuit evaluation).
- **`HOW` $\rightarrow$ Actionable Guidance**: Actionable remediation distinguishing deterministic fixes from intent-dependent choices.

#### Adaptive Complexity Levels
- **Simple Syntax Errors**: Location + concise error + deterministic fix when obvious. No unnecessary semantic explanation.
- **Type-Boundary Errors**: Location + concise error + actual involved types or operands + help or alternatives.
- **XoX Semantic Invariant Errors**: Location + concise error + short semantic context explaining `Unknown`/`XoX` behavior + help or alternatives.

### Action Policy: Deterministic Help vs. Intent-Dependent Alternatives
- **`help`**: Permitted strictly when the compiler knows a deterministic, semantics-preserving correction and does not need to infer developer intent.
- **`alternatives`**: Required when multiple valid corrections exist and the correct choice depends on developer intent or domain policy.
- **Compiler Intent Neutrality**: The compiler must never choose semantic policy on behalf of the developer, nor present speculative fixes as certain.

### User-Facing Diagnostic UX Standard (LOCKED_ADVERSARIAL_SPEC)
- **Authority Matrix**: User-facing compiler and runtime diagnostic messages are formally governed by `experiments/DIAGNOSTIC_UX_COUNTEREXAMPLES.md` (`LOCKED_ADVERSARIAL_SPEC`). All constraints across `CTX-DIAG-01` through `CTX-DIAG-12` are mandatory conformance constraints.
- **Internal Exception Taxonomy**: Internal exception classes (`LexerError`, `ParseError`, `TypeDiagnosticError`, `ExhaustivenessError`, `MissingReturnError`, `TypeError`, `UnknownValueError`) remain technical implementation details and are strictly invariant.
- **Plain-English Problem Explanation**: User-facing message strings must explain the developer's actual problem directly in plain English without exposing compiler internals.
- **Prohibited Jargon & Phrasing**:
  - Raw `TokenKind` enum names (e.g. `RPAREN`, `IDENTIFIER`, `LPAREN`, `EOF`) must never be leaked to the developer; punctuation and tokens must be described in plain terms (e.g. `')'`, `'('`, `parameter name`).
  - AST node class names (e.g. `Program AST node`, `Statement`, `Expression`) and compiler pipeline phase numbers (e.g. `Phase 2`, `Phase 3`, `Phase 4`) must not appear in user messages.
  - Language versioning milestones and historical tags (e.g. `in V1`, `in V1 grammar`, `in V1 lexical core`) are strictly prohibited in error messages.
  - Mechanically displaying raw `WHO`/`WHAT`/`WHEN`/`WHERE`/`WHY`/`HOW` labels for every error.
  - Verbose tutorial-style explanations for trivial errors, or paternalistic / conversational filler.
- **Deterministic Actionable Guidance & Semantic Integrity**:
  - Diagnostics must provide a concise corrective hint whenever the resolution is deterministic (`help`), and present non-speculative choices when intent-dependent (`alternatives`).
  - Domain conversions must exclusively guide the developer using canonical language surface syntax: `xox(expr)` for Bool-to-XoX promotion and `.unwrap_or(default_bool)` for XoX-to-Bool collapse.
  - Guiding developers toward obsolete runtime helper methods such as `XoX.from_bool` is strictly forbidden.
  - Unhandled uncertainty in conditionals must guide developers toward adding `xen` or `xen: ignore`.
  - Diagnostics must never describe a rule more narrowly than the actual type system enforces (e.g. claiming `unwrap_or` requires a literal Bool when any valid Bool expression is accepted).
  - All code examples and snippets presented within diagnostics must themselves be valid canonical XoXLang.
- **Mandatory Adversarial Matrix (`CTX-DIAG-01` through `CTX-DIAG-12`)**:
  - **CTX-DIAG-01**: Jargon-free syntax and token expectation messages.
  - **CTX-DIAG-02**: Canonical promotion guidance (`xox(...)`) for mixed domain operations.
  - **CTX-DIAG-03**: Actionable guidance for `unwrap_or` collapses (`source: XoX`, `fallback: Bool`).
  - **CTX-DIAG-04**: Actionable exhaustiveness and `xen: ignore` guidance.
  - **CTX-DIAG-05**: Non-versioning grammar error messages.
  - **CTX-DIAG-06**: Problem-oriented definite-return diagnostics.
  - **CTX-DIAG-07**: Concise rendering for simple syntax errors without tutorial filler.
  - **CTX-DIAG-08**: Contextual WHEN/WHY explanations for non-obvious XoX semantic invariants.
  - **CTX-DIAG-09**: Deterministic semantics-preserving single corrections exposed exclusively as `help`.
  - **CTX-DIAG-10**: Intent-dependent corrections exposed exclusively as non-speculative `alternatives`.
  - **CTX-DIAG-11**: Accurate semantic scope in error messages without artificial rule narrowing (e.g. Bool expressions in `unwrap_or`).
  - **CTX-DIAG-12**: Full syntactic validity of all code examples and suggested snippets shown in diagnostics.
- **Fail-Closed Safety Discipline**: Enhancing diagnostic UX, human-readable explanations, and adaptive phrasing must strictly preserve all static rejection rules, type safety boundaries, and exhaustiveness requirements without weakening fail-closed compiler invariants.

### Canonical Diagnostic Categories

| Diagnostic Context | Category | Violated Rule | Description |
|---|---|---|---|
| `xen` with `Bool` condition | `TypeError` | §5, §6, §12 | `xen` branch is invalid on binary `Bool` conditions. |
| Missing `xen` branch on `XoX` | `ExhaustivenessError` | §5, §10 | `XoX` conditional must handle `Unknown` explicitly via `xen:` block or `xen: ignore`. |
| Missing `else` branch on `XoX` | `ExhaustivenessError` | §10, §12 | `XoX` conditional must declare an `else` (`False`) branch. |
| Reachable path without return | `MissingReturnError` | §11, §19 | Function with declared return type has reachable execution paths (e.g. falling through `xen: ignore`) that terminate without returning a value. |
| Duplicate branches (`if`/`xen`/`else`) | `SyntaxError` | §10, §12 | Duplicate branch declarations in the same conditional are forbidden. |
| Invalid branch ordering | `SyntaxError` | §9, §10, §12 | `XoX` branches must strictly follow canonical sequence `if`, `xen`, `else`. |
| Orphan `xen` branch | `SyntaxError` | §9, §12 | `xen` clause encountered without a preceding `if` block. |
| Orphan `else` branch | `SyntaxError` | §9, §12 | `else` clause encountered without a preceding `if` block. |
| Non-exclusive `xen: ignore` | `SyntaxError` | §11, §12 | `xen: ignore` is an exclusive atomic form; `ignore` cannot coexist with other statements in a `xen` clause. |
| Illegal inline `xen` statement | `SyntaxError` | §11, §12 | Inline `xen:` only permits `xen: ignore`; general forms such as `xen: foo()` are forbidden (CTX-XEN-INLINE-02). |
| Compound inline `xen` statement | `SyntaxError` | §11, §12 | Semicolon chaining or compound statements in compact `xen` (e.g. `xen: ignore; foo()`) are forbidden (CTX-XEN-INLINE-03). |
| `xen` clause with only `pass` | `SyntaxError` | §11, §12 | `xen` branch containing only `pass` statements is invalid; explicit no-op handling of `Unknown` requires `xen: ignore`. Multi-statement `xen` blocks with effective logic may contain `pass`. |
| Use of `elif` keyword | `SyntaxError` | §12, §21 | `elif` is not part of the initial language grammar; multi-branch Bool conditionals must use nested `if` in `else`, and XoX conditionals strictly use `if`/`xen`/`else`. |
| Implicit XoX-to-Bool coercion | `TypeError` | §3, §6, §19 | Cannot evaluate or assign `XoX` where `Bool` is expected without explicit handling or conversion. |
| Unannotated XoX return | `TypeError` | §16, §18, §19 | Returning any expression of resolved type `XoX` (e.g. `Unknown`, `XoX` variable, `XoX` call, `XoX` logical op) requires an explicit `-> XoX` return annotation; implicit return inference is forbidden. |
| Mixed Bool/XoX logical operation | `TypeError` | §7, §19 | Logical operations between mixed `Bool` and `XoX` operands are invalid without explicit conversion. |
| Mixed Bool/XoX equality comparison | `TypeError` | §8, §19 | Equality (`==`) and inequality (`!=`) comparisons between mixed `Bool` and `XoX` operands are invalid without explicit conversion. |
| Arithmetic / bitwise on Bool or XoX | `TypeError` | §3, §19 | Arithmetic (`+`, `-`, `*`, `/`, `%`) and bitwise (`&`, `|`, `^`, `~`, `<<`, `>>`) operators are forbidden on `Bool` and `XoX`. |
| Ordering comparison on Bool or XoX | `TypeError` | §3, §19 | Ordering comparisons (`<`, `<=`, `>`, `>=`) are forbidden on `Bool` and `XoX`. |
| Misplaced contextual `ignore` | `SyntaxError` | §11, §12 | Attempted contextual `ignore` construct used outside the permitted `xen:` (`Unknown`) branch context (ordinary identifier uses of `ignore` elsewhere remain valid; CTX-XEN-INLINE-04). |
| Missing fallback in `unwrap_or` | `SyntaxError` | §12, §19 | `unwrap_or` requires an explicit fallback argument; bare `x.unwrap_or()` is forbidden (CTX-COLLAPSE-06). |
| `unwrap_or` on non-`XoX` source | `TypeError` | §3, §19 | `unwrap_or` source must be statically typed `XoX`; invoking on `Bool` is forbidden (CTX-COLLAPSE-05). |
| Non-`Bool` fallback in `unwrap_or` | `TypeError` | §3, §19 | `unwrap_or` fallback must be statically typed `Bool`; passing `XoX` or `Unknown` is forbidden (CTX-COLLAPSE-04). |

## 14. Conceptual AST Requirements

### Generic Conditional Node Structure
A conceptual AST node for conditionals must contain:
- `condition`: Expression node producing a condition value.
- `true_branch`: Statement / block executed on `True`.
- `unknown_branch`: Optional statement / block executed on `Unknown` (or an explicit `IgnoreStatement` marker).
- `false_branch`: Optional statement / block executed on `False`.

### Type-Specific Structural Invariants
- **Bool Conditional AST**:
  - Contains `condition`, `true_branch`, and optionally `false_branch`.
  - Must never contain an `unknown_branch`.
- **XoX Conditional AST**:
  - Contains `condition`, `true_branch`, `unknown_branch`, and `false_branch`.
  - The `unknown_branch` holds either a statement `Block` or the canonical `IgnoreStatement` marker node.
  - **AST Normalization Equivalence**: Both the block form `xen:\n    ignore` and the compact single-line form `xen: ignore` normalize directly to the exact same `IgnoreStatement` AST node in `unknown_branch`. No separate AST node type or wrapper is introduced.

### Metadata & Semantic Rules
- **Source Span Preservation**: AST nodes must preserve exact source spans for the condition expression and every branch keyword (`if`, `xen`, `else`, `ignore`).
- **Post-Resolution Differentiation**: Semantic analysis must clearly distinguish `Bool` and `XoX` conditionals after type resolution to perform exhaustiveness and branch legality checks.
- **Conversion & Collapse Nodes**:
  - `PromoteBoolToXoX(expr)`: AST node representing explicit promotion `xox(expr)`.
  - `CollapseXoXToBoolWithDefault(source, fallback)`: AST node representing explicit collapse `x.unwrap_or(default_bool)`. Contains `source` (expression of type `XoX`) and `fallback` (expression of type `Bool`), with fixed result type `Bool`. It is a dedicated flow-control node, never desugared into a generic `MethodCall`.
- **Implementation Neutrality**: The AST structure is an abstract conceptual model and must not encode runtime representations, memory layouts, or byte-level `XoX` encodings.

## 15. Python Lowering Semantics

### Dispatch and Evaluation Strategy (Prototype Canonical)
- **Single Evaluation & Hygienic Temporary**: Every `XoX` conditional expression is evaluated exactly once at runtime. The resulting value is bound to a hygienic compiler-generated temporary variable whose identifier is guaranteed never to collide with user identifiers.
- **Explicit Identity Dispatch**: Lowering generates an explicit identity-based three-way dispatch against singleton `XoX` states (`TRUE`, `UNKNOWN`, and `FALSE`), canonically evaluating in the order: `TRUE`, then `UNKNOWN`, then `FALSE`.
- **Strict Anti-Coercion**: Lowering must never rely on Python `bool()`, truthiness coercion, or bare `if <xox_temp>:` branches for `XoX` dispatch.
- **Branch Semantic Fidelity**:
  - `if` $\rightarrow$ executed when `<xox_temp> is XoX.TRUE`.
  - `xen` $\rightarrow$ executed when `<xox_temp> is XoX.UNKNOWN`.
  - `else` $\rightarrow$ executed when `<xox_temp> is XoX.FALSE`.
- **Ignore Lowering**: `xen: ignore` lowers to an explicit no-op (e.g. `pass`) within the `Unknown` dispatch branch.
- **Fail-Closed Runtime Validation**: If the evaluated value is not a valid `XoX` state at runtime, lowering must fail explicitly (e.g., raise an internal runtime error) rather than falling through silently.
- **Bool Lowering**: Ordinary `Bool` conditionals lower directly to standard Python `if` / `else` control-flow statements without intermediate `XoX` wrapping.
- **Source Map Preservation**: Lowering maintains source span mappings so diagnostics refer back accurately to the original source positions.
- **Scope of Strategy**: This explicit identity-dispatch model is the canonical lowering strategy for the initial Python prototype; it does not freeze or restrict future native backends.

### Python Prototype Runtime Representation
- **Standard Python Enum Model**: The three runtime `XoX` states are represented as singleton members of a standard Python `Enum` (`XoX.FALSE`, `XoX.TRUE`, `XoX.UNKNOWN`) or semantically equivalent non-numeric singleton representation.
- **Prohibition of IntEnum**: The runtime model must use standard `Enum` and strictly forbids `IntEnum` or any inheritance from `int`.
- **Internal Member Names**: The internal runtime enum members are named `FALSE`, `TRUE`, and `UNKNOWN` to avoid collisions with Python reserved keywords while keeping attribute names clear and deterministic.
- **Source-to-Runtime Mapping**: Source-language `True`, `False`, and `Unknown` literals and expressions map directly to runtime singletons (`XoX.TRUE`, `XoX.FALSE`, `XoX.UNKNOWN`) without modifying source-language syntax.
- **Identity Dispatch**: XoX runtime dispatch uses exact object identity checks (`is`) against the singleton members (`<xox_temp> is XoX.TRUE`, `<xox_temp> is XoX.UNKNOWN`, `<xox_temp> is XoX.FALSE`), guaranteeing $O(1)$ state determination without relying on value comparison or truthiness.
- **Strict Anti-Truthiness (`__bool__` Rejection)**: Python truthiness conversion of a runtime `XoX` value is strictly forbidden. The runtime `XoX` class must define `__bool__` to reject evaluation by raising a runtime `TypeError` (or dedicated internal runtime error), ensuring that constructs such as `bool(xox_val)` or bare Python `if xox_val:` fail closed immediately.
- **Isolation from Numeric / Bitwise / Ordering Behaviors**: The runtime representation must not inherit from `int` and must never expose arithmetic (`+`, `-`), bitwise (`&`, `|`), or relational ordering (`<`, `>`) operations on `XoX`.
- **Prototype-Only Scope & Non-Freezing of Native Layout**: Python `Enum` is an implementation choice strictly for the Python prototype. It is not normative for future native backends. Integer member values or internal enum payloads are private prototype details and are not frozen as part of any language ABI, byte layout (e.g. `0x00`, `0x01`, `0x02`), or native memory representation.

### Python Prototype Staged Compiler Architecture
- **Source-to-Source Model**: The initial prototype is architected as a source-to-source transpiler/compiler implemented in Python targeting standard Python, without modifying CPython internals.
- **Deterministic Staged Pipeline**: The prototype processes XoX source code through a sequence of discrete, deterministic phases with strict one-way data flow:
  1. **Lexing**: Tokenizes source text, tracking line and column source spans without emitting global soft keywords (e.g. `ignore`).
  2. **Parsing**: Constructs a type-agnostic generic AST according to §12 and §14 without performing type evaluation or symbol table lookup.
  3. **AST Construction**: Produces generic AST nodes with exact source spans intact across every node.
  4. **Type Resolution**: Performs bidirectional literal resolution (§18), expression type checking, and fixes static monomorphic types (§19).
  5. **Semantic Validation**: Classifies conditionals as `BoolConditional` or `XoXConditional` post-type (§12), enforcing branch legality (§13 Phase 2) and exhaustiveness (§13 Phase 3).
  6. **Definite-Return Analysis**: Performs reachability analysis on value-returning functions (§11, §13 Phase 4, §19).
  7. **Python Lowering**: Lowers fully validated, typed AST structures into valid target Python code using canonical three-way identity dispatch (§15).
  8. **Generated Execution**: Executes lowered Python code against the prototype runtime module.
- **One-Way Architectural Dependencies**:
  - Later stages consume representations from earlier stages; earlier stages must not import or depend on lowering logic or runtime behavior.
  - Lowering is strictly a backend emission phase that consumes validated typed semantics; it must never invent language semantics or make typing decisions.
  - Runtime representation (`XoX` enum) is isolated from parser, AST, type-checker, diagnostics, and lowering modules.
- **Fail-Closed Phase Precedence**: Each phase fails closed on the earliest authoritative diagnostic (§13) and never attempts implicit error correction or heuristic guessing.
- **Span Preservation**: Source-span information (file, line, column start/end) must survive all compiler stages to guarantee precise diagnostic reporting.
- **Standard Library Preference**: The prototype relies on the Python standard library, avoiding external dependencies or parser-generator frameworks. Exact module, file, class, and package structures remain flexible implementation details adhering to these stage boundaries.

## 16. XoX Usage Discipline
- **Default vs Opt-In**: `Bool` is the default truth type for determinate propositions. `XoX` is strictly an opt-in type, used only when `Unknown` is a meaningful domain state.
- **No Speculative Use**: `XoX` must not be used merely for speculative future extensibility or syntax convenience.
- **No Replacement for Determinate Propositions**: `XoX` must not replace ordinary `Bool` when a proposition is fully determinable.
- **Explicit Return Signatures**: Functions and APIs that can return `XoX` must declare that return type explicitly.
- **Not a Generic Option/Nullable Type**: `XoX` is not a generic replacement for nullable values or `Option<Bool>`.
- **Epistemic vs Storage Absence**: `Unknown` represents uncertainty or lack of knowledge regarding truth, not the simple absence of stored data or an uninitialized memory slot.
- **Core Conceptual Distinction**:
  - `Bool` represents **truth values** directly (`True` or `False`).
  - `XoX` represents **knowledge states about a truth value** (`True`, `False`, or `Unknown`).

## 17. Xen Keyword Rationale

### Role Separation: Keyword vs Data Value
`xen` is strictly a control-flow keyword designated for handling the `XoX` `Unknown` branch. `Unknown` remains the actual `XoX` data value. `xen` is not an alias for `Unknown` and must never be used as a `XoX` value or expression literal.

### Primary Rationale: Ergonomics and Visual Differentiation
The primary justification for `xen` is its brevity, visual distinctiveness, compact structural fit beside `if` and `else`, and strong `i` / `x` / `e` scanning contrast. In visual flow, `if` (2 characters), `xen` (3 characters), and `else` (4 characters) produce a compact lexical sequence with distinct initial characters (`i`, `x`, `e`). These properties are design and ergonomic observations regarding syntactic shape and visual differentiation, rather than scientifically proven readability claims.

### Evaluated Alternatives
- **`unknown`**: Rejected because `Unknown` is already the semantic XoX data value name. The language design intentionally enforces a strict boundary between data values and control-flow keywords.
- **`maybe`**: Rejected because "maybe" suggests probability or possibility, whereas `Unknown` specifically represents epistemic uncertainty (insufficient information to establish `True` or `False`).
- **`so`**: Rejected because in ordinary English, "so" strongly suggests consequence or deduction ("therefore", "thus") rather than uncertainty.

### Known Cognitive Tradeoff: Compiler Disambiguation vs Human Recognition
The keyword choice introduces a recognized naming collision with the Xen Project hypervisor—a known cognitive tradeoff, particularly for systems and infrastructure developers:
- **Compiler Disambiguation**: To the compiler, `xen` is syntactically and positionally unambiguous because it is a reserved control-flow keyword accepted exclusively within the `xen` clause position of an `if` / `xen` / `else` construct.
- **Human Cognitive Recognition**: Compiler disambiguation and human cognitive recognition are distinct concerns. Developers familiar with the Xen Project may experience a brief first-contact mental association with the hypervisor.
- **Tradeoff Acceptance**: This tradeoff is deliberately accepted because the surrounding `if` / `xen` / `else` conditional structure is intended to make the control-flow role rapidly apparent after initial exposure (without claiming that cognitive friction is entirely eliminated or empirically proven to disappear).

### Secondary Mnemonic Note
As a secondary mnemonic observation, `xen` draws loose inspiration from the *xen-* / *xenos* root associated with the foreign, unfamiliar, or outside known bounds. This is strictly a mnemonic association; *xenos* does not literally mean "Unknown".

## 18. Literal Type Resolution

### Context-Sensitive Truth Literals
The literals `True` and `False` are context-sensitive truth literals capable of directly constructing either `Bool` or `XoX` values depending on expected-type context:
- **Default Inference**: When no expected type information is available from surrounding context and no typed operand constrains the expression, `True` and `False` infer `Bool` (`Bool` remains the default truth type).
- **XoX Contextual Construction**: When the surrounding type context explicitly expects `XoX`, `True` and `False` construct `XoX.True` and `XoX.False` directly.
- **Intrinsic XoX Type Anchor of `Unknown`**: `Unknown` is exclusively and intrinsically a `XoX` literal/value (never `Bool`). Inside expressions, `Unknown` acts as a strong `XoX` type anchor.

### Valid Sources of Literal Context
The compiler propagates expected-type context to uncommitted `True` and `False` literals from the following structural sources:
1. **Variable Annotations**: An explicit type annotation forces literals directly (e.g., `x: Bool = True` $\rightarrow$ `Bool.True`; `y: XoX = True` $\rightarrow$ `XoX.True`).
2. **Function Return Types**: A function's declared return type provides the expected-type context for return expressions (e.g. `fn f() -> XoX: return True` constructs `XoX.True`).
3. **Function Parameter Types**: When calling a function, parameter type declarations provide expected-type context for literal arguments (e.g., passing `True` to a parameter typed `XoX` constructs `XoX.True`; passing to `Bool` constructs `Bool.True`).
4. **Typed Binary Operator Operands & Unknown Anchor**: In binary operations (`AND`, `OR`, `==`, `!=`), an already-typed operand or an `Unknown` literal provides expected-type context to uncommitted literal operands:
   - In `my_xox AND True`, the typed `XoX` operand provides `XoX` context, resolving `True` directly as `XoX.True` (evaluating as `XoX`).
   - In `Unknown AND True`, the `Unknown` anchor resolves `True` directly as `XoX.True` (typed as `XoX AND XoX` returning `XoX`).
   - In `True OR Unknown`, `Unknown` anchors the expression in the `XoX` domain, resolving `True` as `XoX.True` (typed as `XoX OR XoX` returning `XoX`).
   - In `True == Unknown`, `Unknown` acts as a strong `XoX` anchor in equality, resolving the uncommitted literal `True` directly as `XoX.True`; the operation evaluates as `XoX.True == XoX.Unknown` and returns `Bool False` under exact state-identity equality (§8).
   - In `False == Unknown`, `False` resolves as `XoX.False`, evaluating as `XoX.False == XoX.Unknown` and returning `Bool False` (`False != Unknown` returns `Bool True`).
   - In `my_bool AND True`, the typed `Bool` operand provides `Bool` context, resolving `True` directly as `Bool.True` (evaluating as `Bool`).
   - **Traversal Order Invariance**: Syntactic traversal order must not cause an uncommitted `True` or `False` literal to be prematurely fixed as `Bool` before the full expression's domain constraints are resolved.
5. **Unary NOT Context**: Unary `NOT` propagates its expected result domain to an unresolved `True` or `False` operand when that expected type is known:
   - In `t: XoX = NOT True`, the outer `XoX` expected type propagates through `NOT`, causing `True` to resolve directly as `XoX.True` and `NOT` to evaluate and return `XoX.False`.
   - In a `Bool` context (or when unconstrained), `NOT True` resolves `True` as `Bool.True` and returns `Bool.False`.
   - `NOT` strictly preserves operand typing (`NOT Bool` $\rightarrow$ `Bool`, `NOT XoX` $\rightarrow$ `XoX`) and never retypes an already-typed `Bool` or `XoX` expression.
6. **Outer Compound Expression Context**: Expected type context propagates through compound logical expressions solely to resolve uncommitted `True` and `False` literals. For example, in `t: XoX = True AND False`, the outer `XoX` expectation propagates to both literals, resolving both as `XoX` values and typing the compound `AND` expression as `XoX`.
7. **Inline Conditional Branches**: In inline conditionals (`t if c else f` or `t if c xen u else f`), an expected-type context propagates to all branch expressions. When unconstrained by an outer type, if any branch contains an established `XoX` expression or an `Unknown` literal, it anchors the other uncommitted literal branches to `XoX` (e.g. in `True if cond xen Unknown else False`, `Unknown` anchors `True` and `False` to `XoX.True` and `XoX.False`, typing the expression as `XoX`).
8. **Collapse Fallback Context (`unwrap_or`)**: In `source.unwrap_or(fallback)`, the expected domain for `source` is `XoX`, and the expected domain for `fallback` is strictly `Bool`. An uncommitted literal `True` or `False` in `source` resolves directly to `XoX.True` or `XoX.False`, and an uncommitted literal `True` or `False` in `fallback` resolves directly to `Bool.True` or `Bool.False`. Passing the `Unknown` literal in `fallback` fails closed as a static `TypeError` because `Unknown` cannot inhabit `Bool` (CTX-COLLAPSE-04).

### Scope and Invariants of Literal Propagation
- **Limited Scope**: This mechanism is limited bidirectional contextual typing of uncommitted truth literals. It is not unrestricted implicit type conversion or general-purpose bidirectional inference.
- **Immutable Typed Expressions**: Already-typed expressions (variables, function calls, or sub-expressions with established static types) are never retyped or coerced by expected-type propagation.
- **Strict Anti-Coercion & TypeErrors Preserved**: Combining an already-typed `Bool` expression with an already-typed `XoX` expression (or with `Unknown`, e.g. `my_bool AND Unknown`, `my_bool == Unknown`, `Unknown != my_bool`) remains a static `TypeError` without explicit `xox(expr)` conversion (§19). Contextual literal resolution applies strictly to raw uncommitted literals, not to already-typed values.
- **Equality Result-Type Barrier**: `==` and `!=` establish a strict boundary between operand typing and result typing. Expected-type context may operate inward to resolve uncommitted `True` or `False` literals used as operands (e.g., `True == Unknown` resolves `True` to `XoX.True`), but operand contextualization never alters the fixed `Bool` result type. An outer expected `XoX` type never crosses the equality result barrier to turn the comparison result into `XoX`.

## 19. Bool and XoX Assignment and Conversion

### Assignment Invariants for Typed Expressions
- **No Implicit Bool-to-XoX Assignment**: An expression whose static type is `Bool` cannot be implicitly assigned to a variable or parameter of type `XoX`. Attempting to do so without explicit conversion is a static `TypeError`.
- **No Implicit XoX-to-Bool Assignment**: An expression whose static type is `XoX` cannot be implicitly assigned to a variable or parameter of type `Bool`. Attempting to do so without explicit conversion is a static `TypeError`.
- **Literal Resolution vs Value Coercion**: Context-sensitive `True` and `False` literals directly construct `XoX` values when `XoX` is the expected type (§18). This contextual literal resolution applies exclusively to literal expressions and is not a value coercion mechanism for already-typed `Bool` expressions.

### Monomorphic Variable Binding and Reassignment
- **Static Monomorphic Typing**: Every variable binding has exactly one static, monomorphic type throughout its lifetime. The language does not permit dynamic variable retagging or union-type inference (`Bool | XoX`).
- **Binding Forms and Type Determination**:
  - **Inferred Initialized Binding (`x = expr`)**: When no type annotation exists, the variable's static type is permanently fixed by its initial type inference (e.g. `flag = True` infers `flag: Bool`).
  - **Annotated Initialized Binding (`x: Type = expr`)**: An explicit type annotation (`Bool` or `XoX`) permanently fixes the variable's static type at declaration (e.g. `flag: Bool = True` or `status: XoX = True`). The annotation provides expected-type context to uncommitted `True` and `False` literals without value coercion (§18).
  - **Reassignment (`x = expr`)**: Reassigning an existing variable uses the identical `x = expr` syntax. The initializer must match the variable's established static type.
  - **Prohibition of Uninitialized Declarations (SyntaxError)**: V1 does not support uninitialized declarations (such as `x: XoX` or `x: Bool` without an initializer). Requiring immediate initialization avoids uninitialized variables and complex definite-assignment analysis.
- **Reassignment Type Invariance**: Subsequent reassignments must preserve the established static type:
  - **Bool Variables**: For a variable `flag` typed as `Bool`, later reassigning `flag = False` is valid (`False` resolves in the established `Bool` context), but `flag = Unknown` is a static `TypeError`.
  - **XoX Variables**: For a variable `t` typed as `XoX`, later reassigning `t = True`, `t = False`, or `t = Unknown` is valid, with `True` and `False` literals resolving directly within the established `XoX` domain.
  - **Cross-Type Reassignments**: Assigning an already-typed `Bool` expression to a `XoX` variable or an already-typed `XoX` expression to a `Bool` variable requires explicit conversion (`xox(expr)`) under penalty of `TypeError`.
- **Value Mutation vs Type Immutability**: Variable values may change across runtime assignments, but the variable's static type does not.

### Function Return Typing and Explicit Annotations
- **Mandatory Explicit Return Annotation for XoX Expressions**: Any function containing a return statement whose resolved static type is `XoX` must explicitly declare an `-> XoX` return type (e.g. `fn get_status() -> XoX:`).
- **Universal Static Type Application**: This rule applies universally to every return expression whose static type resolves to `XoX`, regardless of syntactic shape or expression form:
  - The `Unknown` literal (`return Unknown`).
  - An already-typed `XoX` variable or parameter (`return my_xox`).
  - A function or method call returning `XoX` (`return fetch_status()`).
  - The result of `XoX` logical operations (`return t1 AND t2`, `return t1 OR t2`, `return NOT t1`).
- **Prohibition of Implicit XoX Return Inference (TypeError)**: `XoX` is strictly opt-in (§16) and must never be inferred implicitly as the return type of an unannotated function. Returning any `XoX`-typed expression from a function without an explicit `-> XoX` return annotation is statically invalid and produces a `TypeError`.
- **Expected Return Context**: An explicit `-> XoX` return annotation establishes expected-type context for all return expressions within that function:
  - Under `-> XoX`, `return True` and `return False` resolve directly as `XoX.True` and `XoX.False` via contextual literal resolution (§18).
  - `return Unknown` evaluates as `XoX.Unknown`.
- **Traversal-Order Independence**: Return statements must not be typed sequentially in a way that makes function return type or literal resolution depend on source-order traversal.
- **No Whole-Function Type Promotion**: No implicit whole-function promotion of already-typed `Bool` return expressions to `XoX` occurs. Already-typed `Bool` expressions returned from a `-> XoX` function require explicit conversion (`xox(expr)`).
- **Definite-Return Path Completeness (MissingReturnError)**: Definite-return analysis requires every reachable terminal control-flow path in a function with a declared return type to return a type-compatible value (§11). Using `xen: ignore` satisfies XoX branch exhaustiveness but does not synthesize a return value; any execution path through `xen: ignore` reaching the end of the function without returning produces a `MissingReturnError`.

### Explicit Value Conversion
- **Explicit Bool-to-XoX Promotion (`xox(expr)`)**:
  - **Syntax**: `xox(expr)` (with mandatory parentheses).
  - **Typing Rule**: $\Gamma \vdash e : \text{Bool} \implies \Gamma \vdash \text{xox}(e) : \text{XoX}$.
  - **Semantics**:
    - $\text{xox}(\text{True}) = \text{XoX.True}$
    - $\text{xox}(\text{False}) = \text{XoX.False}$
    - **No other rule**.
    - `xox(expr)` never introduces `Unknown`.
    - `xox(expr)` is strictly **non-idempotent** (`xox(xox(flag))` $\rightarrow$ static `TypeError`).
    - `XoX` and `Unknown` are never valid operands (`xox(Unknown)` $\rightarrow$ static `TypeError`).
    - The typed AST preserves `PromoteBoolToXoX(expr)`.
    - `expr` is evaluated **exactly once** (single evaluation).
    - **No reordering** of the operational trace (strictly condition-first evaluation preserved).
    - Parentheses are **mandatory** (`xox a == b` $\rightarrow$ `SyntaxError`).
  - **Reference Invariants**:
    - `xox(Unknown)` $\rightarrow$ `TypeError`
    - `xox(True)` $\rightarrow$ `XoX.True`
    - `xox(False)` $\rightarrow$ `XoX.False`
  - **Mandatory Adversarial Matrix**:
    - **CTX-PROMOT-01 (Rejected Idempotence)**: `xox(xox(flag))` $\rightarrow$ static `TypeError` (receives `XoX`, expects `Bool`).
    - **CTX-PROMOT-02 (Rejected XoX Compound)**: `xox(xox_a AND xox_b)` $\rightarrow$ static `TypeError` (operand is already `XoX`).
    - **CTX-PROMOT-03 (Precedence Without Parentheses)**: `xox a == b` $\rightarrow$ `SyntaxError`.
    - **CTX-PROMOT-04 (Trace & Single evaluation)**: `xox(side_effect())` $\rightarrow$ `PASS` with proof of a single call at its exact sequential position.
  - **Runtime & Library Mapping**: At the runtime boundary, `XoX.from_bool(value)` implements the lower-level function mapping `Bool False` $\rightarrow$ `XoX.False` and `Bool True` $\rightarrow$ `XoX.True`.
  - **Lossless Boundary**: While `Bool`-to-`XoX` promotion is strictly lossless, it must remain explicit in code to preserve the semantic type boundary between binary truth values and 3-valued knowledge states.
- **Explicit XoX-to-Bool Collapse (`source.unwrap_or(default_bool)`)**:
  - **Syntax**: `source.unwrap_or(default_bool)` (postfix invocation on expressions).
  - **Typing Rule**: $\Gamma \vdash x : \text{XoX} \land \Gamma \vdash d : \text{Bool} \implies \Gamma \vdash x.\text{unwrap\_or}(d) : \text{Bool}$.
  - **Semantic AST Representation**: Evaluated and represented in the typed AST as `CollapseXoXToBoolWithDefault(source, fallback)`, strictly distinct from any generic `MethodCall`.
  - **Operational Semantics**:
    - `source` is evaluated **exactly once** prior to any decision.
    - If `source == XoX.True`, returns `Bool.True` without evaluating `fallback`.
    - If `source == XoX.False`, returns `Bool.False` without evaluating `fallback`.
    - If `source == XoX.Unknown`, evaluates `fallback` **exactly once** and returns its `Bool` result.
    - `fallback` is strictly lazy and conditioned on `Unknown`.
  - **Boundary Invariants**:
    - `unwrap_or` is an explicit information-reducing projection (information-losing) `XoX` $\rightarrow$ `Bool`.
    - No truthiness.
    - No implicit coercion.
    - No implicit fallback (the `default_bool` argument is strictly mandatory; omission $\rightarrow$ static `SyntaxError`).
    - The static type of fallback must be `Bool`, even if the runtime value of source would make the fallback unreachable (CTX-COLLAPSE-04).
    - The source must be statically of type `XoX` (CTX-COLLAPSE-05).
    - No alternative `??` or coalesce syntax is permitted.
  - **Reference Invariants**:
    | Input Expression | Fallback Expression | Static / Runtime Result | Invariant Enforced |
    | :--- | :--- | :--- | :--- |
    | `XoX.True.unwrap_or(d)` | `d: Bool` | `Bool.True` | Short-circuit; fallback `d` not evaluated |
    | `XoX.False.unwrap_or(d)` | `d: Bool` | `Bool.False` | Short-circuit; fallback `d` not evaluated |
    | `XoX.Unknown.unwrap_or(d)` | `d: Bool` | `d` (Bool) | Fallback `d` evaluated exactly once |
    | `xox_val.unwrap_or(Unknown)` | `Unknown` (XoX) | `TypeError` (Static) | Static type of fallback must be `Bool` |
    | `bool_val.unwrap_or(False)` | `False` (Bool) | `TypeError` (Static) | Static type of source must be `XoX` |
    | `xox_val.unwrap_or()` | *Absent* | `ParseError` / `StaticError` | Mandatory fallback argument; no implicit default |
  - **Mandatory Adversarial Matrix (LOCKED_ADVERSARIAL_SPEC)**:
    - **CTX-COLLAPSE-01**: `XoX.True.unwrap_or(trace_effect())` $\rightarrow$ `Bool.True`; source evaluated exactly 1 time; `trace_effect()` called 0 times (`PASS`).
    - **CTX-COLLAPSE-02**: `XoX.False.unwrap_or(trace_effect())` $\rightarrow$ `Bool.False`; source evaluated exactly 1 time; `trace_effect()` called 0 times (`PASS`).
    - **CTX-COLLAPSE-03**: `XoX.Unknown.unwrap_or(trace_effect())` $\rightarrow$ `Bool` result of `trace_effect()`; source evaluated exactly 1 time; `trace_effect()` called exactly 1 time after determining `Unknown` (`PASS`).
    - **CTX-COLLAPSE-04**: `xox_val.unwrap_or(Unknown)` $\rightarrow$ static `TypeError` because fallback must be `Bool`, even if the source value makes the fallback unreachable at runtime (`REJECTED_STATIC_TYPE_ERROR`).
    - **CTX-COLLAPSE-05**: `bool_val.unwrap_or(False)` $\rightarrow$ static `TypeError` because source must be `XoX` (`REJECTED_STATIC_TYPE_ERROR`).
    - **CTX-COLLAPSE-06**: `xox_val.unwrap_or()` $\rightarrow$ mandatory static rejection for missing fallback; no implicit fallback (`REJECTED_STATIC_ERROR`).
    - Locked Reference Matrix: `experiments/COLLAPSE_COUNTEREXAMPLES.md`.
- **Explicit XoX-to-Bool Extraction (`xox_value.unwrap_bool()`)**:
  - Canonical explicit potentially-failing extraction from `XoX` to `Bool` is defined as `xox_value.unwrap_bool()`.
  - Mapping:
    - `XoX.True.unwrap_bool()` $\rightarrow$ returns `Bool.True`.
    - `XoX.False.unwrap_bool()` $\rightarrow$ returns `Bool.False`.
    - `XoX.Unknown.unwrap_bool()` $\rightarrow$ raises a dedicated runtime `UnknownValueError`.
  - **Explicit Potentially-Failing Extraction**: `unwrap_bool()` is an explicit potentially-failing extraction operation, not an implicit coercion or type cast. The failure on `Unknown` is a runtime extraction error, not a static `TypeError` merely because the source expression has type `XoX`.
  - **No Silent Collapsing**: `Unknown` is never mapped automatically or silently to `True` or `False`.
  - **Immutability**: Calling `unwrap_bool()` does not mutate the underlying `XoX` value.

### Logical Expression Typing and Mixed Operations
- **Homogeneous Operations**:
  - `Bool AND Bool` $\rightarrow$ returns `Bool`.
  - `Bool OR Bool` $\rightarrow$ returns `Bool`.
  - `NOT Bool` $\rightarrow$ returns `Bool`.
  - `XoX AND XoX` $\rightarrow$ returns `XoX` (evaluating via Strong Kleene $K_3$).
  - `XoX OR XoX` $\rightarrow$ returns `XoX` (evaluating via Strong Kleene $K_3$).
  - `NOT XoX` $\rightarrow$ returns `XoX` (evaluating via Strong Kleene $K_3$).
- **No Implicit Promotion (TypeError)**: Mixed logical operations (`Bool AND XoX`, `XoX AND Bool`, `Bool OR XoX`, and `XoX OR Bool`) are statically invalid without explicit conversion and must raise a `TypeError`. The compiler must never implicitly promote `Bool` to `XoX` for logical operations.
- **Explicit Conversion Workflow**: To evaluate a `Bool` expression alongside a `XoX` expression, the developer must explicitly convert the `Bool` operand using `xox(expr)` (e.g. `xox(b) AND t`). Once converted to `XoX`, Strong Kleene logic rules apply normally.
- **Preservation of Evaluation and Literals**: Left-to-right evaluation, short-circuit semantics (§7), and context-sensitive literal resolution for uncommitted literals (§18) remain strictly preserved.

### Equality Typing and Mixed Comparisons
- **Homogeneous Comparisons**:
  - `Bool == Bool` and `Bool != Bool` are valid and evaluate to `Bool`.
  - `XoX == XoX` and `XoX != XoX` are valid and evaluate to `Bool` (under exact state-identity semantics; `Unknown == Unknown` is `Bool True`).
- **Strict Result-Type Barrier**: Equality (`==`) and inequality (`!=`) always and exclusively return `Bool`. An outer expected `XoX` type never causes the result of a comparison to become `XoX`.
- **TypeError on Direct Assignment to XoX**: In `res: XoX = (val1 == val2)`, the comparison evaluates to `Bool` and assigning it directly to `res` is a static `TypeError`. The developer must explicitly convert the comparison result using `res: XoX = xox(val1 == val2)`.
- **No Implicit Promotion (TypeError)**: Direct equality (`==`) or inequality (`!=`) comparisons between an already-typed `Bool` expression and an already-typed `XoX` expression are statically invalid and must raise a `TypeError`. The compiler must never implicitly promote `Bool` to `XoX` for equality comparisons.
- **Explicit Conversion for Comparison**: To compare a `Bool` expression with a `XoX` expression, the `Bool` operand must be explicitly converted using `xox(expr)` (e.g. `xox(b) == t`).
- **Contextual Literal Resolution in Comparisons**:
  - When an already-typed `XoX` operand or an `Unknown` literal is compared directly with an uncommitted literal `True` or `False` (e.g. `my_xox == True`, `True == Unknown`, `False != Unknown`), the literal resolves directly to `XoX.True` or `XoX.False` via contextual resolution (§18), evaluating under XoX state identity (`True == Unknown` $\rightarrow$ `Bool False`).
  - When an already-typed `Bool` operand is compared directly with an uncommitted literal `True` or `False`, the literal resolves directly to `Bool.True` or `Bool.False`.
  - Inward literal contextualization of operands does not alter the fixed `Bool` return type of the comparison.
  - Contextual literal resolution is a static literal construction mechanism, not an implicit value coercion of an already-typed expression.
- **Strictly Binary Invariant & SyntaxError**: Comparisons are strictly binary. Chained comparison syntax (such as `a == b == c` or `a == b != c`) is rejected with a static `SyntaxError` (§8). Multiple comparisons must be written explicitly as conjuncts (e.g. `(a == b) AND (b == c)`).
- **Symmetric Application**: All typing invariants, barrier rules, and error conditions apply symmetrically to both `==` and `!=`.

### Numeric, Bitwise, and Ordering Isolation
- **Non-Numeric Logical Types**: `Bool` and `XoX` are purely logical types with no numeric or integer identity.
- **Prohibition of Arithmetic Operators (TypeError)**: Arithmetic operators (`+`, `-`, `*`, `/`, `%`, and equivalent numeric operations) are strictly forbidden on `Bool` and `XoX` operands. Expressions such as `True + 1`, `XoX.True * 2`, or `Unknown + 0` are static `TypeError`s.
- **Prohibition of Bitwise Operators (TypeError)**: Integer bitwise operators (`&`, `|`, `^`, `~`, `<<`, `>>`) are strictly forbidden on `Bool` and `XoX` operands. Logical conjunction, disjunction, and negation must exclusively use `AND`, `OR`, and `NOT`. Expressions such as `True & False` or `Unknown | True` are static `TypeError`s.
- **Prohibition of Ordering Comparisons (TypeError)**: Ordering comparison operators (`<`, `<=`, `>`, `>=`) are strictly forbidden for `Bool` and `XoX`. Expressions such as `True < False`, `Unknown >= False`, or `Unknown < True` are static `TypeError`s.
- **Preserved Operators**: `==` and `!=` remain valid according to state-identity equality rules (§8), and `AND`, `OR`, and `NOT` remain the canonical logical operators (§7).
- **Isolation from Python Prototype Subtyping**: Python-specific runtime characteristics (such as Python's `bool` subclassing `int` where `True == 1` and `True + 1 == 2`) must never leak into XoX language semantics.
- **Representation Independence**: Low-level runtime representation choices (e.g. byte or integer representation in native or bytecode backends) must not compromise or alter these language-level type restrictions.

## 20. Resolved Items
- **[RESOLVED] Ignore Mechanism Syntax**: Canonical syntax resolved as `xen:` followed by indented `ignore`.
- **[RESOLVED] Python Lowering Strategy**: Explicit three-way identity dispatch over a hygienic single-evaluation temporary variable.
- **[RESOLVED] XoX-to-Bool Conversion API**: Canonical explicit extraction defined as `xox_value.unwrap_bool()`, returning `Bool.True` for `XoX.True`, `Bool.False` for `XoX.False`, and raising a runtime `UnknownValueError` on `XoX.Unknown` without implicit conversion or V1 fallback parameters.
- **[RESOLVED] Python Prototype Runtime Representation**: Standard non-numeric Python `Enum` with internal singleton members `FALSE`, `TRUE`, `UNKNOWN`, exact `is` identity dispatch, explicit rejection of truthiness (`__bool__` raises `TypeError`), and no `int` inheritance.
- **[RESOLVED] Python Prototype Compiler Architecture**: Source-to-source transpiler/compiler targeting standard Python with a deterministic staged pipeline (lexer $\rightarrow$ parser $\rightarrow$ generic AST $\rightarrow$ type resolution $\rightarrow$ semantic validation $\rightarrow$ definite-return analysis $\rightarrow$ Python lowering) with one-way architectural dependencies and standard library preference.
- **[RESOLVED] Variable Binding, Annotation, and Reassignment Syntax**: Initialized inferred binding (`x = expr`), annotated binding (`x: Type = expr` with `Type` in `Bool`, `XoX`), and monomorphic reassignment (`x = expr`), with uninitialized declarations excluded from V1.
- **[RESOLVED] Function Definition, Typed Parameter, Return Annotation, and Return Statement Syntax**: Canonical function definition (`fn name(params) -> Type:`), explicitly typed parameters (`p: Bool | XoX`), syntactically optional return annotation (`-> Bool | XoX`), and value-returning `return expr` statements (bare `return` and non-truth types excluded from V1).
- **[RESOLVED] Inline Conditional Expression Syntax, Grammar, AST, Precedence, Static Typing, and Lowering**: Defined dual-form inline conditionals (`t if c else f` for `Bool` and `t if c xen u else f` for `XoX`) with lowest precedence below `OR`, right-associativity, homogeneous branch typing, domain-anchor resolution, and static exhaustiveness verification (§5.1, §18). Lowering and runtime code generation for the reference Python backend/transpiler are fully resolved and implemented using hygienic condition temporaries and branch-local preludes, ensuring single condition evaluation, lazy branch execution, Operational Trace Preservation (§7.1), and strict anti-truthiness preservation.
- **[RESOLVED] Explicit Bool-to-XoX Promotion (`xox(expr)`)**: Explicit promotion syntax `xox(expr)` with mandatory parentheses, static typing rule $\Gamma \vdash e : \text{Bool} \implies \Gamma \vdash \text{xox}(e) : \text{XoX}$, non-idempotent semantics, AST node `PromoteBoolToXoX(expr)`, single evaluation guarantee, and preserved operational trace ordering (§19).

## 21. Unresolved Items (OPEN)
- **[OPEN] Implementation & Architecture (Native Backend & Broader Architecture)**:
  - While the Python prototype architecture and runtime representation are resolved, future native backends, native memory layout, native byte encodings, VM/bytecode formats, native ABI, optimizations, packaging, and non-prototype toolchains remain **OPEN**.
- **[OPEN] Chained Comparison Syntax & Semantics**:
  - Chained comparisons (such as `a == b == c` or `a == b != c`) are intentionally excluded from the initial language scope to preserve explicit, minimal binary semantics.
  - Possible future support remains **OPEN** and will require explicitly defining evaluation order, single evaluation of shared middle operands, short-circuit behavior, pairwise typing, literal-context propagation, and semantics for both `==` and `!=`.
- **[OPEN] `elif` Multi-Branch Syntax & Semantics**:
  - `elif` is intentionally excluded from the initial language grammar for both `Bool` and `XoX` conditionals to keep the grammar minimal and explicit.
  - Possible future support remains **OPEN**.
  - Any future `elif` design must strictly preserve the architectural distinction between ordinary multi-branch `Bool` control flow and the dedicated `xen` branch for `XoX` `Unknown` (`elif` must never be used to represent the `Unknown` state).
