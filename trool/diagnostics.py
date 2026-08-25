"""Diagnostic definitions and categories for Trool prototype."""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional
from trool.tokens import SourceSpan


class DiagnosticCategory(Enum):
    """Canonical diagnostic categories defined in TROOL_SPEC.md §13."""
    SYNTAX_ERROR = auto()
    TYPE_ERROR = auto()
    EXHAUSTIVENESS_ERROR = auto()
    MISSING_RETURN_ERROR = auto()


@dataclass(frozen=True)
class Diagnostic:
    """Static compiler diagnostic structure."""
    category: DiagnosticCategory
    message: str
    span: Optional[SourceSpan] = None
    violated_rule: Optional[str] = None


class TypeDiagnosticError(Exception):
    """Static type error raised during semantic/type analysis (Phase 2)."""
    def __init__(self, message: str, span: Optional[SourceSpan] = None, violated_rule: Optional[str] = None):
        super().__init__(f"TypeError: {message}")
        self.message = message
        self.span = span
        self.violated_rule = violated_rule


class ExhaustivenessError(Exception):
    """Static exhaustiveness error raised during conditional analysis (Phase 3)."""
    def __init__(self, message: str, span: Optional[SourceSpan] = None, violated_rule: Optional[str] = None):
        super().__init__(f"ExhaustivenessError: {message}")
        self.message = message
        self.span = span
        self.violated_rule = violated_rule


class MissingReturnError(Exception):
    """Static missing return error raised during definite-return analysis (Phase 4)."""
    def __init__(self, message: str, span: Optional[SourceSpan] = None, violated_rule: Optional[str] = None):
        super().__init__(f"MissingReturnError: {message}")
        self.message = message
        self.span = span
        self.violated_rule = violated_rule
