"""Experimental O0/SAFE Authority and Governance Extension for XoXLang.

This package implements context-bound capability envelopes, authority boundaries,
and policy governance (ResolutionToken, WorldStateAuthority, FallbackPolicyIdentity)
governing explicit collapse and authority replay protection.

Unidirectional dependency rule:
- experimental.safe depends on xoxlang (CORE_S1).
- xoxlang never depends on experimental.safe.
"""
from experimental.safe.authority import (
    FallbackPolicyIdentity,
    NO_FALLBACK,
    ResolutionToken,
    WorldStateAuthority,
    resolve_unwrap_or,
    resolve_xen_ignore,
)

__all__ = [
    "WorldStateAuthority",
    "FallbackPolicyIdentity",
    "NO_FALLBACK",
    "ResolutionToken",
    "resolve_unwrap_or",
    "resolve_xen_ignore",
]
