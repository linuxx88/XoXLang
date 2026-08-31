"""Runtime representation and pure value semantics for XoX (X-o-X) prototype."""
from enum import Enum, auto

__all__ = [
    "UnknownValueError",
    "XoX",
    "xox_and",
    "xox_not",
    "xox_or",
]


class UnknownValueError(Exception):
    """Runtime error raised when attempting to unwrap XoX.UNKNOWN to a Boolean."""
    def __init__(self, message: str = "Cannot unwrap XoX.UNKNOWN to a Boolean value; Unknown is an unresolved 3-valued state"):
        super().__init__(message)


class XoX(Enum):
    """Runtime representation of 3-valued XoX logic (§3, §15, §20)."""
    FALSE = auto()
    TRUE = auto()
    UNKNOWN = auto()

    def __bool__(self) -> bool:
        """Anti-truthiness protection (§15, §20)."""
        raise TypeError(
            f"Cannot evaluate truthiness of XoX state '{self.name}'; XoX does not participate in implicit Boolean truthiness"
        )

    def unwrap_bool(self) -> bool:
        """Explicit lossless extraction from XoX to language/Python bool (§19, §20)."""
        if self is XoX.TRUE:
            return True
        if self is XoX.FALSE:
            return False
        raise UnknownValueError()

    @classmethod
    def from_bool(cls, value: bool) -> "XoX":
        """Explicit lossless conversion from language/Python bool to XoX (§19, §20)."""
        if type(value) is not bool:
            raise TypeError(f"XoX.from_bool() expected a bool instance, got {type(value).__name__} ({value!r})")
        return cls.TRUE if value else cls.FALSE


def xox_not(val: XoX) -> XoX:
    """Strong Kleene K3 logical NOT (§7)."""
    if not isinstance(val, XoX):
        raise TypeError(f"xox_not() expected a XoX instance, got {type(val).__name__} ({val!r})")
    if val is XoX.TRUE:
        return XoX.FALSE
    if val is XoX.FALSE:
        return XoX.TRUE
    return XoX.UNKNOWN


def xox_and(left: XoX, right: XoX) -> XoX:
    """Strong Kleene K3 logical AND (§7)."""
    if not isinstance(left, XoX) or not isinstance(right, XoX):
        raise TypeError(f"xox_and() expected XoX instances, got {type(left).__name__} and {type(right).__name__}")
    if left is XoX.FALSE or right is XoX.FALSE:
        return XoX.FALSE
    if left is XoX.TRUE and right is XoX.TRUE:
        return XoX.TRUE
    return XoX.UNKNOWN


def xox_or(left: XoX, right: XoX) -> XoX:
    """Strong Kleene K3 logical OR (§7)."""
    if not isinstance(left, XoX) or not isinstance(right, XoX):
        raise TypeError(f"xox_or() expected XoX instances, got {type(left).__name__} and {type(right).__name__}")
    if left is XoX.TRUE or right is XoX.TRUE:
        return XoX.TRUE
    if left is XoX.FALSE and right is XoX.FALSE:
        return XoX.FALSE
    return XoX.UNKNOWN


