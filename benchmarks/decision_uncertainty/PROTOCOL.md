# Decision Uncertainty Benchmark Protocol

## 1. Research Question
Does XoXLang prevent or expose unjustified definitive decisions more reliably than conventional Python approaches (classic and structured) when the underlying proposition remains operationally or epistemically unresolved?

## 2. Threat Model
1. **Operational Failure**: Network timeouts, transport drops, or resource exhaustion causing silent fallback to falsy defaults.
2. **Evidential Conflict**: Contradictory reports from co-equal authorities silently merged or decided via arbitrary last-write-wins.
3. **Context / Temporal Drift**: Stale credentials or cached decisions accepted after environment mutation.
4. **Asymmetric Incomplete Execution**: Tool dispatch or message transmission mistaken for verified state completion.
5. **Accidental Type Coercion**: Truthy evaluation (`if (obj):`) coercing indeterminate objects into `True`.
6. **Contradiction Masking**: Mutually unsatisfiable premises treated as normal failures rather than fail-closed aborts.
7. **Policy-Truth Conflation**: Fallback decisions (`unwrap_or(default)`) falsely recorded as discovered factual truths.

## 3. Compared Paradigms
- **Baseline A (Classic Python)**: Native booleans, `None`, try/except blocks, status strings, default parameter fallbacks.
- **Baseline B (Structured Python)**: Typed enums (`State.TRUE`, `State.FALSE`, `State.UNKNOWN`), `Optional[bool]`, `Result[T, E]`, frozen dataclasses, exhaustive match statements.
- **Target XoX (XoXLang)**: First-class `True`/`False`/`Unknown`, `if`/`xen`/`else` branching, `unwrap_or` with `ResolutionToken`, non-forgeable `DefinednessWitness`, fail-closed contradiction abort.

## 4. Oracle Ground-Truth Model
The Oracle evaluates proposition $P$ across admissible execution realities $W_{\text{factive}}$:
- **TRUE**: $\text{Supp}(P, W_{\text{factive}}) = \{\text{True}\}$.
- **FALSE**: $\text{Supp}(P, W_{\text{factive}}) = \{\text{False}\}$.
- **UNRESOLVED**: $\text{Supp}(P, W_{\text{factive}}) = \{\text{False}, \text{True}\}$. Multiple admissible realities where $P$ is invariant do not constitute UNRESOLVED.
- **CONTRADICTION**: $W_{\text{factive}} = \emptyset$ (mutually unsatisfiable active constraints).
- **COMPOUND_DEFINITE_OPERANDS_UNRESOLVED**: $\text{Supp}(f(P_1, \dots, P_k), W_{\text{factive}}) \in \{\{\text{True}\}, \{\text{False}\}\}$ while $\exists i. \text{Supp}(P_i) = \{\text{False}, \text{True}\}$.

## 5. Primary Safety Metrics (Hard Failures)
- **M1 (Unjustified Definitive Factive Decision)**: Asserting TRUE or FALSE when Oracle is UNRESOLVED or CONTRADICTION.
- **M2 (Silent Uncertainty Loss)**: Indeterminate state disappearing without an explicit, recorded fallback/decision operation.
- **M3 (Contradiction Masking)**: Treating CONTRADICTION as ordinary failure, False, or Unknown instead of fail-closed abort.
- **M4 (Stale Authority Acceptance)**: Accepting an invalidated or replayed token across mutated WorldStateID.

## 6. Secondary Engineering Metrics
- **M5 (Decision-vs-Truth Separation)**: API preserving separation between resolved fact and fallback policy.
- **M6 (Manual Branch Burden)**: Count of explicit manual exception handlers and None guards.
- **M7 (Code Complexity)**: LOC, cyclomatic complexity, helper classes, and custom guards.
- **M8 (Mutation Resistance)**: Number of syntactic mutations survived before safety invariant failure.
- **M9 (Comprehension Accuracy)**: Prediction accuracy of independent evaluators on scenario outputs.

## 7. Falsification Criteria
- **F1**: Baseline B achieves zero M1–M4 failures with lower/equal complexity (M7) and higher mutation resistance (M8) than XoXLang.
- **F2**: Independent developers score higher comprehension (M9) on Python baselines than XoXLang in blind tests.
- **F3**: XoXLang produces M1 false certainty on correlated compound invariants (RW-09) where Baseline B correctly computes joint truth.
