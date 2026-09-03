# XoXLang Core Semantics: Atomic Fact Identity

This document specifies the minimal validated and implemented semantic slice for atomic unresolved fact identity, references, persistent storage locations, and host-operation boundaries in `xoxlang/identity.py`.

---

## 1. Problem this slice solves

In XoXLang, reasoning under uncertainty requires distinguishing repeated references to the *same* unresolved fact occurrence from references to *distinct* unresolved facts that happen to share equal descriptions or coincident values across admissible histories.

Furthermore, language execution requires cleanly separating:
- **Fact Identity**: An immutable token identifying a unique unresolved fact occurrence.
- **Reference Designation**: Syntactic or semantic bindings that point to an existing fact identity.
- **Storage Identity**: Persistent container locations whose contents can change over time without altering the identity of the container or earlier facts.
- **Value Relations / Equivalence**: Equalities or constraints that restrict values without unifying distinct fact identities.

---

## 2. Atomic fact identity versus value equality

An atomic unresolved fact occurrence is represented by `AtomicFact`:
- **Unique Semantic Identity**: Every instantiation of `AtomicFact` is assigned a unique, immutable semantic identity token (`identity`). Identity is generated internally and cannot be chosen or forged by callers. (The reference Python implementation uses an internally generated monotonic integer, but the semantic contract requires only unique, immutable identity).
- **Value Orthogonality**: Two distinct `AtomicFact` occurrences remain unequal and distinct even if they carry identical payloads or representations.
- **Non-Semantic Payload**: Any payload attached to an `AtomicFact` is purely descriptive host metadata; it is not the semantic valuation of the fact and does not participate in equality comparison or hash computation.
- **Hash and Equality Invariance**: `AtomicFact` equality (`__eq__`) and hashing (`__hash__`) depend strictly on the underlying `identity`. In-place mutations to attached payloads do not alter the fact's identity, hash code, or set membership.

---

## 3. FactReference semantics

A reference designating an atomic fact is represented by `FactReference`:
- **Permanent Designation**: A `FactReference` permanently designates a single `AtomicFact` occurrence.
- **Identity Preservation**: Multiple references to the same `AtomicFact` share and expose the same underlying `identity`.
- **Occurrence Resolution**: `FactReference.resolve()` returns the exact `AtomicFact` instance originally designated.
- **Closed-Domain Validation**: `FactReference` accepts only valid `AtomicFact` instances; non-`AtomicFact` targets are rejected at construction.

---

## 4. Storage identity and rebinding

A persistent mutable container holding an atomic fact binding is represented by `StorageLocation`:
- **Independent Storage Identity**: Every `StorageLocation` receives a persistent, immutable `storage_id` that remains distinct from the identity of any bound `AtomicFact`.
- **Always Bound in this Slice**: A `StorageLocation` must be initialized with an `AtomicFact`. Unbound (`None`) storage states are not part of this minimal slice.
- **Rebinding Semantics (`rebind`)**: Rebinding updates the currently observed fact (`read()`) and returns the previously bound fact. Rebinding leaves the `storage_id` invariant and never mutates earlier or incoming `AtomicFact` instances.
- **Guarded Mutation**: Rebinding validates that the incoming fact is an `AtomicFact`. Rejected rebinding attempts leave both the current binding and storage identity completely unchanged.
- **Slot and Attribute Protection**: Direct external modification or deletion of `_storage_id` or `_bound_fact` is blocked; binding updates must proceed exclusively through `rebind()`.

---

## 5. Copy and deepcopy boundary

Host-level copying via Python's `copy.copy` and `copy.deepcopy` enforces strict non-duplication invariants:
- **`AtomicFact` Self-Preservation**: Both `copy.copy` and `copy.deepcopy` on an `AtomicFact` return the exact same instance (`self`). This prevents synthesizing duplicate Python objects sharing an existing fact identity.
- **`FactReference` Self-Preservation**: Both `copy.copy` and `copy.deepcopy` on a `FactReference` return the exact same reference instance (`self`), preventing accidental cloning of the underlying target fact.
- **`StorageLocation` Copy Rejection**: Both `copy.copy` and `copy.deepcopy` on a `StorageLocation` fail closed by raising `TypeError`. Mutable storage identities cannot be duplicated.

---

## 6. Serialization boundary

Host serialization via Python's `pickle` fails closed across all three identity entities:
- Calling `pickle.dumps()` on `AtomicFact`, `FactReference`, or `StorageLocation` raises `TypeError`.
- Persistent or cross-process identity recovery is unmodeled in this slice. Failing closed prevents out-of-band synthesis of duplicate semantic identities upon deserialization.

---

## 7. Failure behavior and problem-oriented errors

Invalid operations are rejected immediately with clear, problem-oriented error messages:
- Attempting to pass non-`AtomicFact` objects to `FactReference`, `StorageLocation.__init__`, or `StorageLocation.rebind` raises a `TypeError` indicating that an `AtomicFact` instance is required.
- Attempting to modify or delete attributes on `AtomicFact` or `FactReference` post-construction raises an `AttributeError` indicating that their attributes are immutable.
- Attempting direct assignment to `StorageLocation` protected attributes raises an `AttributeError` indicating that direct assignment is forbidden and instructing callers to use `rebind()` for fact updates. Deleting `StorageLocation` attributes raises an `AttributeError` indicating that attributes are permanent.
- Attempting to copy a `StorageLocation` raises a `TypeError` explaining that mutable storage identity cannot be duplicated.
- Attempting to serialize any identity object raises a `TypeError` explaining that serialization is unsupported because persistent or cross-process semantic identity is not defined.

---

## 8. Explicit examples

```python
import copy
import pickle
from xoxlang.identity import AtomicFact, FactReference, StorageLocation

# 1. Two facts with equal payloads remain distinct
f1 = AtomicFact(payload="data")
f2 = AtomicFact(payload="data")
assert f1 != f2
assert f1.identity != f2.identity

# 2. Two references to one fact preserve one fact identity
ref1 = FactReference(f1)
ref2 = FactReference(f1)
assert ref1.identity == ref2.identity == f1.identity
assert ref1.resolve() is f1

# 3. Two storage locations containing the same fact have distinct storage identities
loc1 = StorageLocation(f1)
loc2 = StorageLocation(f1)
assert loc1.storage_id != loc2.storage_id
assert loc1.read() is f1 and loc2.read() is f1

# 4. Storage rebinding preserves storage identity
sid = loc1.storage_id
old = loc1.rebind(f2)
assert old is f1
assert loc1.read() is f2
assert loc1.storage_id == sid

# 5. Copy of AtomicFact returns the same object
assert copy.copy(f1) is f1
assert copy.deepcopy(f1) is f1

# 6. Deepcopy of FactReference returns the same object
assert copy.deepcopy(ref1) is ref1

# 7. Copy of StorageLocation is rejected
try:
    copy.copy(loc1)
except TypeError as e:
    assert "cannot be duplicated" in str(e)

# 8. Pickle serialization is rejected
try:
    pickle.dumps(f1)
except TypeError as e:
    assert "serialization is unsupported" in str(e)
```

---

## 9. Semantic Authority: DefinednessWitness & OntologicalConstraintToken

To maintain absolute mathematical isolation between empirical observations, definedness verification, and hard world boundaries ($W_{\text{factive}}$), XoXLang formalizes two distinct evaluator-issued authority capabilities:

### 9.1 Observational Evidence vs Hard Constraints
- **Evidence Isolation**: Observational reports, candidate claims, and empirical testimonies inhabit the Candidate Evidence domain ($\mathcal{C}$). They assert facts *within* admissible worlds but possess **zero ontological authority** to restrict $W_{\text{factive}}$.
- **No Authority Synthesis**: Source trust levels, cryptographic signatures, repetitions, corroborations, or identical textual payloads never synthesize ontological authority.
- **Local Evidential Conflict**: Conflicting observational evidence with non-empty remaining alternatives evaluates strictly to `Unknown` ($|W_{\text{factive}}| \ge 2$), never Contradiction.
- **Hard Constraints**: $W_{\text{factive}}$ is restricted exclusively by active hard constraints possessing explicit, valid `OntologicalConstraintToken` authority.

### 9.2 DefinednessWitness
A **`DefinednessWitness`** is an evaluator-issued non-forgeable capability certifying that an expression or fact is semantically defined (`is_defined == True`) for evaluation:
- **Exact 3-Tuple Binding**: A `DefinednessWitness` binds strictly to:
  $$\text{DefinednessWitness}(\text{RootID}, \text{SemanticPath}, \text{WorldStateID})$$
- **Zero World-Restriction Authority**: A `DefinednessWitness` holds zero power to restrict, shrink, or bound $W_{\text{factive}}$. It certifies observational definedness only.
- **Anti-Staleness & Fail-Closed**: Any relevant context or state mutation increments `WorldStateID`, immediately rendering prior witnesses stale. Stale, missing, or mismatched witnesses fail closed by refusing classification (`DefinednessPreconditionError`).
- **No Implicit Migration**: Witnesses cannot migrate across roots, paths, or world states.

### 9.3 OntologicalConstraintToken
An **`OntologicalConstraintToken`** is an evaluator-issued non-forgeable capability authorizing exactly one hard constraint to restrict the factive reality space ($W_{\text{factive}}$):
- **Exact 5-Tuple Binding**: An `OntologicalConstraintToken` binds strictly to:
  $$\text{OntologicalConstraintToken}(\text{RootID}, \text{SemanticPath}, \text{WorldStateID}, \text{EvaluatorSemanticProfile}, \text{ConstraintContentIdentity})$$
- **Non-Inheritance**: Authority is strictly nominal and non-inheritable. Authority does not transfer across parent, child, or sibling paths, across distinct roots, across world states, across constraint identities, or across evaluator profiles.
- **Zero Mismatch Authority**: Missing, forged, stale, or scope-mismatched tokens possess zero power to restrict $W_{\text{factive}}$ and fail closed.

### 9.4 ConstraintContentIdentity
**`ConstraintContentIdentity`** establishes the exact structural semantic identity of an authorized constraint:
- **Canonical Structure Digest**: Defined as the cryptographic digest of the canonical structural AST with fully resolved semantic referents under the active `EvaluatorSemanticProfile`:
  $$\text{ConstraintContentIdentity} = \text{CanonicalSemanticStructureDigest}(\text{CanonicalStructuralAST}, \text{ResolvedReferentMap}, \text{EvaluatorSemanticProfile})$$
- **Formatting Invariance**: Syntax trivia and formatting differences canonicalize to the identical AST structure.
- **No Logical Equivalence Substitution**: Logical equivalence alone never authorizes constraint substitution without explicit evaluator re-issuance.
- **Operational Trace Preservation**: Operationally significant operand order (governed by left-to-right evaluation) is an integral part of semantic identity.

### 9.5 EvaluatorSemanticProfile & Orthogonality to WorldStateID
- **EvaluatorSemanticProfile**: The immutable identity of a closed semantic environment, defined by the finite transitive closure of its Directed Semantic Dependency Graph (DSDG) covering all parsing, typing, resolution, operator, and primitive specifications.
- **Predeclared Dynamic Dispatch**: Runtime dynamic dispatch and dynamic loading are sound if and only if all possible reachable semantic targets reside entirely within the sealed profile closure. Reaching an undeclared dependency fails closed.
- **Evolution via Distinct Profiles**: The global ecosystem evolves by creating new profile identities; existing profile identities never mutate.
- **Orthogonal Axes**: `WorldStateID` (mutable domain/context state) and `EvaluatorSemanticProfile` (immutable evaluation rules) represent strictly orthogonal axes.

### 9.6 Unknown Provenance Set ($\Pi$)
- **Immutable Provenance Set**: Every `Unknown` semantic outcome carries a non-empty, immutable provenance set $\Pi = \{p_1, \dots, p_k\}$ identifying the exact unresolved fact identities or derived canonical projection targets in $W_{\text{factive}}$.
- **Trusted Origin Authority**: Provenance originates strictly from trusted factive evaluation over authentic unresolved facts or derived projection targets in $W_{\text{factive}}$. Arbitrary application callers, assertions, or trust labels cannot synthesize or inject provenance identities.
- **Propagation Invariance**: Assignments, parameter passing, and copying preserve $\Pi$ while semantic dependency survives.
- **Operational Short-Circuiting**: Skipped operands contribute zero provenance.
- **Semantic Independence vs Authorized Resolution**: When Strong Kleene ($K_3$) evaluation yields a determinate truth value (`True` or `False`) independent of unresolved sub-expressions, that provenance disappears from the resulting semantic value by proven semantic independence without requiring resolution authority.
- **Surviving Combination**: When multiple unresolved dependencies survive into the evaluated result, surviving provenance sets combine strictly by exact set union ($\Pi_1 \cup \Pi_2$).
- **Audit Trace Separation**: Semantic provenance $\Pi$ on values is mathematically distinct from operational execution audit logs ($\mathcal{A}ud$).

### 9.7 Operational Authority and Resolution Boundaries (O0/SAFE)
Resolution capabilities, fallback policies, resolution tokens, and operational gateways (`ResolutionToken`, `FallbackPolicyIdentity`, `WorldStateAuthority`, `resolve_unwrap_or`, `resolve_xen_ignore`) are part of the experimental O0/SAFE extension and are documented in [experimental/safe/README.md](../experimental/safe/README.md).

---

## 10. Intentionally unsupported semantics

The following capabilities are explicitly outside the scope of this slice and intentionally unmodeled:
- **Compound Facts & Projections**: No record, tuple, or struct facts; no field projections or sub-object identities.
- **Value Constraint Solving**: No SMT/unification solver; does not solve `u == v` constraints.
- **World & History Generation**: No dynamic state space exploration or trajectory enumeration.
- **Storage Cloning**: No duplication or branching of mutable storage cells.
- **Persistent / Cross-Process Identity**: No global registry, interning table, or serialization protocol.
- **Parser & Syntax**: No language grammar, AST extensions, or keyword lowering for unresolved facts.
- **Unknown Propagation & Concurrency**: No runtime 3-valued truth propagation, thread synchronization, or certification logic.

---

## 11. Validation evidence

- **Implementation**: `xoxlang/identity.py` (CORE_S1 factive identity)
- **Normal Tests**: `tests/test_identity.py` (covering identity distinction, reference resolution, storage rebinding, type guards, and attribute immutability)
- **SAFE Tests**: `tests/safe/` (covering authority tokens, resolution policies, and adversarial attacks)
- **Full Repository Suite**: Full repository test suite passing with 0 failures.
- **Alignment Audit**: Verified bidirectionally aligned (`ALIGNED`) under task `XOX_ATOMIC_IDENTITY_ALIGNMENT_AUDIT_001`.


