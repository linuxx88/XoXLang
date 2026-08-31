# X-o-X (Xen)

**X-o-X** (pronounced *Xen*) is a domain-specific ternary logic programming language and reference compiler.

In conventional two-valued Boolean logic, uncertainty or uncomputed state is frequently modeled using out-of-band sentinel values like `None` or `Optional[bool]`. This forces ad-hoc null checks, creates implicit truthiness bugs, and obscures logical domain reasoning.

X-o-X elevates uncertainty to a first-class citizen with exactly three mutually exclusive truth states: `True`, `False`, and `Unknown`.

---

## Truth States & Control Flow

X-o-X conditional statements require exhaustive handling of all three truth states using the dedicated `if`, `xen`, and `else` constructs:

| State | Branch Keyword | Semantic Meaning |
| :--- | :--- | :--- |
| `True` | `if` | Definite truth |
| `Unknown` | `xen` | Epistemic uncertainty |
| `False` | `else` | Definite falsity |

### Syntax Example

```python
status: XoX = Unknown

if status:
    action = True
xen:
    ignore
else:
    action = False
```

When no action is required on uncertainty, `xen: ignore` explicitly declares intentional no-action handling for the `Unknown` state.

### Direct vs. Derived Control

- **Direct XoX Control (`if/xen/else`)**: Static tripartite exhaustiveness is enforced at compile time on `XoX` conditions. Omitting `xen` is a compile error.
- **Derived Bool Control (`==`, `unwrap_or`)**: Operations producing `Bool` enter binary control flow. Comparing `if x == True:` explicitly partitions state (merging `False` and `Unknown` into `else`), while `x.unwrap_or(False)` performs explicit policy collapse. XoXLang prevents implicit `Unknown` loss and guarantees exhaustive handling strictly under direct `XoX` control.


---

## Why XoX is Not `Optional[bool]`

1. **Logical Domain Membership**: `Unknown` participates directly in logical operators (`AND`, `OR`, `NOT`) following **Strong Kleene 3-valued logic ($K_3$)**, rather than raising `TypeError` or silently coercing to falsity.
2. **Anti-Truthiness Runtime**: `XoX` values strictly forbid implicit Boolean evaluation (`bool(x)` raises a runtime `TypeError`).
3. **State Identity Equality**: Equality (`==`) evaluates exact state identity (`Unknown == Unknown` evaluates to `Bool True`), returning binary `Bool`.
4. **Exhaustiveness**: Conditionals on `XoX` values enforce explicit coverage of `Unknown` at compile time.

---

## Strong Kleene Logic Summary

Logical operations on `XoX` follow Strong Kleene short-circuit dominance:

- `NOT Unknown` $\rightarrow$ `Unknown`
- `True AND Unknown` $\rightarrow$ `Unknown`, but `False AND Unknown` $\rightarrow$ `False`
- `False OR Unknown` $\rightarrow$ `Unknown`, but `True OR Unknown` $\rightarrow$ `True`

Logical expressions evaluate operands strictly from left to right with dominant short-circuit skipping (§7). Under **Operational Trace Preservation (§7.1)**, mathematical $K_3$ value equivalence does not imply observable equivalence when side effects are involved, and compiler transformations must strictly preserve canonical observable execution traces.

---

## Type Conversion & Resolution

X-o-X maintains strict isolation between `Bool` and `XoX` without implicit coercion.

### Explicit Promotion: `xox(expr)`

Promote a two-valued `Bool` expression explicitly to ternary `XoX`:

```python
is_ready: Bool = True
status: XoX = xox(is_ready)  # Evaluates to XoX True
```

### Explicit Collapse: `expr.unwrap_or(default_bool)`

Collapse a ternary `XoX` value to `Bool` with short-circuiting lazy fallback evaluation (note: X-o-X source uses method syntax `expr.unwrap_or(default_bool)`, not standalone function syntax `unwrap_or(expr, default_bool)`):

```python
status: XoX = Unknown
active: Bool = status.unwrap_or(False)  # Evaluates fallback only when status is Unknown
```



### Unknown Provenance & Resolution Authority

In X-o-X, `Unknown` carries an immutable, non-empty provenance set identifying unresolved semantic facts established by factive evaluation. An `Unknown` value cannot be arbitrarily resolved or manufactured by application code; resolution operations require exact authority validation against authorized host policies.

For complete formal specifications and operational semantics, refer to [XOX_SPEC.md](XOX_SPEC.md).


---

## Installation & Python API

X-o-X requires **Python >= 3.10**. Install locally from source:

```bash
git clone https://github.com/linuxx88/XoXLang.git
cd XoXLang
pip install .
```

### Compiler Usage

The compiler transpiles X-o-X source to standard Python via the `xoxlang` package:

```python
from xoxlang import compile_source

source_code = """
flag: XoX = Unknown
if flag:
    result = True
xen:
    ignore
else:
    result = False
"""

python_code = compile_source(source_code)
print(python_code)
```

---

## Testing

Run the complete test suite:

```bash
python3 -m unittest discover -s tests
```

---

## Project Status & License

- **Maturity**: Beta (Reference implementation and specification)
- **Specification**: [XOX_SPEC.md](XOX_SPEC.md)
- **License**: [Apache License 2.0](LICENSE)