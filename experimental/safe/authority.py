"""Experimental O0/SAFE Authority and Governance Module.

Provides:
1. FallbackPolicyIdentity and NO_FALLBACK.
2. ResolutionToken capability bound to exact (ProvenanceSet, OperationType, WorldStateID, FallbackPolicyIdentity).
3. WorldStateAuthority host environment managing world states, constraints, and policy tokens.
4. resolve_unwrap_or and resolve_xen_ignore resolution gateways enforcing capability token verification.

Unidirectional Dependency Rule:
- experimental.safe depends on xoxlang (CORE_S1).
- xoxlang never depends on experimental.safe.
"""
import itertools
from typing import Any, Callable, Optional, Sequence, Tuple, Union

from xoxlang.core_semantics import DefinednessPreconditionError, SemanticOutcome
from xoxlang.identity import (
    AtomicFact,
    CompoundFact,
    ConstraintContentIdentity,
    DerivedProjectionFact,
    EvaluatorSemanticProfile,
    FactiveEvaluator,
    FactiveTrajectory,
    OntologicalConstraintToken,
    ProvenanceSet,
    UnknownValue,
    WorldStateID,
    _world_state_id_counter,
)
from xoxlang.runtime import XoX

_policy_id_counter = itertools.count(1)
_resolution_token_id_counter = itertools.count(1)


class FallbackPolicyIdentity:
    """An immutable canonical structural semantic identity of an authorized resolution fallback policy.

    Reuses the canonical semantic structural identity mechanism used by ConstraintContentIdentity.
    """
    __slots__ = ("_policy_id", "_structural_digest", "_referents", "_profile_id")

    def __init__(
        self,
        structural_digest: Optional[str] = None,
        referents: Optional[Sequence[Union[int, "AtomicFact", "CompoundFact"]]] = None,
        profile: Optional[Union[int, "EvaluatorSemanticProfile"]] = None,
    ) -> None:
        object.__setattr__(self, "_policy_id", next(_policy_id_counter))
        object.__setattr__(
            self,
            "_structural_digest",
            str(structural_digest) if structural_digest is not None else f"Policy_{self._policy_id}",
        )
        if referents is None:
            norm_refs = ()
        else:
            refs_list = []
            for r in referents:
                if isinstance(r, int):
                    refs_list.append(r)
                elif isinstance(r, (AtomicFact, CompoundFact)):
                    refs_list.append(r.identity)
                else:
                    raise TypeError(f"Referents must be int or fact instances, got {type(r).__name__}")
            norm_refs = tuple(refs_list)
        object.__setattr__(self, "_referents", norm_refs)

        if profile is None:
            p_id = None
        elif isinstance(profile, EvaluatorSemanticProfile):
            p_id = profile.profile_id
        elif isinstance(profile, int):
            p_id = profile
        else:
            raise TypeError(f"profile must be int or EvaluatorSemanticProfile, got {type(profile).__name__}")
        object.__setattr__(self, "_profile_id", p_id)

    @property
    def policy_id(self) -> int:
        return self._policy_id

    @property
    def structural_digest(self) -> str:
        return self._structural_digest

    @property
    def referents(self) -> Tuple[int, ...]:
        return self._referents

    @property
    def profile_id(self) -> Optional[int]:
        return self._profile_id

    def __copy__(self) -> "FallbackPolicyIdentity":
        return self

    def __deepcopy__(self, memo: Any) -> "FallbackPolicyIdentity":
        return self

    def __reduce__(self) -> Any:
        raise TypeError("FallbackPolicyIdentity serialization is unsupported; persistent or cross-process semantic identity is not defined")

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"FallbackPolicyIdentity attributes are immutable; cannot modify '{name}'")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"FallbackPolicyIdentity attributes are immutable; cannot delete '{name}'")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FallbackPolicyIdentity):
            return False
        return self._policy_id == other._policy_id

    def __hash__(self) -> int:
        return hash(self._policy_id)

    def __repr__(self) -> str:
        return f"FallbackPolicyIdentity(id={self._policy_id}, digest={self._structural_digest!r})"


NO_FALLBACK = FallbackPolicyIdentity(structural_digest="NO_FALLBACK")


class ResolutionToken:
    """An unforgeable authority capability permitting one exact resolution policy over one exact unresolved provenance set.

    Binds strictly to the 4-tuple:
    (ProvenanceSet, OperationType, WorldStateID, FallbackPolicyIdentity).
    Direct caller instantiation is prohibited; tokens are issued via WorldStateAuthority.
    """
    __slots__ = (
        "_provenance_set",
        "_operation_type",
        "_world_state_id",
        "_policy_id",
        "_token_id",
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise PermissionError(
            "Direct construction of ResolutionToken is prohibited; tokens must be issued by an authorized WorldStateAuthority."
        )

    @classmethod
    def _issue_from_authority(cls, *args: Any, **kwargs: Any) -> "ResolutionToken":
        raise PermissionError(
            "Direct invocation of ResolutionToken._issue_from_authority is prohibited; tokens must be issued via WorldStateAuthority."
        )

    @property
    def provenance_set(self) -> ProvenanceSet:
        """The exact ProvenanceSet bound to this token."""
        return self._provenance_set

    @property
    def operation_type(self) -> str:
        """The OperationType ('unwrap_or' or 'xen_ignore') bound to this token."""
        return self._operation_type

    @property
    def world_state_id(self) -> int:
        """The WorldStateID bound to this token."""
        return self._world_state_id

    @property
    def policy_id(self) -> int:
        """The FallbackPolicyIdentity ID bound to this token."""
        return self._policy_id

    @property
    def token_id(self) -> int:
        """Internal unique token capability identifier."""
        return self._token_id

    def matches(
        self,
        provenance_set: ProvenanceSet,
        operation_type: str,
        world_state_id: Union[int, "WorldStateID"],
        fallback_policy: Union[int, FallbackPolicyIdentity],
    ) -> bool:
        """Verify exact 4-tuple match."""
        if not isinstance(provenance_set, ProvenanceSet):
            return False
        w_id = world_state_id.state_id if isinstance(world_state_id, WorldStateID) else world_state_id
        pol_id = fallback_policy.policy_id if isinstance(fallback_policy, FallbackPolicyIdentity) else fallback_policy
        return (
            self._provenance_set == provenance_set
            and self._operation_type == str(operation_type)
            and self._world_state_id == w_id
            and self._policy_id == pol_id
        )

    def verify(
        self,
        provenance_set: ProvenanceSet,
        operation_type: str,
        world_state_id: Union[int, "WorldStateID"],
        fallback_policy: Union[int, FallbackPolicyIdentity],
    ) -> None:
        """Verify exact 4-tuple match or fail closed with DefinednessPreconditionError."""
        if not self.matches(provenance_set, operation_type, world_state_id, fallback_policy):
            w_id = world_state_id.state_id if isinstance(world_state_id, WorldStateID) else world_state_id
            pol_id = fallback_policy.policy_id if isinstance(fallback_policy, FallbackPolicyIdentity) else fallback_policy
            mismatches = []
            if not isinstance(provenance_set, ProvenanceSet) or self._provenance_set != provenance_set:
                mismatches.append(f"ProvenanceSet (expected {self._provenance_set!r}, got {provenance_set!r})")
            if self._operation_type != str(operation_type):
                mismatches.append(f"OperationType (expected {self._operation_type!r}, got {operation_type!r})")
            if self._world_state_id != w_id:
                mismatches.append(f"WorldStateID (expected {self._world_state_id}, got {w_id})")
            if self._policy_id != pol_id:
                mismatches.append(f"FallbackPolicyIdentity (expected {self._policy_id}, got {pol_id})")
            raise DefinednessPreconditionError(
                f"ResolutionToken mismatch: token authority does not match requested target on: {', '.join(mismatches)}."
            )

    def __copy__(self) -> "ResolutionToken":
        return self

    def __deepcopy__(self, memo: Any) -> "ResolutionToken":
        return self

    def __reduce__(self) -> Any:
        raise TypeError("ResolutionToken serialization is unsupported; persistent or cross-process semantic identity is not defined")

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"ResolutionToken attributes are immutable; cannot modify '{name}'")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"ResolutionToken attributes are immutable; cannot delete '{name}'")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ResolutionToken):
            return False
        return self._token_id == other._token_id

    def __hash__(self) -> int:
        return hash(self._token_id)

    def __repr__(self) -> str:
        return (
            f"ResolutionToken(provenance={self._provenance_set!r}, op={self._operation_type!r}, "
            f"world_state_id={self._world_state_id}, policy_id={self._policy_id})"
        )


class WorldStateAuthority:
    """Authoritative host environment responsible for establishing factive world states, authorized ontological constraints, and resolution policies."""
    __slots__ = ("_authority_id", "_authorized_constraints", "_authorized_resolutions", "_is_revoked")

    def __init__(
        self,
        authorized_constraints: Optional[Sequence[Union["ConstraintContentIdentity", int]]] = None,
        authorized_resolutions: Optional[Sequence[Tuple[Union["ProvenanceSet", Sequence[Union[int, "AtomicFact", "DerivedProjectionFact"]]], str, Union["FallbackPolicyIdentity", int]]]] = None,
    ) -> None:
        object.__setattr__(self, "_authority_id", next(_world_state_id_counter))
        object.__setattr__(self, "_is_revoked", False)

        if authorized_constraints is None:
            norm = ()
        else:
            c_list = []
            for c in authorized_constraints:
                if isinstance(c, ConstraintContentIdentity):
                    c_list.append(c.constraint_id)
                elif isinstance(c, int):
                    c_list.append(c)
                else:
                    raise TypeError(
                        f"Authorized constraints must be ConstraintContentIdentity or int, got {type(c).__name__}"
                    )
            norm = tuple(c_list)
        object.__setattr__(self, "_authorized_constraints", norm)

        if authorized_resolutions is None:
            norm_res = ()
        else:
            r_list = []
            for r in authorized_resolutions:
                if not (isinstance(r, tuple) and len(r) == 3):
                    raise TypeError("Each authorized resolution policy must be a 3-tuple (ProvenanceSet, OperationType, FallbackPolicyIdentity)")
                p_item, op_item, pol_item = r
                p_set = p_item if isinstance(p_item, ProvenanceSet) else ProvenanceSet(p_item)
                op_str = str(op_item)
                pol_id = pol_item.policy_id if isinstance(pol_item, FallbackPolicyIdentity) else pol_item
                r_list.append((p_set, op_str, pol_id))
            norm_res = tuple(r_list)
        object.__setattr__(self, "_authorized_resolutions", norm_res)

    @classmethod
    def create_host_authority(
        cls,
        authorized_constraints: Optional[Sequence[Union["ConstraintContentIdentity", int]]] = None,
        authorized_resolutions: Optional[Sequence[Any]] = None,
    ) -> "WorldStateAuthority":
        """Internal host boundary to instantiate an authoritative WorldStateAuthority."""
        return cls(authorized_constraints=authorized_constraints, authorized_resolutions=authorized_resolutions)

    @property
    def authority_id(self) -> int:
        """Unique identifier of this authority instance."""
        return self._authority_id

    @property
    def authorized_constraints(self) -> Tuple[int, ...]:
        """The sealed authorized constraint IDs held by this authority."""
        return self._authorized_constraints

    @property
    def authorized_resolutions(self) -> Tuple[Tuple["ProvenanceSet", str, int], ...]:
        """The sealed authorized resolution policies held by this authority."""
        return self._authorized_resolutions

    @property
    def is_revoked(self) -> bool:
        """Whether this authority instance has been revoked."""
        return self._is_revoked

    def revoke(self) -> None:
        """Revoke this authority instance, preventing any subsequent world state creation or token issuance."""
        object.__setattr__(self, "_is_revoked", True)

    def create_world_state(
        self,
        trajectories: Optional[Sequence[Union["FactiveTrajectory", Callable[..., SemanticOutcome]]]] = None,
        authorized_constraints: Optional[Sequence[Union["ConstraintContentIdentity", int]]] = None,
        authorized_resolutions: Optional[Sequence[Tuple[Union["ProvenanceSet", Sequence[Union[int, "AtomicFact", "DerivedProjectionFact"]]], str, Union["FallbackPolicyIdentity", int]]]] = None,
    ) -> "WorldStateID":
        """Authoritatively create a WorldStateID sealed with authorized ontological constraints and resolution policies."""
        if self._is_revoked:
            raise PermissionError("Cannot create world state from revoked WorldStateAuthority.")

        if authorized_constraints is None:
            target_constraints = self._authorized_constraints
        else:
            norm_list = []
            for c in authorized_constraints:
                c_id = c.constraint_id if isinstance(c, ConstraintContentIdentity) else c
                if c_id not in self._authorized_constraints:
                    raise DefinednessPreconditionError(
                        f"Cannot seal unauthorized constraint {c_id}: not permitted by WorldStateAuthority {self._authority_id}."
                    )
                norm_list.append(c_id)
            target_constraints = tuple(norm_list)

        if authorized_resolutions is None:
            target_resolutions = self._authorized_resolutions
        else:
            norm_res_list = []
            for r in authorized_resolutions:
                p_item, op_item, pol_item = r
                p_set = p_item if isinstance(p_item, ProvenanceSet) else ProvenanceSet(p_item)
                op_str = str(op_item)
                pol_id = pol_item.policy_id if isinstance(pol_item, FallbackPolicyIdentity) else pol_item
                res_tuple = (p_set, op_str, pol_id)
                if res_tuple not in self._authorized_resolutions:
                    raise DefinednessPreconditionError(
                        f"Cannot seal unauthorized resolution policy {res_tuple}: not permitted by WorldStateAuthority {self._authority_id}."
                    )
                norm_res_list.append(res_tuple)
            target_resolutions = tuple(norm_res_list)

        if trajectories is None:
            norm_trajectories = (FactiveTrajectory(),)
        else:
            norm_list_t = []
            for t in trajectories:
                if isinstance(t, FactiveTrajectory):
                    norm_list_t.append(t)
                elif callable(t):
                    norm_list_t.append(FactiveTrajectory(t))
                else:
                    raise TypeError(
                        f"Trajectories must be FactiveTrajectory instances or callables, got {type(t).__name__}"
                    )
            norm_trajectories = tuple(norm_list_t)

        ws = object.__new__(WorldStateID)
        object.__setattr__(ws, "_state_id", next(_world_state_id_counter))
        object.__setattr__(ws, "_trajectories", norm_trajectories)
        object.__setattr__(ws, "_authorized_constraints", target_constraints)
        object.__setattr__(ws, "_authorized_resolutions", target_resolutions)
        return ws

    def authorize_resolution(
        self,
        provenance_set: Union["ProvenanceSet", Sequence[Union[int, "AtomicFact", "DerivedProjectionFact"]]],
        operation_type: str,
        world_state: "WorldStateID",
        fallback_policy: Union[int, "FallbackPolicyIdentity"],
    ) -> "ResolutionToken":
        """Authoritatively issue a ResolutionToken for exact 4-tuple."""
        if self._is_revoked:
            raise PermissionError("Cannot issue ResolutionToken from revoked WorldStateAuthority.")

        if not isinstance(world_state, WorldStateID):
            raise TypeError(f"world_state must be WorldStateID, got {type(world_state).__name__}")

        p_set = provenance_set if isinstance(provenance_set, ProvenanceSet) else ProvenanceSet(provenance_set)
        op_type = str(operation_type)
        pol_id = fallback_policy.policy_id if isinstance(fallback_policy, FallbackPolicyIdentity) else fallback_policy

        target_tuple = (p_set, op_type, pol_id)
        if target_tuple not in self._authorized_resolutions or target_tuple not in world_state.authorized_resolutions:
            raise DefinednessPreconditionError(
                f"Cannot authorize resolution policy {target_tuple}: not authorized in WorldStateAuthority {self._authority_id} and WorldStateID {world_state.state_id}."
            )

        token = object.__new__(ResolutionToken)
        object.__setattr__(token, "_provenance_set", p_set)
        object.__setattr__(token, "_operation_type", op_type)
        object.__setattr__(token, "_world_state_id", world_state.state_id)
        object.__setattr__(token, "_policy_id", pol_id)
        object.__setattr__(token, "_token_id", next(_resolution_token_id_counter))
        return token

    def __copy__(self) -> "WorldStateAuthority":
        return self

    def __deepcopy__(self, memo: Any) -> "WorldStateAuthority":
        return self

    def __reduce__(self) -> Any:
        raise TypeError(
            "WorldStateAuthority serialization is unsupported; persistent or cross-process semantic authority is not defined"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_is_revoked" and not getattr(self, "_is_revoked", False):
            object.__setattr__(self, name, value)
            return
        raise AttributeError(f"WorldStateAuthority attributes are immutable; cannot modify '{name}'")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"WorldStateAuthority attributes are immutable; cannot delete '{name}'")

    def __repr__(self) -> str:
        return f"WorldStateAuthority(id={self._authority_id}, revoked={self._is_revoked})"


def resolve_unwrap_or(
    source_val: Any,
    fallback_callable: Callable[[], bool],
    token: Optional[ResolutionToken] = None,
    world_state: Optional[WorldStateID] = None,
    fallback_policy: Optional[Union[int, FallbackPolicyIdentity]] = None,
) -> bool:
    """Collapse an XoX or UnknownValue to bool, requiring ResolutionToken for Unknown with provenance."""
    if source_val is True or source_val is XoX.TRUE:
        return True
    if source_val is False or source_val is XoX.FALSE:
        return False
    if isinstance(source_val, UnknownValue):
        if not isinstance(token, ResolutionToken):
            raise DefinednessPreconditionError(
                f"Cannot unwrap Unknown with provenance without a valid ResolutionToken, got {type(token).__name__}."
            )
        if world_state is None or fallback_policy is None:
            raise DefinednessPreconditionError(
                "Cannot unwrap Unknown with provenance without a valid WorldStateID and FallbackPolicyIdentity."
            )
        if source_val.world_state_id != world_state.state_id:
            raise DefinednessPreconditionError(
                f"Unknown value world state mismatch: value is bound to WorldStateID {source_val.world_state_id}, but evaluation is in WorldStateID {world_state.state_id}."
            )
        token.verify(source_val.provenance_set, "unwrap_or", world_state, fallback_policy)
        # Lazy fallback execution
        return fallback_callable()
    if source_val is XoX.UNKNOWN:
        # Fallback executed lazily
        return fallback_callable()
    raise TypeError(f"Cannot unwrap non-XoX value {type(source_val).__name__}")


def resolve_xen_ignore(
    source_val: Any,
    token: Optional[ResolutionToken] = None,
    world_state: Optional[WorldStateID] = None,
) -> bool:
    """Acknowledge and abandon an Unknown branch, requiring ResolutionToken for Unknown with provenance."""
    if isinstance(source_val, UnknownValue):
        if not isinstance(token, ResolutionToken):
            raise DefinednessPreconditionError(
                f"Cannot ignore Unknown with provenance without a valid ResolutionToken, got {type(token).__name__}."
            )
        if world_state is None:
            raise DefinednessPreconditionError(
                "Cannot ignore Unknown with provenance without a valid WorldStateID."
            )
        if source_val.world_state_id != world_state.state_id:
            raise DefinednessPreconditionError(
                f"Unknown value world state mismatch: value is bound to WorldStateID {source_val.world_state_id}, but evaluation is in WorldStateID {world_state.state_id}."
            )
        token.verify(source_val.provenance_set, "xen_ignore", world_state, NO_FALLBACK)
        return True
    if source_val is XoX.UNKNOWN:
        return True
    raise TypeError(f"xen:ignore applies only to Unknown, got {type(source_val).__name__}")


__all__ = [
    "WorldStateAuthority",
    "FallbackPolicyIdentity",
    "NO_FALLBACK",
    "ResolutionToken",
    "resolve_unwrap_or",
    "resolve_xen_ignore",
]
