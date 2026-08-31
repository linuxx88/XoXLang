# Independent Developer Comprehension Study Protocol

## 1. Research Question
Can an independent developer or coding agent correctly understand, predict, and safely modify uncertainty-sensitive behavior in XoXLang at least as reliably as in conventional Python approaches (Python Classic and Python Structured)?

## 2. Hypotheses Under Test
- **H1**: XoXLang reduces incorrect predictions about unresolved states compared to Python Classic/Structured.
- **H2**: XoXLang makes the distinction between factive truth and policy decisions easier to identify.
- **H3**: XoXLang makes contradiction fail-closed behavior easier to predict.
- **H4**: XoXLang reduces unsafe modifications caused by forgotten uncertainty branches.
- **H5**: XoXLang may impose an initial learning overhead due to unfamiliar ternary syntax (`xen`, `unwrap_or`, `xox(...)`).

## 3. Study Design & Participant Model
- **Study Structure**: 3-condition randomized within-subject or matched between-subject evaluation.
- **Conditions**:
  - `COND_A`: Python Classic (`baseline_a_classic.py`)
  - `COND_B`: Python Structured (`baseline_b_structured.py`)
  - `COND_X`: XoXLang (`target_xox.py` + `xox_minimal_primer.md`)
- **Participant Profile**: General software engineering competence; no prior knowledge of XoXLang internal governance, proofs, or benchmark answers.
- **Fairness Baseline**: Python participants rely on standard Python knowledge. XoX participants receive only `xox_minimal_primer.md` (a 1-page neutral language primer explaining `True`, `False`, `Unknown`, `if`/`xen`/`else`, `unwrap_or`, and `xox(...)`).

## 4. Study Phases
1. **Phase 1: Behavior Prediction** (Tasks DEV-01 to DEV-06)
   Predict execution outcomes, truth states, exception triggers, and fallback behaviors given code snippets and scenario inputs.
2. **Phase 2: Bug Identification** (Tasks DEV-07 to DEV-09)
   Inspect code mutations and identify whether they introduce silent safety violations.
3. **Phase 3: Safe Modification** (Task DEV-10)
   Implement a behavioral requirement while maintaining frozen safety invariants.
4. **Phase 4: Conceptual Explanation**
   Explain in plain language the difference between missing evidence, conflicting evidence, contradiction, and policy fallback.

## 5. Primary & Secondary Metrics
- **D1 (Semantic Prediction Accuracy)**: % of tasks where factive state and runtime behavior are predicted correctly.
- **D2 (Unsafe Modification Rate)**: % of code modifications introducing M1–M4 safety violations.
- **D3 (Truth-vs-Policy Comprehension)**: Accuracy distinguishing factive truth assertions from fallback decisions.
- **D4 (Contradiction Comprehension)**: Accuracy distinguishing fail-closed contradiction from Unknown.
- **D5 (Mutation Detection Accuracy)**: % of safety-violating mutations identified prior to execution.
- **D6 (Explanation Quality)**: Semantic correctness rubric score (0–2 scale).
- **D7 (Required Hints)**: Number of documentation clarifications requested.
- **D8 (Conceptual Error Taxonomy)**: Frequencies of specific misconceptions (e.g. `Unknown == False`, `Contradiction == Unknown`, `Timeout == False`).

## 6. Falsification Criteria
- **F2-A**: If XoXLang achieves lower semantic prediction accuracy (D1) than Baseline B after the minimal primer.
- **F2-B**: If XoXLang produces equal or higher unsafe modification rates (D2) than Baseline B.
- **F2-C**: If participants repeatedly confuse `Unknown`, `Contradiction`, or policy fallbacks under XoXLang.
- **F2-D**: If Baseline B matches XoX safety comprehension with fewer conceptual errors (D8) and zero learning overhead.
