# XoXLang Core Semantics: Finite-World Classifier

This document specifies the minimal validated semantic core implemented in `xoxlang/core_semantics.py`.

---

## 1. Problem this slice solves

When reasoning about software execution under uncertainty, an expression may be evaluated across a set of admissible execution realities ($W_{\text{factive}}$). 

This slice provides the canonical classifier that answers:
- Is the knowledge space contradictory (empty, $W_{\text{factive}} = \emptyset$)?
- Does the expression resolve to a single concrete, invariant behavior across all realities (**Known**)?
- Does the expression produce multiple distinguishable behaviors across realities (**Unknown** / Local Evidential Conflict)?
- Is the expression semantically undefined on any admissible reality (Precondition Failure)?

---

## 2. Classification contract

The classifier is exposed via `classify_factive_behaviors`:

```python
def classify_factive_behaviors(
    behaviors: Sequence[SemanticOutcome[T]],
    equivalence_fn: Optional[Callable[[T, T], bool]] = None,
) -> SemanticClassification:
    ...
```

### Inputs
1. `behaviors`: A finite sequence of `SemanticOutcome` items, each representing the evaluated behavior of the expression on an admissible execution history in $W_{\text{factive}}$.
2. `equivalence_fn` *(optional)*: A binary predicate `(a, b) -> bool` defining whether two defined outcomes are observationally equivalent. When omitted, defaults to `a == b`.

### Outputs & Control Flow
- Returns `SemanticClassification.INCONSISTENT` (Ontological Contradiction)
- Returns `SemanticClassification.KNOWN`
- Returns `SemanticClassification.UNKNOWN` (Local Evidential Conflict / Uncertainty)
- Raises `DefinednessPreconditionError` (refuses classification)

---

## 3. Difference between INCONSISTENT, KNOWN, UNKNOWN, and classification refusal

| State / Result | Condition in $W_{\text{factive}}$ | Meaning |
| :--- | :--- | :--- |
| **`INCONSISTENT` (Contradiction)** | $\text{len}(behaviors) == 0$ | The factive world space is empty ($W_{\text{factive}} = \emptyset$), indicating contradictory/unsatisfiable hard constraints. Vacuous truth over an empty world space has zero epistemic authority and can never produce `KNOWN`. Contradiction is not a fourth $K_3$ truth value; an evaluated Contradiction propagates immediately fail-closed. |
| **`KNOWN`** | $\text{len}(behaviors) \ge 1$, all defined, all equivalent | Every admissible reality produces an outcome considered equivalent under the supplied `equivalence_fn`. Requires a non-empty satisfiable context. |
| **`UNKNOWN` (Local Evidential Conflict)** | $\text{len}(behaviors) \ge 2$, all defined, $\ge 2$ distinguishable | Multiple admissible realities produce distinguishable outcomes under `equivalence_fn`. Local evidential disagreement or variance with non-empty alternatives is strictly `UNKNOWN`, never Contradiction. *(Note: UNKNOWN indicates genuine behavioral variance, never solver timeout or prover failure).* |
| **Refusal (`DefinednessPreconditionError`)** | $\ge 1$ trajectory has `is_defined == False` | The expression lacks defined semantics on at least one admissible trajectory. Classification is strictly refused. This is a precondition failure, not a fourth semantic state. |

---

## 4. Definedness priority, Provenance & Authority Capabilities

The classifier enforces **absolute definedness priority**:
- Every trajectory in $W_{\text{factive}}$ is verified for definedness before any equivalence comparison occurs.
- If any trajectory has undefined semantics, `DefinednessPreconditionError` is raised immediately.
- Undefined behavior prevents classification even if distinguishable defined outcomes were already observed on other trajectories.
- **DefinednessWitness**: Evaluator-issued non-forgeable capability certifying definedness only, binding exactly `(RootID, SemanticPath, WorldStateID)`. It holds zero authority to restrict $W_{\text{factive}}$ and is invalidated fail-closed upon relevant `WorldStateID` mutation.
- **Unknown Provenance ($\Pi$)**: Every `UNKNOWN` outcome carries an immutable, non-empty set of unresolved fact identities $\Pi$. Provenance propagates across $K_3$ logical operators, combines on unresolved branches via exact set union ($\Pi_1 \cup \Pi_2$), and disappears without tokens only when proven semantic independence renders the truth value determinate (`True` or `False`).
- **Resolution Authority**: Resolving or collapsing `UNKNOWN[\Pi]` via `unwrap_or` or `xen: ignore` requires a valid `ResolutionToken` issued by `WorldStateAuthority`, binding the exact 4-tuple `(ProvenanceSet, OperationType, WorldStateID, FallbackPolicyIdentity)`. Partial coverage, subset reuse, superset reuse, and caller-side composition are strictly prohibited.


---

## 5. Observational equivalence

In the broader XoXLang semantic model, observational equivalence determines whether two execution outcomes produce indistinguishable behavior under valid continuations or external interactions.

In this minimal classifier slice:
- **Equivalence is supplied, not computed**: This slice does not analyze program continuations or external environments directly. The equivalence relation is supplied explicitly via the `equivalence_fn` argument.
- **Evaluation rule**: Two outcomes `a` and `b` are treated as observationally equivalent if and only if `equivalence_fn(a, b)` returns `True`.
- **Default `a == b` is an implementation fallback**: When `equivalence_fn` is omitted, standard Python equality `a == b` is used as a default convenience. This fallback is an implementation detail and must not be confused with the universal definition of XoXLang observational equivalence (for example, when identity comparison or type-strict discrimination is semantically required, an appropriate `equivalence_fn` must be supplied).
- **No universal structural equivalence claim**: Two objects are not universally equivalent merely because their data fields match; equivalence depends strictly on the observational predicate provided.

---

## 6. Examples using explicit finite behavior sets

```python
from xoxlang.core_semantics import (
    SemanticClassification,
    SemanticOutcome,
    classify_factive_behaviors,
)

# 1. Inconsistent (Empty world space)
classify_factive_behaviors([])
# -> SemanticClassification.INCONSISTENT

# 2. Known (Single world or multiple equivalent outcomes)
classify_factive_behaviors([
    SemanticOutcome.defined(42),
    SemanticOutcome.defined(42),
])
# -> SemanticClassification.KNOWN

# 3. Unknown (Distinguishable outcomes across worlds)
classify_factive_behaviors([
    SemanticOutcome.defined(True),
    SemanticOutcome.defined(False),
])
# -> SemanticClassification.UNKNOWN

# 4. Custom Equivalence (e.g. strict type + value check)
strict_eq = lambda a, b: type(a) is type(b) and a == b
classify_factive_behaviors(
    [SemanticOutcome.defined(1), SemanticOutcome.defined(True)],
    equivalence_fn=strict_eq,
)
# -> SemanticClassification.UNKNOWN (prevents accidental Python 1 == True equivalence)

# 5. Classification Refusal (Undefined behavior present)
classify_factive_behaviors([
    SemanticOutcome.defined(42),
    SemanticOutcome.undefined(),
])
# -> Raises DefinednessPreconditionError
```

---

## 7. What is intentionally not implemented

To maintain mathematical minimalism and avoid premature complexity, the following areas are strictly out of scope for this slice:
- **No Contextual Equivalence Synthesis**: Does not analyze future continuations or observer capabilities; relies on supplied `equivalence_fn`.
- **No World Generation / Constraint Solvers**: Accepts explicit, already-evaluated behavior collections.
- **No Parser / AST Lowering**: Operates purely on semantic outcome representations.
- **No Dynamic History Generation**: Does not generate runtime RNG draws, network I/O, or thread schedules.
- **No Premise Authority Inference**: Does not parse user assumptions or verify factive status.
- **No Proof Certification**: Solver timeouts and static analysis heuristics are separated from the semantic model.

---

## 8. Semantic Authority & Truth Boundaries

This section specifies the canonical Tier 1 (S1) semantic boundaries governing value evaluation, truth projection, and operational authority limits in XoXLang.

### 8.1 Canonical S1 Semantic Invariants
- **`INV_SEMANTIC_AUTHORITY_SEPARATION`**: Semantic evaluation may produce information or values, but does not itself create operational authority.
- **`INV_UNKNOWN_NO_SELF_AUTHORITY`**: `Unknown` carries indeterminacy only and has no intrinsic allow, deny, fallback, policy, or authority meaning.
- **`INV_LOGIC_NO_AUTHORITY_SYNTHESIS`**: `True`, `False`, `Unknown`, and valid logical evaluation results cannot themselves create, enlarge, or substitute for authority.
- **`INV_REPRESENTATION_NO_PROVENANCE_UPGRADE`**: Changing representation or semantic type cannot increase the factual provenance or evidentiary authority attributable to the source value.

### 8.2 Boundary Clarifications & Non-Normative Disclaimers
1. **Explicit Promotion (`xox(expr)`)**: `xox(expr)` is an explicit Bool-to-XoX semantic representation promotion. It converts a bivalent boolean into a trivalent XoX value and does not certify or upgrade the origin, trustworthiness, or factual provenance of `expr`.
2. **Policy Neutrality of `Unknown`**: `Unknown` represents factual indeterminacy across admissible realities ($|W_{\text{factive}}| \ge 2$). The semantic core defines `Unknown` as strictly policy-neutral: it neither universally authorizes (fail-open) nor universally rejects (fail-closed).
3. **Explicit Collapse (`unwrap_or(...)`)**: `unwrap_or(default_bool)` provides a deterministic short-circuiting flow-control mapping from `XoX` to `Bool`. While the evaluation produces a bivalent `Bool` under language semantics, the resulting `Bool` is purely a computational value and does not constitute an authorization certificate or entitlement.
4. **K3 Evaluation and Truth**: An expression evaluating to `True` under Strong Kleene ($K_3$) logic establishes only the semantic result of that expression under the formal language rules. Truth value alone does not synthesize or imply decision or execution authority.
5. **Scope Bounding**: These invariants define core semantic limits of the evaluation language. They do not specify or govern external policy engines, access control capabilities, multi-agent delegation chains, authorization workflows, or operational execution policies.

---

### 9.1 Primitive Domain and Realization Support
For binary propositions, the primitive world-level evaluation codomain is $D = \{\text{False}, \text{True}\}$.

Let $W_{\text{factive}}$ denote the set of non-empty admissible execution realities under the active factual, contextual, semantic, and authorization frame. For any proposition $P$, its **realization support** $S_P \subseteq D$ is the extensional image of $P$ across admissible realities:
$$S_P = \{ \text{eval}(P, w) \mid w \in W_{\text{factive}} \}$$

The full binary possibility carrier is the Boolean lattice:
$$\mathcal{P}(D) = \{ \emptyset, \{\text{False}\}, \{\text{True}\}, \{\text{False}, \text{True}\} \}$$

### 9.2 The Binary Factive Realization Theorem
Under four minimal mathematical assumptions:
1. **Bivalent World Codomain**: For every $w \in W_{\text{factive}}$, $\text{eval}(P, w) \in \{\text{False}, \text{True}\}$.
2. **Non-Empty Context**: $W_{\text{factive}} \neq \emptyset$.
3. **Definedness**: Every $w \in W_{\text{factive}}$ satisfies definedness preconditions for $P$.
4. **Extensional Realization**: Truth-functional state depends strictly on the set $S_P$.

**Theorem**: The realization support $S_P$ is a non-empty subset of the 2-element set $D$. Because a 2-element set has exactly $2^2 - 1 = 3$ non-empty subsets, there exist exactly three non-contradictory realization classes, which map canonically via factive projection $\pi_v: \mathcal{P}(D) \setminus \{\emptyset\} \to \mathbb{X}$ to the XoX truth domain:
- $S_P = \{\text{True}\} \implies \pi_v(S_P) = \text{XoX.True}$ (Invariant True across all admissible realities)
- $S_P = \{\text{False}\} \implies \pi_v(S_P) = \text{XoX.False}$ (Invariant False across all admissible realities)
- $S_P = \{\text{False}, \text{True}\} \implies \pi_v(S_P) = \text{XoX.Unknown}$ (Realization variance across admissible realities)

### 9.3 Contradiction Isolation & The Empty Set
The bottom element $S_P = \emptyset$ (corresponding to $W_{\text{factive}} = \emptyset$) represents **Ontological Contradiction** (mutually unsatisfiable premise constraints). 
- $\emptyset$ is algebraically required in the underlying Boolean lattice $\mathcal{P}(D)$ for meet-closure (e.g. $\{\text{True}\} \cap \{\text{False}\} = \emptyset$).
- $\emptyset$ is **not** an executable XoX truth value. An evaluated contradiction aborts fail-closed outside $\mathbb{X}$ and cannot be captured by `xen` or collapsed by `unwrap_or`.

### 9.4 Pointwise Negation vs Set Complement
- **Logical Negation**: Acts by elementwise Boolean inversion on realization support:
  $$\text{not}(S_P) = \{ \neg_{\text{Bool}} x \mid x \in S_P \}$$
  Therefore: $\text{not}(\{\text{True}\}) = \{\text{False}\}$, $\text{not}(\{\text{False}\}) = \{\text{True}\}$, and $\text{not}(\{\text{False}, \text{True}\}) = \{\text{False}, \text{True}\}$. Logical NOT is an exact bijection on realization classes.
- **Non-Equivalence with Set Complement**: Set complement $D \setminus S_P$ does **not** represent logical negation. For $S_P = \{\text{False}, \text{True}\}$, $D \setminus S_P = \emptyset$ (Contradiction), whereas logical negation preserves `Unknown`.

### 9.5 Finite Extensional Capacity vs Structured World Models
- **Full Extensional Carrier Exactness**: For $N = |W_{\text{obs}}| < \infty$ observationally distinguishable admissible worlds, the full mathematical extensional support carrier is defined as $C_{\text{full}}(W_{\text{obs}}) = \mathcal{P}(W_{\text{obs}}) \setminus \{\emptyset\}$, with $|C_{\text{full}}(W_{\text{obs}})| = 2^N - 1$ exactly by definition of the non-empty powerset.
- **Admissible, Reachable, and Observable Families**:
  - **Admissible Supports**: $\mathcal{F}_{\text{adm}} \subseteq C_{\text{full}}(W_{\text{obs}})$ is the family of supports permitted by relational and domain constraints.
  - **Reachable Supports**: $\mathcal{F}_{\text{reach}}(s_0, \text{Auth}) \subseteq \mathcal{F}_{\text{adm}}$ is the family reachable from initial support $s_0$ under legal capability transitions.
  - **Observational Quotient Space**: $\mathcal{F}_{\text{obs}} = \mathcal{F}_{\text{adm}} / \sim_{\text{Obs}}$ is the quotient of distinguishable states under the observational continuation language.
  - **Reachable Observational Quotient**: $\mathcal{F}_{\text{reach\_obs}} = \mathcal{F}_{\text{reach}} / \sim_{\text{Obs}}$.
- **Valid Cardinality Relations**:
  $$|\mathcal{F}_{\text{reach}}| \le |\mathcal{F}_{\text{adm}}| \le |C_{\text{full}}(W_{\text{obs}})| = 2^N - 1$$
  $$|\mathcal{F}_{\text{obs}}| \le |\mathcal{F}_{\text{adm}}|$$
  $$|\mathcal{F}_{\text{reach\_obs}}| \le |\mathcal{F}_{\text{reach}}| \quad \text{and} \quad |\mathcal{F}_{\text{reach\_obs}}| \le |\mathcal{F}_{\text{obs}}|$$
  *(Note: $\mathcal{F}_{\text{reach}}$ is a subset while $\mathcal{F}_{\text{obs}}$ is a quotient; their cardinalities are not ordered relative to each other).*
- **Capacity vs Structure Boundary**: Equal cardinality $N$ implies isomorphic bare powerset lattices $C_{\text{full}}(W_{\text{obs}})$, but does **not** imply semantic equivalence. Relational constraints, causal reachability, temporal accessibility, coordinate dependencies, and authority transition policies are irreducible to $N$.
- **Structured World Model**: Rich factive contexts are represented explicitly by the structured world model:
  $$M = (W_{\text{obs}}, \{R_i\}, G_{\text{trans}}, \text{Auth})$$
  where $\{R_i\}$ are joint relational constraints, $G_{\text{trans}}$ is the causal/temporal reachability relation, and $\text{Auth}$ governs legal transition permissions.

---

## 10. Two-Tier Epistemic Architecture & Composition Boundaries

### 10.1 Two-Tier Algebra Architecture
XoXLang maintains a strict separation between two orthogonal algebraic systems:
1. **Epistemic Constraint Algebra**: Operates on $\mathcal{P}(D)$ under $(\cap, \cup, \emptyset, D)$ representing evidence refinement on a single claim. Meet ($\cap$) represents constraint conjunction; Join ($\cup$) represents uncertainty disjunction; $\emptyset$ represents contradictory constraints.
2. **Factive Truth Algebra**: Operates on propositional truth projections over joint realization spaces $R_{(P_1, \dots, P_k)} \subseteq D^k$ under Strong Kleene ($K_3$) logic.

### 10.2 Generic Constraint-Satisfaction Core & Non-Equivalence to Symmetry Breaking
- **Generic Constrained System**: For state space $X$ and active constraints $C$, admissible support is $A(C) = \{ x \in X \mid \forall c \in C.\, x \text{ satisfies } c \}$. Adding compatible constraints yields monotone subset reduction $A(C \cup \{c\}) \subseteq A(C)$. Incompatible constraints yield $A(C) = \emptyset$ (contradiction / unsatisfiability).
- **Refinement is not Symmetry Breaking**: Support reduction ($A(C') \subset A(C)$) and automorphism/symmetry reduction ($\text{Stab}(C') \subset \text{Stab}(C)$) are distinct operations. Neither implies the other without additional structure.

### 10.3 Mandatory Semantic Boundaries
- **Intersection is not AND**: $S_A \cap S_B$ is the conjunction of constraints on a single proposition, not the logical conjunction $A \land B$ of two propositions. (e.g., if $S_A = \{\text{True}\}$ and $S_B = \{\text{False}\}$, $S_A \cap S_B = \emptyset \neq S_{A \land B} = \{\text{False}\}$).
- **Union is not OR**: $S_A \cup S_B$ is uncertainty weakening, not logical disjunction $A \lor B$.
- **Set Complement is not NOT**: $D \setminus S_A \neq \text{not}(S_A)$.
- **Contradiction is not False**: Contradiction is $\emptyset$ (unsatisfiable); False is $\{\text{False}\}$ (invariant refutation).
- **Unknown is not Contradiction**: Unknown is $\{\text{False}, \text{True}\}$ ($|W_{\text{factive}}| \ge 2$); Contradiction is $\emptyset$ ($W_{\text{factive}} = \emptyset$).
- **Unknown is not Probability / Confidence**: Continuous probability distributions and confidence intervals inhabit evidence metadata ($\pi$) and decision policies ($\kappa$), not the ontological truth domain $\mathbb{X}$.
- **Truth Projection vs Complete Epistemic Record**: $\mathbb{X} = \{\text{True}, \text{False}, \text{Unknown}\}$ is a factive quotient projection, not the complete epistemic record $(v, \pi, \Omega, \Delta)$.
- **Observation is not Authorized Resolution**: Equality (`==`) and inequality (`!=`) observe XoX state identity across the result-type barrier and return a `Bool` observation; observation of state uncertainty does not constitute authorized uncertainty resolution, epistemic possibility reduction, or decision collapse.
- **Relational Composition Boundary**: Exact multi-proposition evaluation uses joint realization relations $R_{(A, B)} \subseteq D^2$. Marginal $K_3$ tables represent exact evaluation under epistemic independence ($R_{(A,B)} = S_A \times S_B$) and a sound conservative over-approximation ($S_{A \land B} \subseteq K_3\text{-AND}(\pi_v(S_A), \pi_v(S_B))$) under arbitrary correlation.

---

## 11. Authority & Provenance as Transition DAGs

### 11.1 Authority as Legal Possibility Reduction
- An authoritative capability (e.g. `DefinednessWitness`, `OntologicalConstraintToken`, `CoverageCertificate`) represents authorized permission to legally eliminate non-realizable possibilities: $S \to S' \subset S$.
- Unauthorized observations or heuristics have zero authority to eliminate admissible possibilities.
- Authority and provenance are operational structures governing XoX truth resolution; they are not intrinsic to abstract mathematical or geometric state spaces.

### 11.2 Provenance as a Labeled Derivation DAG
- Epistemic lifecycle is non-monotone across time: authorized evidence acquisition reduces support ($S \to S'$), while invalidation, retraction, frame drift, or world mutation expands or shifts support ($S \to S''$).
- Provenance ($\pi \in \Pi$) is formalized as a labeled directed acyclic graph (DAG) recording the historical trajectory of authorized reductions, invalidation transitions, and authority tokens justifying the current realization state.

---

## 12. Current validation evidence

- **Test Suite**: `tests/test_core_semantics.py`, `tests/test_identity_adversarial.py`
  - **Normal Tests**: All core classifier and identity tests pass.
  - **Adversarial Stress Tests**: Verified against permutation invariance, scale up to 10,000 worlds, definedness priority, duplicate handling, custom equivalence, capability tokens, and correlation boundaries.
- **Alignment Audit**: Verified `ALIGNED` under task `XOX_FINAL_CANONICAL_SPEC_CONSOLIDATION_001` with zero semantic deviations.
