# Independent Developer Comprehension Full Study Protocol

## 1. Study Specification & Goals
- **Study ID**: `XOX_INDEPENDENT_DEVELOPER_COMPREHENSION_FULL_STUDY_001`
- **Scope**: Expanded blind evaluation of developer comprehension, safe modification, and code construction across 3 conditions:
  - `COND_A_PYTHON_CLASSIC` (Binary boolean idiom, `None` for missingness)
  - `COND_B_PYTHON_STRUCTURED` (Ternary enum `TruthVal`, explicit `Verdict` container, manual exception guards)
  - `COND_X_XOXLANG` (Native 3-valued logic, `xen` branch, anti-coercion, `unwrap_or`, fail-closed contradiction)
- **Primary Goal**: Test whether XoXLang preserves comprehension and safety parity with structured Python when evaluators must predict behavior, detect bugs, modify code, construct uncertainty-sensitive flows, and explain core semantic invariants.

## 2. Participant & Cohort Design
- **Total Participants**: N=45 (15 per condition).
- **Subgroups**:
  - `agent_cohort`: N=10 per condition (30 total) — independent coding agents with fresh contexts.
  - `human_cohort`: N=5 per condition (15 total) — experienced software engineers.
- **Isolation**: Single-condition assignment per participant in fresh, isolated sessions. No cross-condition contamination.
- **Primer**: COND_X receives only the frozen `xox_minimal_primer.md` and task prompts. No internal proofs, historical artifacts, or oracle keys.

## 3. Task Categories (20 Tasks Total)
- **T1: Behavior Prediction** (Tasks T1-01 to T1-06): TRUE, FALSE, UNRESOLVED, CONTRADICTION, Policy Fallback, Correlated Compound.
- **T2: Bug Identification** (Tasks T2-01 to T2-04): Guard Omission, Implicit Coercion, Contradiction Masking, Unsafe Operator Composition.
- **T3: Safe Code Modification** (Tasks T3-01 to T3-04): Change Fallback Policy, Add Timeout Handling, Preserve Conflict Provenance, Modify Compound Condition without Collapsing Unknown.
- **T4: Code Construction** (Tasks T4-01 to T4-03): Write Small Authorization Flow, Write Tool-Call Completion Check, Write Uncertainty-Sensitive Branch from Scratch.
- **T5: Plain-Language Explanation** (Tasks T5-01 to T5-03): Unknown vs False, Unknown vs Contradiction, Fact vs Policy Decision.

## 4. Metrics Definition
- **D1 (Semantic Prediction Accuracy %)**: Accuracy across T1 prediction tasks.
- **D2 (Unsafe Modification Rate %)**: Percentage of T3 modifications introducing M1-M4 safety violations.
- **D3 (Truth-vs-Policy Comprehension %)**: Accuracy in distinguishing factual truth state from policy decisions.
- **D4 (Contradiction Comprehension %)**: Accuracy in identifying fail-closed contradiction vs open uncertainty.
- **D5 (Mutation Detection Accuracy %)**: Accuracy across T2 bug identification tasks.
- **D6 (Explanation Quality Mean 0-2)**: Mean rubric score across T5 explanation tasks.
- **D7 (Clarifications Requested)**: Total hint or clarification queries raised by participants.
- **D8 (Conceptual Error Count)**: Total classified conceptual errors from taxonomy.
- **D9 (Safe Code Construction Rate %)**: % of T4 constructed programs free of safety/semantic flaws.
- **D10 (M1-M4 Violations Introduced)**: Absolute count of M1-M4 violations introduced in participant code (T3 & T4).

## 5. Falsification Criteria
- **F2-A**: XoXLang semantic prediction accuracy (D1) is materially below Python Structured.
- **F2-B**: XoXLang unsafe modification rate (D2) is equal to or higher than Python Structured.
- **F2-C**: XoX participants repeatedly confuse Unknown, Contradiction, or fallback semantics.
- **F2-D**: Python Structured achieves equal or better safety/comprehension with fewer conceptual errors and lower learning burden.
- **F2-E**: XoX's structural runtime protections fail to reduce M1-M4 violations in participant-written code.
- **F2-F**: XoX requires substantially more hints or documentation lookups to reach parity.
