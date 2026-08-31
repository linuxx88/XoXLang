# Adversarial Counterexample Matrix for Epistemic Resolution Model

## Document Status & Evaluation Context
- **Status**: `EXPERIMENTAL_NON_NORMATIVE`
- **Target Specification**: `experiments/EPISTEMIC_RESOLUTION_MODEL.md` (Frozen Reference)
- **Role**: Closed adversarial falsification test suite.
- **Rules of Evaluation**:
  1. All derivations are evaluated strictly against the frozen axioms, domain definitions, and invariants of `EPISTEMIC_RESOLUTION_MODEL.md`.
  2. No modifications, extensions, or ad-hoc repairs are made to the target specification.
  3. Outcomes are classified strictly as:
     - `PASS`: The existing frozen model uniquely and unambiguously derives a safe, internally consistent outcome.
     - `NEEDS_REVISION`: The model is underspecified, permits multiple valid behaviors, or has signature gaps requiring formal refinement.
     - `FAIL`: The model permits an unsafe, unsound, or contradictory outcome.

---

## 1. Adversarial Test Matrix

### CTX-01: Unknown Resolving to True
- **Initial State**: Claim $q = (P, \eta, \phi)$, journal $\mathcal{L}_0$, $\text{Eval}(q, \text{Adm}(\mathcal{L}_0, \eta, \phi)) = (\text{Unknown}, \pi_0, \{\omega_1\})$.
- **Invariants Tested**: Invariants 2, 7, 8, 10; Section 6.2 (8-step pipeline).
- **Execution Trace**:
  1. $\text{Obl}(q, E_0) = \{\omega_1\}$.
  2. Canonical contract $\kappa = \text{Contract}_\eta(q, \{\omega_1\}, \phi)$.
  3. $\text{Acquire}(\kappa) \rightsquigarrow \{c_1\} \subset \mathcal{C}$ with payload confirming $P$.
  4. $\text{Validate}(\{c_1\}) \to (\Delta \mathcal{E}v_{\text{acc}} = \{e_1\}, \Delta \mathcal{A}ud_{\text{val}} = \emptyset, \Delta_{\text{val}} = \emptyset)$.
  5. Journal appends $\text{EvEntry}(e_1) \to \mathcal{L}_1$; $E_1 = \text{Adm}(\mathcal{L}_1, \eta, \phi)$.
  6. $\text{Eval}(q, E_1) = (\text{True}, \pi_1, \emptyset)$.
- **Expected Output**: $(\mathcal{L}_1, r_1)$ where $r_1 = (\text{True}, \pi_1, \emptyset, \emptyset) \in \mathcal{R}es$.
- **Verdict**: `PASS`

---

### CTX-02: Unknown Resolving to False
- **Initial State**: Claim $q = (P, \eta, \phi)$, $\text{Eval}(q, \text{Adm}(\mathcal{L}_0, \eta, \phi)) = (\text{Unknown}, \pi_0, \{\omega_1\})$.
- **Invariants Tested**: Invariants 2, 7, 8, 10; Section 6.2.
- **Execution Trace**:
  1. $\text{Acquire}(\kappa) \rightsquigarrow \{c_{\text{refute}}\} \subset \mathcal{C}$ with disconfirming payload.
  2. $\text{Validate}(\{c_{\text{refute}}\}) \to (\Delta \mathcal{E}v_{\text{acc}} = \{e_{\text{refute}}\}, \Delta \mathcal{A}ud_{\text{val}} = \emptyset, \Delta_{\text{val}} = \emptyset)$.
  3. $\mathcal{L}_1 = \mathcal{L}_0 \mathbin{+\!\!+} [\text{EvEntry}(e_{\text{refute}})]$; $E_1 = \text{Adm}(\mathcal{L}_1, \eta, \phi)$.
  4. $\text{Eval}(q, E_1) = (\text{False}, \pi_{\text{refute}}, \emptyset)$.
- **Expected Output**: $(\mathcal{L}_1, r_1)$ where $r_1 = (\text{False}, \pi_{\text{refute}}, \emptyset, \emptyset) \in \mathcal{R}es$.
- **Verdict**: `PASS`

---

### CTX-03: Insufficient Acquired Evidence
- **Initial State**: Claim $q = (P, \eta, \phi)$, $\text{Eval}(q, E_0) = (\text{Unknown}, \pi_0, \{\omega_A, \omega_B\})$.
- **Invariants Tested**: Invariants 6, 7; Section 6.4 (Single-attempt invariant).
- **Execution Trace**:
  1. $\text{Acquire}(\kappa) \rightsquigarrow \{c_A\}$ satisfying $\omega_A$ only; query for $\omega_B$ returns no candidate.
  2. $\text{Validate}$ accepts $e_A \in \mathcal{E}v$.
  3. $\mathcal{L}_1 = \mathcal{L}_0 \mathbin{+\!\!+} [\text{EvEntry}(e_A)]$; $E_1 = \text{Adm}(\mathcal{L}_1, \eta, \phi)$.
  4. $\text{Eval}(q, E_1) = (\text{Unknown}, \pi_1, \{\omega_B\})$.
- **Expected Output**: $(\mathcal{L}_1, r_1)$ where $r_1 = (\text{Unknown}, \pi_1, \{\omega_B\}, \emptyset) \in \mathcal{R}es$.
- **Verdict**: `PASS`

---

### CTX-04: Acquisition Network Timeout & Diagnostic Journaling
- **Initial State**: Claim $q = (P, \eta, \phi)$, $\text{Eval}(q, E_0) = (\text{Unknown}, \pi_0, \{\omega_1\})$.
- **Invariants Tested**: Invariant 1 (Three-valued closed domain), Invariant 8 (Separation of $\Omega$ and $\Delta$), Section 5.3 ($\text{Auditize}$), Section 6.2 (Step 6 & 7).
- **Execution Trace**:
  1. $\text{Acquire}(\kappa)$ times out, outputting $(\mathcal{C}_{\text{cand}} = \emptyset, \Delta_{\text{acq}} = [\text{TimeoutDiag}])$.
  2. $\text{Validate}(\emptyset, \mathcal{L}_0, \eta, \phi, \kappa)$ processes candidate set $\emptyset$, yielding $(\Delta \mathcal{E}v_{\text{acc}} = \emptyset, \Delta \mathcal{A}ud_{\text{val}} = \emptyset, \Delta_{\text{val}} = \emptyset)$.
  3. $\text{Auditize}$ maps acquisition diagnostics: $\Delta \mathcal{A}ud_{\text{acq}} = \text{Auditize}([\text{TimeoutDiag}], t_{\text{rec}}) = [\text{TimeoutAudit}]$.
  4. Journal ingestion appends $\mathcal{L}_1 = \mathcal{L}_0 \mathbin{+\!\!+} [\text{AuditEntry}(\text{TimeoutAudit})]$; $\text{Adm}(\mathcal{L}_1, \eta, \phi) = E_0$.
  5. Step 8 re-evaluation against $E_0$ preserves $\text{Eval}(q, E_0) = (\text{Unknown}, \pi_0, \{\omega_1\})$.
  6. Pipeline returns $(\mathcal{L}_1, r_1)$ where $r_1 = (\text{Unknown}, \pi_0, \{\omega_1\}, [\text{TimeoutDiag}]) \in \mathcal{R}es$.
- **Expected Output**: $(\mathcal{L}_1, (\text{Unknown}, \pi_0, \{\omega_1\}, [\text{TimeoutDiag}]))$.
- **Verdict**: `PASS`

---

### CTX-05: Invalid Candidate Signature
- **Initial State**: Claim $q = (P, \eta, \phi)$, $\text{Eval}(q, E_0) = (\text{Unknown}, \pi_0, \{\omega_1\})$.
- **Invariants Tested**: Invariants 8, 9; Section 5.2 (Primary validation boundary).
- **Execution Trace**:
  1. $\text{Acquire}(\kappa) \rightsquigarrow \{c_{\text{bad\_sig}}\} \subset \mathcal{C}$.
  2. $\text{Validate}$ detects cryptographic signature invalidity under policy $\eta$.
  3. Candidate is discarded; $\Delta \mathcal{A}ud_{\text{val}} = [\text{SignatureFailureAudit}]$, $\Delta_{\text{val}} = [\text{UntrustedSourceDiag}]$.
  4. $\mathcal{L}_1 = \mathcal{L}_0 \mathbin{+\!\!+} [\text{AuditEntry}(\text{SignatureFailureAudit})]$.
  5. Re-evaluation against unchanged $E_0$ preserves $(\text{Unknown}, \pi_0, \{\omega_1\})$.
- **Expected Output**: $(\mathcal{L}_1, r_1)$ where $r_1 = (\text{Unknown}, \pi_0, \{\omega_1\}, [\text{UntrustedSourceDiag}]) \in \mathcal{R}es$.
- **Verdict**: `PASS`

---

### CTX-06: Candidate with Cyclic Provenance
- **Initial State**: Claim $q = (P, \eta, \phi)$, $\text{Eval}(q, E_0) = (\text{Unknown}, \pi_0, \{\omega_1\})$.
- **Invariants Tested**: Invariants 8, 9; Section 5.2.
- **Execution Trace**:
  1. $\text{Acquire}(\kappa) \rightsquigarrow \{c_{\text{cyclic}}\}$ where $\Gamma_{\text{raw}}$ contains cycle $e_a \to e_b \to e_a$.
  2. $\text{Validate}$ executes DAG topological sort, detects cycle, rejects candidate.
  3. Discards candidate; appends $\text{AuditEntry}(\text{CycleDetectedAudit})$ to $\mathcal{L}_1$.
  4. Re-evaluation yields $(\text{Unknown}, \pi_0, \{\omega_1\})$.
- **Expected Output**: $(\mathcal{L}_1, r_1)$ where $r_1 = (\text{Unknown}, \pi_0, \{\omega_1\}, [\text{CyclicProvenanceDiag}]) \in \mathcal{R}es$.
- **Verdict**: `PASS`

---

### CTX-07: Candidate Outside Fixed Observation Frame
- **Initial State**: Claim $q = (P, \eta, \phi)$ with $I_{\text{frame}} = [t_0, t_0 + \Delta t]$; $\text{Eval}(q, E_0) = (\text{Unknown}, \pi_0, \{\omega_1\})$.
- **Invariants Tested**: Section 3.2 (Bitemporal interval model), Section 5.2.
- **Execution Trace**:
  1. $\text{Acquire}(\kappa) \rightsquigarrow \{c_{\text{stale}}\}$ with $I_{\text{valid}}(c_{\text{stale}}) = [t_{-10}, t_{-5}]$.
  2. $\text{Validate}$ tests interval relation $\mathcal{R}_{\text{temp}}^\eta([t_{-10}, t_{-5}], I_{\text{frame}}) = \text{False}$.
  3. Candidate is rejected at the validation boundary; appends $\text{AuditEntry}(\text{OutOfFrameAudit})$ to $\mathcal{L}_1$.
  4. Admissible evidence view $E_0$ is unchanged; $\text{Eval}$ yields $(\text{Unknown}, \pi_0, \{\omega_1\})$.
- **Expected Output**: $(\mathcal{L}_1, r_1)$ where $r_1 = (\text{Unknown}, \pi_0, \{\omega_1\}, [\text{OutOfFrameDiag}]) \in \mathcal{R}es$.
- **Verdict**: `PASS`

---

### CTX-08: Unexpected Runtime World Mutation During Acquisition
- **Initial State**: Claim $q = (P, \eta, \phi)$, initial evaluation $\text{Eval}(q, E_0) = (\text{Unknown}, \pi_0, \{\omega_1\})$.
- **Invariants Tested**: Invariant 11 (Claim-Relevant Non-Interference), Section 5.5 (Post-execution mutation semantics), Section 6.2 (Step 8).
- **Execution Trace**:
  1. Acquisition probe unexpectedly mutates proposition-relevant world state: $\text{Proj}_P(\sigma(\text{world}_{\text{post}})) \neq \text{Proj}_P(\sigma(\text{world}_{\text{pre}}))$.
  2. Observation frame $\phi$ is invalidated; all candidates produced by the interfering acquisition are discarded ($\Delta \mathcal{E}v_{\text{acc}} = \emptyset$).
  3. $\Delta_{\text{acq}} = [\text{FrameInvalidatedDiag}]$; $\Delta \mathcal{A}ud_{\text{mut}} = \text{Auditize}([\text{FrameInvalidatedDiag}], t_{\text{rec}})$.
  4. Journal ingestion appends $\mathcal{L}_{\text{final}} = \mathcal{L}_0 \mathbin{+\!\!+} [\text{AuditEntry}(\text{FrameInvalidatedAudit})]$.
  5. Step 8 Frame Invalidation Branch executes: no re-evaluation of $q$ occurs after frame invalidation; prior evaluation $(v_0 = \text{Unknown}, \pi_0, \{\omega_1\})$ is preserved.
  6. Pipeline returns $(\mathcal{L}_{\text{final}}, r_{\text{inval}})$ where $r_{\text{inval}} = (\text{Unknown}, \pi_0, \{\omega_1\}, [\text{FrameInvalidatedDiag}]) \in \mathcal{R}es$.
  7. Any continuation against the changed world state strictly requires a distinct claim $q' = (P, \eta, \phi_{\text{new}})$.
- **Expected Output**: $(\mathcal{L}_{\text{final}}, (\text{Unknown}, \pi_0, \{\omega_1\}, [\text{FrameInvalidatedDiag}]))$.
- **Verdict**: `PASS`

---

### CTX-09: Unproven Non-Interference Probe (Pre-Execution)
- **Initial State**: Claim $q = (P, \eta, \phi)$, $\text{Eval}(q, E_0) = (\text{Unknown}, \pi_0, \{\omega_1\})$.
- **Invariants Tested**: Invariant 11; Section 5.5 (Fail-closed non-interference rule).
- **Execution Trace**:
  1. Probe method has underspecified projection boundary: $\text{ProvableNonInterference}(\text{method}, P, \phi) = \text{Bool.False}$.
  2. Fail-closed rule strictly forbids probe execution prior to execution.
  3. Discards probe method; appends $\text{AuditEntry}(\text{UnprovenInterferenceAudit})$ to $\mathcal{L}_1$.
  4. Re-evaluation yields $(\text{Unknown}, \pi_0, \{\omega_1\})$.
- **Expected Output**: $(\mathcal{L}_1, r_1)$ where $r_1 = (\text{Unknown}, \pi_0, \{\omega_1\}, [\text{UnprovenInterferenceDiag}]) \in \mathcal{R}es$.
- **Verdict**: `PASS`

---

### CTX-10: Evaluator Version Drift During Resolution
- **Initial State**: Claim $q = (P, \eta_{\text{v1}}, \phi)$, initial evaluation $(v_0 = \text{Unknown}, \pi_0, \{\omega_1\})$.
- **Invariants Tested**: Section 2.2 (Claim identity invariance & evaluator drift abort), Invariant 10, Section 6.2 (Step 8).
- **Execution Trace**:
  1. Runtime attempts to evaluate step 8 under $\eta_{\text{v2}} \neq \eta_{\text{v1}}$.
  2. Step 8 Evaluator Drift Branch detects attempted version mutation and immediately aborts fail-closed.
  3. No evaluation occurs under $\eta_{\text{v2}}$ or after drift detection; prior evaluation $(v_0, \pi_0, \Omega_0)$ under $\eta_{\text{v1}}$ is preserved.
  4. $\Delta_{\text{drift}} = [\text{EvaluatorDriftDiag}]$; $\Delta \mathcal{A}ud_{\text{drift}} = \text{Auditize}(\Delta_{\text{drift}}, t_{\text{rec}})$.
  5. Journal becomes $\mathcal{L}_{\text{final}} = \mathcal{L}' \mathbin{+\!\!+} [\text{AuditEntry}(\text{EvaluatorDriftAudit})]$.
  6. $\Delta_{\text{total}} = \Delta_{\text{acq}} \mathbin{+\!\!+} \Delta_{\text{val}} \mathbin{+\!\!+} [\text{EvaluatorDriftDiag}]$.
  7. Pipeline returns $(\mathcal{L}_{\text{final}}, r_{\text{abort}})$ where $r_{\text{abort}} = (\text{Unknown}, \pi_0, \{\omega_1\}, \Delta_{\text{total}}) \in \mathcal{R}es$.
  8. Evaluation under $\eta_{\text{v2}}$ requires construction of distinct claim $q' = (P, \eta_{\text{v2}}, \phi)$.
- **Expected Output**: $(\mathcal{L}_{\text{final}}, (\text{Unknown}, \pi_0, \{\omega_1\}, \Delta_{\text{total}}))$.
- **Verdict**: `PASS`

---

### CTX-11: Observation Frame Drift During Resolution
- **Initial State**: Claim $q = (P, \eta, \phi_1)$.
- **Invariants Tested**: Section 2.2; Section 11 (resolve vs revalidate boundary).
- **Execution Trace**:
  1. System attempts to re-evaluate $q$ against a shifted temporal window $\phi_2 = (I_{\text{frame}}', \sigma, C)$.
  2. Specification defines frame $\phi$ as invariant during `resolve`.
  3. Evaluating under $\phi_2$ constitutes cross-frame `revalidate` of a new claim $(P, \eta, \phi_2)$, not `resolve` of $q$.
  4. `resolve` continues strictly with $\phi_1$.
- **Expected Output**: Invariance of $\phi_1$ preserved across all 8 pipeline steps.
- **Verdict**: `PASS`

---

### CTX-12: Direct Resolver Truth Injection
- **Initial State**: Claim $q = (P, \eta, \phi)$, $\text{Eval}(q, E_0) = (\text{Unknown}, \pi_0, \{\omega_1\})$.
- **Invariants Tested**: Invariant 2 (Sole Evaluation Authority), Invariant 3 (No Direct Truth Coercion).
- **Execution Trace**:
  1. A resolver implementation attempts to return $r = (\text{True}, \text{None}, \emptyset, \emptyset)$ directly without executing $\text{Eval}(q, E')$.
  2. Specification prohibits truth emission from any component other than $\text{Eval}$.
  3. Transition relation $(q, \mathcal{L}) \xrightarrow{\text{resolve}} (\mathcal{L}', r)$ mandates $v = \text{Val}(q, E')$.
- **Expected Output**: Transition rejected as structurally invalid; resolver has zero truth authority.
- **Verdict**: `PASS`

---

### CTX-13: Resolution Attempt on Naked XoX Scalar
- **Initial State**: An unanchored value $x: \text{XoX} = \text{Unknown}$.
- **Invariants Tested**: Invariant 4 (Target Specificity), Section 2.2.
- **Execution Trace**:
  1. Caller attempts to invoke $\text{resolve}(x)$.
  2. $x$ lacks proposition AST $P$, evaluator version $\eta$, and observation frame $\phi$.
  3. $\text{Contract}_\eta(q, \Omega, \phi)$ and $\text{Eval}(q, E)$ cannot be computed without $q = (P, \eta, \phi) \in \mathcal{Q}$.
- **Expected Output**: Static / semantic rejection; `resolve` requires fully qualified claim $q \in \mathcal{Q}$.
- **Verdict**: `PASS`

---

### CTX-14: Admissible Local Evidential Conflict with No Policy Tie-Break
- **Initial State**: Claim $q = (P, \eta, \phi)$, admissible observational evidence $E = \{e_{\text{true}}, e_{\text{false}}\}$ both admitted by $\text{Adm}$ in an open world with non-empty admissible alternatives ($|W_{\text{factive}}| \ge 2$).
- **Invariants Tested**: Invariant 1 (Three-valued closed domain), Invariant 12; Section 4.6.
- **Execution Trace**:
  1. $\text{Adm}(\mathcal{L}, \eta, \phi)$ admits both $e_{\text{true}}$ and $e_{\text{false}}$.
  2. Evaluator policy $\eta$ contains no dispute-resolution rule to break the conflict.
  3. $\text{Eval}(q, E)$ evaluates modularly to $(\text{Unknown}, \pi_{\text{conflict}}, \{\omega_{\text{conflict}}(P)\})$.
  4. System does not invent a fourth truth state (e.g. "Bottom" or "Conflicted"); open evidential conflict remains `Unknown`.
- **Expected Output**: $(\mathcal{L}, r)$ where $r = (\text{Unknown}, \pi_{\text{conflict}}, \{\omega_{\text{conflict}}(P)\}, \emptyset) \in \mathcal{R}es$.
- **Verdict**: `PASS`

---

### CTX-15: Evidential Conflict Resolved Deterministically by Policy
- **Initial State**: Claim $q = (P, \eta, \phi)$, admissible evidence $E = \{e_{\text{tier1\_false}}, e_{\text{tier2\_true}}\}$.
- **Invariants Tested**: Invariant 2; Section 4.6 (Deterministic policy resolution).
- **Execution Trace**:
  1. Policy $\eta$ contains an explicit hierarchical dispute-resolution rule: Tier-1 authority overrides Tier-2 authority.
  2. $\text{Eval}(q, E)$ applies the policy rule deterministically, yielding $\text{False}$ with proof certificate $\pi_{\text{tier\_rule}}$.
  3. $\text{Obl}(q, E) = \emptyset$.
- **Expected Output**: $(\mathcal{L}, r)$ where $r = (\text{False}, \pi_{\text{tier\_rule}}, \emptyset, \emptyset) \in \mathcal{R}es$.
- **Verdict**: `PASS`

---

### CTX-16: Strong Kleene Conjunction: Unknown AND False
- **Initial State**: Proposition $P = A \land B$, subclaims $\text{Val}(A) = \text{Unknown}$, $\text{Val}(B) = \text{False}$.
- **Invariants Tested**: Invariant 6 (Total claim domain), Invariant 12; Section 4.4, Section 4.5.
- **Execution Trace**:
  1. $\text{Val}((A \land B, \eta, \phi), E) = \text{Unknown} \land_{K_3} \text{False} = \text{False}$.
  2. $\text{Obl}(A \land B, E) = \emptyset$ (unresolved subclaim $A$ is pruned).
  3. Step 2 short-circuit executes: no acquisition attempted.
- **Epistemic vs Operational Semantics Note**: In the epistemic resolution model, dominant subclaims mathematically prune active acquisition obligations. In concrete XoXLang program execution (XOX_SPEC §7, §7.1), expressions evaluate strictly left-to-right: `Unknown AND False` evaluates the left operand before reaching `False`, whereas `False AND Unknown` short-circuits immediately. While $K_3$ value-equivalent (`False`), they are not observably equivalent if operands carry side effects under the Strict Operational Trace Preservation Invariant (§7.1).
- **Expected Output**: $(\mathcal{L}, r)$ where $r = (\text{False}, \pi_{\land}, \emptyset, \emptyset) \in \mathcal{R}es$.
- **Verdict**: `PASS`

---

### CTX-17: Strong Kleene Disjunction: Unknown OR True
- **Initial State**: Proposition $P = A \lor B$, subclaims $\text{Val}(A) = \text{Unknown}$, $\text{Val}(B) = \text{True}$.
- **Invariants Tested**: Section 4.4, Section 4.5; Invariant 6.
- **Execution Trace**:
  1. $\text{Val}((A \lor B, \eta, \phi), E) = \text{Unknown} \lor_{K_3} \text{True} = \text{True}$.
  2. $\text{Obl}(A \lor B, E) = \emptyset$ (subclaim $A$ pruned).
  3. Step 2 short-circuit executes: no acquisition attempted.
- **Epistemic vs Operational Semantics Note**: Symmetrically to conjunction, the epistemic resolution model prunes acquisition obligations for $A$ upon finding dominant $\text{Val}(B) = \text{True}$. In language runtime execution (XOX_SPEC §7, §7.1), `Unknown OR True` executes the left operand before evaluating `True`, whereas `True OR Unknown` short-circuits on the left operand. Both yield value $K_3$ `True`, but produce distinct observable execution traces when operands have side effects under Operational Trace Preservation (§7.1).
- **Expected Output**: $(\mathcal{L}, r)$ where $r = (\text{True}, \pi_{\lor}, \emptyset, \emptyset) \in \mathcal{R}es$.
- **Verdict**: `PASS`

---

### CTX-18: Strong Kleene Conjunction: Unknown AND Unknown
- **Initial State**: Proposition $P = A \land B$, subclaims $\text{Val}(A) = \text{Unknown}$, $\text{Val}(B) = \text{Unknown}$.
- **Invariants Tested**: Section 4.4, Section 4.5.
- **Execution Trace**:
  1. $\text{Val}(P, E) = \text{Unknown} \land_{K_3} \text{Unknown} = \text{Unknown}$.
  2. Obligations tracked conservatively: $\text{Obl}(P, E) = \text{Obl}(A) \cup \text{Obl}(B)$.
  3. $\text{resolve}$ derives contract $\kappa = \text{Contract}_\eta(q, \text{Obl}(P, E), \phi)$ and queries witness sources for both subclaims.
- **Expected Output**: Valid transition seeking evidence for active obligations in $\text{Obl}(A) \cup \text{Obl}(B)$.
- **Verdict**: `PASS`

---

### CTX-19: Strong Kleene Disjunction: Unknown OR Unknown
- **Initial State**: Proposition $P = A \lor B$, subclaims $\text{Val}(A) = \text{Unknown}$, $\text{Val}(B) = \text{Unknown}$.
- **Invariants Tested**: Section 4.4, Section 4.5.
- **Execution Trace**:
  1. $\text{Val}(P, E) = \text{Unknown} \lor_{K_3} \text{Unknown} = \text{Unknown}$.
  2. Obligations tracked conservatively: $\text{Obl}(P, E) = \text{Obl}(A) \cup \text{Obl}(B)$.
  3. $\text{Contract}_\eta$ executes canonical acquisition policy over $\text{Obl}(P, E)$.
- **Expected Output**: Valid transition seeking evidence across active atomic obligations.
- **Verdict**: `PASS`

---

### CTX-20: Nested K3 Proposition with Decision-Irrelevant Subclaim
- **Initial State**: Proposition $P = (A \land \text{False}) \lor B$, where subclaim $A$ is unresolved with local evidential conflict ($|W_{\text{factive}}| \ge 2$), and subclaim $B$ evaluates to $\text{True}$.
- **Invariants Tested**: Section 4.3 (Modular subclaim truth), Section 4.4, Section 4.6.
- **Execution Trace**:
  1. Local evaluation of $A$: $\text{Val}(A) = \text{Unknown}$ (evidential ambiguity).
  2. Left conjunct: $\text{Val}(A \land \text{False}) = \text{Unknown} \land_{K_3} \text{False} = \text{False}$.
  3. Root evaluation: $\text{Val}(P) = \text{False} \lor_{K_3} \text{Val}(B) = \text{False} \lor_{K_3} \text{True} = \text{True}$.
  4. All obligations pruned: $\text{Obl}(P, E) = \emptyset$. Ambiguity on $A$ is completely decision-irrelevant to root.
- **Expected Output**: $(\mathcal{L}, r)$ where $r = (\text{True}, \pi_{\text{nested}}, \emptyset, \emptyset) \in \mathcal{R}es$.
- **Verdict**: `PASS`

---

### CTX-21: Concurrent Resolution with Admissible View Drift
- **Initial State**: Task 1 and Task 2 concurrently resolve claim $q$ against snapshot $\mathcal{L}_0$.
- **Invariants Tested**: Invariant 13 (Snapshot Isolation), Section 7.
- **Execution Trace**:
  1. Task 1 validates candidates and appends $\Delta_1$ to $\mathcal{L}$, producing $\mathcal{L}_1$. $\text{Adm}(\mathcal{L}_1, \eta, \phi) = E_1 \neq E_0$.
  2. Task 2 finishes evaluation against stale snapshot $E_0$ and attempts to publish decision $r_{\text{stale}}$.
  3. Anti-staleness publication rule detects that admissible view for $(q, \phi)$ has drifted ($E_1 \neq E_0$).
  4. Publication from stale snapshot is aborted; Task 2 must re-evaluate against $E_1$ before committing.
- **Expected Output**: Stale decision publication blocked; re-evaluation against fresh admissible snapshot enforced.
- **Verdict**: `PASS`

---

### CTX-22: Concurrent Audit-Only Append
- **Initial State**: Task 1 resolves claim $q$; concurrently, Task 2 appends $\text{AuditEntry}(a_{\text{diag}})$ to $\mathcal{L}$.
- **Invariants Tested**: Section 3.3 (Audit isolation), Section 7.
- **Execution Trace**:
  1. Journal becomes $\mathcal{L}' = \mathcal{L} \mathbin{+\!\!+} [\text{AuditEntry}(a_{\text{diag}})]$.
  2. Task 1 verifies admissible view: $\text{Adm}(\mathcal{L}', \eta, \phi) = \text{Adm}(\mathcal{L}, \eta, \phi) = E$.
  3. Because audit entries are filtered out by $\text{Adm}$, evidence view $E$ did not drift.
  4. Task 1 commits and publishes its decision $r$ safely.
- **Expected Output**: Valid publication without false conflict abort.
- **Verdict**: `PASS`

---

### CTX-23: Malicious Acquirer Source Cherry-Picking
- **Initial State**: Claim $q = (P, \eta, \phi)$, canonical contract $\kappa = (\mathcal{S}_{\text{allowed}}, \mathcal{M}_{\text{allowed}}, k_{\text{wit}}, B_{\text{res}})$.
- **Invariants Tested**: Section 5.2, Section 5.4; Invariant 9.
- **Execution Trace**:
  1. Acquirer ignores $\mathcal{S}_{\text{allowed}}$ and queries an unauthorized biased source $s_{\text{rogue}} \notin \mathcal{S}_{\text{allowed}}$.
  2. Acquirer returns candidate $c_{\text{rogue}} \in \mathcal{C}$.
  3. $\text{Validate}$ checks source against $\kappa$, identifies unauthorized source, and rejects candidate.
  4. Appends $\text{AuditEntry}(\text{ContractBreachAudit})$; admissible evidence view unchanged.
  5. Resolution fails closed to $(\text{Unknown}, \pi_0, \Omega_{\text{eval}}, [\text{ContractBreachDiag}])$.
- **Expected Output**: Rogue candidate rejected; system fails closed to `Unknown`.
- **Verdict**: `PASS`

---

### CTX-24: Malformed Candidate Attempting Validate Bypass
- **Initial State**: External provider attempts to inject malformed raw data directly into journal $\mathcal{L}$.
- **Invariants Tested**: Invariant 9 (Candidate Domain Barrier), Section 5.2.
- **Execution Trace**:
  1. Raw candidate data inhabits $\mathcal{C}$, not $\mathcal{E}v$.
  2. Journal entries of type $\text{EvEntry}(e)$ require typed $e \in \mathcal{E}v$.
  3. Only the $\text{Validate}$ operator possesses the signature to produce $\mathcal{E}v$ events.
  4. Direct injection without $\text{Validate}$ is type-theoretically impossible under the domain definitions.
- **Expected Output**: Structural/type-level rejection; domain barrier strictly enforced.
- **Verdict**: `PASS`

---

### CTX-25: Operational AuditEntry Attempting to Influence Eval
- **Initial State**: Journal $\mathcal{L}$ contains multiple $\text{AuditEntry}(a)$ records detailing past failures.
- **Invariants Tested**: Section 3.3 (Strict Audit Isolation), Section 4.2.
- **Execution Trace**:
  1. $\text{Adm}(\mathcal{L}, \eta, \phi)$ projects exclusively over $\text{EvEntry}(e)$ items.
  2. For all $a \in \mathcal{A}ud$, $\text{AuditEntry}(a)$ is stripped by $\text{Adm}$ and cannot inhabit $E$.
  3. $\text{Eval}(q, E)$ receives only $E \subseteq \mathcal{E}v$.
- **Expected Output**: Audit records have zero mathematical influence on $\text{Eval}$.
- **Verdict**: `PASS`

---

### CTX-26: Repeated Explicit Resolve Invocations
- **Initial State**: Claim $q = (P, \eta, \phi)$, initial journal $\mathcal{L}_0$.
- **Invariants Tested**: Invariant 5 (Atomic Single Attempt), Section 6.4.
- **Execution Trace**:
  1. Invocation 1: $\text{resolve}(q, \mathcal{L}_0) \to (\mathcal{L}_1, r_1)$ with $v_1 = \text{Unknown}$ (single acquisition attempt).
  2. Invocation 2: $\text{resolve}(q, \mathcal{L}_1) \to (\mathcal{L}_2, r_2)$ with $v_2 = \text{True}$ (single acquisition attempt).
  3. Invocation 3: $\text{resolve}(q, \mathcal{L}_2) \to (\mathcal{L}_2, r_3)$ with $v_3 = \text{True}$ (determinate short-circuit, zero acquisition).
  4. No invocation executes an implicit retry loop; repeated resolution is explicitly orchestrated by caller.
- **Expected Output**: Each individual call satisfies the single-attempt invariant deterministically.
- **Verdict**: `PASS`

---

### CTX-27: Unproven Universe Closure Preserving Unknown on Empty Search
- **Initial State**: Claim $q = (P_{\text{exist}}, \eta, \phi)$ where $P_{\text{exist}} = \exists x.\, R(x)$, initial journal $\mathcal{L}_0$, $\text{Eval}(q, \text{Adm}(\mathcal{L}_0, \eta, \phi)) = (\text{Unknown}, \pi_0, \{\omega_{\text{witness}}\})$.
- **Invariants Tested**: Invariant 1 (Three-valued closed domain), Invariant 14 (Evidence of Absence Requirement), Section 5.1 (Open-World Principle), Section 5.5, Section 5.6.
- **Execution Trace**:
  1. $\text{Acquire}(\kappa)$ executes query over an apparently relevant data source $\mathcal{S}$, returning an empty candidate witness set ($\mathcal{C}_{\text{cand}} = \emptyset$).
  2. The source provides no validated CoverageCertificate $\chi$ proving that search universe $\mathcal{U}$ is exhaustive/closed for relation $R$ over $I_{\text{frame}}(\phi)$ with $\text{CoversClaimScope} = \text{True}$.
  3. In the absence of a validated coverage event $e_\chi \in E$, condition 4 of $\text{IsValidNegativeCertificate}$ fails; hence $N_-(q, E) = \emptyset$.
  4. Both deterministic collections are empty: $W_+(q, E) = \emptyset$ and $N_-(q, E) = \emptyset$.
  5. Step 8 evaluation yields $\text{Eval}(q, E) = (\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{unproven\_closure}}(\mathcal{U})\})$.
  6. Empty search over an unverified or open source cannot establish `False`. Open-world semantics are strictly preserved.
- **Expected Output**: $(\mathcal{L}', (\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{unproven\_closure}}(\mathcal{U})\}, \emptyset))$.
- **Verdict**: `PASS`

---

#### CTX-28: Partial Temporal Coverage Ineffective for Whole-Frame Falsification
- **Initial State**: Claim $q = (P_{\text{exist}}, \eta, \phi)$ where $P_{\text{exist}} = \exists x.\, R(x)$ with frame $I_{\text{frame}}(\phi) = [t_0, t_{10}]$, initial journal $\mathcal{L}_0$, $\text{Eval}(q, E_0) = (\text{Unknown}, \pi_0, \{\omega_{\text{witness}}\})$.
- **Invariants Tested**: Invariant 14 (Evidence of Absence Requirement), Section 5.3 (Full Temporal Coverage Direction), Section 5.5 (Condition 5), Section 5.6.
- **Execution Trace**:
  1. $\text{Acquire}(\kappa)$ retrieves CoverageCertificate $\chi$ proving universe $\mathcal{U}$ closed only over strict subinterval $I_{\text{covered}}(\chi) = [t_0, t_5] \subset [t_0, t_{10}]$, alongside an exhaustive negative certificate $\nu$ over $[t_0, t_5]$ returning zero witnesses.
  2. $\text{Validate}$ ingests $\chi$ and $\nu$ into $\mathcal{L}'$, producing $E' = \text{Adm}(\mathcal{L}', \eta, \phi)$.
  3. In evaluating $q$, $\text{IsValidNegativeCertificate}(e_\nu, q, \eta, \phi, E')$ tests temporal containment: $I_{\text{frame}}(\phi) \subseteq I_{\text{covered}}(\chi) \iff [t_0, t_{10}] \subseteq [t_0, t_5] = \text{False}$.
  4. Condition 5 fails for the whole-frame claim $q$; hence $e_\nu$ is not a valid negative certificate for $q$, yielding $N_-(q, E') = \emptyset$.
  5. With $W_+(q, E') = \emptyset$ and $N_-(q, E') = \emptyset$, $\text{Eval}(q, E')$ computes $(\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{temporal\_gap}}([t_5, t_{10}])\})$.
  6. Partial temporal coverage cannot establish `False` for the whole claim frame.
- **Expected Output**: $(\mathcal{L}', (\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{temporal\_gap}}([t_5, t_{10}])\}, \emptyset))$.
- **Verdict**: `PASS`

---

### CTX-29: Partial Scope Coverage Ineffective for Broad Falsification
- **Initial State**: Claim $q = (P_{\text{exist}}, \eta, \phi)$ where $P_{\text{exist}} = \exists x \in \text{GlobalOrg}.\; \text{ActiveComplianceViolation}(x)$, initial journal $\mathcal{L}_0$, $\text{Eval}(q, E_0) = (\text{Unknown}, \pi_0, \{\omega_{\text{witness}}\})$.
- **Invariants Tested**: Invariant 14 (Evidence of Absence Requirement), Section 5.2 (Scope Subsumption), Section 5.5 (Condition 3: $\text{CoversClaimScope}$), Section 5.6.
- **Execution Trace**:
  1. $\text{Acquire}(\kappa)$ retrieves CoverageCertificate $\chi$ proving closed/exhaustive records over a strict regional sub-scope $\mathcal{U}_{\text{regional}} = \text{EuropeanBranch} \subset \text{GlobalOrg}$ for the full claim period $I_{\text{frame}}(\phi)$, alongside an exhaustive negative certificate $\nu$ over $\mathcal{U}_{\text{regional}}$ returning zero witnesses.
  2. $\text{Validate}$ ingests $\chi$ and $\nu$ into $\mathcal{L}'$, producing $E' = \text{Adm}(\mathcal{L}', \eta, \phi)$.
  3. In evaluating $q$, $\text{IsValidNegativeCertificate}(e_\nu, q, \eta, \phi, E')$ tests scope subsumption: $\text{CoversClaimScope}(\mathcal{U}_{\text{regional}}, q, \eta, \phi) = \text{False}$.
  4. Condition 3 fails for the broad organizational claim $q$; hence $e_\nu$ is not a valid negative certificate for $q$, yielding $N_-(q, E') = \emptyset$.
  5. With $W_+(q, E') = \emptyset$ and $N_-(q, E') = \emptyset$, $\text{Eval}(q, E')$ computes $(\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{scope\_gap}}(\text{GlobalOrg} \setminus \text{EuropeanBranch})\})$.
  6. Closure of a strict structural or jurisdictional sub-scope cannot establish `False` for a broader claim.
- **Expected Output**: $(\mathcal{L}', (\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{scope\_gap}}(\text{GlobalOrg} \setminus \text{EuropeanBranch})\}, \emptyset))$.
- **Verdict**: `PASS`

---

### CTX-30: Narrow Query Predicate Ineffective for Existential Falsification
- **Initial State**: Claim $q = (P_{\text{exist}}, \eta, \phi)$ where $P_{\text{exist}} = \exists x \in \mathcal{U}.\; \text{Vulnerability}(x)$, initial journal $\mathcal{L}_0$, $\text{Eval}(q, E_0) = (\text{Unknown}, \pi_0, \{\omega_{\text{witness}}\})$.
- **Invariants Tested**: Invariant 14 (Evidence of Absence Requirement), Section 5.4 (Query Predicate Subsumption), Section 5.5 (Condition 6), Section 5.6.
- **Execution Trace**:
  1. Search universe $\mathcal{U}$ is closed and fully covers $I_{\text{frame}}(\phi)$ with valid CoverageCertificate $\chi$.
  2. $\text{Acquire}(\kappa)$ executes query procedure $\mathcal{Q}_e$ using a strict sub-predicate $R_Q = \text{CriticalSeverityVulnerability}$ ($R_Q \subset R$). The query returns zero candidate witnesses, producing candidate $\nu_{\text{raw}}$.
  3. $\text{Validate}$ checks predicate subsumption under policy $\eta$: $\text{ProvablePredicateCover}(R_Q, R, \eta) = \text{False}$ because non-critical vulnerabilities ($R \setminus R_Q$) were left unqueried.
  4. Validation boundary rejects candidate $\nu_{\text{raw}}$, emitting $\Delta_{\text{val}} = [\text{InvalidQueryPredicateDiag}]$ and admitting no negative evidence event ($N_-(q, E') = \emptyset$).
  5. With $W_+(q, E') = \emptyset$ and $N_-(q, E') = \emptyset$, $\text{Eval}(q, E')$ computes $(\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{unproven\_closure}}(\mathcal{U})\})$.
  6. Exhaustive search over a narrower query predicate cannot establish `False` for the broader existential claim.
- **Expected Output**: $(\mathcal{L}', (\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{unproven\_closure}}(\mathcal{U})\}, [\text{InvalidQueryPredicateDiag}]))$.
- **Verdict**: `PASS`

---

### CTX-31: Snapshot Drift Invalidating Negative Decision Publication
- **Initial State**: Claim $q = (P_{\text{exist}}, \eta, \phi)$, initial journal $\mathcal{L}_0$. Negative certificate $\nu_1$ proving empty search over snapshot $\Sigma_1$ is validated, yielding intermediate decision $r_{\text{draft}} = (\text{False}, \pi_{\text{abs}}, \emptyset, \emptyset)$.
- **Invariants Tested**: Invariant 13 (Snapshot Isolation), Invariant 14 (Evidence of Absence Requirement), Section 5.5 (Condition 10: Snapshot Freshness), Section 8 (Anti-Staleness Publication Rule).
- **Execution Trace**:
  1. Before decision publication is committed, concurrent transaction appends to search universe $\mathcal{U}$, transitioning the admissible universe state from snapshot $\Sigma_1$ to snapshot $\Sigma_2$.
  2. Anti-staleness publication rule (§8) detects that the underlying evidence/universe snapshot for claim $(q, \phi)$ has drifted ($\Sigma_2 \neq \Sigma_1$).
  3. Publication of the stale $\text{False}$ decision from snapshot $\Sigma_1$ is strictly blocked.
  4. System enforces mandatory re-evaluation against the fresh evidence snapshot $E_{\text{fresh}}$.
  5. In re-evaluation, $\text{IsValidNegativeCertificate}(e_{\nu1}, q, \eta, \phi, E_{\text{fresh}})$ tests snapshot freshness: condition 10 fails ($\nu_1.\Sigma_{\text{snap}} = \Sigma_1 \neq \Sigma_2$).
  6. Stale certificate $e_{\nu1}$ is excluded from valid negative evidence ($N_-(q, E_{\text{fresh}}) = \emptyset$); $\text{Eval}(q, E_{\text{fresh}})$ evaluates safely to $(\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{snapshot\_mismatch}}\})$.
- **Expected Output**: Stale $\text{False}$ publication aborted; re-evaluation yields $(\mathcal{L}', (\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{snapshot\_mismatch}}\}, \emptyset))$.
- **Verdict**: `PASS`

---

### CTX-32: Positive Witness and Negative Certificate Contradiction without Decisive Policy
- **Initial State**: Claim $q = (P_{\text{exist}}, \eta, \phi)$ where $P_{\text{exist}} = \exists x.\, R(x)$, initial journal $\mathcal{L}_0$. Admissible evidence view $E = \text{Adm}(\mathcal{L}_0, \eta, \phi)$ contains both a valid positive witness event $e_w$ ($W_+(q, E) \neq \emptyset$) and a valid negative evidence certificate event $e_\nu$ ($N_-(q, E) \neq \emptyset$). Evaluator $\eta$ specifies no decisive deterministic dispute-resolution policy.
- **Invariants Tested**: Invariant 1 (Three-valued closed domain), Invariant 4 (Determinism), Section 5.6 (Deterministic Conflict Resolution: $\text{ResolveConflict}$).
- **Execution Trace**:
  1. Collection partitioning yields non-empty positive and negative evidence sets: $W_+(q, E) = \{e_w\}$ and $N_-(q, E) = \{e_\nu\}$.
  2. In Step 8, $\text{Eval}(q, E)$ invokes $\text{ResolveConflict}(\eta, q, W_+(q, E), N_-(q, E))$.
  3. Because evaluator policy $\eta$ contains no decisive priority or timestamp override rule, $\text{ResolveConflict}$ deterministically produces $(\text{Unknown}, \pi_{\text{unresolved\_conflict}}, \{\omega_{\text{conflict}}(q, W_+, N_-)\})$.
  4. Projections yield $\text{Val}(q, E) = \text{Unknown}$, $\text{Cert}(q, E) = \pi_{\text{unresolved\_conflict}}$, and $\text{Obl}(q, E) = \{\omega_{\text{conflict}}(q, W_+, N_-)\}$.
  5. Contradictory evidence without an authoritative tie-break rule safely retains `Unknown` without inventing a fourth truth state.
- **Expected Output**: $(\mathcal{L}_0, (\text{Unknown}, \pi_{\text{unresolved\_conflict}}, \{\omega_{\text{conflict}}(q, W_+, N_-)\}, \emptyset))$.
- **Verdict**: `PASS`

---

### CTX-33: Self-Declared or Unvalidated Completeness Ineffective for Falsification
- **Initial State**: Claim $q = (P_{\text{exist}}, \eta, \phi)$ where $P_{\text{exist}} = \exists x.\, R(x)$, initial journal $\mathcal{L}_0$. Candidate negative certificate $\nu_{\text{raw}}$ is submitted based on an exhaustive query yielding zero witnesses over external database $\mathcal{S}$, which self-declares that its index is 100% complete.
- **Invariants Tested**: Invariant 9 (Candidate Domain Barrier), Invariant 14 (Evidence of Absence Requirement), Section 5.3 (Coverage Certificates), Section 5.5 (Condition 4), Section 6.2 ($\text{Validate}$).
- **Execution Trace**:
  1. Data provider submits candidate negative evidence $\nu_{\text{raw}}$ referencing unverified completeness claims without an independent, authority-signed, formal coverage proof $\chi$ recognized under $\eta$.
  2. $\text{Validate}$ evaluates candidate coverage claims against evaluator trust anchors: self-declared or unverified completeness assertions fail validation.
  3. No valid $\text{EvEntry}(e_\chi)$ enters journal $\mathcal{L}'$; operational diagnostic $[\text{UntrustedCoverageAuthorityDiag}]$ is ingested via $\text{Auditize}$ into $\mathcal{L}'$.
  4. In evaluating $q$ over $E' = \text{Adm}(\mathcal{L}', \eta, \phi)$, condition 4 of $\text{IsValidNegativeCertificate}$ fails (no admissible coverage certificate in $E'$).
  5. Negative certificate collection is empty ($N_-(q, E') = \emptyset$); with $W_+(q, E') = \emptyset$, $\text{Eval}(q, E')$ computes $(\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{unproven\_closure}}(\mathcal{U})\})$.
  6. Self-declared or unvalidated completeness cannot establish universe closure or `False`.
- **Expected Output**: Candidate rejected; re-evaluation yields $(\mathcal{L}', (\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{unproven\_closure}}(\mathcal{U})\}, [\text{UntrustedCoverageAuthorityDiag}]))$.
- **Verdict**: `PASS`

---

### CTX-34: Valid Negative Evidence Certificate Establishing False for Existential Claim
- **Initial State**: Claim $q = (P_{\text{exist}}, \eta, \phi)$ where $P_{\text{exist}} = \exists x.\, R(x)$, initial journal $\mathcal{L}_0$, $\text{Eval}(q, E_0) = (\text{Unknown}, \pi_0, \{\omega_{\text{witness}}\})$.
- **Invariants Tested**: Invariant 1 (Three-valued closed domain), Invariant 14 (Evidence of Absence Requirement), Section 5.3 (Coverage Certificates), Section 5.4, Section 5.5, Section 5.6.
- **Execution Trace**:
  1. $\text{Acquire}(\kappa)$ retrieves a valid CoverageCertificate $\chi$ proving search universe $\mathcal{U}$ closed for relation $R$ with $I_{\text{frame}}(\phi) \subseteq I_{\text{covered}}(\chi)$ and $\text{CoversClaimScope}(\mathcal{U}, q, \eta, \phi) = \text{True}$.
  2. $\text{Acquire}(\kappa)$ executes deterministic exhaustive query $\mathcal{Q}_e$ over snapshot $\Sigma_{\text{snap}}$ with query predicate $R_Q$ proven equivalent/subsuming $R$, obtaining zero witnesses and generating NegativeEvidenceCertificate $\nu$.
  3. $\text{Validate}$ verifies authority signatures, temporal coverage, scope coverage, predicate subsumption, snapshot identity, partition exhaustiveness, and empty-result proof, committing $\text{EvEntry}(e_\chi)$ and $\text{EvEntry}(e_\nu)$ into $\mathcal{L}'$.
  4. In Step 8, $\text{IsValidNegativeCertificate}(e_\nu, q, \eta, \phi, E')$ evaluates to $\text{Bool.True}$, yielding $N_-(q, E') = \{e_\nu\}$.
  5. With $W_+(q, E') = \emptyset$ and $N_-(q, E') \neq \emptyset$, $\text{Eval}(q, E')$ deterministically evaluates to $(\text{False}, \pi_{\text{abs}}(N_-), \emptyset)$.
  6. A fully validated negative evidence certificate validly establishes the existential claim as $\text{False}$ through $\text{Eval}$.
- **Expected Output**: $(\mathcal{L}', (\text{False}, \pi_{\text{abs}}(N_-), \emptyset, \emptyset))$.
- **Verdict**: `PASS`

---

### CTX-35: Decisive Deterministic Policy Resolving Positive and Negative Evidence Conflict
- **Initial State**: Claim $q = (P_{\text{exist}}, \eta, \phi)$, initial journal $\mathcal{L}_0$. Admissible evidence view $E = \text{Adm}(\mathcal{L}_0, \eta, \phi)$ contains both a valid positive witness event $e_w \in W_+(q, E)$ and a valid negative evidence certificate event $e_\nu \in N_-(q, E)$. Evaluator $\eta$ defines an explicit decisive priority rule: verified physical sensor witnesses strictly take precedence over database index closure certificates.
- **Invariants Tested**: Invariant 1 (Three-valued closed domain), Invariant 4 (Determinism), Section 5.6 (Deterministic Conflict Resolution: $\text{ResolveConflict}$).
- **Execution Trace**:
  1. Admissible collection partitioning yields $W_+(q, E) \neq \emptyset$ and $N_-(q, E) \neq \emptyset$.
  2. $\text{Eval}(q, E)$ delegates to $\text{ResolveConflict}(\eta, q, W_+(q, E), N_-(q, E))$.
  3. Under evaluator policy $\eta$'s decisive priority rule, physical witness $e_w$ overrides negative certificate $e_\nu$.
  4. $\text{ResolveConflict}$ computes the complete evaluation triple $(v, \pi, \Omega) = (\text{True}, \pi_{\text{conflict\_resolved}}(e_w, e_\nu), \emptyset)$.
  5. Projections yield $\text{Val}(q, E) = \text{True}$, $\text{Cert}(q, E) = \pi_{\text{conflict\_resolved}}(e_w, e_\nu)$, and $\text{Obl}(q, E) = \emptyset$.
  6. Evaluator with a decisive dispute-resolution policy deterministically resolves coexisting positive and negative evidence to a determinate truth value without ambiguity.
- **Expected Output**: $(\mathcal{L}_0, (\text{True}, \pi_{\text{conflict\_resolved}}(e_w, e_\nu), \emptyset, \emptyset))$.
- **Verdict**: `PASS`

---

### CTX-36: Universal Negative Claim via Strong Kleene Negation of Falsified Existential Claim
- **Initial State**: Base claim $q_{\text{exist}} = (P_{\text{exist}}, \eta, \phi)$ where $P_{\text{exist}} = \exists x.\, R(x)$, initial journal $\mathcal{L}_0$. Admissible evidence $E = \text{Adm}(\mathcal{L}_0, \eta, \phi)$ contains a validated negative evidence certificate event $e_\nu \in N_-(q_{\text{exist}}, E)$ with $W_+(q_{\text{exist}}, E) = \emptyset$, establishing $\text{Eval}(q_{\text{exist}}, E) = (\text{False}, \pi_{\text{abs}}(N_-), \emptyset)$. Caller evaluates logical negation $q_{\text{neg}} = (\neg P_{\text{exist}}, \eta, \phi)$ (equivalent to universal negative claim $\forall x.\, \neg R(x)$).
- **Invariants Tested**: Invariant 1 (Three-valued closed domain), Invariant 14 (Evidence of Absence Requirement), Section 5.7 (Standard Strong Kleene Negation for Universal Claims), Section 11.1 (Strong Kleene Consistency).
- **Execution Trace**:
  1. $\text{Val}(q_{\text{exist}}, E)$ evaluates strictly to $\text{False}$ through validated exhaustive negative certificate $e_\nu$.
  2. In accordance with Section 5.7, evaluation of the negated AST node applies standard Strong Kleene negation:
     $$\text{Val}(q_{\text{neg}}, E) = \neg_{K_3} \text{Val}(q_{\text{exist}}, E) = \neg_{K_3} \text{False} = \text{True}$$
  3. Derivation certificate $\pi_{\text{neg}}(\pi_{\text{abs}})$ justifies the truth value; obligation set remains empty ($\text{Obl}(q_{\text{neg}}, E) = \emptyset$).
  4. The truth value $\text{True}$ is derived solely via ordinary $K_3$ compositional negation of the proven-$\text{False}$ existential claim.
  5. No new absence, negative-truth, or fourth logical state is introduced into $\mathbb{X} = \{\text{True}, \text{False}, \text{Unknown}\}$.
- **Expected Output**: $(\mathcal{L}_0, (\text{True}, \pi_{\text{neg}}(\pi_{\text{abs}}), \emptyset, \emptyset))$.
- **Verdict**: `PASS`

---

### CTX-37: Local Observational Proof Ineffective for Globally Quantified Consistency
- **Initial State**: Globally quantified claim $q_{\text{univ}} = (\forall o \in \text{Observers}.\; C(o), \eta, \phi)$ where $\text{Observers} = \{\text{Alice}, \text{Bob}, \dots\}$, equivalent under Section 5.7 to $\neg (\exists o \in \text{Observers}.\; \neg C(o))$. Initial journal $\mathcal{L}_0$. Admissible evidence contains a cryptographically verified proof $e_{\text{Alice}}$ establishing that Alice's local view is fully consistent ($C(\text{Alice}) = \text{True}$). No evidence is provided for Bob or other observers.
- **Invariants Tested**: Invariant 1 (Three-valued closed domain), Invariant 14 (Evidence of Absence Requirement), Section 5.2 (Scope Subsumption), Section 5.5 (Condition 3: $\text{CoversClaimScope}$), Section 5.7 (Universal Claims under $K_3$).
- **Execution Trace**:
  1. Under Section 5.7, evaluating universal claim $q_{\text{univ}}$ reduces via Strong Kleene negation to evaluating existential counterexample claim $q_{\text{exist}} = (\exists o \in \text{Observers}.\; \neg C(o), \eta, \phi)$.
  2. To prove $q_{\text{exist}} = \text{False}$ (which would make $q_{\text{univ}} = \text{True}$), the system requires a validated NegativeEvidenceCertificate $\nu$ over a universe covering the full domain of quantification ($\text{Observers}$).
  3. Alice's local evidence provides coverage only for the singleton sub-scope $\mathcal{U}_{\text{Alice}} = \{\text{Alice}\} \subset \text{Observers}$.
  4. Predicate $\text{CoversClaimScope}(\mathcal{U}_{\text{Alice}}, q_{\text{exist}}, \eta, \phi)$ evaluates to $\text{False}$ because Bob and the remaining observer population are omitted.
  5. Condition 3 of $\text{IsValidNegativeCertificate}$ fails for $q_{\text{exist}}$, yielding $N_-(q_{\text{exist}}, E) = \emptyset$.
  6. With $W_+(q_{\text{exist}}, E) = \emptyset$ (no violation witness discovered) and $N_-(q_{\text{exist}}, E) = \emptyset$, $\text{Eval}(q_{\text{exist}}, E)$ evaluates to $(\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{scope\_gap}}(\text{Observers} \setminus \{\text{Alice}\})\})$.
  7. Strong Kleene negation yields $\text{Val}(q_{\text{univ}}, E) = \neg_{K_3} \text{Unknown} = \text{Unknown}$.
  8. Valid local observation cannot establish a globally quantified claim unless $\text{CoversClaimScope}$ formally covers the entire required observer population.
- **Expected Output**: $(\mathcal{L}_0, (\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{scope\_gap}}(\text{Observers} \setminus \{\text{Alice}\})\}, \emptyset))$.
- **Verdict**: `PASS`

---

### CTX-38: Incompatible Locally Valid Views Positively Falsifying Consistency
- **Initial State**: Globally quantified uniqueness/consistency claim $q_{\text{unique}} = (\forall o_1, o_2.\; \text{Root}(o_1, n) = \text{Root}(o_2, n), \eta, \phi)$ for log tree size $n$, equivalent under Section 5.7 to $\neg (\exists o_1, o_2.\; \text{Root}(o_1, n) \neq \text{Root}(o_2, n))$. Initial journal $\mathcal{L}_0$. Admissible evidence view $E = \text{Adm}(\mathcal{L}_0, \eta, \phi)$ contains two cryptographically signed, valid witness events: $e_{\text{Alice}}$ signing root $R_A$ at size $n$, and $e_{\text{Bob}}$ signing root $R_B$ at size $n$, where $R_A \neq R_B$.
- **Invariants Tested**: Invariant 1 (Three-valued closed domain), Invariant 14 (Evidence of Absence Requirement), Section 5.6 (Existential Evaluation), Section 5.7 (Universal Claims under $K_3$), Section 11.1 (Strong Kleene Consistency).
- **Execution Trace**:
  1. Under Section 5.7, evaluating $q_{\text{unique}}$ reduces via Strong Kleene negation to evaluating existential split-view claim $q_{\text{exist}} = (\exists o_1, o_2.\; \text{Root}(o_1, n) \neq \text{Root}(o_2, n), \eta, \phi)$.
  2. The combined admissible evidence snapshot $E$ supplies witness pair $(e_{\text{Alice}}, e_{\text{Bob}})$ where both signatures verify under $\eta$ and $R_A \neq R_B$.
  3. Witness set $W_+(q_{\text{exist}}, E) = \{(e_{\text{Alice}}, e_{\text{Bob}})\}$ is non-empty; negative evidence set $N_-(q_{\text{exist}}, E) = \emptyset$.
  4. Under Section 5.6, $\text{Eval}(q_{\text{exist}}, E)$ evaluates strictly to $(\text{True}, \pi_{\text{wit}}(e_{\text{Alice}}, e_{\text{Bob}}), \emptyset)$.
  5. Applying Strong Kleene negation under Section 5.7:
     $$\text{Val}(q_{\text{unique}}, E) = \neg_{K_3} \text{Val}(q_{\text{exist}}, E) = \neg_{K_3} \text{True} = \text{False}$$
  6. The global uniqueness claim is positively established as $\text{False}$ with proof certificate $\pi_{\text{falsified}}(\pi_{\text{wit}})$ and cleared obligations ($\text{Obl} = \emptyset$).
  7. The falsification result is derived strictly from combining both admissible local views into $E$, whereas each local view in isolation was insufficient to establish the global outcome.
- **Expected Output**: $(\mathcal{L}_0, (\text{False}, \pi_{\text{falsified}}(\pi_{\text{wit}}), \emptyset, \emptyset))$.
- **Verdict**: `PASS`

---

### CTX-39: Unproven Intersubjective Comparability Preserving Unknown
- **Initial State**: Universal consistency claim $q_{\text{cons}} = (\forall o_1, o_2.\; (\text{Comparable}(o_1, o_2) \implies \text{Compatible}(o_1, o_2)), \eta, \phi)$, equivalent under Section 5.7 to $\neg (\exists o_1, o_2.\; \text{Comparable}(o_1, o_2) \land \neg \text{Compatible}(o_1, o_2))$. Initial journal $\mathcal{L}_0$. Admissible evidence contains cryptographically valid local histories $e_{\text{Alice}}$ and $e_{\text{Bob}}$ from different sources, but no admissible evidence establishes that the two histories refer to the same comparable log state, prefix, or context.
- **Invariants Tested**: Invariant 1 (Three-valued closed domain), Invariant 14 (Evidence of Absence Requirement), Section 5.1 (Open-World Principle), Section 5.6 (Existential Evaluation), Section 5.7 (Universal Claims under $K_3$).
- **Execution Trace**:
  1. Evaluating universal claim $q_{\text{cons}}$ reduces via Strong Kleene negation to evaluating existential inconsistency claim $q_{\text{exist}} = (\exists o_1, o_2.\; \text{Comparable}(o_1, o_2) \land \neg \text{Compatible}(o_1, o_2), \eta, \phi)$.
  2. The available evidence presents distinct local states, but neither $(e_{\text{Alice}}, e_{\text{Bob}})$ nor any other pair satisfies the compound witness predicate $(\text{Comparable} \land \neg \text{Compatible})$ because proof of $\text{Comparable}$ is absent.
  3. Consequently, the positive witness set is empty: $W_+(q_{\text{exist}}, E) = \emptyset$.
  4. Furthermore, no validated CoverageCertificate $\chi$ exists covering the full cross-observer domain; hence $N_-(q_{\text{exist}}, E) = \emptyset$.
  5. Under Section 5.6, $\text{Eval}(q_{\text{exist}}, E)$ evaluates strictly to $(\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{unproven\_comparability}}(e_{\text{Alice}}, e_{\text{Bob}})\})$.
  6. Applying Strong Kleene negation under Section 5.7:
     $$\text{Val}(q_{\text{cons}}, E) = \neg_{K_3} \text{Val}(q_{\text{exist}}, E) = \neg_{K_3} \text{Unknown} = \text{Unknown}$$
  7. Difference or variation across local views cannot establish global falsity (`False`) without positive evidence demonstrating that the views are comparable and contradictory. The model uniquely derives `Unknown`.
- **Expected Output**: $(\mathcal{L}_0, (\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{unproven\_comparability}}(e_{\text{Alice}}, e_{\text{Bob}})\}, \emptyset))$.
- **Verdict**: `PASS`

---

### CTX-40: Near-Complete Observational Coverage Ineffective for Universal Verification
- **Initial State**: Globally quantified consistency claim $q_{\text{univ}} = (\forall o \in \text{Observers}_{1000}.\; C(o), \eta, \phi)$ over 1000 observers, equivalent under Section 5.7 to $\neg (\exists o \in \text{Observers}_{1000}.\; \neg C(o))$. Initial journal $\mathcal{L}_0$. Admissible evidence contains cryptographically verified consistent observations for 999 observers ($o_1 \dots o_{999}$), but observer $o_{1000}$ has no admissible observation.
- **Invariants Tested**: Invariant 1 (Three-valued closed domain), Invariant 14 (Evidence of Absence Requirement), Section 5.2 (Scope Subsumption), Section 5.5 (Condition 3: $\text{CoversClaimScope}$), Section 5.7 (Universal Claims under $K_3$).
- **Execution Trace**:
  1. Under Section 5.7, evaluating universal claim $q_{\text{univ}}$ requires evaluating existential counterexample claim $q_{\text{exist}} = (\exists o \in \text{Observers}_{1000}.\; \neg C(o), \eta, \phi)$.
  2. To prove $q_{\text{exist}} = \text{False}$ (which would derive $q_{\text{univ}} = \text{True}$), the system requires a validated CoverageCertificate $\chi$ and negative certificate $\nu$ covering all 1000 observers.
  3. The available coverage proof covers only the 999-observer subset $\mathcal{U}_{999} = \text{Observers}_{1000} \setminus \{o_{1000}\}$.
  4. Predicate $\text{CoversClaimScope}(\mathcal{U}_{999}, q_{\text{exist}}, \eta, \phi)$ evaluates strictly to $\text{False}$ under Section 5.2 because $o_{1000}$ is omitted from the domain of quantification.
  5. Condition 3 of $\text{IsValidNegativeCertificate}$ fails for $q_{\text{exist}}$, yielding $N_-(q_{\text{exist}}, E) = \emptyset$.
  6. With $W_+(q_{\text{exist}}, E) = \emptyset$ (no violation witnessed among the 999) and $N_-(q_{\text{exist}}, E) = \emptyset$, $\text{Eval}(q_{\text{exist}}, E)$ evaluates to $(\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{scope\_gap}}(\{o_{1000}\})\})$.
  7. Strong Kleene negation yields $\text{Val}(q_{\text{univ}}, E) = \neg_{K_3} \text{Unknown} = \text{Unknown}$.
  8. Deriving $\text{True}$ on partial or 99.9% coverage is strictly forbidden. The unobserved 1000th observer leaves the whole universal claim deterministically `Unknown`.
- **Expected Output**: $(\mathcal{L}_0, (\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{scope\_gap}}(\{o_{1000}\})\}, \emptyset))$.
- **Verdict**: `PASS`

---

### CTX-41: Subsequent Incompatible Evidence Overriding Previously Evaluated True
- **Initial State**: Universal consistency claim $q_{\text{unique}} = (\forall o_1, o_2.\; \text{Root}(o_1, n) = \text{Root}(o_2, n), \eta, \phi)$, equivalent under Section 5.7 to $\neg (\exists o_1, o_2.\; \text{Root}(o_1, n) \neq \text{Root}(o_2, n))$. At state 0, journal $\mathcal{L}_0$ contains valid CoverageCertificate $\chi$ and negative certificate $\nu$, yielding $E_0 = \text{Adm}(\mathcal{L}_0, \eta, \phi)$ and initial evaluation $\text{Val}(q_{\text{unique}}, E_0) = \text{True}$. Later, new transactions append to journal $\mathcal{L}_1 = \mathcal{L}_0 \mathbin{+\!\!+} [\text{EvEntry}(e_A), \text{EvEntry}(e_B)]$, recording two incompatible signed roots $R_A \neq R_B$ for tree size $n$.
- **Invariants Tested**: Invariant 2 (Snapshot Determinism), Invariant 13 (Snapshot Isolation), Section 4.1 (Evaluation Function: $\text{Eval}$ over Current $E$), Section 5.6, Section 5.7, Section 8 (Anti-Staleness Publication Rule).
- **Execution Trace**:
  1. Append-only journal evolves monotonically: $\mathcal{L}_0 \sqsubseteq \mathcal{L}_1$.
  2. The admissible view is recomputed over the fresh state: $E_1 = \text{Adm}(\mathcal{L}_1, \eta, \phi)$, containing $e_A$ and $e_B$.
  3. Under the anti-staleness and snapshot isolation rules (§4.1, §8), prior decision $r_0$ bound to snapshot $E_0$ is stale and cannot serve as the authoritative truth value for state $\mathcal{L}_1$.
  4. Evaluating existential contradiction claim $q_{\text{exist}}$ over $E_1$: witness pair $(e_A, e_B)$ satisfies $\text{Root}(o_1, n) \neq \text{Root}(o_2, n)$, yielding $W_+(q_{\text{exist}}, E_1) \neq \emptyset$.
  5. Under Section 5.6, $\text{Eval}(q_{\text{exist}}, E_1)$ evaluates to $(\text{True}, \pi_{\text{wit}}(e_A, e_B), \emptyset)$.
  6. Applying Strong Kleene negation under Section 5.7:
     $$\text{Val}(q_{\text{unique}}, E_1) = \neg_{K_3} \text{Val}(q_{\text{exist}}, E_1) = \neg_{K_3} \text{True} = \text{False}$$
  7. The old $\text{True}$ result is superseded; the current state evaluates strictly and uniquely to $\text{False}$.
- **Expected Output**: $(\mathcal{L}_1, (\text{False}, \pi_{\text{falsified}}(\pi_{\text{wit}}), \emptyset, \emptyset))$.
- **Verdict**: `PASS`

---

### CTX-42: Historical Consistency Invalidation Persisting Despite Subsequent Convergence
- **Initial State**: Historical universal consistency claim $q_{\text{hist}} = (\forall o_1, o_2.\; \text{Root}(o_1, n) = \text{Root}(o_2, n), \eta, \phi)$ anchored to temporal observation frame $\phi = (I_{\text{frame}}, \sigma, C)$ where $I_{\text{frame}} = [t_1, t_5]$. Incompatible signed roots $R_A \neq R_B$ for tree size $n$ are observed and committed with valid time $t_2 \in [t_1, t_5]$. At subsequent time $t_8 > t_5$, both observers converge to identical valid root $R_C$ and corresponding observation events are appended to journal $\mathcal{L}$.
- **Invariants Tested**: Invariant 1 (Three-valued closed domain), Invariant 11 (Non-Overwriting Journal), Section 3.2 (Bitemporal Interval Model), Section 3.3 (Admissible Evidence View), Section 5.6, Section 5.7, Section 12.
- **Execution Trace**:
  1. The observation frame window $I_{\text{frame}}(\phi) = [t_1, t_5]$ remains strictly fixed for claim $q_{\text{hist}}$ (Invariant 11, Section 12).
  2. Admissible evidence view $E = \text{Adm}(\mathcal{L}, \eta, \phi)$ selects all validated evidence events whose valid time overlaps $[t_1, t_5]$.
  3. The historical witness pair $(e_{A, t2}, e_{B, t2})$ has $I_{\text{valid}} = [t_2, t_2] \subseteq [t_1, t_5]$, cryptographic signatures verified under $\eta$, and $R_A \neq R_B$.
  4. Subsequent convergence at $t_8$ appends new events with $I_{\text{valid}} = [t_8, t_8]$ (outside $I_{\text{frame}}$) but cannot mutate or delete prior journal entries $(e_{A, t2}, e_{B, t2})$.
  5. Evaluating existential contradiction claim $q_{\text{exist}}$ over $E$: witness set $W_+(q_{\text{exist}}, E)$ contains $(e_{A, t2}, e_{B, t2})$, yielding $\text{Eval}(q_{\text{exist}}, E) = (\text{True}, \pi_{\text{wit}}(e_{A, t2}, e_{B, t2}), \emptyset)$.
  6. Applying Strong Kleene negation under Section 5.7:
     $$\text{Val}(q_{\text{hist}}, E) = \neg_{K_3} \text{Val}(q_{\text{exist}}, E) = \neg_{K_3} \text{True} = \text{False}$$
  7. Subsequent real-world convergence cannot retroactively erase a proven historical violation within the anchored frame $\phi$.
- **Expected Output**: $(\mathcal{L}, (\text{False}, \pi_{\text{falsified}}(\pi_{\text{wit}}), \emptyset, \emptyset))$.
- **Verdict**: `PASS`

---

### CTX-43: Collocated Vantage Points Ineffective for Independent Vantage Coverage
- **Initial State**: Universal consistency claim $q_{\text{univ}} = (\forall v \in \text{VantagePoints}.\; C(v), \eta, \phi)$ requiring proof of consistency across independent observation paths/vantage points under context $C(\phi)$. Proponent provides 1000 observations associated with 1000 distinct observer account IDs, but causal provenance DAG analysis ($\Gamma$) reveals that all 1000 observations trace to a single underlying hardware probe/gateway ($|\text{VantagePoints}_{\text{observed}}| = 1 < |\text{VantagePoints}|$).
- **Invariants Tested**: Invariant 1 (Three-valued closed domain), Invariant 14 (Evidence of Absence Requirement), Section 3.2 (Provenance DAG $\Gamma$), Section 5.2 (Scope Subsumption: $\text{CoversClaimScope}$), Section 5.5 (Condition 3), Section 5.7.
- **Execution Trace**:
  1. Evaluating universal claim $q_{\text{univ}}$ reduces via Strong Kleene negation to evaluating existential counterexample claim $q_{\text{exist}} = (\exists v \in \text{VantagePoints}.\; \neg C(v), \eta, \phi)$.
  2. To prove $q_{\text{exist}} = \text{False}$, the system requires a validated CoverageCertificate $\chi$ proving exhaustive coverage of independent vantage points.
  3. Although 1000 nominal identities are presented, structural scope analysis of $\mathcal{U}$ against provenance DAGs $\Gamma$ demonstrates that only 1 physical vantage point was sampled.
  4. Predicate $\text{CoversClaimScope}(\mathcal{U}, q_{\text{exist}}, \eta, \phi)$ evaluates strictly to $\text{False}$ under Section 5.2 because the relational and contextual diversity of vantage points required by $(q, \phi)$ is unfulfilled.
  5. Condition 3 of $\text{IsValidNegativeCertificate}$ fails, yielding $N_-(q_{\text{exist}}, E) = \emptyset$.
  6. With $W_+(q_{\text{exist}}, E) = \emptyset$ and $N_-(q_{\text{exist}}, E) = \emptyset$, $\text{Eval}(q_{\text{exist}}, E)$ evaluates to $(\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{scope\_gap}}(\text{UnobservedVantagePoints})\})$.
  7. Strong Kleene negation yields $\text{Val}(q_{\text{univ}}, E) = \neg_{K_3} \text{Unknown} = \text{Unknown}$.
  8. Distinct identity count alone cannot substitute for genuine observational diversity; the claim deterministically retains `Unknown`.
- **Expected Output**: $(\mathcal{L}_0, (\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{scope\_gap}}(\text{UnobservedVantagePoints})\}, \emptyset))$.
- **Verdict**: `PASS`

---

### CTX-44: Acquisition-Conditioned Behavior Ineffective for Global Claim Verification
- **Initial State**: Universal consistency claim $q_{\text{global}} = (\forall c \in \text{Clients}.\; C(c), \eta, \phi)$ anchored to unconditioned client observation frame $\phi = (I_{\text{frame}}, \sigma, C_{\text{client}})$. An adversarial log serves split views to ordinary clients in context $C_{\text{client}}$, but detects audit probes and serves a coherent single view during probe acquisition in audit context $C_{\text{audit}}$. Acquisition over $C_{\text{audit}}$ produces an apparently empty violation set.
- **Invariants Tested**: Invariant 1 (Three-valued closed domain), Invariant 14 (Evidence of Absence Requirement), Section 3.2 (Observation Frame $\phi$), Section 5.2 (Scope Subsumption: $\text{CoversClaimScope}$), Section 5.5 (Condition 3), Section 6.1 (Acquisition Non-Interference), Section 12.
- **Execution Trace**:
  1. Evaluating universal claim $q_{\text{global}}$ reduces under Section 5.7 to existential counterexample claim $q_{\text{exist}} = (\exists c \in \text{Clients}.\; \neg C(c), \eta, \phi)$.
  2. The candidate negative evidence $\nu_{\text{audit}}$ acquired by the audit probe is conditioned on audit context $C_{\text{audit}}$, where probe detection altered system behavior.
  3. Under Section 5.2, $\text{CoversClaimScope}(\mathcal{U}_{\text{audit}}, q_{\text{exist}}, \eta, \phi)$ checks whether the contextual domain $C(\phi) = C_{\text{client}}$ is subsumed by $\mathcal{U}_{\text{audit}}$.
  4. Because the audit observation mechanism altered behavior and lacks proven non-interference with $C_{\text{client}}$, context subsumption fails ($\text{CoversClaimScope} = \text{False}$).
  5. Condition 3 of $\text{IsValidNegativeCertificate}$ fails for $q_{\text{exist}}$, yielding $N_-(q_{\text{exist}}, E) = \emptyset$.
  6. With $W_+(q_{\text{exist}}, E) = \emptyset$ (no violation witnessed directly by probes) and $N_-(q_{\text{exist}}, E) = \emptyset$, $\text{Eval}(q_{\text{exist}}, E)$ evaluates to $(\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{unproven\_non\_interference}}(C_{\text{audit}}, C_{\text{client}})\})$.
  7. Strong Kleene negation yields $\text{Val}(q_{\text{global}}, E) = \neg_{K_3} \text{Unknown} = \text{Unknown}$.
  8. Deriving $\text{True}$ for the original global claim from probe-conditioned evidence is strictly forbidden; verifying the probe-conditioned regime would require anchoring a separate, distinct claim $q_{\text{audit}} = (P, \eta, \phi_{\text{audit}})$.
- **Expected Output**: $(\mathcal{L}_0, (\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{unproven\_non\_interference}}(C_{\text{audit}}, C_{\text{client}})\}, \emptyset))$.
- **Verdict**: `PASS`

---

### CTX-45: Post-Acquisition State Evidence Ineffective for Earlier Anchored Temporal Frame
- **Initial State**: Universal consistency claim $q_{\text{hist}} = (\forall c \in \text{Clients}.\; C(c), \eta, \phi_1)$ anchored to earlier temporal observation frame $\phi_1 = (T_1, \sigma, C)$. During evidence acquisition, the underlying log advances to a new state at interval $T_2$ ($T_1 \cap T_2 = \emptyset$). Newly acquired evidence is cryptographically valid and proves consistency over $T_2$, but no evidence is acquired for historical interval $T_1$.
- **Invariants Tested**: Invariant 1 (Three-valued closed domain), Invariant 14 (Evidence of Absence Requirement), Section 3.2 (Bitemporal Model), Section 3.3 (Admissible Evidence View), Section 5.3 (Full Temporal Coverage), Section 5.5 (Condition 5), Section 5.7, Section 12.
- **Execution Trace**:
  1. Evaluating historical universal claim $q_{\text{hist}}$ requires evaluating existential counterexample claim $q_{\text{exist}} = (\exists c \in \text{Clients}.\; \neg C(c), \eta, \phi_1)$ anchored to frame $T_1$.
  2. Admissible evidence view $E_1 = \text{Adm}(\mathcal{L}, \eta, \phi_1)$ strictly filters for evidence whose valid interval overlaps $T_1$.
  3. The newly acquired negative evidence $\nu_2$ carries valid interval $I_{\text{valid}}(\nu_2) = T_2$.
  4. Under Section 5.3 and Section 5.5 (Condition 5), validated temporal coverage must satisfy $I_{\text{frame}}(\phi_1) \subseteq I_{\text{covered}}(\chi_2)$, i.e. $T_1 \subseteq T_2$.
  5. Because $T_1 \not\subseteq T_2$, Condition 5 fails, yielding $N_-(q_{\text{exist}}, E_1) = \emptyset$.
  6. With $W_+(q_{\text{exist}}, E_1) = \emptyset$ and $N_-(q_{\text{exist}}, E_1) = \emptyset$, $\text{Eval}(q_{\text{exist}}, E_1)$ evaluates strictly to $(\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{temporal\_gap}}(T_1)\})$.
  7. Applying Strong Kleene negation under Section 5.7:
     $$\text{Val}(q_{\text{hist}}, E_1) = \neg_{K_3} \text{Unknown} = \text{Unknown}$$
  8. Valid evidence from a later epoch $T_2$ cannot retroactively establish `True` for an earlier anchored frame $T_1$. Evaluating $T_2$ requires anchoring an independent new claim $q_2 = (P_{\text{univ}}, \eta, \phi_2)$.
- **Expected Output**: $(\mathcal{L}, (\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{temporal\_gap}}(T_1)\}, \emptyset))$.
- **Verdict**: `PASS`

---

### CTX-46: Unproven Temporal Comparability Preserving Unknown
- **Initial State**: Universal temporal consistency claim $q_{\text{sync}} = (\forall o_1, o_2.\; (\text{SameLogicalTime}(o_1, o_2) \implies \text{Root}(o_1) = \text{Root}(o_2)), \eta, \phi)$, equivalent under Section 5.7 to $\neg (\exists o_1, o_2.\; \text{SameLogicalTime}(o_1, o_2) \land \text{Root}(o_1) \neq \text{Root}(o_2))$. Initial journal $\mathcal{L}_0$. Admissible evidence contains cryptographically valid signed roots $e_A$ ($R_A$) and $e_B$ ($R_B$) carrying identical nominal timestamp strings `12:00:00Z`, but the local clock synchronization and timestamp semantics between Alice and Bob are unproven.
- **Invariants Tested**: Invariant 1 (Three-valued closed domain), Invariant 14 (Evidence of Absence Requirement), Section 3.2 (Bitemporal Model), Section 3.3 (Admissible Evidence View), Section 5.1, Section 5.6, Section 5.7.
- **Execution Trace**:
  1. Evaluating universal claim $q_{\text{sync}}$ requires evaluating existential contradiction claim $q_{\text{exist}} = (\exists o_1, o_2.\; \text{SameLogicalTime}(o_1, o_2) \land \text{Root}(o_1) \neq \text{Root}(o_2), \eta, \phi)$.
  2. Under Section 3.2 and Section 3.3, establishing predicate $\text{SameLogicalTime}(e_A, e_B)$ requires validated clock-synchronization certificates or causal order proofs rooting in trusted anchors under $\eta$.
  3. Identical nominal timestamp values from uncalibrated or unsynchronized local clocks do not prove identical physical or logical coordination points.
  4. The candidate witness pair $(e_A, e_B)$ fails to satisfy the compound witness predicate $(\text{SameLogicalTime} \land R_A \neq R_B)$, leaving $W_+(q_{\text{exist}}, E) = \emptyset$.
  5. Negative evidence set $N_-(q_{\text{exist}}, E) = \emptyset$.
  6. Under Section 5.6, $\text{Eval}(q_{\text{exist}}, E)$ evaluates strictly to $(\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{unproven\_clock\_synchronization}}(e_A, e_B)\})$.
  7. Strong Kleene negation yields $\text{Val}(q_{\text{sync}}, E) = \neg_{K_3} \text{Unknown} = \text{Unknown}$.
  8. Apparent timestamp equivalence cannot establish a proven contradiction without validated temporal comparability; the model uniquely preserves `Unknown`.
- **Expected Output**: $(\mathcal{L}_0, (\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{unproven\_clock\_synchronization}}(e_A, e_B)\}, \emptyset))$.
- **Verdict**: `PASS`

---

### CTX-47: Unproven Key-Epoch Continuity Preserving Unknown
- **Initial State**: Universal consistency claim $q_{\text{epoch}} = (\forall o_1, o_2.\; (\text{SameEpochAndState}(o_1, o_2) \implies \text{Root}(o_1) = \text{Root}(o_2)), \eta, \phi)$, equivalent under Section 5.7 to $\neg (\exists o_1, o_2.\; \text{SameEpochAndState}(o_1, o_2) \land \text{Root}(o_1) \neq \text{Root}(o_2))$. Initial journal $\mathcal{L}_0$. Admissible evidence contains valid root $e_A$ ($R_1$) signed under key $K_1$ and valid root $e_B$ ($R_2$) signed under successor key $K_2$ after a key rotation, but no evidence proves whether $R_1$ and $R_2$ belong to the same signing epoch and comparable log state.
- **Invariants Tested**: Invariant 1 (Three-valued closed domain), Invariant 14 (Evidence of Absence Requirement), Section 3.2 (Cryptographic Provenance DAG $\Gamma$), Section 5.1 (Open-World Principle), Section 5.6, Section 5.7.
- **Execution Trace**:
  1. Evaluating universal consistency claim $q_{\text{epoch}}$ reduces to evaluating existential inconsistency claim $q_{\text{exist}} = (\exists o_1, o_2.\; \text{SameEpochAndState}(o_1, o_2) \land \text{Root}(o_1) \neq \text{Root}(o_2), \eta, \phi)$.
  2. Under Section 3.2 and Section 5.6, establishing predicate $\text{SameEpochAndState}(e_A, e_B)$ requires validating a key-rotation continuity proof linking $K_1 \to K_2$ and certifying that $R_1$ and $R_2$ index the exact same log state rather than different sequential epochs.
  3. In the absence of an epoch continuity certificate, $\text{SameEpochAndState}(e_A, e_B)$ is unproven.
  4. The candidate witness pair $(e_A, e_B)$ fails to satisfy the compound witness predicate, yielding positive witness set $W_+(q_{\text{exist}}, E) = \emptyset$.
  5. Negative evidence set $N_-(q_{\text{exist}}, E) = \emptyset$.
  6. Under Section 5.6, $\text{Eval}(q_{\text{exist}}, E)$ evaluates strictly to $(\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{unproven\_epoch\_continuity}}(e_A, e_B)\})$.
  7. Strong Kleene negation yields $\text{Val}(q_{\text{epoch}}, E) = \neg_{K_3} \text{Unknown} = \text{Unknown}$.
  8. Divergent roots across distinct signing keys without proven epoch and state continuity cannot establish a contradiction (`False`); the model uniquely preserves `Unknown`.
- **Expected Output**: $(\mathcal{L}_0, (\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{unproven\_epoch\_continuity}}(e_A, e_B)\}, \emptyset))$.
- **Verdict**: `PASS`

---

### CTX-48: Cryptographically Valid Signature under Revoked Key Ineffective as Contradiction Witness
- **Initial State**: Universal consistency claim $q_{\text{auth}} = (\forall o_1, o_2.\; (\text{AuthorizedState}(o_1, o_2) \implies \text{Root}(o_1) = \text{Root}(o_2)), \eta, \phi)$, equivalent under Section 5.7 to $\neg (\exists o_1, o_2.\; \text{AuthorizedState}(o_1, o_2) \land \text{Root}(o_1) \neq \text{Root}(o_2))$. Initial journal $\mathcal{L}_0$. Alice observes valid root $e_A$ ($R_A$) signed by authorized key $K_2$. Bob observes different root candidate $e_B$ ($R_B$) whose mathematical signature verifies under key $K_1$, but admissible evidence includes a key-revocation certificate proving $K_1$ had been revoked prior to $t_{\text{sign}}(R_B)$.
- **Invariants Tested**: Invariant 1 (Three-valued closed domain), Invariant 14 (Evidence of Absence Requirement), Section 3.2 (Authority & Trust Anchors), Section 3.3 (Admissible Evidence View), Section 6.2 (Validation Boundary), Section 5.6, Section 5.7.
- **Execution Trace**:
  1. Evaluating universal claim $q_{\text{auth}}$ reduces to evaluating existential contradiction claim $q_{\text{exist}} = (\exists o_1, o_2.\; \text{AuthorizedState}(o_1, o_2) \land \text{Root}(o_1) \neq \text{Root}(o_2), \eta, \phi)$.
  2. Candidate evidence validation $\text{Validate}(\mathcal{C}, \eta, \phi)$ distinguishes mathematical cryptographic correctness from authority validity.
  3. Because $K_1$ was provably revoked prior to signing time $t_{\text{sign}}(R_B)$, candidate $e_B$ is rejected at $\text{Validate}$ with diagnostic $\Delta_{\text{val}} = [\text{RevokedSigningKeyDiag}]$ (or filtered out by $\text{IsAdmissible}$).
  4. Admissible evidence snapshot $E = \text{Adm}(\mathcal{L}, \eta, \phi)$ contains only Alice's authorized observation $e_A$.
  5. Without an admissible second root for comparison, witness set $W_+(q_{\text{exist}}, E) = \emptyset$.
  6. Negative evidence set $N_-(q_{\text{exist}}, E) = \emptyset$.
  7. Under Section 5.6, $\text{Eval}(q_{\text{exist}}, E)$ evaluates strictly to $(\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{unproven\_closure}}\})$.
  8. Strong Kleene negation yields $\text{Val}(q_{\text{auth}}, E) = \neg_{K_3} \text{Unknown} = \text{Unknown}$.
  9. An unauthorized or revoked signature cannot serve as admissible witness of an authorized state conflict; the model strictly prevents deriving `False` and deterministically preserves `Unknown`.
- **Expected Output**: $(\mathcal{L}_0, (\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{unproven\_closure}}\}, \emptyset))$.
- **Verdict**: `PASS`

---

### CTX-49: Key Compromise Prior to Signing Invalidating Contradiction Witness
- **Initial State**: Universal consistency claim $q_{\text{trust}} = (\forall o_1, o_2.\; (\text{TrustworthyState}(o_1, o_2) \implies \text{Root}(o_1) = \text{Root}(o_2)), \eta, \phi)$, equivalent under Section 5.7 to $\neg (\exists o_1, o_2.\; \text{TrustworthyState}(o_1, o_2) \land \text{Root}(o_1) \neq \text{Root}(o_2))$. Initial journal $\mathcal{L}_0$. Alice observes valid root $e_A$ ($R_A$) signed by authorized key $K_2$. Bob observes different root candidate $e_B$ ($R_B$) signed by key $K_1$ at time $t_{\text{sign}}$ when $K_1$ was formally authorized; however, subsequent admissible evidence includes a cryptographically proven key compromise certificate establishing that $K_1$ was compromised at $t_{\text{comp}} < t_{\text{sign}}$.
- **Invariants Tested**: Invariant 1 (Three-valued closed domain), Invariant 14 (Evidence of Absence Requirement), Section 3.2 (Provenance DAG $\Gamma$), Section 3.3 (Admissible Evidence View), Section 6.2 (Validation Boundary), Section 5.6, Section 5.7.
- **Execution Trace**:
  1. Evaluating universal claim $q_{\text{trust}}$ reduces to evaluating existential contradiction claim $q_{\text{exist}} = (\exists o_1, o_2.\; \text{TrustworthyState}(o_1, o_2) \land \text{Root}(o_1) \neq \text{Root}(o_2), \eta, \phi)$.
  2. Under Section 3.2 and Section 6.2, valid evidence requires an uncompromised trust root in provenance DAG $\Gamma$.
  3. Admissible evidence proving that key $K_1$ was compromised prior to signing time $t_{\text{sign}}(R_B)$ severs the trust-anchor grounding in $\Gamma(e_B)$, causing $\text{IsAdmissible}(e_B, \eta, \phi)$ to evaluate to $\text{False}$.
  4. Admissible evidence snapshot $E = \text{Adm}(\mathcal{L}, \eta, \phi)$ quarantines $e_B$, retaining only Alice's trustworthy observation $e_A$.
  5. Without an admissible contradictory witness, $W_+(q_{\text{exist}}, E) = \emptyset$.
  6. Negative evidence set $N_-(q_{\text{exist}}, E) = \emptyset$.
  7. Under Section 5.6, $\text{Eval}(q_{\text{exist}}, E)$ evaluates strictly to $(\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{compromised\_key\_quarantine}}(e_B)\})$.
  8. Strong Kleene negation yields $\text{Val}(q_{\text{trust}}, E) = \neg_{K_3} \text{Unknown} = \text{Unknown}$.
  9. Signatures generated under a compromised key cannot force `False` against global consistency; the model uniquely preserves `Unknown`.
- **Expected Output**: $(\mathcal{L}_0, (\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{compromised\_key\_quarantine}}(e_B)\}, \emptyset))$.
- **Verdict**: `PASS`

---

### CTX-50: Unproven Log Instance Identity Preserving Unknown
- **Initial State**: Universal consistency claim $q_{\text{inst}} = (\forall o_1, o_2.\; (\text{SameLogInstance}(o_1, o_2) \implies \text{Root}(o_1) = \text{Root}(o_2)), \eta, \phi)$, equivalent under Section 5.7 to $\neg (\exists o_1, o_2.\; \text{SameLogInstance}(o_1, o_2) \land \text{Root}(o_1) \neq \text{Root}(o_2))$. Initial journal $\mathcal{L}_0$. Alice and Bob observe different valid signed roots $e_A$ ($R_A$) and $e_B$ ($R_B$) from the same service operator, but admissible evidence does not prove that both roots refer to the exact same canonical log identity rather than distinct log instances, partition shards, or service aliases.
- **Invariants Tested**: Invariant 1 (Three-valued closed domain), Invariant 14 (Evidence of Absence Requirement), Section 3.2 (Claim-Relative Domain Identity), Section 5.1 (Open-World Principle), Section 5.6, Section 5.7.
- **Execution Trace**:
  1. Evaluating universal consistency claim $q_{\text{inst}}$ reduces to evaluating existential contradiction claim $q_{\text{exist}} = (\exists o_1, o_2.\; \text{SameLogInstance}(o_1, o_2) \land \text{Root}(o_1) \neq \text{Root}(o_2), \eta, \phi)$.
  2. Under Section 3.2 and Section 5.6, establishing predicate $\text{SameLogInstance}(e_A, e_B)$ requires validated cryptographic origin or genesis tree identity proofs under $\eta$.
  3. Surface operator branding, hostnames, or endpoint similarity cannot establish formal instance equivalence.
  4. The candidate pair $(e_A, e_B)$ fails to satisfy the compound witness predicate, yielding positive witness set $W_+(q_{\text{exist}}, E) = \emptyset$.
  5. Negative evidence set $N_-(q_{\text{exist}}, E) = \emptyset$.
  6. Under Section 5.6, $\text{Eval}(q_{\text{exist}}, E)$ evaluates strictly to $(\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{unproven\_instance\_identity}}(e_A, e_B)\})$.
  7. Strong Kleene negation yields $\text{Val}(q_{\text{inst}}, E) = \neg_{K_3} \text{Unknown} = \text{Unknown}$.
  8. Distinct roots across unproven log instances cannot establish a proven contradiction (`False`); the model uniquely preserves `Unknown`.
- **Expected Output**: $(\mathcal{L}_0, (\text{Unknown}, \pi_{\text{open}}, \{\omega_{\text{unproven\_instance\_identity}}(e_A, e_B)\}, \emptyset))$.
- **Verdict**: `PASS`

---

## 2. Summary & Aggregate Audit

| Category | Total Cases | PASS | NEEDS_REVISION | FAIL |
|---|---|---|---|---|
| **Core Epistemic Resolution** (CTX-01 to CTX-03) | 3 | 3 | 0 | 0 |
| **Fail-Closed & Validation Boundaries** (CTX-04 to CTX-09) | 6 | 6 | 0 | 0 |
| **Identity & Invariant Protection** (CTX-10 to CTX-13) | 4 | 4 | 0 | 0 |
| **Contradiction & Evidence Hierarchy** (CTX-14, CTX-15) | 2 | 2 | 0 | 0 |
| **Strong Kleene ($K_3$) Composition** (CTX-16 to CTX-20) | 5 | 5 | 0 | 0 |
| **Concurrency & Audit Isolation** (CTX-21, CTX-22, CTX-25) | 3 | 3 | 0 | 0 |
| **Adversarial Integrity & Domain Barrier** (CTX-23, CTX-24, CTX-26) | 3 | 3 | 0 | 0 |
| **Epistemic Falsification & Negative Evidence** (CTX-27 to CTX-50) | 24 | 24 | 0 | 0 |
| **TOTAL** | **50** | **50** | **0** | **0** |

### Overall Verification Verdict
**VERDICT: PASS**

### Audit Summary:
1. **Zero Unsound Fails (`FAIL = 0`)**: The model permits zero unsafe states, zero truth-coercion bypasses, and zero fourth logical states.
2. **50 Unambiguous Derivations (`PASS = 50`)**: All 50 counterexamples—including unproven log instance identity preserving Unknown (CTX-50), compromised key quarantine (CTX-49), revoked key signature exclusion (CTX-48), unproven key-epoch continuity preserving Unknown (CTX-47), unproven clock comparability preserving Unknown (CTX-46), later epoch evidence ineffective for earlier temporal claims (CTX-45), acquisition-conditioned probe behavior invalidating unconditioned claims (CTX-44), vantage point colocation vs diversity checking (CTX-43), historical violation immutability despite subsequent convergence (CTX-42), new evidence overriding stale True to False (CTX-41), 99.9% partial observer coverage preserving Unknown (CTX-40), unproven comparability preserving Unknown (CTX-39), split-view positive falsification of global uniqueness (CTX-38), observer population scope restriction on universal claims (CTX-37), standard K3 universal negation of falsified claims (CTX-36), decisive policy conflict resolution (CTX-35), sound falsification via valid negative evidence (CTX-34), unvalidated completeness rejection (CTX-33), unresolved positive/negative contradiction handling (CTX-32), snapshot drift anti-staleness enforcement (CTX-31), narrow query predicate rejection (CTX-30), partial scope coverage restriction (CTX-29), partial temporal coverage restriction (CTX-28), open-world empty search preserving Unknown (CTX-27), diagnostic routing ($\text{Auditize}$ in CTX-04), post-mutation recovery without rollback (CTX-08), and fail-closed evaluator drift aborts (CTX-10)—derive unique, deterministic, and fail-closed outcomes under the specification.
