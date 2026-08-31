"""Minimal executable slice of the canonical XoXLang semantic core.

Provides finite factive world classification into Inconsistent, Known, and Unknown,
while strictly enforcing the definedness precondition.
"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Generic, Optional, Sequence, TypeVar

T = TypeVar("T")


class SemanticClassification(Enum):
    """The exhaustive semantic partition for well-defined expressions over W_factive."""
    INCONSISTENT = auto()
    KNOWN = auto()
    UNKNOWN = auto()

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"SemanticClassification.{self.name}"


class DefinednessPreconditionError(Exception):
    """Raised when an expression has undefined semantic behavior on one or more factive trajectories."""
    def __init__(self, message: str = "Classification precondition failed: expression has undefined semantic behavior on at least one admissible history."):
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class SemanticOutcome(Generic[T]):
    """A semantic execution behavior on an admissible history.

    Represents either a defined observational behavior/value or an undefined behavior.
    """
    value: Optional[T] = None
    is_defined: bool = True

    @classmethod
    def defined(cls, value: T) -> "SemanticOutcome[T]":
        """Construct a defined semantic outcome with the given observable behavior/value."""
        return cls(value=value, is_defined=True)

    @classmethod
    def undefined(cls) -> "SemanticOutcome[T]":
        """Construct an outcome representing undefined semantic behavior."""
        return cls(value=None, is_defined=False)


def classify_factive_behaviors(
    behaviors: Sequence[SemanticOutcome[T]],
    equivalence_fn: Optional[Callable[[T, T], bool]] = None,
) -> SemanticClassification:
    """Classify a finite collection of factive execution behaviors over W_factive.

    Rules:
    1. Definedness Precondition: If any trajectory in W_factive has undefined semantic behavior,
       classification is refused and DefinednessPreconditionError is raised.
    2. Inconsistent: If W_factive is empty (no admissible histories), the state is Inconsistent.
    3. Known: If W_factive is non-empty, all trajectories are defined, and all resulting behaviors
       are observationally equivalent.
    4. Unknown: If W_factive is non-empty, all trajectories are defined, and at least two resulting
       behaviors are observationally distinguishable.
    """
    # 1. Inconsistent: Empty factive world space cannot produce a Known or Unknown judgment
    if not behaviors:
        return SemanticClassification.INCONSISTENT

    # 2. Definedness Precondition: Every admissible trajectory must be semantically defined
    for index, outcome in enumerate(behaviors):
        if not outcome.is_defined:
            raise DefinednessPreconditionError(
                f"Classification precondition failed: trajectory at index {index} has undefined semantic behavior in W_factive."
            )

    # 3. Observational Equivalence Check
    is_equivalent = equivalence_fn if equivalence_fn is not None else (lambda a, b: a == b)

    first_value = behaviors[0].value
    for outcome in behaviors[1:]:
        if not is_equivalent(first_value, outcome.value):  # type: ignore[arg-type]
            return SemanticClassification.UNKNOWN

    return SemanticClassification.KNOWN
