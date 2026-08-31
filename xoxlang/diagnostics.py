"""Diagnostic definitions, structured representations, and adaptive rendering for XoXLang."""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Sequence, Union
from xoxlang.tokens import SourceLocation, SourceSpan


class DiagnosticCategory(Enum):
    """Canonical diagnostic categories defined in XOX_SPEC.md §13."""
    SYNTAX_ERROR = auto()
    TYPE_ERROR = auto()
    EXHAUSTIVENESS_ERROR = auto()
    MISSING_RETURN_ERROR = auto()

    def display_name(self) -> str:
        names = {
            DiagnosticCategory.SYNTAX_ERROR: "SyntaxError",
            DiagnosticCategory.TYPE_ERROR: "TypeError",
            DiagnosticCategory.EXHAUSTIVENESS_ERROR: "ExhaustivenessError",
            DiagnosticCategory.MISSING_RETURN_ERROR: "MissingReturnError",
        }
        return names.get(self, self.name)


@dataclass(frozen=True)
class Diagnostic:
    """Structured compiler diagnostic model following the adaptive 5W+H contract."""
    category: DiagnosticCategory
    message: str
    span: Optional[SourceSpan] = None
    violated_rule: Optional[str] = None
    primary_error: Optional[str] = None
    note: Optional[str] = None
    help: Optional[str] = None
    alternatives: Optional[Sequence[str]] = None
    annotations: Optional[Dict[str, Any]] = None

    def get_primary_error(self) -> str:
        return self.primary_error if self.primary_error is not None else self.message


class TypeDiagnosticError(Exception):
    """Static type error raised during semantic/type analysis (Phase 2)."""
    def __init__(
        self,
        message: str,
        span: Optional[SourceSpan] = None,
        violated_rule: Optional[str] = None,
        note: Optional[str] = None,
        help: Optional[str] = None,
        alternatives: Optional[Sequence[str]] = None,
        annotations: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(f"TypeError: {message}")
        self.message = message
        self.span = span
        self.violated_rule = violated_rule
        self.note = note
        self.help = help
        self.alternatives = list(alternatives) if alternatives is not None else None
        self.annotations = annotations

    def to_diagnostic(self) -> Diagnostic:
        return Diagnostic(
            category=DiagnosticCategory.TYPE_ERROR,
            message=self.message,
            span=self.span,
            violated_rule=self.violated_rule,
            primary_error=self.message,
            note=self.note,
            help=self.help,
            alternatives=self.alternatives,
            annotations=self.annotations,
        )

    def render(self, source_text: Optional[str] = None, filename: Optional[str] = None) -> str:
        return render_diagnostic(self, source_text=source_text, filename=filename)


class ExhaustivenessError(Exception):
    """Static exhaustiveness error raised during conditional analysis (Phase 3)."""
    def __init__(
        self,
        message: str,
        span: Optional[SourceSpan] = None,
        violated_rule: Optional[str] = None,
        note: Optional[str] = None,
        help: Optional[str] = None,
        alternatives: Optional[Sequence[str]] = None,
        annotations: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(f"ExhaustivenessError: {message}")
        self.message = message
        self.span = span
        self.violated_rule = violated_rule
        self.note = note
        self.help = help
        self.alternatives = list(alternatives) if alternatives is not None else None
        self.annotations = annotations

    def to_diagnostic(self) -> Diagnostic:
        return Diagnostic(
            category=DiagnosticCategory.EXHAUSTIVENESS_ERROR,
            message=self.message,
            span=self.span,
            violated_rule=self.violated_rule,
            primary_error=self.message,
            note=self.note,
            help=self.help,
            alternatives=self.alternatives,
            annotations=self.annotations,
        )

    def render(self, source_text: Optional[str] = None, filename: Optional[str] = None) -> str:
        return render_diagnostic(self, source_text=source_text, filename=filename)


class MissingReturnError(Exception):
    """Static missing return error raised during definite-return analysis (Phase 4)."""
    def __init__(
        self,
        message: str,
        span: Optional[SourceSpan] = None,
        violated_rule: Optional[str] = None,
        note: Optional[str] = None,
        help: Optional[str] = None,
        alternatives: Optional[Sequence[str]] = None,
        annotations: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(f"MissingReturnError: {message}")
        self.message = message
        self.span = span
        self.violated_rule = violated_rule
        self.note = note
        self.help = help
        self.alternatives = list(alternatives) if alternatives is not None else None
        self.annotations = annotations

    def to_diagnostic(self) -> Diagnostic:
        return Diagnostic(
            category=DiagnosticCategory.MISSING_RETURN_ERROR,
            message=self.message,
            span=self.span,
            violated_rule=self.violated_rule,
            primary_error=self.message,
            note=self.note,
            help=self.help,
            alternatives=self.alternatives,
            annotations=self.annotations,
        )

    def render(self, source_text: Optional[str] = None, filename: Optional[str] = None) -> str:
        return render_diagnostic(self, source_text=source_text, filename=filename)


def render_diagnostic(
    diagnostic: Union[Diagnostic, TypeDiagnosticError, ExhaustivenessError, MissingReturnError, Any],
    source_text: Optional[str] = None,
    filename: Optional[str] = None,
) -> str:
    """Render a structured diagnostic adaptively."""
    effective_filename = filename
    if effective_filename is None and hasattr(diagnostic, "filename") and getattr(diagnostic, "filename", None):
        effective_filename = getattr(diagnostic, "filename")

    if hasattr(diagnostic, "to_diagnostic"):
        diag = diagnostic.to_diagnostic()
    elif isinstance(diagnostic, Diagnostic):
        diag = diagnostic
    else:
        diag = Diagnostic(
            category=getattr(diagnostic, "category", DiagnosticCategory.TYPE_ERROR),
            message=getattr(diagnostic, "message", str(diagnostic)),
            span=getattr(diagnostic, "span", None),
            violated_rule=getattr(diagnostic, "violated_rule", None),
        )

    lines: List[str] = []
    primary = diag.get_primary_error()
    cat_name = diag.category.display_name() if hasattr(diag.category, "display_name") else str(diag.category)

    # 1. Location prefix
    loc_prefix = ""
    start_loc: Optional[SourceLocation] = None
    end_loc: Optional[SourceLocation] = None

    if diag.span is not None:
        start_loc = diag.span.start
        end_loc = diag.span.end

    file_prefix = f"{effective_filename}:" if effective_filename else ""
    if start_loc is not None and start_loc.line > 0 and start_loc.column > 0:
        loc_prefix = f"{file_prefix}{start_loc.line}:{start_loc.column}: "
    elif file_prefix:
        loc_prefix = f"{file_prefix} "

    lines.append(f"{loc_prefix}{cat_name}: {primary}")

    # 2. Source excerpt and caret line
    if source_text is not None and start_loc is not None and start_loc.line > 0:
        source_lines = source_text.splitlines()
        line_idx = start_loc.line - 1
        if 0 <= line_idx < len(source_lines):
            raw_line = source_lines[line_idx]
            lines.append(f"  {raw_line}")

            start_col = max(1, start_loc.column)
            if end_loc is not None and end_loc.line == start_loc.line and end_loc.column >= start_col:
                span_len = max(1, end_loc.column - start_col)
            else:
                span_len = 1

            caret_indent = " " * (2 + (start_col - 1))
            caret_str = "^" * span_len
            lines.append(f"{caret_indent}{caret_str}")

    # 3. Contextual note (WHY / WHEN)
    if diag.note:
        lines.append(f"  Note: {diag.note}")

    # 4. Deterministic help (HOW)
    if diag.help:
        lines.append(f"  Help: {diag.help}")

    # 5. Alternatives (HOW)
    if diag.alternatives:
        lines.append("  Alternatives:")
        for alt in diag.alternatives:
            lines.append(f"    - {alt}")

    return "\n".join(lines)
