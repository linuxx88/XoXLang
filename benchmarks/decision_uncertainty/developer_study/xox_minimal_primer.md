# Minimal XoXLang Primer for Comprehension Study

## 1. What is XoXLang?
XoXLang is a programming language with native 3-valued factive logic:
- `True`: Established factual truth across all admissible execution realities.
- `False`: Established factual falsehood across all admissible execution realities.
- `Unknown`: Epistemic indeterminacy (multiple distinguishable outcomes or incomplete information).

## 2. Control Flow: `if` / `xen` / `else`
In XoXLang, a condition that evaluates to `Unknown` cannot be silently converted to `True` or `False`. An `if` statement on an `XoX` condition requires an explicit `xen` (unknown) branch:

```text
if condition {
    // executes when condition is True
} xen {
    // executes when condition is Unknown
} else {
    // executes when condition is False
}
```

## 3. Anti-Coercion
- An `XoX` truth value does **not** participate in implicit boolean truthiness.
- Attempting `bool(Unknown)` or using `Unknown` in a standard binary condition without `xen` is a compile-time or runtime `TypeError`.

## 4. Decision Fallbacks: `unwrap_or`
To convert an unresolved `Unknown` value into a standard binary boolean for a downstream system, you must call `unwrap_or(default)`:
- `True.unwrap_or(False)` -> `True`
- `False.unwrap_or(True)` -> `False`
- `Unknown.unwrap_or(False)` -> `False` (Explicit policy decision, leaves underlying truth unresolved)

## 5. Logical Operators (Strong Kleene $K_3$)
- `True and Unknown` -> `Unknown`
- `False and Unknown` -> `False` (Short-circuit dominance)
- `True or Unknown` -> `True` (Short-circuit dominance)
- `False or Unknown` -> `Unknown`
- `not Unknown` -> `Unknown`

## 6. Contradiction
When premises are mutually exclusive and admit zero admissible realities, evaluation produces **Ontological Contradiction**. Contradiction is not `Unknown`; it immediately aborts fail-closed.
