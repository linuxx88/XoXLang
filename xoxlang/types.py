"""Static type representations for XoX (X-o-X) prototype."""
from enum import Enum


class TypeKind(Enum):
    """Static logical truth types in XoX (§3)."""
    BOOL = "Bool"
    XOX = "XoX"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"TypeKind.{self.name}"


class ConditionalKind(Enum):
    """Post-type semantic conditional classification (§12, §19)."""
    BOOL = "Bool"
    XOX = "XoX"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"ConditionalKind.{self.name}"


# Type constants
BOOL = TypeKind.BOOL
XOX = TypeKind.XOX



