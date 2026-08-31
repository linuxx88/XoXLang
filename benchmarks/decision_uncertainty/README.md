# Decision Uncertainty Benchmark Specification

## 1. Overview
This benchmark evaluates how software systems handle decision-making under operational, evidential, and temporal uncertainty.
It compares three implementation paradigms against an isolated, objective Ground Truth Oracle across 12 realistic failure scenarios:
1. **Baseline A**: Idiomatic classic Python (`bool`, `None`, exceptions, flags, default branches).
2. **Baseline B**: Modern structured Python (`Enum`, `Optional`, `Result[T, E]`, explicit dataclasses, exhaustive pattern matching).
3. **Target XoX**: XoXLang formal ternary semantics (`True`, `False`, `Unknown`, `if`/`xen`/`else`, `unwrap_or`, `DefinednessWitness`, `ResolutionToken`).

---

## 2. Specification Freeze Invariant
- **Status**: `FROZEN_PRE_IMPLEMENTATION`
- **Rule**: This specification and its accompanying JSON definitions (`scenarios.json`, `oracle_spec.json`, `metrics.json`) are strictly frozen before any baseline or target implementation code is authored.
- **Append-Only Modification**: Any future adjustment to scenario parameters or evaluation contracts requires an explicit, audited errata log entry.

---

## 3. Directory Layout
- `README.md`: Overview, reproduction commands, and execution guide.
- `PROTOCOL.md`: Full formal protocol, threat model, metric formulas, and falsification rules.
- `scenarios.json`: Declarative scenario catalog containing inputs, execution triggers, and expected oracle assertions.
- `oracle_spec.json`: Formal mathematical specification of the ground-truth oracle.
- `metrics.json`: Primary safety metrics (M1–M4) and secondary software engineering metrics (M5–M9).
- `baselines/`: Implementations of Baseline A, Baseline B, and Target XoX (to be implemented in subsequent phases).
- `runner.py`: Deterministic test runner executing scenarios and generating compliance matrices.
