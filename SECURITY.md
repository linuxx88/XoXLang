# Security Policy

## Security Model
XoXLang is a domain-specific programming language designed to eliminate implicit Boolean truthiness bugs and make epistemic uncertainty explicit via three-valued logic (True, False, Unknown). Its security model centers on fail-closed evaluation, strict domain isolation, and compile-time exhaustiveness.

XoXLang is **not** an untrusted-code sandbox, a cryptographic framework, or a complete security boundary for hostile execution environments.

---

## Verified Properties
The following properties are implemented in the reference compiler and validated by adversarial automated tests:

1. **Runtime Anti-Truthiness**: `XoX` runtime values strictly forbid implicit Boolean coercion. Evaluating `bool(x)`, `if x:`, `while x:`, or Python `and`/`or` on an `XoX` instance raises a runtime `TypeError` (`tests/test_runtime.py`).
2. **Compile-Time Exhaustiveness**: Conditionals on `XoX`-typed expressions require explicit handling of all three truth states (`if`, `xen`, `else` or `xen: ignore`), rejecting unhandled `Unknown` branches at compile time (`tests/test_conditionals.py`).
3. **Explicit Type Isolation**: Transitions between binary `Bool` and ternary `XoX` require explicit, non-idempotent operations (`xox(expr)` for promotion; `expr.unwrap_or(default_bool)` or `unwrap_bool()` for collapse). Implicit type mixing is rejected at compile time (`tests/test_promotion_adversarial.py`, `tests/test_collapse_adversarial.py`).
4. **Lazy Fallback Evaluation**: In `expr.unwrap_or(default_bool)`, the fallback expression is evaluated strictly on demand when the source evaluates to `Unknown`, and skipped when the source is `True` or `False`.
5. **Operational Trace Preservation**: Lowered execution strictly evaluates conditions first and executes branch preludes only inside the selected runtime branch, preventing side effects in unselected branches (`tests/test_lowering_expressions.py`).

---

## Trust Boundaries

- **XoX Logic vs. Host Python Code**: XoXLang guarantees apply within XoX source expressions and managed runtime types. Once an `XoX` value is explicitly unwrapped into a Python `bool` via `unwrap_bool()` or `unwrap_or()`, standard Python truthiness rules apply.
- **In-Process Memory vs. External Storage**: XoXLang identity checks and state verifications operate within the single Python process heap. External files, network storage, and operating-system resources reside outside the language trust boundary.
- **Compiler Pipeline vs. Dynamic AST Bypass**: Static typing, definite returns, and exhaustiveness guarantees apply to code processed through `xoxlang.compiler.compile_source` and `SemanticAnalyzer`. Manually constructed ASTs or directly executed raw lowering templates that bypass static analysis are not guaranteed.

---

## Scope-Limited and Experimental Mechanisms

- **Process-Local Fact Identity (`AtomicFact`, `WorldStateAuthority`)**: Implemented and tested, but strictly limited to in-process memory. WorldStateID checks detect in-process state staleness, but do not provide cross-process cryptographic tamper resistance or distributed Byzantine fault tolerance (`xoxlang/identity.py`, `tests/test_identity.py`).
- **Epistemic Provenance Resolution Model**: Experimental research framework (`experiments/EPISTEMIC_RESOLUTION_MODEL.md`). It is a formal mathematical model for factive consensus and must not be used as a production authentication, authorization, or cryptographic access-control protocol.

---

## Limitations and Non-Goals

- **Not a Code Execution Sandbox**: XoXLang does not isolate system resources (filesystem, memory, network, CPU). Do not execute untrusted source code without external OS-level sandboxing.
- **Logical Fallback Safety**: Using `unwrap_or(default_bool)` forces a binary decision. If a developer supplies an incorrect fallback value, XoXLang cannot prevent resulting application-level logic errors.
- **External TOCTOU Races**: XoXLang cannot prevent time-of-check to time-of-use (TOCTOU) mutations in unmanaged external storage or databases occurring between evaluation steps.
- **Host Reflection and C Extensions**: Python introspection, byte manipulation, or native C extensions can subvert runtime type barriers and in-memory constants.
- **Native Backend Out of Scope**: Memory safety, spatial safety, and ABI guarantees for future native compilation backends remain unresolved and out of scope (§21.1).
- **Side-Channel Resistance**: Operational trace preservation ensures observable programmatic execution order, but does not guarantee constant-time execution or side-channel resistance.

---

## Reporting Security Issues

To report a potential vulnerability in XoXLang:
- Open a private security advisory via [GitHub Security Advisories](https://github.com/linuxx88/XoXLang/security/advisories).
- Alternatively, contact the repository maintainers via the public contact metadata published in `pyproject.toml` (`60791469+linuxx88@users.noreply.github.com`).

Please provide a minimal reproducible test case, description of the impact, and the affected XoXLang version.

---

## Canonical References

For canonical specifications and formal definitions, consult:
- [XOX_SPEC.md](XOX_SPEC.md) (§3, §7, §7.1, §18, §19, §21.1)
- [docs/core_semantics.md](docs/core_semantics.md)
- [docs/atomic_identity_semantics.md](docs/atomic_identity_semantics.md)
- [experiments/DIAGNOSTIC_UX_COUNTEREXAMPLES.md](experiments/DIAGNOSTIC_UX_COUNTEREXAMPLES.md)
- [experiments/EPISTEMIC_RESOLUTION_MODEL.md](experiments/EPISTEMIC_RESOLUTION_MODEL.md)
