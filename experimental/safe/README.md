# Experimental O0/SAFE Authority and Governance Extension

## 1. Overview
The `experimental.safe` package provides an optional operational authority, context binding, and capability governance layer for XoXLang.
It is explicitly separated from the normative S1 semantic core (`xoxlang/`).

## 2. Unidirectional Dependency Rule
- `experimental.safe` depends on `xoxlang` (`xoxlang.identity`, `xoxlang.core_semantics`, `xoxlang.runtime`).
- `xoxlang` **never** depends on `experimental.safe`.
- If `experimental/safe` is removed entirely, the core language compiler, runtime, parser, AST, K3 logic, mandatory `xen` branch, and factive semantics remain 100% operational.

## 3. Key Abstractions
- **`WorldStateAuthority`**: Authoritative host environment responsible for establishing factive world states, authorized ontological constraints, and resolution policies.
- **`FallbackPolicyIdentity`**: Immutable canonical structural semantic identity of an authorized resolution fallback policy.
- **`NO_FALLBACK`**: Singleton policy identity denoting the intentional absence of a fallback value for `xen: ignore`.
- **`ResolutionToken`**: Unforgeable capability 4-tuple `(ProvenanceSet, OperationType, WorldStateID, FallbackPolicyIdentity)` issued by `WorldStateAuthority`.
- **`resolve_unwrap_or`**: Resolution gateway enforcing capability token verification when collapsing an `UnknownValue` to a boolean.
- **`resolve_xen_ignore`**: Resolution gateway enforcing capability token verification when acknowledging and abandoning an `UnknownValue` branch.

## 4. Empirical Guarantees Demonstrated in Benchmarks
1. **Unauthorized Permissive Fallback Containment (`MUT-04`)**:
   - At S1, `unwrap_or(True)` evaluates to `True` by design (S1 policy neutrality).
   - Under `experimental.safe`, unauthenticated permissive fallbacks (`unwrap_or(True)`) are structurally rejected fail-closed via `INV_AUTHORIZED_RESOLUTION_BOUNDARY`.
2. **Contextual Authority Replay Protection (`MUT-06`)**:
   - A `ResolutionToken` issued under `WorldStateID` A cannot be reused after state transition to `WorldStateID` B (`INV_RELEVANT_CONTEXT_BINDING`).
3. **Host Ingress Freshness Boundary (`MUT-05`)**:
   - XoXLang rejects stale context once a state advance is signaled by the host environment via `WorldStateID`.
   - Autonomous external drift discovery without host ingress is a Host Boundary Limitation.
