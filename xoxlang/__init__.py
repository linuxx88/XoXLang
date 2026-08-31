"""XoXLang (X-o-X) reference compiler package."""
from xoxlang.compiler import compile_source
from xoxlang.core_semantics import DefinednessPreconditionError
from xoxlang.diagnostics import Diagnostic, DiagnosticCategory, render_diagnostic
from xoxlang.runtime import UnknownValueError, XoX, xox_and, xox_not, xox_or

__version__ = "0.1.0"
__all__ = [
    "compile_source",
    "Diagnostic",
    "DiagnosticCategory",
    "render_diagnostic",
    "XoX",
    "xox_not",
    "xox_and",
    "xox_or",
    "UnknownValueError",
    "DefinednessPreconditionError",
    "__version__",
]






