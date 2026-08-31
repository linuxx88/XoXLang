# Epistemic Resolution Model for X-o-X

## Document Status & Preamble
- **Status**: `EXPERIMENTAL_NON_NORMATIVE`
- **Scope**: Epistemic resolution formalization, negative evidence semantics, semantic boundary consistency, and mathematical hardening for `X-o-X`.
- **Non-Normative Declaration**: This document is an exploratory specification and does **not** alter, extend, or supersede the normative language core defined in `XOX_SPEC.md`.
- **Preservation Invariant**: The base language type system ($\mathbb{X} = \{\text{True}, \text{False}, \text{Unknown}\}$), Strong Kleene ($K_3$) logical operators, state-identity equality returning binary `Bool`, canonical `if` / `xen` / `else` control flow, and compiler/runtime pipelines remain unmodified and strictly authoritative.

---

## 1. Executive Summary & Core Principle

In `X-o-X`, `Unknown` is a first-class, valid epistemic state denoting insufficient information to establish `True` or `False`. It is fundamentally distinct from `False`, `null`, `nil`, `None`, or an exception.

Epistemic resolution is the formal process by which an unresolved epistemic state is refined through contract-constrained observational acquisition and re-evaluation.

### Fundamental Principle
> **Resolution is strictly observational evidence acquisition and re-evaluation against an invariant claim identity.**
> 
> A resolver possesses zero authority to directly assign or coerce a truth value. Only the total evaluation operator $\text{Eval}$ holds the authority to emit a truth value in $\mathbb{X} = \{\text{True}, \text{False}, \text{Unknown}\}$.

---

## 2. Semantic Domains & Formal Notation

### 2.1 Core Semantic Domains

| Domain | Symbol | Type / Structure | Description |
|---|---|---|---|
| **Truth States** | $\mathbb{X}$ | $\{\text{True}, \text{False}, \text{Unknown}\}$ | Closed three-valued logical domain. |
| **Propositions** | $\mathcal{P}$ | Inductive AST | Abstract statement, predicate, or compound proposition over $K_3$. |
| **Evaluator Identity & Version** | $\eta \in \mathcal{E} \times \mathcal{V}$ | $\text{ID} \times \text{SemVer}$ | Exact identity and immutable semantic version of evaluator, policy, and inference rules. |
| **Observation Frame** | $\phi \in \Phi$ | $(I_{\text{frame}}, \sigma, C)$ | Valid-time frame window $I_{\text{frame}} \subset \mathbb{T}$, world projection boundary $\sigma$, and environment context $C$. |
| **Claim Identity** | $\mathcal{Q}$ | $\mathcal{P} \times (\mathcal{E} \times \mathcal{V}) \times \Phi$ | Fully qualified resolvable claim tuple: $q = (P, \eta, \phi) \in \mathcal{Q}$. |
| **Search Universe** | $\mathcal{U} \in \mathbb{U}$ | $(U_{\text{id}}, \text{scope}, I_{\text{valid}}, \Sigma_{\text{snap}}, \text{spec})$ | Claim-relative bounded universe anchored to $P$, $\eta$, and $\phi$. |
| **Coverage Certificate** | $\chi \in \mathcal{X}$ | $(\mathcal{U}, \text{entity\_class}, \text{authority}, \text{proof}, \Gamma_\chi)$ | Formal proof certifying that universe snapshot $\Sigma_{\text{snap}}$ is closed/exhaustive for the target class over $I_{\text{covered}}(\chi) = I_{\text{valid}}(\mathcal{U})$. |
| **Exhaustive Query** | $\mathcal{Q}_e \in \mathbf{Q}$ | $(\mathcal{U}, \Sigma_{\text{snap}}, R_Q, \text{eval\_spec})$ | Deterministic query procedure bound to immutable snapshot $\Sigma_{\text{snap}}$ of $\mathcal{U}$ with query predicate $R_Q$. |
| **Negative Evidence Certificate** | $\nu \in \mathcal{N}$ | $(\mathcal{U}, \chi, \mathcal{Q}_e, \Sigma_{\text{snap}}, \text{empty\_proof}, \Gamma_\nu)$ | Proof certifying that exhaustive search over closed snapshot $\Sigma_{\text{snap}}$ yielded zero witnesses for $R_Q$. |
| **Evidence Payload** | $\text{EvPayload}$ | Tagged Sum Type | $\text{WitnessPayload}(d) \mid \text{CoveragePayload}(\chi) \mid \text{NegativePayload}(\nu)$. |
| **Obligation Universe** | $\mathcal{O}$ | Universal Set | Set of all well-formed epistemic obligations, causes, and witness requirements. |
| **Epistemic Obligations** | $\Omega$ | $\mathcal{P}(\mathcal{O})$ | Finite subset $\Omega \subseteq \mathcal{O}$ of decision-relevant unresolved atomic obligations derived strictly by $\text{Eval}$. |
| **Operational Diagnostics** | $\Delta$ | $\mathcal{D}^*$ | List/sequence of operational execution diagnostics (timeouts, transport errors, validation rejections). |
| **Auditizing Operator** | $\text{Auditize}$ | $\mathcal{D}^* \times \mathbb{T} \to \mathcal{A}ud^*$ | Deterministic mapping transforming operational execution diagnostics into typed audit records. |
| **Acquisition Contract** | $\mathcal{K}$ | $(\mathcal{S}_{\text{allowed}}, \mathcal{M}_{\text{allowed}}, k_{\text{wit}}, B_{\text{res}})$ | Evaluator-derived constraints on sources, methods, witness threshold, and non-interference bounds. |
| **Candidate Evidence** | $\mathcal{C}$ | Tagged Sum Type | $\text{CandWitness}(d, s, I_{\text{valid}}, \text{target}, \Gamma_{\text{raw}}) \mid \text{CandCoverage}(\chi_{\text{raw}}) \mid \text{CandNegative}(\nu_{\text{raw}})$. |
| **Validated Evidence Events** | $\mathcal{E}v$ | $(d_{\text{ev}}, s, I_{\text{valid}}, t_{\text{rec}}, \text{target}, \Gamma)$ | Accepted evidence: typed payload $d_{\text{ev}} \in \text{EvPayload}$, source $s$, valid-time $I_{\text{valid}}$, record-time $t_{\text{rec}}$, target claim $\text{target} \in \mathcal{Q}$, provenance DAG $\Gamma$. |
| **Audit Events** | $\mathcal{A}ud$ | $(\text{type}, \text{payload}, t_{\text{rec}}, \text{diag})$ | Operational audit record: rejected candidate logs, timeouts, signature failures, contract breaches. |
| **Journal Entries** | $\mathcal{J}$ | $\text{EvEntry}(\mathcal{E}v) \mid \text{AuditEntry}(\mathcal{A}ud)$ | Tagged sum type for entries in the append-only journal. |
| **Provenance Journal** | $\mathcal{L}$ | $\mathcal{J}^*$ | Append-only sequence of verified journal entries: $\mathcal{L} = [j_1, j_2, \dots, j_k]$. |
| **Evaluation Certificate** | $\Pi$ | Derivation Trace | Proof object / derivation tree justifying the evaluation result: $\pi \in \Pi$. |
| **Resolution Result** | $\mathcal{R}es$ | $\mathbb{X} \times \Pi \times \mathcal{P}(\mathcal{O}) \times \mathcal{D}^*$ | Quadruple: $r = (v, \pi, \Omega, \Delta)$. |

### 2.2 Claim Identity Invariance & Evaluator Drift Abort
A resolution operation cannot be applied to an unanchored scalar `XoX` value. Resolution requires a fully qualified claim identity:
$$q = (P, \eta, \phi)$$
where:
1. $P \in \mathcal{P}$: The immutable proposition.
2. $\eta \in \mathcal{E} \times \mathcal{V}$: The exact evaluator and policy version.
3. $\phi \in \Phi$: The fixed observation frame.

**Canonical Evaluator Drift Invariant**:
- If resolution of $q = (P, \eta_1, \phi)$ attempts any evaluation under $\eta_2$ where $\eta_2 \neq \eta_1$, the resolution invocation **aborts fail-closed immediately**.
- The system **does not silently substitute $\eta_1$** and **does not evaluate $q$ under $\eta_2$**.
- The system preserves the last truth result produced by $\text{Eval}$ for $q$ under $\eta_1$ ($v_0 = \text{Unknown}, \pi_0, \Omega_0$).
- An operational diagnostic $\text{EvaluatorDriftDiag}$ is recorded in $\Delta$ and appended as $\text{AuditEntry}(\text{EvaluatorDriftAudit})$ to $\mathcal{L}'$ via $\text{Auditize}$.
- Any evaluation under $\eta_2$ strictly requires the caller to construct a distinct claim $q' = (P, \eta_2, \phi)$.

### 2.3 Possibility-Support Semantics & Binary Factive Realization Theorem
For a bivalent factive proposition $P$ evaluated over a non-empty admissible world space $W_{\text{factive}}$, let $D = \{\text{False}, \text{True}\}$.

1. **Realization Support**: The possibility support $S_P \subseteq D$ is the extensional set of realized truth values across admissible realities:
   $$S_P = \{ \text{eval}(P, w) \mid w \in W_{\text{factive}} \}$$
2. **Boolean Possibility Carrier**: The carrier is the finite Boolean lattice $\mathcal{P}(D) = \{ \emptyset, \{\text{False}\}, \{\text{True}\}, \{\text{False}, \text{True}\} \}$ with bottom element $\emptyset = \text{Contradiction}$.
3. **Binary Factive Realization Theorem**: Under bivalent, total, defined world-level evaluation over non-empty $W_{\text{factive}}$, $S_P$ is a non-empty subset of $D$. Exactly $2^2 - 1 = 3$ non-empty realization classes exist, which project canonically via $\pi_v: \mathcal{P}(D) \setminus \{\emptyset\} \to \mathbb{X}$ to the XoX truth domain:
   - $S_P = \{\text{True}\} \implies \pi_v(S_P) = \text{True}$
   - $S_P = \{\text{False}\} \implies \pi_v(S_P) = \text{False}$
   - $S_P = \{\text{False}, \text{True}\} \implies \pi_v(S_P) = \text{Unknown}$
4. **Contradiction Isolation**: $S_P = \emptyset$ represents Ontological Contradiction ($W_{\text{factive}} = \emptyset$). It is required in $\mathcal{P}(D)$ for algebraic meet-closure but is not an executable XoX truth value and aborts fail-closed outside $\mathbb{X}$.
5. **Two-Tier Algebra Architecture**:
   - **Constraint Layer**: $\mathcal{P}(D)$ under $(\cap, \cup, \emptyset, D)$ governs single-claim evidence refinement (meet $\cap$ = constraint conjunction, join $\cup$ = uncertainty disjunction).
   - **Evaluation Layer**: Pointwise push-forward over joint realization spaces $R_{(P_1, \dots, P_k)} \subseteq D^k$ governs propositional truth composition under $K_3$.
6. **Pointwise Negation Invariance**: Logical NOT operates by elementwise Boolean inversion $\text{not}(S_P) = \{ \neg_{\text{Bool}} x \mid x \in S_P \}$, strictly distinct from set complement $D \setminus S_P$.
7. **Relational Composition Boundary**: Marginal Strong Kleene $K_3$ composition is exact under epistemic independence ($R_{(A,B)} = S_A \times S_B$) and a sound conservative over-approximation ($S_{A \land B} \subseteq K_3\text{-AND}(\pi_v(S_A), \pi_v(S_B))$) under arbitrary inter-propositional correlation.
8. **Full Extensional Carrier Exactness**: For an observationally distinguishable world space $W_{\text{obs}}$ with $N = |W_{\text{obs}}| < \infty$, the full mathematical extensional support carrier is defined as $C_{\text{full}}(W_{\text{obs}}) = \mathcal{P}(W_{\text{obs}}) \setminus \{\emptyset\}$, with $|C_{\text{full}}(W_{\text{obs}})| = 2^N - 1$ exactly by definition of the non-empty powerset. Adding an independent factor of arity $k$ transforms world cardinality to $k N$ and carrier capacity to $E' = 2^{k N} - 1 = (E + 1)^k - 1$. For independent binary variables ($k=2$), $E_{n+1} = (E_n + 1)^2 - 1$.
9. **Admissible, Reachable, and Observable Hierarchy**:
   - $\mathcal{F}_{\text{adm}} \subseteq C_{\text{full}}(W_{\text{obs}})$: Admissible supports permitted by relational constraints.
   - $\mathcal{F}_{\text{reach}}(s_0, \text{Auth}) \subseteq \mathcal{F}_{\text{adm}}$: Supports reachable from initial state $s_0$ under legal capability transitions.
   - $\mathcal{F}_{\text{obs}} = \mathcal{F}_{\text{adm}} / \sim_{\text{Obs}}$: Observational quotient space.
   - $\mathcal{F}_{\text{reach\_obs}} = \mathcal{F}_{\text{reach}} / \sim_{\text{Obs}}$: Reachable observational quotient.
   - Valid relations: $|\mathcal{F}_{\text{reach}}| \le |\mathcal{F}_{\text{adm}}| \le |C_{\text{full}}(W_{\text{obs}})| = 2^N - 1$, $|\mathcal{F}_{\text{obs}}| \le |\mathcal{F}_{\text{adm}}|$, $|\mathcal{F}_{\text{reach\_obs}}| \le |\mathcal{F}_{\text{reach}}|$, and $|\mathcal{F}_{\text{reach\_obs}}| \le |\mathcal{F}_{\text{obs}}|$. ($\mathcal{F}_{\text{reach}}$ is a subset while $\mathcal{F}_{\text{obs}}$ is a quotient; their cardinalities are not generally ordered relative to each other).
10. **Capacity vs Structure Boundary**: Equal cardinality $N$ implies isomorphic bare powerset lattices $C_{\text{full}}(W_{\text{obs}})$, but does not imply semantic equivalence: coordinate dependencies, causal transitions, temporal accessibility, and authority policies constitute irreducible relational structure.

### 2.4 Structured World Model ($M$)
To avoid conflating raw support capacity with relational structure, a structured factive context is modeled as:
$$M = (W_{\text{obs}}, \{R_i\}, G_{\text{trans}}, \text{Auth})$$
where:
1. $W_{\text{obs}}$: The set of distinguishable admissible world states ($N = |W_{\text{obs}}|$).
2. $\{R_i\}$: Relational and coordinate dependency constraints across variables ($R_i \subseteq D_1 \times \dots \times D_m$).
3. $G_{\text{trans}} = (W_{\text{obs}}, E_{\text{trans}})$: Causal and temporal accessibility transition DAG between worlds.
4. $\text{Auth}: \mathcal{P}(W_{\text{obs}}) \times \text{Capability} \to \mathcal{P}(W_{\text{obs}})$: Formal capability authorization function governing legal support reductions.

### 2.5 Generic Constrained-Possibility Model & Geometric Illustration
A general constrained possibility space is defined by $(X, C, A)$, where $X$ is a state space, $C$ is a set of active constraints, and admissible support is $A(C) = \{ x \in X \mid \forall c \in C.\, x \text{ satisfies } c \}$.

#### Non-Normative Mathematical Illustration: Isotropic Origin
At an origin point $O \in \mathbb{R}^n$, the unconstrained space of unit directions is the continuous sphere $S^{n-1} = \{ v \in T_O(\mathbb{R}^n) \mid \|v\| = 1 \}$ with maximal rotation symmetry group $O(n)$. Selecting a reference unit vector $v_1$ reduces the admissible direction set and breaks symmetry to the stabilizer subgroup $\text{Stab}_{O(n)}(v_1) \cong O(n-1)$.

#### Exact Correspondence vs Mere Analogy

| Dimension | Generic Constraint Refinement | XoX Factive Epistemology | Continuous Geometric Space ($S^{n-1}$) | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Initial State** | Unconstrained carrier $X$ | Maximal support $S_0 = D$ ($W_{\text{factive}}$) | Isotropic unit sphere $S^{n-1}$ | **Exact** |
| **Refinement** | Subset shrinking $A(C') \subseteq A(C)$ | Evidence reduction $S \to S' \subset S$ | Directional constraint cone | **Exact** |
| **Contradiction** | Incompatible constraints ($A(C) = \emptyset$) | Unsatisfiable context ($W_{\text{factive}} = \emptyset$) | Incompatible vectors ($A(C) = \emptyset$) | **Exact** |
| **Symmetry Loss** | Stabilizer reduction $\text{Stab}(C') \subseteq \text{Stab}(C)$ | Permutation subgroup reduction | Orthogonal group cascade $O(n) \to O(n-1)$ | **Exact** |
| **Cardinality** | Discrete or continuous | Discrete finite powerset ($2^N - 1$) | Uncountable continuum ($2^{\aleph_0}$) | **Boundary** (Requires finite partition) |
| **Authority** | Abstract constraint parameter | Explicit cryptographic tokens (`Auth`) | Memoryless / Permissionless | **Analogy Only** (No geometric analogue) |
| **Provenance** | Labeled derivation path | Non-monotone DAG ($\pi \in \Pi$) | Memoryless geometric state | **Analogy Only** (No geometric analogue) |
| **Truth Projection** | None | Modular 3-valued quotient ($\mathbb{X}$) | Continuous Lie coordinates | **Analogy Only** (No geometric analogue) |

---

## 3. Evidence Journal & Interval-Based Admissibility

### 3.1 Tagged Append-Only Journal ($\mathcal{L}$)
All evidence events and operational audit events are recorded in an append-only journal $\mathcal{L} \in \mathcal{J}^*$:
$$\mathcal{L}' = \mathcal{L} \mathbin{+\!\!+} [j_{\text{new}}]$$
where $j_{\text{new}} \in \{\text{EvEntry}(e), \text{AuditEntry}(a)\}$. Journal entries are immutable once appended.

### 3.2 Bitemporal Interval Model & Evidence Structure
Every evidence event $e \in \mathcal{E}v$ possesses:
1. **Evidence Payload** $d_{\text{ev}}(e) \in \text{EvPayload}$: Domain witness payload, coverage certificate $\chi$, or negative certificate $\nu$.
2. **Source Identity** $s(e) \in \mathcal{S}$: Cryptographically verified source or registry authority.
3. **Valid-Time Interval** $I_{\text{valid}}(e) = [t_{\text{start}}(e), t_{\text{end}}(e)] \subset \mathbb{T}$: The time interval during which the observed phenomenon held true in the world (with $t_{\text{start}} = t_{\text{end}}$ for point observations).
4. **Record Time** $t_{\text{rec}}(e) \in \mathbb{T}$: Monotonic transaction timestamp when $e$ was verified and committed to $\mathcal{L}$.
5. **Target Claim Anchor** $\text{target}(e) \in \mathcal{Q}$: Anchored resolvable claim $q = (P, \eta, \phi)$ for which the evidence event was acquired and validated.
6. **Provenance DAG** $\Gamma(e)$: Acyclic causal provenance graph rooting in recognized trust anchors.

### 3.3 Admissible Evidence View ($\text{Adm}$) & Validation Separation
The primary gatekeeper for raw candidate evidence is the $\text{Validate}$ operator (§6.2), which rejects temporal or policy mismatches before candidate data can enter $\mathcal{E}v$.

Evaluation never consumes the raw journal $\mathcal{L}$ directly. The admissible view $E \subseteq \mathcal{E}v$ is computed as a secondary defensive projection:
$$E = \text{Adm}(\mathcal{L}, \eta, \phi) = \{ e \in \mathcal{E}v \mid \exists i.\; \mathcal{L}[i] = \text{EvEntry}(e) \land \text{IsAdmissible}(e, \eta, \phi) \}$$
where $\text{IsAdmissible}(e, \eta, \phi)$ verifies:
- **Temporal Interval Alignment**: The interval relation $\mathcal{R}_{\text{temp}}^\eta(I_{\text{valid}}(e), I_{\text{frame}}(\phi)) = \text{True}$ holds under evaluator policy $\eta$ (e.g. Allen interval relations: *Within*, *Overlaps*, or *Contains*).
- **Policy Admissibility**: Source $s(e)$, cryptographic credentials, and payload format satisfy policy $\eta$.
- **Provenance Integrity**: The provenance DAG $\Gamma(e)$ is acyclic and roots exclusively in trust anchors recognized by $\eta$.
- **Contextual Scope**: $e$ falls within projection boundary $\sigma(\phi)$ and environment constraints $C(\phi)$.

**Strict Audit Isolation**: Audit entries ($\text{AuditEntry}(a)$) are strictly excluded from $E$. Operational diagnostics and failure records cannot influence or pollute the evidence view consumed by $\text{Eval}$.

---

## 4. Evaluation Function, Modular Truth & Strong Kleene Semantics

### 4.1 Evaluation Operator ($\text{Eval}$)
The evaluation of claim $q$ against admissible evidence view $E$ is defined as a total mathematical function:
$$\text{Eval}: \mathcal{Q} \times \mathcal{P}(\mathcal{E}v) \to \mathbb{X} \times \Pi \times \mathcal{P}(\mathcal{O})$$
$$\text{Eval}(q, E) = (v, \pi, \Omega)$$

We define canonical projection operators:
- $\text{Val}(q, E) = \pi_v(\text{Eval}(q, E)) \in \mathbb{X}$
- $\text{Cert}(q, E) = \pi_\Pi(\text{Eval}(q, E)) \in \Pi$
- $\text{Obl}(q, E) = \pi_\Omega(\text{Eval}(q, E)) \subseteq \mathcal{O}$

### 4.2 Separation of Epistemic Obligations ($\Omega$) vs Operational Diagnostics ($\Delta$)
- **Epistemic Obligations** $\Omega \subseteq \mathcal{O}$ are derived **exclusively by $\text{Eval}$ from admissible evidence $E$**. They identify domain-level missing information, witness needs, unproven closure requirements, temporal coverage gaps, or unresolvable evidential contradictions for proposition $P$.
- **Operational Diagnostics** $\Delta \in \mathcal{D}^*$ record execution anomalies (such as network timeouts, transport errors, candidate validation rejections, or contract breaches).
- **Boundary Invariant**: Operational execution events belong strictly to $\Delta$ and $\mathcal{A}ud$. They are **never injected into $\Omega$** unless independently established as admissible domain evidence in $E$.

### 4.3 Modular Subclaim Truth & Context Independence
The truth value of any anchored subclaim $(S, \eta, \phi)$ evaluated against admissible evidence $E$ depends **strictly and exclusively** on $(S, \eta, \phi)$ and $E$:
$$\text{Val}((S, \eta, \phi), E) \text{ is invariant with respect to the enclosing parent AST context.}$$

Parent proposition AST structure never mutates or overrides the local truth value of subclaim $S$.

### 4.4 Strong Kleene ($K_3$) Consistency for Compound Propositions
Strong Kleene logical operators apply strictly to the **truth-value projection** $\text{Val}(q, E) \in \mathbb{X}$:

$$\text{Val}((P_1 \land P_2, \eta, \phi), E) = \text{Val}((P_1, \eta, \phi), E) \land_{K_3} \text{Val}((P_2, \eta, \phi), E)$$
$$\text{Val}((P_1 \lor P_2, \eta, \phi), E) = \text{Val}((P_1, \eta, \phi), E) \lor_{K_3} \text{Val}((P_2, \eta, \phi), E)$$
$$\text{Val}((\neg P, \eta, \phi), E) = \neg_{K_3} \text{Val}((P, \eta, \phi), E)$$

### 4.5 Decision-Relevance & Conservative Obligation Tracking
Epistemic obligations $\text{Obl}(q, E) \subseteq \mathcal{O}$ contain only those unresolved atomic subclaims necessary to determine the root claim:
1. **Determinate Root**:
   $$\text{Val}(q, E) \in \{\text{True}, \text{False}\} \implies \text{Obl}(q, E) = \emptyset$$
2. **Dominance in Conjunction ($A \land B$)**:
   - If $\text{Val}(A) = \text{False}$, then $\text{Val}(A \land B) = \text{False}$ and $\text{Obl}(A \land B) = \emptyset$ (subclaim $B$ is short-circuited/pruned).
   - If $\text{Val}(A) = \text{True}$ and $\text{Val}(B) = \text{Unknown}$, then $\text{Obl}(A \land B) = \text{Obl}(B)$.
   - If $\text{Val}(A) = \text{Unknown}$ and $\text{Val}(B) = \text{Unknown}$, both subclaims are unresolved; their obligations are tracked conservatively as $\text{Obl}(A) \cup \text{Obl}(B)$.
3. **Dominance in Disjunction ($A \lor B$)**:
   - If $\text{Val}(A) = \text{True}$, then $\text{Val}(A \lor B) = \text{True}$ and $\text{Obl}(A \lor B) = \emptyset$ (subclaim $B$ pruned).
   - If $\text{Val}(A) = \text{False}$ and $\text{Val}(B) = \text{Unknown}$, then $\text{Obl}(A \lor B) = \text{Obl}(B)$.
4. **Epistemic Obligation Pruning vs Language Operational Trace Semantics**:
   - While mathematical Strong Kleene dominance enables declarative pruning of unneeded acquisition obligations, concrete XoXLang runtime execution evaluates operands strictly left-to-right (XOX_SPEC §7, §7.1).
   - Mathematical value equivalence under $K_3$ does not imply observable equivalence when subexpressions carry side effects or exceptions.
   - Declarative epistemic obligation pruning does not authorize compilers to reorder operands or eliminate left-side expressions without evaluating them (Strict Operational Trace Preservation Invariant, §7.1).

### 4.6 Local Evidential Conflict vs Ontological Contradiction
A fundamental distinction governs conflicting information in the epistemic model:
1. **Local Evidential Conflict ($|W_{\text{factive}}| \ge 2$)**: When admissible observational evidence items $e_1, e_2 \in E$ present competing proofs for an anchored subclaim $(S, \eta, \phi)$ in an open world with non-empty admissible alternatives:
   - If evaluator policy $\eta$ contains an explicit deterministic dispute-resolution rule (e.g. authority hierarchy, calibration window, or physical witness precedence) that decisively resolves the conflict, $\text{Eval}$ applies that rule deterministically to produce $\text{True}$ or $\text{False}$.
   - In the absence of a decisive policy tie-break rule, the local subclaim evaluates modularly to `Unknown`:
     $$\text{Val}((S, \eta, \phi), E) = \text{Unknown}$$
   - **Decision-Relevance at the Root**: Decision-relevance under $K_3$ controls whether this subclaim `Unknown` propagates to the root truth value $\text{Val}(P, E)$ and whether the evidential ambiguity obligation $\omega_{\text{conflict}}(S) \in \mathcal{O}$ is included in root obligations $\text{Obl}(P, E)$.
   - If $S$ is short-circuited by a dominant sibling (e.g. $S \land \text{False} = \text{False}$ or $S \lor \text{True} = \text{True}$), the root evaluates to a determinate truth value and $\omega_{\text{conflict}}(S)$ is pruned from root obligations.
2. **Ontological Contradiction ($W_{\text{factive}} = \emptyset$)**: When active hard constraints possessing authoritative `OntologicalConstraintToken` capabilities are jointly unsatisfiable:
   - Contradiction is not a fourth $K_3$ truth value and cannot be mapped to `Unknown`.
   - An actually evaluated Contradiction propagates immediately fail-closed, aborting evaluation.
   - An unevaluated operand skipped by legitimate left-to-right short-circuiting is never evaluated and produces no Contradiction.

---

## 5. Epistemic Falsification, Search Universes & Negative Evidence

### 5.1 Open-World Principle & Absence of Evidence
`X-o-X` strictly adheres to **Open-World Semantics by default**:
$$\text{Absence of Evidence } \neq \text{ Evidence of Absence}$$

Failure to acquire a witness, query timeouts, empty search results over unverified scopes, or access denial **must never by themselves establish `False`**. In the absence of positive proof or validated exhaustive coverage, the truth state remains `Unknown`.

### 5.2 Claim-Relative Search Universes ($\mathcal{U}$) & Scope Subsumption
Proving the absence of an entity or event requires bounding the search to a **claim-relative Search Universe** $\mathcal{U} \in \mathbb{U}$:
$$\mathcal{U} = (U_{\text{id}}, \text{scope}, I_{\text{valid}}, \Sigma_{\text{snap}}, \text{spec})$$
where:
- $\text{scope}$ is the structural and relational domain boundary.
- $I_{\text{valid}}$ is the temporal validity window of the universe data.
- $\Sigma_{\text{snap}}$ is the immutable, cryptographically identified state snapshot of the universe.
- $\text{spec}$ defines the universe indexing and partitioning rules.

**Formal Scope Subsumption Predicate ($\text{CoversClaimScope}$)**:
$$\text{CoversClaimScope}(\mathcal{U}, q, \eta, \phi) \in \text{Bool}$$
- Verifies that $\mathcal{U}.\text{scope}$ fully subsumes the structural, relational, and contextual domain of quantification required by claim $q = (P_{\text{exist}}, \eta, \phi)$ under evaluator policy $\eta$ and observation frame $\phi$.
- **Strict Scope Localization & Sub-Scope Restriction**: If $\mathcal{U}$ covers only a strict sub-scope of the claim ($\text{CoversClaimScope}(\mathcal{U}, q, \eta, \phi) = \text{Bool.False}$), `False` is strictly forbidden. The existential claim evaluates to $\text{Unknown}$ with a scope-coverage obligation $\omega_{\text{scope\_gap}}(\text{uncovered\_subscope}) \in \mathcal{O}$.

### 5.3 Coverage Certificates ($\chi$) & Full Temporal Coverage Direction
A **Coverage Certificate** $\chi \in \mathcal{X}$ is a formal proof object establishing that a universe snapshot $\Sigma_{\text{snap}}$ is exhaustive and complete for a specified entity/relation class over covered interval $I_{\text{covered}}(\chi) = I_{\text{valid}}(\mathcal{U})$:
$$\chi = (\mathcal{U}, \text{entity\_class}, \text{authority}, \text{completeness\_proof}, \Gamma_\chi)$$

**Full Temporal Coverage Direction Requirement**:
- For $\chi$ to establish valid closure for claim $q = (P_{\text{exist}}, \eta, \phi)$, the validated coverage interval $I_{\text{covered}}(\chi)$ must **fully cover** the observation frame interval $I_{\text{frame}}(\phi)$:
  $$I_{\text{frame}}(\phi) \subseteq I_{\text{covered}}(\chi)$$
- A universe covering only a strict subinterval ($I_{\text{covered}} \subset I_{\text{frame}}$ with $I_{\text{frame}} \setminus I_{\text{covered}} \neq \emptyset$) **cannot** establish `False` for the claim. Partial temporal coverage leaves an unobserved temporal gap, resulting in `Unknown` with obligation $\omega_{\text{temporal\_gap}}(I_{\text{frame}} \setminus I_{\text{covered}}) \in \mathcal{O}$.

### 5.4 Exhaustive Query Procedures & Negative Evidence Certificates ($\nu$)
1. **Exhaustive Query ($\mathcal{Q}_e$)**: A deterministic query procedure bound to immutable snapshot $\Sigma_{\text{snap}}$ with query predicate $R_Q$.
2. **Query Predicate Coverage / Equivalence**:
   - The query predicate $R_Q$ executed by $\mathcal{Q}_e$ must be formally proven under $\eta$ to be semantically equivalent to or conservatively covering existential predicate $R$:
     $$\forall x \in \mathcal{U}.\; R(x) \implies R_Q(x)$$
   - A query predicate narrower than $R$ ($R_Q \subset R$) leaves possible witnesses unqueried and is strictly forbidden from generating valid negative evidence for $R$.
3. **Negative Evidence Certificate ($\nu$)**: A formal derivation object certifying that $\mathcal{Q}_e$ executed over snapshot $\Sigma_{\text{snap}}$ of a validated closed universe $\chi$ produced an empty witness set:
   $$\nu = (\mathcal{U}, \chi, \mathcal{Q}_e, \Sigma_{\text{snap}}, \text{empty\_result\_proof}, \Gamma_\nu)$$
4. **Candidate Domain Ingestion**: $\nu$ originates as Candidate Evidence ($\text{CandNegative}(\nu_{\text{raw}}) \in \mathcal{C}$), enters $\mathcal{E}v$ only through $\text{Validate}$, and is recorded in journal $\mathcal{L}$ as $\text{EvEntry}(e_\nu)$ with payload $e_\nu.d_{\text{ev}} = \text{NegativePayload}(\nu)$.

### 5.5 Validity of Negative Evidence Certificates ($\text{IsValidNegativeCertificate}$)
We formally define the validation predicate:
$$\text{IsValidNegativeCertificate}(e_\nu, q, \eta, \phi, E) \in \text{Bool}$$
where $e_\nu \in \mathcal{E}v$, $q = (P_{\text{exist}}, \eta, \phi) \in \mathcal{Q}$, and $E \subseteq \mathcal{E}v$.

$\text{IsValidNegativeCertificate}(e_\nu, q, \eta, \phi, E) = \text{Bool.True}$ if and only if all of the following conditions hold simultaneously under evaluator policy $\eta$:
1. **Typed Payload & Target Alignment**:
   $$e_\nu.d_{\text{ev}} = \text{NegativePayload}(\nu) \land e_\nu.\text{target} = q \land P_{\text{exist}} = \exists x.\, R(x)$$
2. **Universe & Snapshot Identity**:
   $$\nu.\mathcal{U}.\text{id} = U_{\text{id}} \land \nu.\Sigma_{\text{snap}} = \Sigma_{\text{snap}}(\mathcal{U})$$
3. **Formal Claim Scope Subsumption**:
   $$\text{CoversClaimScope}(\nu.\mathcal{U}, q, \eta, \phi) = \text{Bool.True}$$
4. **Validated Coverage Certificate in $E$**:
   There exists $e_\chi \in E$ such that:
   $$e_\chi.d_{\text{ev}} = \text{CoveragePayload}(\chi) \land \chi.\mathcal{U}.\text{id} = \nu.\mathcal{U}.\text{id} \land \chi.\mathcal{U}.\Sigma_{\text{snap}} = \nu.\Sigma_{\text{snap}} \land \chi.\text{entity\_class} = R \land \text{IsAdmissible}(e_\chi, \eta, \phi)$$
5. **Full Temporal Coverage**:
   $$I_{\text{frame}}(\phi) \subseteq I_{\text{covered}}(\chi)$$
6. **Predicate Subsumption / Equivalence**:
   $$\text{ProvablePredicateCover}(\nu.\mathcal{Q}_e.R_Q, R, \eta) = \text{Bool.True} \quad (\forall x \in \mathcal{U}.\; R(x) \implies R_Q(x))$$
7. **Partition Exhaustiveness**:
   $\nu.\mathcal{Q}_e$ is verified to inspect 100% of partition blocks defined in $\nu.\mathcal{U}.\text{spec}$ for snapshot $\nu.\Sigma_{\text{snap}}$.
8. **Empty-Result Soundness**:
   $\nu.\text{empty\_result\_proof}$ is valid, acyclic, and justifies zero witness count.
9. **Provenance & Cryptographic Integrity**:
   $e_\nu.\Gamma$ is acyclic and signed by recognized trust anchors under $\eta$.
10. **Snapshot Freshness (Anti-Staleness)**:
   Snapshot $\nu.\Sigma_{\text{snap}}$ is fresh and unmutated relative to the current evidence snapshot $E$.

### 5.6 Evaluation of Existential Claims ($P_{\text{exist}} = \exists x.\, R(x)$)
Given claim $q = (P_{\text{exist}}, \eta, \phi)$ where $P_{\text{exist}} = \exists x.\, R(x)$ and admissible evidence view $E = \text{Adm}(\mathcal{L}, \eta, \phi)$, we construct two deterministic, canonical evidence sets:

1. **Admissible Positive Witness Collection**:
   $$W_+(q, E) = \{ w \in E \mid \exists d.\; w.d_{\text{ev}} = \text{WitnessPayload}(d) \land R(d) = \text{True} \land \text{IsValidWitness}(w, \eta, \phi) \}$$
2. **Admissible Negative Evidence Collection**:
   $$N_-(q, E) = \{ e_\nu \in E \mid \exists \nu.\; e_\nu.d_{\text{ev}} = \text{NegativePayload}(\nu) \land \text{IsValidNegativeCertificate}(e_\nu, q, \eta, \phi, E) = \text{Bool.True} \}$$

The evaluation function computes the full evaluation triple:
$$\text{Eval}(q, E) = \begin{cases} 
\text{ResolveConflict}(\eta, q, W_+(q, E), N_-(q, E)) & \text{if } W_+(q, E) \neq \emptyset \land N_-(q, E) \neq \emptyset \\
(\text{True}, \pi_{\text{wit}}(W_+), \emptyset) & \text{if } W_+(q, E) \neq \emptyset \land N_-(q, E) = \emptyset \\
(\text{False}, \pi_{\text{abs}}(N_-), \emptyset) & \text{if } W_+(q, E) = \emptyset \land N_-(q, E) \neq \emptyset \\
(\text{Unknown}, \pi_{\text{open}}, \Omega_{\text{missing}}) & \text{if } W_+(q, E) = \emptyset \land N_-(q, E) = \emptyset
\end{cases}$$

The canonical projections $\text{Val}(q, E) \in \mathbb{X}$, $\text{Cert}(q, E) \in \Pi$, and $\text{Obl}(q, E) \subseteq \mathcal{O}$ are defined by standard projection over $\text{Eval}(q, E)$:
- $\text{Val}(q, E) = \pi_v(\text{Eval}(q, E))$
- $\text{Cert}(q, E) = \pi_\Pi(\text{Eval}(q, E))$
- $\text{Obl}(q, E) = \pi_\Omega(\text{Eval}(q, E))$

**Semantics & Obligation Tracking**:
- **Case `True`**: $W_+(q, E) \neq \emptyset$ and $N_-(q, E) = \emptyset$. Admissible witnesses establish existence with certificate $\pi_{\text{wit}}(W_+)$ and $\text{Obl}(q, E) = \emptyset$.
- **Case `False`**: $W_+(q, E) = \emptyset$ and $N_-(q, E) \neq \emptyset$. Validated negative certificates establish absence within closed frame $\phi$ with certificate $\pi_{\text{abs}}(N_-)$ and $\text{Obl}(q, E) = \emptyset$.
- **Case `Unknown`**: $W_+(q, E) = \emptyset$ and $N_-(q, E) = \emptyset$. Open-world default holds. If candidate queries were attempted without validated closure $\chi$, full scope coverage, or full temporal coverage, $\text{Eval}$ derives missing epistemic obligations $\Omega_{\text{missing}} \subseteq \{\omega_{\text{unproven\_closure}}(\mathcal{U}), \omega_{\text{scope\_gap}}, \omega_{\text{temporal\_gap}}\}$.
- **Deterministic Conflict Resolution ($\text{ResolveConflict}$)**:
  $$\text{ResolveConflict}: (\mathcal{E} \times \mathcal{V}) \times \mathcal{Q} \times \mathcal{P}(\mathcal{E}v) \times \mathcal{P}(\mathcal{E}v) \to \mathbb{X} \times \Pi \times \mathcal{P}(\mathcal{O})$$
  - $\text{ResolveConflict}(\eta, q, W_+, N_-)$ is a total deterministic function evaluating the full admissible collections $W_+$ and $N_-$ under evaluator policy $\eta$.
  - If $\eta$ specifies an explicit deterministic priority or timestamp ordering (e.g. verified physical witness overrides closed-registry timestamp), $\text{ResolveConflict}$ produces $(v_{\text{decisive}}, \pi_{\text{conflict\_resolved}}, \emptyset)$ where $v_{\text{decisive}} \in \{\text{True}, \text{False}\}$.
  - If $\eta$ contains no decisive tie-break rule, $\text{ResolveConflict}$ deterministically yields $(\text{Unknown}, \pi_{\text{unresolved\_conflict}}, \{\omega_{\text{conflict}}(q, W_+, N_-)\})$.

### 5.7 Standard Strong Kleene Negation for Universal Claims
Universal negative claims (e.g. $P_{\text{univ}} = \forall x.\, \neg R(x) \equiv \neg (\exists x.\, R(x))$) require no ad-hoc negative truth machinery:
$$\text{Val}((\neg P_{\text{exist}}, \eta, \phi), E) = \neg_{K_3} \text{Val}((P_{\text{exist}}, \eta, \phi), E)$$
- If $P_{\text{exist}}$ evaluates to $\text{False}$ via validated negative evidence, $\neg P_{\text{exist}}$ evaluates to $\text{True}$ via standard $K_3$ logical negation ($\neg_{K_3} \text{False} = \text{True}$).
- If $P_{\text{exist}}$ evaluates to $\text{Unknown}$, $\neg P_{\text{exist}}$ evaluates to $\text{Unknown}$ ($\neg_{K_3} \text{Unknown} = \text{Unknown}$).

### 5.8 Real-World Universes & Terminal Unknown
In physical, distributed, or open real-world environments, proving exhaustive universe closure $\chi$ is frequently mathematically or operationally impossible. In all such cases:
$$\text{Terminal State is legitimately } \text{Unknown}$$
`Unknown` correctly and safely records that absence cannot be proven.

---

## 6. Tripartite Separation, Candidate Domain & Canonical Contracts

### 6.1 Architecture & Authority Isolation
The resolution pipeline maintains strict isolation among **Acquisition**, **Validation**, and **Evaluation**, mediated by a distinct **Candidate Evidence Domain** $\mathcal{C}$, a canonical **Acquisition Contract** $\kappa$, and a formal diagnostic bridging operator $\text{Auditize}$:

```
                 +-------------------------------------------------------------+
                 |                         Eval(q, E)                          |
                 |     Sole authority to emit True, False, or Unknown for q    |
                 +-------------------------------------------------------------+
                                                ^
                                                | Admissible View E = Adm(L', eta, phi)
                                                |
                 +-------------------------------------------------------------+
                 |              Validate(Cand, L, eta, phi, kappa)             |
                 |     Validates Cand in C -> outputs Ev in Ev and Aud_val     |
                 +-------------------------------------------------------------+
                                                ^
                                                | Candidate Evidence Cand subset C
                                                | (CandWitness, CandCoverage, CandNegative)
                                                |
                 +-------------------------------------------------------------+
                 |                       Acquire(kappa)                        |
                 |       Produces (Cand, Delta_acq); NEVER a truth value       |
                 +-------------------------------------------------------------+
                                                ^
                                                | Canonical Contract kappa = Contract_eta(q, Omega, phi)
                                                |
                 +-------------------------------------------------------------+
                 |                 Derived Obligations (Omega)                 |
                 +-------------------------------------------------------------+
```

### 6.2 Candidate Evidence Domain ($\mathcal{C}$) vs Validated Evidence ($\mathcal{E}v$)
- **Domain Barrier & Tagged Ingestion**: Raw candidate outputs inhabit the unvalidated **Candidate Evidence** domain $\mathcal{C}$:
  $$\mathcal{C} = \text{CandWitness}(d, s, I_{\text{valid}}, \text{target}, \Gamma_{\text{raw}}) \mid \text{CandCoverage}(\chi_{\text{raw}}) \mid \text{CandNegative}(\nu_{\text{raw}})$$
  Raw candidate artifacts **cannot inhabit $\mathcal{E}v$** directly.
- **Primary Validation Boundary ($\text{Validate}$)**:
  $$\text{Validate}: \mathcal{P}(\mathcal{C}) \times \mathcal{L} \times (\mathcal{E} \times \mathcal{V}) \times \Phi \times \mathcal{K} \to \mathcal{P}(\mathcal{E}v) \times \mathcal{P}(\mathcal{A}ud) \times \mathcal{D}^*$$
  $$\text{Validate}(\mathcal{C}_{\text{cand}}, \mathcal{L}, \eta, \phi, \kappa) = (\Delta \mathcal{E}v_{\text{acc}}, \Delta \mathcal{A}ud_{\text{val}}, \Delta_{\text{val}})$$
  - Candidates failing valid-time alignment, temporal containment ($I_{\text{frame}} \subseteq I_{\text{covered}}$), signature verification, DAG acyclicity, predicate equivalence ($R \implies R_Q$), or contract constraints are rejected here.
  - Accepted candidates are transformed into typed $\mathcal{E}v$ events with payload $d_{\text{ev}} \in \text{EvPayload}$; rejected candidates produce validation audit records $\Delta \mathcal{A}ud_{\text{val}}$ and operational diagnostics $\Delta_{\text{val}}$.
  - Neither $\chi$ nor $\nu$ possesses independent truth authority. $\text{Validate}$ processes strictly $\mathcal{C}_{\text{cand}}$ and **does not fabricate acquisition diagnostics** it did not receive.

### 6.3 Diagnostic-to-Audit Bridge ($\text{Auditize}$)
Operational diagnostics generated during acquisition ($\Delta_{\text{acq}}$) are converted into typed audit entries via a deterministic mapping:
$$\text{Auditize}: \mathcal{D}^* \times \mathbb{T} \to \mathcal{A}ud^*$$
$$\Delta \mathcal{A}ud_{\text{acq}} = \text{Auditize}(\Delta_{\text{acq}}, t_{\text{rec}})$$

### 6.4 Deterministic Canonical Contract Synthesis ($\text{Contract}_\eta$)
For a fixed claim $q = (P, \eta, \phi)$ and derived epistemic obligations $\Omega \subseteq \mathcal{O}$, contract synthesis is a deterministic, canonical function:
$$\kappa = \text{Contract}_\eta(q, \Omega, \phi) \in \mathcal{K}$$
where $\kappa = (\mathcal{S}_{\text{allowed}}, \mathcal{M}_{\text{allowed}}, k_{\text{wit}}, B_{\text{res}})$.

**Conservative Acquisition Policy**:
- $\text{Contract}_\eta$ applies a deterministic, conservative acquisition policy (specifying canonical witness sources, closed registry query methods, and observational parameters for all active obligations in $\Omega$), without claiming globally optimal or minimal acquisition.
- $\text{Contract}_\eta$ has **zero independent truth or policy authority**. It is a strictly deterministic projection of evaluator policy $\eta$, claim $q$, frame $\phi$, and obligations $\Omega$.

### 6.5 Claim-Relevant Non-Interference & Runtime Mutation Recovery
Acquisition may cause incidental physical or computational effects, but must preserve state non-interference on the world projection relevant to proposition $P$:
$$\text{Proj}_P(\sigma(\text{world}_{\text{post\_acquire}})) = \text{Proj}_P(\sigma(\text{world}_{\text{pre\_acquire}}))$$

1. **Pre-Execution Fail-Closed Rule**: If the relevant projection $\text{Proj}_P$ is underspecified, or if non-interference cannot be formally or operationally proven prior to execution:
   $$\text{ProvableNonInterference}(\text{method}, P, \phi) = \text{Bool.False} \implies \text{method is forbidden; resolution fails closed to Unknown.}$$
2. **Canonical Semantics for Unexpected Post-Execution World Mutation**:
   If an acquisition probe executes and mutates proposition-relevant world state despite pre-execution approval:
   - **No Rollback Assumption**: The model does not assume or require external physical/system rollback.
   - **No Re-Evaluation of Original Claim**: The original claim $q$ is **not re-evaluated**, because its observation frame $\phi$ has been compromised and invalidated by the acquisition.
   - **Evidence Invalidation**: All candidate evidence produced by the interfering acquisition is unconditionally discarded ($\Delta \mathcal{E}v_{\text{acc}} = \emptyset$).
   - **Truth State Preservation**: The system preserves the last truth result previously produced by $\text{Eval}$ for original claim $q$ (which, for an active resolution, is $v_0 = \text{Unknown}, \pi_0, \Omega_0$).
   - **Audit Recording**: An operational diagnostic $\text{FrameInvalidatedDiag}$ is recorded in $\Delta$ and appended as $\text{AuditEntry}(\text{FrameInvalidatedAudit})$ to $\mathcal{L}'$ via $\text{Auditize}$.
   - **Continuation via New Claim**: Any further reasoning about the post-mutation world state strictly requires the caller to construct a new claim $q' = (P, \eta, \phi_{\text{new}})$ with a newly anchored observation frame $\phi_{\text{new}}$.

---

## 7. Resolution Pipeline & Operational Phase Model

### 7.1 Operational Phases & Resolution Result Typing
To guarantee that operational diagnostics never introduce a fourth logical state, the resolution state is formalized as:
$$S = \langle q, \mathcal{L}, \text{phase} \rangle$$
where $\text{phase} \in \{\text{Start}, \text{SynthesizingContract}, \text{Acquiring}, \text{Validating}, \text{ReEvaluating}, \text{Completed}\}$.

**Formal Resolution Result**: The resolution output is cleanly typed as a pair $(\mathcal{L}', r)$ where $\mathcal{L}' \in \mathcal{J}^*$ is the updated journal and $r \in \mathcal{R}es$ is the resolution result quadruple:
$$r = (v, \pi, \Omega, \Delta) \in \mathbb{X} \times \Pi \times \mathcal{P}(\mathcal{O}) \times \mathcal{D}^*$$
where $v \in \{\text{True}, \text{False}, \text{Unknown}\}$.

### 7.2 The Formal 8-Step Resolution Pipeline
Given initial claim $q = (P, \eta, \phi)$ and initial journal $\mathcal{L}$:

1. **Initial Evaluation**:
   $$(v_0, \pi_0, \Omega_0) = \text{Eval}(q, \text{Adm}(\mathcal{L}, \eta, \phi))$$
2. **Total Determinate Short-Circuit ($\text{True}$ / $\text{False}$)**:
   If $v_0 \in \{\text{True}, \text{False}\}$, resolution completes immediately as a total well-defined operation without acquisition:
   $$r_0 = (v_0, \pi_0, \emptyset, \emptyset) \in \mathcal{R}es,\quad \text{resolve}(q, \mathcal{L}) \to (\mathcal{L}, r_0)$$
3. **Obligation Derivation**:
   If $v_0 = \text{Unknown}$, extract decision-relevant obligations $\Omega_0 = \text{Obl}(q, \text{Adm}(\mathcal{L}, \eta, \phi))$ (e.g. missing positive witness, unproven universe closure, or temporal coverage gaps).
4. **Contract Synthesis**:
   $$\kappa = \text{Contract}_\eta(q, \Omega_0, \phi)$$
5. **Contract-Constrained Acquisition**:
   $$(\mathcal{C}_{\text{cand}}, \Delta_{\text{acq}}) \sim \text{Acquire}(\kappa)$$
   *(Produces candidate evidence in $\mathcal{C}$—including candidate $\nu$ certificates—and diagnostics $\Delta_{\text{acq}}$; never a truth value.)*
6. **Validation & Diagnostic Transformation**:
   $$(\Delta \mathcal{E}v_{\text{acc}}, \Delta \mathcal{A}ud_{\text{val}}, \Delta_{\text{val}}) = \text{Validate}(\mathcal{C}_{\text{cand}}, \mathcal{L}, \eta, \phi, \kappa)$$
   $$\Delta \mathcal{A}ud_{\text{acq}} = \text{Auditize}(\Delta_{\text{acq}}, t_{\text{rec}})$$
7. **Journal Ingestion & Admissibility Recomputation**:
   $$\mathcal{L}' = \mathcal{L} \mathbin{+\!\!+} [\text{EvEntry}(e) \mid e \in \Delta \mathcal{E}v_{\text{acc}}] \mathbin{+\!\!+} [\text{AuditEntry}(a) \mid a \in \Delta \mathcal{A}ud_{\text{acq}} \mathbin{+\!\!+} \Delta \mathcal{A}ud_{\text{val}}]$$
   $$E' = \text{Adm}(\mathcal{L}', \eta, \phi)$$
8. **Snapshot-Bound Re-Evaluation (Same $q$, Same $\eta$, Same $\phi$)**:
   - **Evaluator Drift Branch**: If evaluation is attempted under $\eta_2 \neq \eta_1$:
     $$\Delta_{\text{drift}} = [\text{EvaluatorDriftDiag}]$$
     $$\Delta \mathcal{A}ud_{\text{drift}} = \text{Auditize}(\Delta_{\text{drift}}, t_{\text{rec}})$$
     $$\mathcal{L}_{\text{final}} = \mathcal{L}' \mathbin{+\!\!+} [\text{AuditEntry}(a) \mid a \in \Delta \mathcal{A}ud_{\text{drift}}]$$
     $$\Delta_{\text{total}} = \Delta_{\text{acq}} \mathbin{+\!\!+} \Delta_{\text{val}} \mathbin{+\!\!+} \Delta_{\text{drift}}$$
     $$r_{\text{abort}} = (v_0, \pi_0, \Omega_0, \Delta_{\text{total}}) \in \mathcal{R}es,\quad \text{resolve}(q, \mathcal{L}) \to (\mathcal{L}_{\text{final}}, r_{\text{abort}})$$
     *(Evaluation terminates fail-closed immediately; no Eval occurs under $\eta_2$ or after drift detection).*
   - **Frame Invalidation Branch**: If frame $\phi$ was invalidated by unexpected mutation (§6.5):
     $$\Delta_{\text{mut}} = [\text{FrameInvalidatedDiag}]$$
     $$\Delta \mathcal{A}ud_{\text{mut}} = \text{Auditize}(\Delta_{\text{mut}}, t_{\text{rec}})$$
     $$\mathcal{L}_{\text{final}} = \mathcal{L}' \mathbin{+\!\!+} [\text{AuditEntry}(a) \mid a \in \Delta \mathcal{A}ud_{\text{mut}}]$$
     $$\Delta_{\text{total}} = \Delta_{\text{acq}} \mathbin{+\!\!+} \Delta_{\text{val}} \mathbin{+\!\!+} \Delta_{\text{mut}}$$
     $$r_{\text{inval}} = (v_0, \pi_0, \Omega_0, \Delta_{\text{total}}) \in \mathcal{R}es,\quad \text{resolve}(q, \mathcal{L}) \to (\mathcal{L}_{\text{final}}, r_{\text{inval}})$$
     *(No re-evaluation of $q$ occurs after frame invalidation; prior $v_0$ is preserved).*
   - **Standard Re-Evaluation Branch**: Otherwise, re-evaluate against updated admissible view $E'$:
     $$(v_1, \pi_1, \Omega_1) = \text{Eval}(q, E')$$
     $$\Delta_{\text{total}} = \Delta_{\text{acq}} \mathbin{+\!\!+} \Delta_{\text{val}}$$
     $$r_1 = (v_1, \pi_1, \Omega_1, \Delta_{\text{total}}) \in \mathcal{R}es,\quad \text{resolve}(q, \mathcal{L}) \to (\mathcal{L}', r_1)$$

### 7.3 Transition Relation ($\xrightarrow{\text{resolve}}$)
$$(q, \mathcal{L}) \xrightarrow{\text{resolve}} (\mathcal{L}', r)$$
where $\mathcal{L}' \in \mathcal{J}^*$ and $r = (v, \pi, \Omega, \Delta) \in \mathcal{R}es$.

### 7.4 Single-Attempt Invariant
A single `resolve` invocation performs **at most one** acquisition attempt. There is **no implicit retry loop**. If re-evaluation yields $v_1 = \text{Unknown}$, `resolve` completes with $(\mathcal{L}', (\text{Unknown}, \pi_1, \Omega_1, \Delta_{\text{total}}))$.

---

## 8. Concurrent Ingestion vs Snapshot-Bound Decision Publication

1. **Concurrent Evidence Ingestion**: Verified evidence and audit entries may be concurrently appended to journal $\mathcal{L}$ via atomic/CRDT append operations ($\mathcal{L}' = \mathcal{L} \mathbin{+\!\!+} \Delta$).
2. **Snapshot-Bound Decision Publication**: An evaluated resolution decision $r = (v, \pi, \Omega, \Delta)$ is bound strictly to the admissible snapshot $E = \text{Adm}(\mathcal{L}_{\text{snap}}, \eta, \phi)$.
3. **Anti-Staleness Publication Rule**: If concurrent appends modify the admissible view $E$ for claim $(q, \phi)$ (including updates to search universe snapshots $\Sigma_{\text{snap}}$) before publication is committed, the decision **must not be published from the stale snapshot**. The system must re-evaluate against $E_{\text{fresh}}$ before committing the result.

---

## 9. Mandatory Semantic Invariants

1. **Closed Three-Valued Domain**: $\mathbb{X} = \{\text{True}, \text{False}, \text{Unknown}\}$. No operational failure, contradiction, closed-world assumption, or negative certificate creates a fourth logical state.
2. **Sole Evaluation Authority**: Only $\text{Eval}$ can compute a truth value for claim $q$. Acquirers, validators, and contract synthesizers possess zero truth-assignment authority.
3. **No Direct Truth Coercion**: A resolver cannot inject, coerce, or alter truth values.
4. **Target Specificity**: `resolve` applies exclusively to resolvable claims $q = (P, \eta, \phi)$, never to naked `XoX` scalar values lacking evaluator and frame anchors.
5. **Atomic Single Attempt**: One `resolve` step executes at most one acquisition/validation cycle.
6. **Total Claim Domain**: `resolve` is total over all resolvable claims $q \in \mathcal{Q}$; determinate claims ($\text{True}$/$\text{False}$) short-circuit cleanly with zero acquisition.
7. **Unknown-to-Unknown Validity**: $\text{Unknown} \to \text{Unknown}$ is a successful, valid semantic completion.
8. **Separation of Obligations & Diagnostics**: $\Omega$ contains domain epistemic obligations derived by $\text{Eval}$; $\Delta$ contains operational execution diagnostics.
9. **Candidate Domain Barrier**: Unvalidated candidate evidence in $\mathcal{C}$ (including candidate $\chi$ and $\nu$ certificates) cannot inhabit $\mathcal{E}v$ without passing $\text{Validate}$.
10. **Claim Invariance & Evaluator Drift Abort**: Resolution strictly preserves proposition $P$, evaluator/version $\eta$, and observation frame $\phi$. Attempted evaluator drift aborts fail-closed.
11. **Claim-Relevant Non-Interference**: Acquisition must preserve provable non-interference on $\text{Proj}_P$. Unexpected mutations invalidate the frame and preserve prior `Unknown` without rollback.
12. **Local Evidential Conflict vs Ontological Contradiction**: Competing observational evidence sets subclaim truth to `Unknown` modularly when admissible alternatives remain ($|W_{\text{factive}}| \ge 2$), and decision-relevance under $K_3$ governs root truth propagation; in contrast, an evaluated Ontological Contradiction ($W_{\text{factive}} = \emptyset$) aborts fail-closed immediately and cannot be mapped to `Unknown`.
13. **Snapshot Isolation**: No decision may be committed from a stale admissible evidence snapshot.
14. **Evidence of Absence Requirement**: Proving `False` for an existential proposition requires validated full temporal coverage $\chi$ ($I_{\text{frame}} \subseteq I_{\text{covered}}$), query predicate equivalence/subsumption ($R \implies R_Q$), and exhaustive search certificate $\nu$; empty search alone never produces `False`.

---

## 10. Transition Examples: Legal vs Illegal

### 10.1 Legal Transitions

#### Example L1: Determinate Short-Circuit ($\text{True} \to \text{True}$)
- **Claim**: $q = (P, \eta, \phi)$, initial evaluation $\text{Eval}(q, \text{Adm}(\mathcal{L}, \eta, \phi)) = (\text{True}, \pi_0, \emptyset)$.
- **Action**: $\text{resolve}(q, \mathcal{L})$.
- **Outcome**: Returns $(\mathcal{L}, r_0)$ where $r_0 = (\text{True}, \pi_0, \emptyset, \emptyset) \in \mathcal{R}es$. No acquisition attempted; $\mathcal{L}$ unchanged.

#### Example L2: Strong Kleene Dominance ($A \land B$ with $B = \text{False}$)
- **Claim**: $q = (A \land B, \eta, \phi)$ where subclaim $A$ is unresolved ($\text{Val}(A) = \text{Unknown}$) and $B$ evaluates to $\text{False}$ ($\text{Val}(B) = \text{False}$).
- **Evaluation**: $\text{Val}(q, E) = \text{Val}(A) \land_{K_3} \text{Val}(B) = \text{Unknown} \land \text{False} = \text{False}$.
- **Obligations**: $\text{Obl}(q, E) = \emptyset$. Unresolved obligations of $A$ are decision-irrelevant and pruned from the root result.
- **Operational Note**: In concrete XoXLang runtime lowering (XOX_SPEC §7, §7.1), the expression `A AND B` evaluates $A$ first; declarative obligation pruning in this epistemic model does not alter the language's left-to-right evaluation trace.

#### Example L3: Strong Kleene Disjunctive Resolution ($A \lor B$)
- **Claim**: $q = (A \lor B, \eta, \phi)$, initially $\text{Val}(A) = \text{Unknown}$ and $\text{Val}(B) = \text{False}$, so $\text{Val}(q) = \text{Unknown}$ with $\text{Obl}(q) = \text{Obl}(A) = \{\omega_A\}$.
- **Contract & Acquire**: $\kappa = \text{Contract}_\eta(q, \{\omega_A\}, \phi)$; acquires valid candidate $c_A \in \mathcal{C}$, validated to $e_A \in \mathcal{E}v$.
- **Re-Evaluation**: $\text{Val}(A, E') = \text{True} \implies \text{Val}(q, E') = \text{True} \lor_{K_3} \text{False} = \text{True}$ with $r_1 = (\text{True}, \pi_1, \emptyset, \emptyset) \in \mathcal{R}es$.

#### Example L4: Acquisition Failure (Fail-Closed to Unknown via Auditize)
- **Claim**: $q = (P, \eta, \phi)$, initially $\text{Val}(q) = \text{Unknown}$ with $\Omega = \{\omega_1\}$.
- **Acquire**: Network timeout occurs; $\mathcal{C}_{\text{cand}} = \emptyset$, $\Delta_{\text{acq}} = [\text{TimeoutDiag}]$.
- **Auditize & Validate**: $\Delta \mathcal{A}ud_{\text{acq}} = \text{Auditize}([\text{TimeoutDiag}], t_{\text{rec}}) = [\text{TimeoutAudit}]$; $\Delta \mathcal{E}v_{\text{acc}} = \emptyset$.
- **Journal Appending**: $\mathcal{L}' = \mathcal{L} \mathbin{+\!\!+} [\text{AuditEntry}(\text{TimeoutAudit})]$.
- **Re-Evaluation**: $\text{Adm}(\mathcal{L}', \eta, \phi) = E_0$; $\text{Eval}(q, E_0) = (\text{Unknown}, \pi_0, \{\omega_1\})$.
- **Outcome**: Returns $(\mathcal{L}', r_1)$ where $r_1 = (\text{Unknown}, \pi_0, \{\omega_1\}, [\text{TimeoutDiag}]) \in \mathcal{R}es$.

#### Example L5: Falsification of Existential Claim via Validated Closed Universe ($\text{Unknown} \to \text{False}$)
- **Claim**: $q = (\exists x \in \mathcal{U}.\; \text{RevokedCert}(x), \eta, \phi)$, initially $\text{Eval}(q, E_0) = (\text{Unknown}, \pi_0, \{\omega_{\text{closure}}(\mathcal{U})\})$.
- **Contract & Acquire**: $\kappa = \text{Contract}_\eta(q, \Omega_0, \phi)$ queries authorized registry authority; acquires coverage certificate $\chi$ with $I_{\text{frame}}(\phi) \subseteq I_{\text{covered}}(\chi)$ and exhaustive search certificate $\nu$ proving $\mathcal{Q}_e(\Sigma_{\text{snap}}, \text{RevokedCert}) = \emptyset$.
- **Validate**: $\text{Validate}$ verifies authority signature, full temporal coverage, query equivalence, and snapshot identity $\Sigma_{\text{snap}}$; admits $\Delta \mathcal{E}v_{\text{acc}} = \{e_\chi, e_\nu\}$.
- **Re-Evaluation**: $\text{Eval}(q, \text{Adm}(\mathcal{L}', \eta, \phi)) = (\text{False}, \pi_{\text{absence}}, \emptyset)$.
- **Outcome**: Returns $(\mathcal{L}', r_1)$ where $r_1 = (\text{False}, \pi_{\text{absence}}, \emptyset, \emptyset) \in \mathcal{R}es$.

#### Example L6: Open-World Empty Search Preserving Unknown ($\text{Unknown} \to \text{Unknown}$)
- **Claim**: $q = (\exists x \in \text{ExternalLog}.\; \text{IntrusionEvent}(x), \eta, \phi)$, initially $\text{Eval}(q, E_0) = (\text{Unknown}, \pi_0, \{\omega_{\text{witness}}\})$.
- **Acquire**: Query executes over log stream, returns empty result set, but log source provides **no coverage certificate $\chi$** (unverified logging completeness).
- **Validate**: Rejects completeness claim; admits no negative evidence certificate.
- **Re-Evaluation**: $\text{Eval}(q, E') = (\text{Unknown}, \pi_1, \{\omega_{\text{unproven\_closure}}(\text{ExternalLog})\})$.
- **Outcome**: Empty search alone preserves `Unknown`. Absence of evidence is not evidence of absence.

#### Example L7: Universal Negative Proposition via Strong Kleene Negation ($\neg P_{\text{exist}} = \text{True}$)
- **Claim**: $q_{\text{univ}} = (\neg (\exists x \in \mathcal{U}.\; \text{RevokedCert}(x)), \eta, \phi)$.
- **Subclaim Evaluation**: $P_{\text{exist}}$ evaluates to $\text{False}$ under Example L5 ($\text{Val}(P_{\text{exist}}, E') = \text{False}$).
- **Root Evaluation**: $\text{Val}(q_{\text{univ}}, E') = \neg_{K_3} \text{Val}(P_{\text{exist}}, E') = \neg_{K_3} \text{False} = \text{True}$.
- **Outcome**: Universal proposition evaluates determinately to $\text{True}$ through standard $K_3$ logical negation with $r = (\text{True}, \pi_{\neg}, \emptyset, \emptyset) \in \mathcal{R}es$.

---

### 10.2 Illegal Transitions (Anti-Patterns)

#### Example X1: Direct Resolver Truth Injection (FORBIDDEN)
```
[Illegal Resolver] ---> returns (True) directly without calling Eval(q, E)
```
*Violation*: Violates Invariants 2 and 3.

#### Example X2: Resolution on a Naked Scalar Value (FORBIDDEN)
```
x: XoX = Unknown
resolve(x)  // ILLEGAL: x lacks proposition P, evaluator eta, and frame phi
```
*Violation*: Violates Invariant 4.

#### Example X3: Attempted Evaluator Version Drift (FORBIDDEN)
```
resolve( (P, eta_v1, phi) ) attempts re-evaluation under eta_v2
```
*Violation*: Violates Invariant 10 and Section 2.2. The invocation aborts fail-closed, preserving prior $\text{Eval}$ results under $\eta_{\text{v1}}$.

#### Example X4: Unproven Non-Interference Probe (FORBIDDEN)
```
Acquisition executes probe where ProvableNonInterference(probe, P, phi) = False
```
*Violation*: Violates Invariant 11 and Section 6.5 (Pre-Execution Fail-Closed Rule).

#### Example X5: Commit From Stale Snapshot (FORBIDDEN)
```
Concurrent task appends evidence modifying Adm(L, eta, phi); stale decision committed
```
*Violation*: Violates Invariant 13 (Snapshot Isolation).

#### Example X6: Falsification via Unbounded Empty Search (FORBIDDEN)
```
Acquire queries open network, receives 0 rows, asserts (False)
```
*Violation*: Violates Invariant 14 and Section 5.1 (Open-World Principle).

#### Example X7: Partial Temporal Coverage Proving False (FORBIDDEN)
```
chi covers [t0, t5]; claim frame is [t0, t10]; Eval asserts (False)
```
*Violation*: Violates Invariant 14 and Section 5.3 (Full Temporal Coverage Direction).

---

## 11. Safety Properties & Fail-Closed Specifications

### 11.1 Mathematical Safety Properties

1. **Truth Projection Uniqueness**:
   $$\forall q \in \mathcal{Q},\; \forall E \subseteq \mathcal{E}v.\quad \exists! v \in \mathbb{X}.\; v = \text{Val}(q, E)$$
2. **Journal Monotonicity**:
   $$\mathcal{L} \sqsubseteq \mathcal{L}' \iff \exists \Delta_{\text{entries}} \in \mathcal{J}^*.\; \mathcal{L}' = \mathcal{L} \mathbin{+\!\!+} \Delta_{\text{entries}}$$
3. **Soundness of Proof Certificates**:
   $$\forall q, E.\quad \text{VerifyCertificate}(q, E, \text{Eval}(q, E)) = \text{Bool.True}$$
4. **Strong Kleene Truth Consistency**:
   $$\forall P_1, P_2, \eta, \phi, E.\quad \text{Val}((P_1 \land P_2, \eta, \phi), E) = \text{Val}((P_1, \eta, \phi), E) \land_{K_3} \text{Val}((P_2, \eta, \phi), E)$$
5. **Soundness of Falsification**:
   $$\forall P_{\text{exist}}, E.\quad \text{Val}((P_{\text{exist}}, \eta, \phi), E) = \text{False} \implies \exists e_\nu \in E.\; \text{IsValidNegativeCertificate}(e_\nu, (P_{\text{exist}}, \eta, \phi), \eta, \phi, E) = \text{Bool.True}$$

### 11.2 Fail-Closed Specifications

| Failure Mode | Primary Detection Point | System Response | Resulting State $r \in \mathcal{R}es$ |
|---|---|---|---|
| **Contract Breach** | $\text{Validate}$ | Discard candidate; append `AuditEntry` | $(\text{Unknown}, \pi_0, \Omega_{\text{eval}}, [\text{ContractBreachDiag}])$ |
| **Unproven Non-Interference** | $\text{Contract}_\eta$ / $\text{Validate}$ | Reject probe; append `AuditEntry` | $(\text{Unknown}, \pi_0, \Omega_{\text{eval}}, [\text{InterferenceDiag}])$ |
| **Unexpected World Mutation** | Runtime Monitor / Acquire | Invalidate frame $\phi$; discard evidence; append `AuditEntry` via $\text{Auditize}$; preserve prior `Eval` | $(\text{Unknown}, \pi_0, \Omega_{\text{eval}}, [\text{FrameInvalidatedDiag}])$ |
| **Attempted Evaluator Drift** | Runtime Step 8 Gate | Abort invocation fail-closed; append `AuditEntry` via $\text{Auditize}$; preserve prior `Eval` | $(\text{Unknown}, \pi_0, \Omega_{\text{eval}}, [\text{EvaluatorDriftDiag}])$ |
| **Unproven Universe Coverage** | $\text{Validate}$ / $\text{Eval}$ | Reject closure claim; retain open-world semantics | $(\text{Unknown}, \pi_0, \Omega_{\text{unproven\_closure}}, \emptyset)$ |
| **Partial Scope Coverage** | $\text{Validate}$ / $\text{Eval}$ | Reject whole-claim closure; retain `Unknown` for scope gap | $(\text{Unknown}, \pi_0, \Omega_{\text{scope\_gap}}, \emptyset)$ |
| **Partial Temporal Coverage** | $\text{Validate}$ / $\text{Eval}$ | Reject whole-claim closure; retain `Unknown` for gap | $(\text{Unknown}, \pi_0, \Omega_{\text{temporal\_gap}}, \emptyset)$ |
| **Narrow Query Predicate** | $\text{Validate}$ | Reject certificate ($R_Q \subset R$); discard candidate | $(\text{Unknown}, \pi_0, \Omega_{\text{unproven\_closure}}, [\text{InvalidQueryPredicateDiag}])$ |
| **Snapshot Drift / Mismatch** | $\text{Adm}$ / $\text{Eval}$ | Exclude mismatched $\nu$ certificate from $E$; force re-evaluation | $(\text{Unknown}, \pi_0, \Omega_{\text{snapshot\_mismatch}}, \emptyset)$ |
| **Invalid Signature / Tampering** | $\text{Validate}$ | Discard candidate; append `AuditEntry` | $(\text{Unknown}, \pi_0, \Omega_{\text{eval}}, [\text{UntrustedSourceDiag}])$ |
| **Provenance Cycle** | $\text{Validate}$ | Discard candidate; append `AuditEntry` | $(\text{Unknown}, \pi_0, \Omega_{\text{eval}}, [\text{CyclicProvenanceDiag}])$ |
| **Valid-Time Out of Bounds** | $\text{Validate}$ | Discard candidate; append `AuditEntry` | $(\text{Unknown}, \pi_0, \Omega_{\text{eval}}, [\text{OutOfFrameDiag}])$ |
| **Transport Timeout** | $\text{Acquire}$ | Ingest diagnostic via $\text{Auditize}$; append `AuditEntry` | $(\text{Unknown}, \pi_0, \Omega_{\text{eval}}, [\text{TimeoutDiag}])$ |

*Note: In all failure modes, epistemic obligations $\Omega_{\text{eval}} = \text{Obl}(q, E)$ are preserved from prior $\text{Eval}$, while execution failure causes are recorded in $\Delta$ and $\mathcal{A}ud$.*

---

## 12. Distinction: `resolve` vs Future Revalidation

| Dimension | `resolve` (Epistemic Resolution) | `revalidate` (Temporal / Policy Revalidation) |
|---|---|---|
| **Claim Applicability** | **Total**: Defined over all $q \in \mathcal{Q}$. Determinate claims ($\text{True}$/$\text{False}$) short-circuit with zero acquisition; $\text{Unknown}$ claims activate acquisition. | Applies to claims previously evaluated to $\text{True}$ or $\text{False}$ to check freshness across contexts. |
| **Observation Frame $\phi$** | **Strictly Fixed**: Refines knowledge strictly within existing frame $I_{\text{frame}}$. | **Advanced / New**: Evaluates truth in a fresh temporal frame $I_{\text{frame}}'$. |
| **Evaluator Identity $\eta$** | **Strictly Invariant**: Evaluates strictly under exact original $\eta$. Drift attempts abort fail-closed. | May evaluate under upgraded policy $\eta'$. |
| **Trigger** | Explicit resolution step to discharge epistemic obligations $\Omega \subseteq \mathcal{O}$. | Temporal expiration, TTL, or environmental invalidation. |
| **Journal Operation** | Appends missing observational evidence events for frame $\phi$. | Appends new current observation events for $t_{\text{now}}$. |

---

## 13. Non-Goals & Scope Boundaries

1. **No Surface Syntax Selection**: This specification intentionally leaves concrete language syntax for `resolve` open.
2. **No Paradigm Novelty Claims**: This formalization synthesizes Strong Kleene 3-valued logic, bitemporal intervals, epistemic obligations, search universe closures, and provenance graphs without claiming a new paradigm.
3. **Immutable Baseline Records**: Historical artifacts (`docs/historical/trool-v1/`) and `XOX_V2_BASELINE.json` remain untouched.
4. **No Implementation in Core**: This model is strictly non-normative research and is not implemented in the active V2 compiler or runtime.

---

## 14. Open Research Questions

1. **Obligation Composition Algebra**: Defining formal algebraic lattices and hypergraphs over $\mathcal{P}(\mathcal{O})$ for optimal disjunctive/conjunctive acquisition strategies.
2. **Static Contract Synthesis**: Type-directed compilation of optimal acquisition contracts $\kappa$ from static source annotations.
3. **Asynchronous Execution Semantics**: Lowering `resolve` to cooperative async/await runtimes versus algebraic effect handlers.
4. **Distributed Journal Reconciliation**: CRDT and consensus protocols for multi-region journal replication with monotonic record timestamps.
5. **Automated Universe Coverage Proofs**: Machine-checkable formal proofs for continuous sensor perimeters and cryptographic Merkle tree non-inclusion proofs.
