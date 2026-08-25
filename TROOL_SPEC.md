# Trool Language Specification: Semantic Core

## 1. Purpose
Defines the initial immutable semantic core of the Trool type and the `xen` control flow construct.

## 2. Design Principles
- **Small**
- **Explicit**
- **Deterministic**
- **Human-readable**
- **No silent loss of information**
- **Simple compiler diagnostics**

## 3. Type System
- **Bool**: Exactly two values: `True` and `False`.
- **Trool**: Exactly three values: `True`, `False`, and `Unknown`.
- **Non-Numeric Logical Types**: `Bool` and `Trool` are non-numeric logical types with no numeric subtyping, integer arithmetic, bitwise operations, or ordering relations (§19).
- **Distinctness**: `Bool` and `Trool` are distinct types.
- **Coercion**: No implicit Trool-to-Bool coercion exists.

## 4. Meaning of Unknown
- `Unknown` denotes insufficient information to establish `True` or `False`.
- `Unknown` does not mean half-true.

## 5. Control Flow Semantics
- **Conventional Catch-All Semantics**: The keyword `else` retains its conventional catch-all role covering the only remaining unhandled state. The language does not redefine `else` as a specialized `False` keyword.
- **Bool Conditional**:
  - `if` maps to `True`.
  - `else` catches the only remaining state: `False`.
- **Trool Conditional**:
  - `if` maps to `True`.
  - `xen` maps to `Unknown`.
  - `else` catches the only remaining state: `False`.
- **Exhaustiveness**: A Trool conditional must explicitly handle `Unknown`.

## 6. Semantic Invariants
- **State Cardinality**: `Bool` has exactly 2 states; `Trool` has exactly 3 states.
- **Mutual Exclusivity**: `True`, `False`, and `Unknown` are strictly mutually exclusive `Trool` states.
- **Information Preservation**: `Unknown` cannot be silently treated as `True` or `False`.
- **Branch Selection**: Every executed `Trool` conditional selects exactly one branch among `if`, `xen`, or `else`.
- **Branch Mapping**: In a `Trool` conditional, `if` corresponds only to `True`, `xen` only to `Unknown`, and `else` only to `False`.
- **Mandatory Handling**: A `Trool` conditional cannot silently omit the `Unknown` path.
- **Binary Isolation**: `Bool` control flow remains strictly binary and does not use `xen`.

## 7. Trool Logical Operators
`Trool` logical operators follow **Strong Kleene 3-valued logic ($K_3$)**.
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

## 8. Trool Equality

### State Identity Semantics
- **Exact State Identity**: `Trool` equality (`==`) evaluates exact state identity.
- **Return Type**: `Trool` equality and inequality always return `Bool`, never `Trool`.
- **Strict Result-Type Barrier**: `==` and `!=` form a strict result-type barrier that always and exclusively returns `Bool`. An outer expected `Trool` context must never cause the result of `==` or `!=` to become `Trool`.
- **Identity Evaluation**:
  - `True == True` $\rightarrow$ `Bool True`
  - `False == False` $\rightarrow$ `Bool True`
  - `Unknown == Unknown` $\rightarrow$ `Bool True`
- **State Mismatch**: Any comparison between different `Trool` states evaluates to `Bool False` (e.g. `Trool.True == Trool.Unknown` $\rightarrow$ `Bool False`; `Trool.False == Trool.Unknown` $\rightarrow$ `Bool False`).
- **Inequality**: `Trool` inequality (`!=`) is the exact logical negation of `Trool` equality (e.g. `Trool.True != Trool.Unknown` $\rightarrow$ `Bool True`).
- **Deliberate Strong Kleene Deviation**: While logical operators (`NOT`, `AND`, `OR`) strictly follow Strong Kleene 3-valued logic ($K_3$), `Trool` equality intentionally does not. Equality compares exact state identity and always evaluates to `Bool`.
- **Operand Type Homogeneity**: Equality and inequality require homogeneous operand types (`Bool == Bool` or `Trool == Trool`). Comparing already-typed `Bool` and `Trool` expressions without explicit conversion is a `TypeError` (§19). Direct comparisons with uncommitted literals resolve via contextual literal typing (§18).

### Distinction from SQL NULL
- **Not SQL NULL**: `Trool.Unknown` is not `SQL NULL`.
- **SQL Equality (`=`) Contrast**: In standard SQL three-valued logic, equality comparison using `=` does not treat `NULL = NULL` as `True`; instead, it evaluates to `UNKNOWN` (or `NULL`).
- **Exact State Identity**: `Trool` equality (`==`) instead compares exact `Trool` state identity. `Unknown == Unknown` therefore evaluates to `Bool True`.
- **Pedagogical Analogy (`IS NOT DISTINCT FROM`)**: The state-identity behavior of `Trool` equality is conceptually analogous to SQL's `IS NOT DISTINCT FROM` operator rather than SQL's `=` operator. This comparison serves strictly as a pedagogical analogy for state-identity equivalence, not as a claim that `Trool.Unknown` and `SQL NULL` have equivalent semantics.
- **Epistemic vs Real-World Facts**: Two `Unknown` `Trool` values comparing equal means only that both operands reside in the `Unknown` state. It does not establish equality, identity, or knowledge of any underlying real-world facts represented by those `Unknown` states.
- **Pragmatic Strong Kleene Deviation**: While logical operators (`NOT`, `AND`, `OR`) strictly adhere to Strong Kleene 3-valued logic ($K_3$), the deviation of `Trool` equality to state-identity comparison returning binary `Bool` is a deliberate, pragmatic design decision to guarantee a total equivalence relation.

### Strictly Binary Comparison Invariant
- **Strictly Binary Operators**: Comparison operators (`==`, `!=`) are strictly binary operators in the initial specification. Chained comparison syntax (such as `a == b == c` or `a == b != c`) is not supported in the initial language specification and produces a `SyntaxError`.
- **No Implicit Associativity or Desugaring**: A construct such as `a == b == c` must not be interpreted as left-associative nesting `(a == b) == c` nor as implicit Boolean conjunction `(a == b) AND (b == c)`.
- **Explicit Conjunction Requirement**: Developers must write multiple comparisons explicitly using logical operators and grouping, for example: `(a == b) AND (b == c)`.

### Operator Precedence and Associativity
- **Deliberate Language Precedence**: Operator precedence and associativity are formal, deliberate Trool language design decisions and must not be inferred from Python or any other host language.
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

### Trool Conditional Syntax
`Trool` conditions follow the canonical three-way order: `if`, `xen`, `else`.
```text
if <Trool-expression>:
    <True-block>
xen:
    <Unknown-block>
else:
    <False-block>
```
- **Branch Mapping**: `if` executes on `True`, `xen` executes on `Unknown`, and `else` executes on `False`.
- **Validity Scope**: `xen` is valid only for `Trool` conditions.
- **Dependency**: `xen` cannot appear without a preceding `if`.
- **No `elif` for Unknown**: A `Trool` conditional must not use `elif` to represent `Unknown`.
- **Nesting**: Nested conditionals remain structurally independent.

## 10. Conditional Exhaustiveness
- **Bool Conditionals**: May use `if` alone (implicit no-op for `False`) or `if` with an explicit `else`.
- **Trool Conditionals**: Must fully account for all three states (`True`, `Unknown`, and `False`).
- **Structural `if` Presence**: Because every parsed `ConditionalStatement` structurally begins with `if`, a valid parsed conditional inherently possesses its `True` branch. Standalone `xen` or `else` clauses without an `if` are orphan clauses (`SyntaxError`).
- **Missing Unknown Path (`xen`)**: Omitting the `Unknown` path without an explicit ignore mechanism (`xen:` block or `xen: ignore`) is an `ExhaustivenessError`.
- **Missing False Path (`else`)**: Omitting the `False` branch (`else`) on a `Trool` conditional is an `ExhaustivenessError`.
- **No Duplicate Branches**: Duplicated semantic branches (e.g. multiple `xen` or multiple `else` blocks for the same conditional) are invalid (`SyntaxError`).
- **Canonical Ordering**: The branch order for a `Trool` conditional is canonically `if`, `xen`, `else`.
- **Exhaustiveness Satisfaction**: Using `xen: ignore` satisfies the exhaustiveness requirement for `Trool`.

## 11. Explicit Unknown Ignore Mechanism

### Contextual Keyword Status & Disambiguation Precedence
- **Soft / Contextual Keyword**: `ignore` is a contextual (soft) keyword, not a globally reserved keyword.
- **Syntactic Disambiguation Precedence**: An isolated standalone identifier token spelled `ignore`, when it appears as the direct and sole body statement of a `xen` clause, is **always** parsed and interpreted as the contextual `IgnoreStatement`.
- **Precedence over Identifier Resolution**: This contextual interpretation strictly takes precedence over resolving a variable or expression-statement named `ignore`. `xen: ignore` cannot be used to evaluate an in-scope variable named `ignore` as a standalone expression.
- **Ordinary Identifier Status Everywhere Else**: A variable, function, parameter, attribute, or member named `ignore` remains completely valid everywhere else. Syntactic uses such as `print(ignore)`, `value = ignore`, `object.ignore`, and `ignore()` are parsed as ordinary identifier references according to standard expression syntax.
- **Deterministic Symbol-Table-Free Parsing**: Distinguishing `IgnoreStatement` from an ordinary identifier requires zero symbol-table lookup or scope awareness; it is determined purely by the local syntactic position as the sole statement of a `xen:` clause.
- **Lexer Independence**: The lexer does not need to emit a globally reserved `IGNORE` token.

### Canonical Syntax & Semantics
- **Canonical Syntax**: The canonical ignore syntax for `Unknown` is `xen:` followed by an indented standalone `ignore` statement:
  ```text
  if <Trool-expression>:
      <True-block>
  xen:
      ignore
  else:
      <False-block>
  ```
- **Exclusive Atomic Form**: `xen: ignore` is an exclusive atomic form representing an explicitly acknowledged `Unknown` branch with no user action.
- **Sole Statement Invariant**: When `ignore` is used as the `xen` branch body, it must be the sole and exclusive statement in that `xen` clause.
- **Prohibition of Coexistence (SyntaxError)**: A `xen` clause containing `ignore` alongside any additional statement (e.g. `ignore` followed or preceded by another statement) is structurally invalid and must produce a `SyntaxError`.
- **Exhaustiveness Satisfaction**: Using `xen: ignore` satisfies the exhaustiveness requirement for `Trool`.
- **No Coercion / Mutation**: `ignore` does not convert `Unknown` to `True` or `False`, nor does it mutate the underlying `Trool` value.
- **Not Else**: `ignore` is not equivalent to `else`.
- **Mandatory Clause**: Omission of `xen` remains strictly invalid for `Trool` conditionals; the `xen:` clause must be written explicitly.
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
- **Separation of Exhaustiveness and Definite Return**: `Trool` branch exhaustiveness and function return-path completeness are distinct, independent semantic properties:
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

TypeName             ::= "Bool" | "Trool" ;

ExpressionStatement  ::= Expression ;
PassStatement        ::= "pass" ;

ConditionalStatement ::= "if" Expression ":" Block
                         ( "xen" ":" XenBlock )?
                         ( "else" ":" Block )? ;

XenBlock             ::= Block | IgnoreStatement ;
IgnoreStatement      ::= "ignore" ;
```

### Parser Invariants
- **Type-Agnostic Parsing**: The parser processes expressions and conditions solely as generic `Expression` nodes and does not determine whether an expression evaluates to `Bool`, `Trool`, or any other type.
- **Single Production**: There are no separate grammar productions for Bool versus Trool conditionals at parse time.
- **Function Definition and Parameter Syntax**:
  - `fn` introduces function definitions (`FunctionDefinition ::= "fn" Identifier "(" ParameterList? ")" ReturnAnnotation? ":" Block`).
  - **Explicitly Typed Parameters**: In V1, all function parameters must be explicitly typed (`Identifier ":" TypeName`) using the closed truth-type set `Bool` or `Trool`. Untyped parameters are not supported in V1.
  - **Syntactically Optional Return Annotation**: The return annotation `-> TypeName` is syntactically optional in the grammar and restricted to `Bool` or `Trool`. Semantic analysis enforces that any function returning `Trool` must explicitly declare `-> Trool` (§19).
  - **Value-Return Statements**: `ReturnStatement ::= "return" Expression`. Bare `return` without an expression is not supported in this initial truth-type prototype.
  - **Scope and Function Limitations in V1**: Function-call syntax, recursion, closures, default parameters, variadic parameters, keyword arguments, generics, overloads, higher-order functions, and nested functions are not defined or supported in the initial V1 prototype grammar.
- **Variable Binding and Reassignment Syntax**:
  - Inferred binding: `Identifier "=" Expression` (e.g. `flag = True`).
  - Annotated initialized binding: `Identifier ":" TypeName "=" Expression` (e.g. `status: Trool = True`).
  - Reassignment: uses the identical `Identifier "=" Expression` syntax when the identifier is already bound in the static environment.
  - **Declaration vs Reassignment**: Distinguishing a new variable declaration from a reassignment is performed strictly during semantic analysis via symbol-table lookup, not during parsing or lexing.
  - **Prohibition of Uninitialized Declarations (SyntaxError)**: Variable declarations without an explicit initializer (such as `x: Trool` or `x: Bool`) are not supported in V1 and produce a `SyntaxError`. Requiring immediate initialization guarantees that uninitialized variable states and complex definite-assignment analysis are not introduced into the initial prototype.
- **Structural Ordering**: When present, conditional clauses must appear in strict canonical sequence: `if`, then `xen`, then `else`. `xen` cannot precede `if`, and `else` cannot precede `xen`.
- **No Duplicate Clauses**: Duplicate `if`, `xen`, or `else` clauses within the same conditional construct are syntactically invalid (`SyntaxError`).
- **Exclusive Atomic Unknown Body**: `xen: ignore` is parsed as an exclusive atomic `XenBlock` via contextual soft-keyword matching without symbol-table lookup. `ignore` cannot coexist with other statements in the same `xen` block (`SyntaxError`).
- **No `pass`-Only `xen` Blocks**: A `xen` clause containing only one or more `pass` statements without effective logic cannot silently alias `ignore` and is invalid (`SyntaxError`). Multi-statement `xen` blocks containing effective statements may contain `pass`.
- **No `elif` in Initial Grammar (SyntaxError)**: `elif` is not supported in the initial language grammar for either `Bool` or `Trool` conditionals. Any appearance of `elif` produces a `SyntaxError`.
- **Multi-Branch Bool Control Flow**: Multi-branch `Bool` branching must be expressed explicitly using nested `if` statements inside `else` blocks (`if ...: ... else: if ...: ...`).
- **Trool Ternary Invariant**: `Trool` conditionals remain strictly ternary using `if` / `xen` / `else`. `elif` must never be used to represent the `Unknown` state.
- **Independent Nesting**: Nested conditionals are parsed independently under the same generic production.

### Post-Type Semantic Classification
- **Post-Parsing Type Resolution**: The `condition` expression is type-checked and resolved during semantic analysis following AST construction.
- **Semantic Classifications**: `BoolConditional` and `TroolConditional` are post-type semantic classifications, not concrete grammar productions:
  - **`BoolConditional`**: A `ConditionalStatement` whose condition resolves to type `Bool`. Semantic validation enforces that `xen` is absent (presence of `xen` emits `TypeError`).
  - **`TroolConditional`**: A `ConditionalStatement` whose condition resolves to type `Trool`. A `Trool` condition is fully valid; semantic validation enforces exhaustiveness (both `xen`—or `xen: ignore`—and `else` must be present; omission emits `ExhaustivenessError`).
- **Diagnostic Precedence Alignment**: This separation guarantees that syntax errors are identified in Phase 1 without type checking, type admissibility is validated in Phase 2, and exhaustiveness coverage is verified in Phase 3.

## 13. Static Diagnostic Requirements

### Diagnostic Resolution Precedence
Diagnostics are resolved through a deterministic four-phase pipeline:
1. **Phase 1: SyntaxError (Structural Validity)**
   - Emitted when source code violates grammar or structural invariants (e.g. duplicate branch declarations, invalid clause ordering, orphan `xen` or `else` without `if`, non-exclusive `xen: ignore`, all-`pass` `xen` blocks, use of `elif`, or an attempted contextual `ignore` construct outside `xen:`).
2. **Phase 2: TypeError (Type Admissibility)**
   - Emitted after condition type resolution when an inadmissible type or incompatible keyword is used.
   - If the condition resolves to `Bool` and a `xen` clause is present $\rightarrow$ `TypeError` (`xen` is invalid for binary `Bool` conditions).
   - If an expression is neither `Bool` nor `Trool`, or if implicit coercion is attempted $\rightarrow$ `TypeError`.
3. **Phase 3: ExhaustivenessError (Exhaustive Semantic Coverage)**
   - Emitted when a syntactically valid conditional with an admissible condition type fails to account for all required semantic states.
   - If the condition resolves to `Trool` and lacks a `xen` clause (or `xen: ignore`), or lacks an `else` clause $\rightarrow$ `ExhaustivenessError` (never `TypeError`).
4. **Phase 4: MissingReturnError (Definite-Return Completeness)**
   - Emitted when control-flow reachability analysis determines that a function with a declared return type has reachable terminal paths (e.g. falling through `xen: ignore`) that fail to return a compatible value.

### Diagnostic Structure Requirements
Every static diagnostic emitted for conditional analysis must provide at minimum:
1. **Error Category**: The formal class of diagnostic (`SyntaxError`, `TypeError`, `ExhaustivenessError`, or `MissingReturnError`).
2. **Source Location**: Exact file, line, and column range of the offending construct.
3. **Violated Rule**: Specification section or invariant being violated.
4. **Human-Readable Explanation**: Concise explanation distinguishing compiler-known facts from any suggested correction.

### Canonical Diagnostic Categories

| Diagnostic Context | Category | Violated Rule | Description |
|---|---|---|---|
| `xen` with `Bool` condition | `TypeError` | §5, §6, §12 | `xen` branch is invalid on binary `Bool` conditions. |
| Missing `xen` branch on `Trool` | `ExhaustivenessError` | §5, §10 | `Trool` conditional must handle `Unknown` explicitly via `xen:` block or `xen: ignore`. |
| Missing `else` branch on `Trool` | `ExhaustivenessError` | §10, §12 | `Trool` conditional must declare an `else` (`False`) branch. |
| Reachable path without return | `MissingReturnError` | §11, §19 | Function with declared return type has reachable execution paths (e.g. falling through `xen: ignore`) that terminate without returning a value. |
| Duplicate branches (`if`/`xen`/`else`) | `SyntaxError` | §10, §12 | Duplicate branch declarations in the same conditional are forbidden. |
| Invalid branch ordering | `SyntaxError` | §9, §10, §12 | `Trool` branches must strictly follow canonical sequence `if`, `xen`, `else`. |
| Orphan `xen` branch | `SyntaxError` | §9, §12 | `xen` clause encountered without a preceding `if` block. |
| Orphan `else` branch | `SyntaxError` | §9, §12 | `else` clause encountered without a preceding `if` block. |
| Non-exclusive `xen: ignore` | `SyntaxError` | §11, §12 | `xen: ignore` is an exclusive atomic form; `ignore` cannot coexist with other statements in a `xen` clause. |
| `xen` clause with only `pass` | `SyntaxError` | §11, §12 | `xen` branch containing only `pass` statements is invalid; explicit no-op handling of `Unknown` requires `xen: ignore`. Multi-statement `xen` blocks with effective logic may contain `pass`. |
| Use of `elif` keyword | `SyntaxError` | §12, §21 | `elif` is not part of the initial language grammar; multi-branch Bool conditionals must use nested `if` in `else`, and Trool conditionals strictly use `if`/`xen`/`else`. |
| Implicit Trool-to-Bool coercion | `TypeError` | §3, §6, §19 | Cannot evaluate or assign `Trool` where `Bool` is expected without explicit handling or conversion. |
| Unannotated Trool return | `TypeError` | §16, §18, §19 | Returning any expression of resolved type `Trool` (e.g. `Unknown`, `Trool` variable, `Trool` call, `Trool` logical op) requires an explicit `-> Trool` return annotation; implicit return inference is forbidden. |
| Mixed Bool/Trool logical operation | `TypeError` | §7, §19 | Logical operations between mixed `Bool` and `Trool` operands are invalid without explicit conversion. |
| Mixed Bool/Trool equality comparison | `TypeError` | §8, §19 | Equality (`==`) and inequality (`!=`) comparisons between mixed `Bool` and `Trool` operands are invalid without explicit conversion. |
| Arithmetic / bitwise on Bool or Trool | `TypeError` | §3, §19 | Arithmetic (`+`, `-`, `*`, `/`, `%`) and bitwise (`&`, `|`, `^`, `~`, `<<`, `>>`) operators are forbidden on `Bool` and `Trool`. |
| Ordering comparison on Bool or Trool | `TypeError` | §3, §19 | Ordering comparisons (`<`, `<=`, `>`, `>=`) are forbidden on `Bool` and `Trool`. |
| Chained comparisons (e.g. `a == b == c`) | `SyntaxError` | §8, §19 | Chained comparisons are unsupported in the initial specification; comparisons must be written explicitly (e.g. `(a == b) AND (b == c)`). |
| Misplaced contextual `ignore` | `SyntaxError` | §11, §12 | Attempted contextual `ignore` construct used outside the permitted `xen:` (`Unknown`) branch context (ordinary identifier uses of `ignore` elsewhere remain valid). |

*Note: Exact error codes and final diagnostic wording remain open.*

## 14. Conceptual AST Requirements

### Generic Conditional Node Structure
A conceptual AST node for conditionals must contain:
- `condition`: Expression node producing a condition value.
- `true_branch`: Statement / block executed on `True`.
- `unknown_branch`: Optional statement / block executed on `Unknown` (or an explicit `ignore` marker).
- `false_branch`: Optional statement / block executed on `False`.

### Type-Specific Structural Invariants
- **Bool Conditional AST**:
  - Contains `condition`, `true_branch`, and optionally `false_branch`.
  - Must never contain an `unknown_branch`.
- **Trool Conditional AST**:
  - Contains `condition`, `true_branch`, `unknown_branch`, and `false_branch`.
  - The `unknown_branch` may hold a statement block or an explicit `Ignore` marker node.

### Metadata & Semantic Rules
- **Source Span Preservation**: AST nodes must preserve exact source spans for the condition expression and every branch keyword (`if`, `xen`, `else`, `ignore`).
- **Post-Resolution Differentiation**: Semantic analysis must clearly distinguish `Bool` and `Trool` conditionals after type resolution to perform exhaustiveness and branch legality checks.
- **Implementation Neutrality**: The AST structure is an abstract conceptual model and must not encode runtime representations, memory layouts, or byte-level `Trool` encodings.

## 15. Python Lowering Semantics

### Dispatch and Evaluation Strategy (Prototype Canonical)
- **Single Evaluation & Hygienic Temporary**: Every `Trool` conditional expression is evaluated exactly once at runtime. The resulting value is bound to a hygienic compiler-generated temporary variable whose identifier is guaranteed never to collide with user identifiers.
- **Explicit Identity Dispatch**: Lowering generates an explicit identity-based three-way dispatch against singleton `Trool` states (`TRUE`, `UNKNOWN`, and `FALSE`), canonically evaluating in the order: `TRUE`, then `UNKNOWN`, then `FALSE`.
- **Strict Anti-Coercion**: Lowering must never rely on Python `bool()`, truthiness coercion, or bare `if <trool_temp>:` branches for `Trool` dispatch.
- **Branch Semantic Fidelity**:
  - `if` $\rightarrow$ executed when `<trool_temp> is Trool.TRUE`.
  - `xen` $\rightarrow$ executed when `<trool_temp> is Trool.UNKNOWN`.
  - `else` $\rightarrow$ executed when `<trool_temp> is Trool.FALSE`.
- **Ignore Lowering**: `xen: ignore` lowers to an explicit no-op (e.g. `pass`) within the `Unknown` dispatch branch.
- **Fail-Closed Runtime Validation**: If the evaluated value is not a valid `Trool` state at runtime, lowering must fail explicitly (e.g., raise an internal runtime error) rather than falling through silently.
- **Bool Lowering**: Ordinary `Bool` conditionals lower directly to standard Python `if` / `else` control-flow statements without intermediate `Trool` wrapping.
- **Source Map Preservation**: Lowering maintains source span mappings so diagnostics refer back accurately to the original source positions.
- **Scope of Strategy**: This explicit identity-dispatch model is the canonical lowering strategy for the initial Python prototype; it does not freeze or restrict future native backends.

### Python Prototype Runtime Representation
- **Standard Python Enum Model**: The three runtime `Trool` states are represented as singleton members of a standard Python `Enum` (`Trool.FALSE`, `Trool.TRUE`, `Trool.UNKNOWN`) or semantically equivalent non-numeric singleton representation.
- **Prohibition of IntEnum**: The runtime model must use standard `Enum` and strictly forbids `IntEnum` or any inheritance from `int`.
- **Internal Member Names**: The internal runtime enum members are named `FALSE`, `TRUE`, and `UNKNOWN` to avoid collisions with Python reserved keywords while keeping attribute names clear and deterministic.
- **Source-to-Runtime Mapping**: Source-language `True`, `False`, and `Unknown` literals and expressions map directly to runtime singletons (`Trool.TRUE`, `Trool.FALSE`, `Trool.UNKNOWN`) without modifying source-language syntax.
- **Identity Dispatch**: Trool runtime dispatch uses exact object identity checks (`is`) against the singleton members (`<trool_temp> is Trool.TRUE`, `<trool_temp> is Trool.UNKNOWN`, `<trool_temp> is Trool.FALSE`), guaranteeing $O(1)$ state determination without relying on value comparison or truthiness.
- **Strict Anti-Truthiness (`__bool__` Rejection)**: Python truthiness conversion of a runtime `Trool` value is strictly forbidden. The runtime `Trool` class must define `__bool__` to reject evaluation by raising a runtime `TypeError` (or dedicated internal runtime error), ensuring that constructs such as `bool(trool_val)` or bare Python `if trool_val:` fail closed immediately.
- **Isolation from Numeric / Bitwise / Ordering Behaviors**: The runtime representation must not inherit from `int` and must never expose arithmetic (`+`, `-`), bitwise (`&`, `|`), or relational ordering (`<`, `>`) operations on `Trool`.
- **Prototype-Only Scope & Non-Freezing of Native Layout**: Python `Enum` is an implementation choice strictly for the Python prototype. It is not normative for future native backends. Integer member values or internal enum payloads are private prototype details and are not frozen as part of any language ABI, byte layout (e.g. `0x00`, `0x01`, `0x02`), or native memory representation.

### Python Prototype Staged Compiler Architecture
- **Source-to-Source Model**: The initial prototype is architected as a source-to-source transpiler/compiler implemented in Python targeting standard Python, without modifying CPython internals.
- **Deterministic Staged Pipeline**: The prototype processes Trool source code through a sequence of discrete, deterministic phases with strict one-way data flow:
  1. **Lexing**: Tokenizes source text, tracking line and column source spans without emitting global soft keywords (e.g. `ignore`).
  2. **Parsing**: Constructs a type-agnostic generic AST according to §12 and §14 without performing type evaluation or symbol table lookup.
  3. **AST Construction**: Produces generic AST nodes with exact source spans intact across every node.
  4. **Type Resolution**: Performs bidirectional literal resolution (§18), expression type checking, and fixes static monomorphic types (§19).
  5. **Semantic Validation**: Classifies conditionals as `BoolConditional` or `TroolConditional` post-type (§12), enforcing branch legality (§13 Phase 2) and exhaustiveness (§13 Phase 3).
  6. **Definite-Return Analysis**: Performs reachability analysis on value-returning functions (§11, §13 Phase 4, §19).
  7. **Python Lowering**: Lowers fully validated, typed AST structures into valid target Python code using canonical three-way identity dispatch (§15).
  8. **Generated Execution**: Executes lowered Python code against the prototype runtime module.
- **One-Way Architectural Dependencies**:
  - Later stages consume representations from earlier stages; earlier stages must not import or depend on lowering logic or runtime behavior.
  - Lowering is strictly a backend emission phase that consumes validated typed semantics; it must never invent language semantics or make typing decisions.
  - Runtime representation (`Trool` enum) is isolated from parser, AST, type-checker, diagnostics, and lowering modules.
- **Fail-Closed Phase Precedence**: Each phase fails closed on the earliest authoritative diagnostic (§13) and never attempts implicit error correction or heuristic guessing.
- **Span Preservation**: Source-span information (file, line, column start/end) must survive all compiler stages to guarantee precise diagnostic reporting.
- **Standard Library Preference**: The prototype relies on the Python standard library, avoiding external dependencies or parser-generator frameworks. Exact module, file, class, and package structures remain flexible implementation details adhering to these stage boundaries.

## 16. Trool Usage Discipline
- **Default vs Opt-In**: `Bool` is the default truth type for determinate propositions. `Trool` is strictly an opt-in type, used only when `Unknown` is a meaningful domain state.
- **No Speculative Use**: `Trool` must not be used merely for speculative future extensibility or syntax convenience.
- **No Replacement for Determinate Propositions**: `Trool` must not replace ordinary `Bool` when a proposition is fully determinable.
- **Explicit Return Signatures**: Functions and APIs that can return `Trool` must declare that return type explicitly.
- **Not a Generic Option/Nullable Type**: `Trool` is not a generic replacement for nullable values or `Option<Bool>`.
- **Epistemic vs Storage Absence**: `Unknown` represents uncertainty or lack of knowledge regarding truth, not the simple absence of stored data or an uninitialized memory slot.
- **Core Conceptual Distinction**:
  - `Bool` represents **truth values** directly (`True` or `False`).
  - `Trool` represents **knowledge states about a truth value** (`True`, `False`, or `Unknown`).

## 17. Xen Keyword Rationale

### Role Separation: Keyword vs Data Value
`xen` is strictly a control-flow keyword designated for handling the `Trool` `Unknown` branch. `Unknown` remains the actual `Trool` data value. `xen` is not an alias for `Unknown` and must never be used as a `Trool` value or expression literal.

### Primary Rationale: Ergonomics and Visual Differentiation
The primary justification for `xen` is its brevity, visual distinctiveness, compact structural fit beside `if` and `else`, and strong `i` / `x` / `e` scanning contrast. In visual flow, `if` (2 characters), `xen` (3 characters), and `else` (4 characters) produce a compact lexical sequence with distinct initial characters (`i`, `x`, `e`). These properties are design and ergonomic observations regarding syntactic shape and visual differentiation, rather than scientifically proven readability claims.

### Evaluated Alternatives
- **`unknown`**: Rejected because `Unknown` is already the semantic Trool data value name. The language design intentionally enforces a strict boundary between data values and control-flow keywords.
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
The literals `True` and `False` are context-sensitive truth literals capable of directly constructing either `Bool` or `Trool` values depending on expected-type context:
- **Default Inference**: When no expected type information is available from surrounding context and no typed operand constrains the expression, `True` and `False` infer `Bool` (`Bool` remains the default truth type).
- **Trool Contextual Construction**: When the surrounding type context explicitly expects `Trool`, `True` and `False` construct `Trool.True` and `Trool.False` directly.
- **Intrinsic Trool Type Anchor of `Unknown`**: `Unknown` is exclusively and intrinsically a `Trool` literal/value (never `Bool`). Inside expressions, `Unknown` acts as a strong `Trool` type anchor.

### Valid Sources of Literal Context
The compiler propagates expected-type context to uncommitted `True` and `False` literals from the following structural sources:
1. **Variable Annotations**: An explicit type annotation forces literals directly (e.g., `x: Bool = True` $\rightarrow$ `Bool.True`; `y: Trool = True` $\rightarrow$ `Trool.True`).
2. **Function Return Types**: A function's declared return type provides the expected-type context for return expressions (e.g. `fn f() -> Trool: return True` constructs `Trool.True`).
3. **Function Parameter Types**: When calling a function, parameter type declarations provide expected-type context for literal arguments (e.g., passing `True` to a parameter typed `Trool` constructs `Trool.True`; passing to `Bool` constructs `Bool.True`).
4. **Typed Binary Operator Operands & Unknown Anchor**: In binary operations (`AND`, `OR`, `==`, `!=`), an already-typed operand or an `Unknown` literal provides expected-type context to uncommitted literal operands:
   - In `my_trool AND True`, the typed `Trool` operand provides `Trool` context, resolving `True` directly as `Trool.True` (evaluating as `Trool`).
   - In `Unknown AND True`, the `Unknown` anchor resolves `True` directly as `Trool.True` (typed as `Trool AND Trool` returning `Trool`).
   - In `True OR Unknown`, `Unknown` anchors the expression in the `Trool` domain, resolving `True` as `Trool.True` (typed as `Trool OR Trool` returning `Trool`).
   - In `True == Unknown`, `Unknown` acts as a strong `Trool` anchor in equality, resolving the uncommitted literal `True` directly as `Trool.True`; the operation evaluates as `Trool.True == Trool.Unknown` and returns `Bool False` under exact state-identity equality (§8).
   - In `False == Unknown`, `False` resolves as `Trool.False`, evaluating as `Trool.False == Trool.Unknown` and returning `Bool False` (`False != Unknown` returns `Bool True`).
   - In `my_bool AND True`, the typed `Bool` operand provides `Bool` context, resolving `True` directly as `Bool.True` (evaluating as `Bool`).
   - **Traversal Order Invariance**: Syntactic traversal order must not cause an uncommitted `True` or `False` literal to be prematurely fixed as `Bool` before the full expression's domain constraints are resolved.
5. **Unary NOT Context**: Unary `NOT` propagates its expected result domain to an unresolved `True` or `False` operand when that expected type is known:
   - In `t: Trool = NOT True`, the outer `Trool` expected type propagates through `NOT`, causing `True` to resolve directly as `Trool.True` and `NOT` to evaluate and return `Trool.False`.
   - In a `Bool` context (or when unconstrained), `NOT True` resolves `True` as `Bool.True` and returns `Bool.False`.
   - `NOT` strictly preserves operand typing (`NOT Bool` $\rightarrow$ `Bool`, `NOT Trool` $\rightarrow$ `Trool`) and never retypes an already-typed `Bool` or `Trool` expression.
6. **Outer Compound Expression Context**: Expected type context propagates through compound logical expressions solely to resolve uncommitted `True` and `False` literals. For example, in `t: Trool = True AND False`, the outer `Trool` expectation propagates to both literals, resolving both as `Trool` values and typing the compound `AND` expression as `Trool`.

### Scope and Invariants of Literal Propagation
- **Limited Scope**: This mechanism is limited bidirectional contextual typing of uncommitted truth literals. It is not unrestricted implicit type conversion or general-purpose bidirectional inference.
- **Immutable Typed Expressions**: Already-typed expressions (variables, function calls, or sub-expressions with established static types) are never retyped or coerced by expected-type propagation.
- **Strict Anti-Coercion & TypeErrors Preserved**: Combining an already-typed `Bool` expression with an already-typed `Trool` expression (or with `Unknown`, e.g. `my_bool AND Unknown`, `my_bool == Unknown`, `Unknown != my_bool`) remains a static `TypeError` without explicit `Trool.from_bool()` conversion (§19). Contextual literal resolution applies strictly to raw uncommitted literals, not to already-typed values.
- **Equality Result-Type Barrier**: `==` and `!=` establish a strict boundary between operand typing and result typing. Expected-type context may operate inward to resolve uncommitted `True` or `False` literals used as operands (e.g., `True == Unknown` resolves `True` to `Trool.True`), but operand contextualization never alters the fixed `Bool` result type. An outer expected `Trool` type never crosses the equality result barrier to turn the comparison result into `Trool`.

## 19. Bool and Trool Assignment and Conversion

### Assignment Invariants for Typed Expressions
- **No Implicit Bool-to-Trool Assignment**: An expression whose static type is `Bool` cannot be implicitly assigned to a variable or parameter of type `Trool`. Attempting to do so without explicit conversion is a static `TypeError`.
- **No Implicit Trool-to-Bool Assignment**: An expression whose static type is `Trool` cannot be implicitly assigned to a variable or parameter of type `Bool`. Attempting to do so without explicit conversion is a static `TypeError`.
- **Literal Resolution vs Value Coercion**: Context-sensitive `True` and `False` literals directly construct `Trool` values when `Trool` is the expected type (§18). This contextual literal resolution applies exclusively to literal expressions and is not a value coercion mechanism for already-typed `Bool` expressions.

### Monomorphic Variable Binding and Reassignment
- **Static Monomorphic Typing**: Every variable binding has exactly one static, monomorphic type throughout its lifetime. The language does not permit dynamic variable retagging or union-type inference (`Bool | Trool`).
- **Binding Forms and Type Determination**:
  - **Inferred Initialized Binding (`x = expr`)**: When no type annotation exists, the variable's static type is permanently fixed by its initial type inference (e.g. `flag = True` infers `flag: Bool`).
  - **Annotated Initialized Binding (`x: Type = expr`)**: An explicit type annotation (`Bool` or `Trool`) permanently fixes the variable's static type at declaration (e.g. `flag: Bool = True` or `status: Trool = True`). The annotation provides expected-type context to uncommitted `True` and `False` literals without value coercion (§18).
  - **Reassignment (`x = expr`)**: Reassigning an existing variable uses the identical `x = expr` syntax. The initializer must match the variable's established static type.
  - **Prohibition of Uninitialized Declarations (SyntaxError)**: V1 does not support uninitialized declarations (such as `x: Trool` or `x: Bool` without an initializer). Requiring immediate initialization avoids uninitialized variables and complex definite-assignment analysis.
- **Reassignment Type Invariance**: Subsequent reassignments must preserve the established static type:
  - **Bool Variables**: For a variable `flag` typed as `Bool`, later reassigning `flag = False` is valid (`False` resolves in the established `Bool` context), but `flag = Unknown` is a static `TypeError`.
  - **Trool Variables**: For a variable `t` typed as `Trool`, later reassigning `t = True`, `t = False`, or `t = Unknown` is valid, with `True` and `False` literals resolving directly within the established `Trool` domain.
  - **Cross-Type Reassignments**: Assigning an already-typed `Bool` expression to a `Trool` variable or an already-typed `Trool` expression to a `Bool` variable requires explicit conversion (`Trool.from_bool()`) under penalty of `TypeError`.
- **Value Mutation vs Type Immutability**: Variable values may change across runtime assignments, but the variable's static type does not.

### Function Return Typing and Explicit Annotations
- **Mandatory Explicit Return Annotation for Trool Expressions**: Any function containing a return statement whose resolved static type is `Trool` must explicitly declare an `-> Trool` return type (e.g. `fn get_status() -> Trool:`).
- **Universal Static Type Application**: This rule applies universally to every return expression whose static type resolves to `Trool`, regardless of syntactic shape or expression form:
  - The `Unknown` literal (`return Unknown`).
  - An already-typed `Trool` variable or parameter (`return my_trool`).
  - A function or method call returning `Trool` (`return fetch_status()`).
  - The result of `Trool` logical operations (`return t1 AND t2`, `return t1 OR t2`, `return NOT t1`).
- **Prohibition of Implicit Trool Return Inference (TypeError)**: `Trool` is strictly opt-in (§16) and must never be inferred implicitly as the return type of an unannotated function. Returning any `Trool`-typed expression from a function without an explicit `-> Trool` return annotation is statically invalid and produces a `TypeError`.
- **Expected Return Context**: An explicit `-> Trool` return annotation establishes expected-type context for all return expressions within that function:
  - Under `-> Trool`, `return True` and `return False` resolve directly as `Trool.True` and `Trool.False` via contextual literal resolution (§18).
  - `return Unknown` evaluates as `Trool.Unknown`.
- **Traversal-Order Independence**: Return statements must not be typed sequentially in a way that makes function return type or literal resolution depend on source-order traversal.
- **No Whole-Function Type Promotion**: No implicit whole-function promotion of already-typed `Bool` return expressions to `Trool` occurs. Already-typed `Bool` expressions returned from a `-> Trool` function require explicit conversion (`Trool.from_bool()`).
- **Definite-Return Path Completeness (MissingReturnError)**: Definite-return analysis requires every reachable terminal control-flow path in a function with a declared return type to return a type-compatible value (§11). Using `xen: ignore` satisfies Trool branch exhaustiveness but does not synthesize a return value; any execution path through `xen: ignore` reaching the end of the function without returning produces a `MissingReturnError`.

### Explicit Value Conversion
- **Explicit Bool-to-Trool (`Trool.from_bool`)**:
  - Conceptual explicit conversion is defined as `Trool.from_bool(value)`.
  - Mapping: `Bool False` $\rightarrow$ `Trool False`, and `Bool True` $\rightarrow$ `Trool True`.
  - **Lossless Boundary**: While `Bool`-to-`Trool` conversion is strictly lossless, it must remain explicit in code to preserve the semantic type boundary between binary truth values and 3-valued knowledge states.
- **Explicit Trool-to-Bool (`trool_value.unwrap_bool()`)**:
  - Canonical explicit extraction from `Trool` to `Bool` is defined as `trool_value.unwrap_bool()`.
  - Mapping:
    - `Trool.True.unwrap_bool()` $\rightarrow$ returns `Bool.True`.
    - `Trool.False.unwrap_bool()` $\rightarrow$ returns `Bool.False`.
    - `Trool.Unknown.unwrap_bool()` $\rightarrow$ raises a dedicated runtime `UnknownValueError`.
  - **Explicit Potentially-Failing Extraction**: `unwrap_bool()` is an explicit potentially-failing extraction operation, not an implicit coercion or type cast. The failure on `Unknown` is a runtime extraction error, not a static `TypeError` merely because the source expression has type `Trool`.
  - **No Silent Collapsing**: `Unknown` is never mapped automatically or silently to `True` or `False`.
  - **No Fallback / Collapsing APIs in V1**: V1 does not provide `to_bool(default=...)`, fallback parameters, default-value converters, truthiness conversions, or any other `Unknown`-collapsing convenience API.
  - **Idiomatic Handling**: Application code requiring distinct behavior for `Unknown` should normally use explicit `Trool` control flow (such as `if` / `xen` / `else`) rather than attempting to collapse `Unknown`.
  - **Immutability**: Calling `unwrap_bool()` does not mutate the underlying `Trool` value.

### Logical Expression Typing and Mixed Operations
- **Homogeneous Operations**:
  - `Bool AND Bool` $\rightarrow$ returns `Bool`.
  - `Bool OR Bool` $\rightarrow$ returns `Bool`.
  - `NOT Bool` $\rightarrow$ returns `Bool`.
  - `Trool AND Trool` $\rightarrow$ returns `Trool` (evaluating via Strong Kleene $K_3$).
  - `Trool OR Trool` $\rightarrow$ returns `Trool` (evaluating via Strong Kleene $K_3$).
  - `NOT Trool` $\rightarrow$ returns `Trool` (evaluating via Strong Kleene $K_3$).
- **No Implicit Promotion (TypeError)**: Mixed logical operations (`Bool AND Trool`, `Trool AND Bool`, `Bool OR Trool`, and `Trool OR Bool`) are statically invalid without explicit conversion and must raise a `TypeError`. The compiler must never implicitly promote `Bool` to `Trool` for logical operations.
- **Explicit Conversion Workflow**: To evaluate a `Bool` expression alongside a `Trool` expression, the developer must explicitly convert the `Bool` operand using `Trool.from_bool(value)` (e.g. `Trool.from_bool(b) AND t`). Once converted to `Trool`, Strong Kleene logic rules apply normally.
- **Preservation of Evaluation and Literals**: Left-to-right evaluation, short-circuit semantics (§7), and context-sensitive literal resolution for uncommitted literals (§18) remain strictly preserved.

### Equality Typing and Mixed Comparisons
- **Homogeneous Comparisons**:
  - `Bool == Bool` and `Bool != Bool` are valid and evaluate to `Bool`.
  - `Trool == Trool` and `Trool != Trool` are valid and evaluate to `Bool` (under exact state-identity semantics; `Unknown == Unknown` is `Bool True`).
- **Strict Result-Type Barrier**: Equality (`==`) and inequality (`!=`) always and exclusively return `Bool`. An outer expected `Trool` type never causes the result of a comparison to become `Trool`.
- **TypeError on Direct Assignment to Trool**: In `res: Trool = (val1 == val2)`, the comparison evaluates to `Bool` and assigning it directly to `res` is a static `TypeError`. The developer must explicitly convert the comparison result using `res: Trool = Trool.from_bool(val1 == val2)`.
- **No Implicit Promotion (TypeError)**: Direct equality (`==`) or inequality (`!=`) comparisons between an already-typed `Bool` expression and an already-typed `Trool` expression are statically invalid and must raise a `TypeError`. The compiler must never implicitly promote `Bool` to `Trool` for equality comparisons.
- **Explicit Conversion for Comparison**: To compare a `Bool` expression with a `Trool` expression, the `Bool` operand must be explicitly converted using `Trool.from_bool(value)` (e.g. `Trool.from_bool(b) == t`).
- **Contextual Literal Resolution in Comparisons**:
  - When an already-typed `Trool` operand or an `Unknown` literal is compared directly with an uncommitted literal `True` or `False` (e.g. `my_trool == True`, `True == Unknown`, `False != Unknown`), the literal resolves directly to `Trool.True` or `Trool.False` via contextual resolution (§18), evaluating under Trool state identity (`True == Unknown` $\rightarrow$ `Bool False`).
  - When an already-typed `Bool` operand is compared directly with an uncommitted literal `True` or `False`, the literal resolves directly to `Bool.True` or `Bool.False`.
  - Inward literal contextualization of operands does not alter the fixed `Bool` return type of the comparison.
  - Contextual literal resolution is a static literal construction mechanism, not an implicit value coercion of an already-typed expression.
- **Strictly Binary Invariant & SyntaxError**: Comparisons are strictly binary. Chained comparison syntax (such as `a == b == c` or `a == b != c`) is rejected with a static `SyntaxError` (§8). Multiple comparisons must be written explicitly as conjuncts (e.g. `(a == b) AND (b == c)`).
- **Symmetric Application**: All typing invariants, barrier rules, and error conditions apply symmetrically to both `==` and `!=`.

### Numeric, Bitwise, and Ordering Isolation
- **Non-Numeric Logical Types**: `Bool` and `Trool` are purely logical types with no numeric or integer identity.
- **Prohibition of Arithmetic Operators (TypeError)**: Arithmetic operators (`+`, `-`, `*`, `/`, `%`, and equivalent numeric operations) are strictly forbidden on `Bool` and `Trool` operands. Expressions such as `True + 1`, `Trool.True * 2`, or `Unknown + 0` are static `TypeError`s.
- **Prohibition of Bitwise Operators (TypeError)**: Integer bitwise operators (`&`, `|`, `^`, `~`, `<<`, `>>`) are strictly forbidden on `Bool` and `Trool` operands. Logical conjunction, disjunction, and negation must exclusively use `AND`, `OR`, and `NOT`. Expressions such as `True & False` or `Unknown | True` are static `TypeError`s.
- **Prohibition of Ordering Comparisons (TypeError)**: Ordering comparison operators (`<`, `<=`, `>`, `>=`) are strictly forbidden for `Bool` and `Trool`. Expressions such as `True < False`, `Unknown >= False`, or `Unknown < True` are static `TypeError`s.
- **Preserved Operators**: `==` and `!=` remain valid according to state-identity equality rules (§8), and `AND`, `OR`, and `NOT` remain the canonical logical operators (§7).
- **Isolation from Python Prototype Subtyping**: Python-specific runtime characteristics (such as Python's `bool` subclassing `int` where `True == 1` and `True + 1 == 2`) must never leak into Trool language semantics.
- **Representation Independence**: Low-level runtime representation choices (e.g. byte or integer representation in native or bytecode backends) must not compromise or alter these language-level type restrictions.

## 20. Resolved Items
- **[RESOLVED] Ignore Mechanism Syntax**: Canonical syntax resolved as `xen:` followed by indented `ignore`.
- **[RESOLVED] Python Lowering Strategy**: Explicit three-way identity dispatch over a hygienic single-evaluation temporary variable.
- **[RESOLVED] Trool-to-Bool Conversion API**: Canonical explicit extraction defined as `trool_value.unwrap_bool()`, returning `Bool.True` for `Trool.True`, `Bool.False` for `Trool.False`, and raising a runtime `UnknownValueError` on `Trool.Unknown` without implicit conversion or V1 fallback parameters.
- **[RESOLVED] Python Prototype Runtime Representation**: Standard non-numeric Python `Enum` with internal singleton members `FALSE`, `TRUE`, `UNKNOWN`, exact `is` identity dispatch, explicit rejection of truthiness (`__bool__` raises `TypeError`), and no `int` inheritance.
- **[RESOLVED] Python Prototype Compiler Architecture**: Source-to-source transpiler/compiler targeting standard Python with a deterministic staged pipeline (lexer $\rightarrow$ parser $\rightarrow$ generic AST $\rightarrow$ type resolution $\rightarrow$ semantic validation $\rightarrow$ definite-return analysis $\rightarrow$ Python lowering) with one-way architectural dependencies and standard library preference.
- **[RESOLVED] Variable Binding, Annotation, and Reassignment Syntax**: Initialized inferred binding (`x = expr`), annotated binding (`x: Type = expr` with `Type` in `Bool`, `Trool`), and monomorphic reassignment (`x = expr`), with uninitialized declarations excluded from V1.
- **[RESOLVED] Function Definition, Typed Parameter, Return Annotation, and Return Statement Syntax**: Canonical function definition (`fn name(params) -> Type:`), explicitly typed parameters (`p: Bool | Trool`), syntactically optional return annotation (`-> Bool | Trool`), and value-returning `return expr` statements (bare `return` and non-truth types excluded from V1).

## 21. Unresolved Items (OPEN)
- **[OPEN] Implementation & Architecture (Native Backend & Broader Architecture)**:
  - While the Python prototype architecture and runtime representation are resolved, future native backends, native memory layout, native byte encodings, VM/bytecode formats, native ABI, optimizations, packaging, and non-prototype toolchains remain **OPEN**.
- **[OPEN] Inline / Expression-Level Trool Conditionals**:
  - The current specification defines only statement-level conditional blocks using `if` / `xen` / `else`.
  - No inline or expression-level conditional syntax (such as `a if cond xen b else c`) is currently part of the language specification.
  - Expression-level Trool branching is intentionally deferred until statement-level semantics and the prototype implementation are validated.
  - The future existence, syntax, typing, precedence, associativity, and lowering of inline conditional expressions remain **OPEN**.
- **[OPEN] Chained Comparison Syntax & Semantics**:
  - Chained comparisons (such as `a == b == c` or `a == b != c`) are intentionally excluded from the initial language scope to preserve explicit, minimal binary semantics.
  - Possible future support remains **OPEN** and will require explicitly defining evaluation order, single evaluation of shared middle operands, short-circuit behavior, pairwise typing, literal-context propagation, and semantics for both `==` and `!=`.
- **[OPEN] `elif` Multi-Branch Syntax & Semantics**:
  - `elif` is intentionally excluded from the initial language grammar for both `Bool` and `Trool` conditionals to keep the grammar minimal and explicit.
  - Possible future support remains **OPEN**.
  - Any future `elif` design must strictly preserve the architectural distinction between ordinary multi-branch `Bool` control flow and the dedicated `xen` branch for `Trool` `Unknown` (`elif` must never be used to represent the `Unknown` state).
