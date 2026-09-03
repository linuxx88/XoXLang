"""Minimal executable slice of XoXLang fact identity and compound projection semantics.

Defines immutable atomic fact identities, fact references, persistent storage locations,
compound fact occurrences, semantic selectors, canonical paths, and derived projection facts.
"""
import itertools
from typing import Any, Callable, Optional, Sequence, Tuple, Union

from xoxlang.core_semantics import DefinednessPreconditionError, SemanticOutcome

_fact_id_counter = itertools.count(1)
_storage_id_counter = itertools.count(1)
_compound_id_counter = itertools.count(1)
_selector_id_counter = itertools.count(1)
_world_state_id_counter = itertools.count(1)
_witness_id_counter = itertools.count(1)
_trajectory_id_counter = itertools.count(1)
_profile_id_counter = itertools.count(1)
_constraint_id_counter = itertools.count(1)
_token_id_counter = itertools.count(1)
_provenance_id_counter = itertools.count(1)







class AtomicFact:
    """An immutable atomic unresolved fact occurrence with a unique semantic identity.

    Identity is determined strictly by an internally generated unique identifier,
    never by caller assignment, payload representation, or accidental value equality.
    """
    __slots__ = ("_identity", "_payload")

    def __init__(self, payload: Any = None) -> None:
        object.__setattr__(self, "_identity", next(_fact_id_counter))
        object.__setattr__(self, "_payload", payload)

    @property
    def identity(self) -> int:
        """Unique semantic identifier of this atomic fact occurrence."""
        return self._identity

    @property
    def payload(self) -> Any:
        """Descriptive occurrence payload (non-semantic)."""
        return self._payload

    def __copy__(self) -> "AtomicFact":
        return self

    def __deepcopy__(self, memo: Any) -> "AtomicFact":
        return self

    def __reduce__(self) -> Any:
        raise TypeError(
            "AtomicFact serialization is unsupported; persistent or cross-process semantic identity is not defined"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(
            f"AtomicFact attributes are immutable; cannot modify '{name}'"
        )

    def __delattr__(self, name: str) -> None:
        raise AttributeError(
            f"AtomicFact attributes are immutable; cannot delete '{name}'"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AtomicFact):
            return False
        return self._identity == other._identity

    def __hash__(self) -> int:
        return hash(self._identity)

    def __repr__(self) -> str:
        if self._payload is not None:
            return f"AtomicFact(identity={self._identity}, payload={self._payload!r})"
        return f"AtomicFact(identity={self._identity})"


class FactReference:
    """A reference designating an atomic fact identity.

    Copying or aliasing a reference preserves designation of the target fact identity.
    """
    __slots__ = ("_target",)

    def __init__(self, target: AtomicFact) -> None:
        if not isinstance(target, AtomicFact):
            raise TypeError(
                f"FactReference requires an AtomicFact instance, got {type(target).__name__}"
            )
        object.__setattr__(self, "_target", target)

    @property
    def target(self) -> AtomicFact:
        """The designated atomic fact occurrence."""
        return self._target

    @property
    def identity(self) -> int:
        """Return the designated fact identity."""
        return self._target.identity

    def resolve(self) -> AtomicFact:
        """Resolve the designated atomic fact occurrence."""
        return self._target

    def __copy__(self) -> "FactReference":
        return self

    def __deepcopy__(self, memo: Any) -> "FactReference":
        return self

    def __reduce__(self) -> Any:
        raise TypeError(
            "FactReference serialization is unsupported; persistent or cross-process semantic identity is not defined"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(
            f"FactReference attributes are immutable; cannot modify '{name}'"
        )

    def __delattr__(self, name: str) -> None:
        raise AttributeError(
            f"FactReference attributes are immutable; cannot delete '{name}'"
        )

    def __repr__(self) -> str:
        return f"FactReference(target={self._target!r})"


class StorageLocation:
    """A persistent mutable storage identity holding a binding to an atomic fact identity.

    Storage identity persists across rebinding operations, while previous and new
    bound facts remain distinct and immutable.
    """
    __slots__ = ("_storage_id", "_bound_fact")

    def __init__(self, initial_fact: AtomicFact) -> None:
        if not isinstance(initial_fact, AtomicFact):
            raise TypeError(
                f"StorageLocation requires an AtomicFact instance, got {type(initial_fact).__name__}"
            )
        object.__setattr__(self, "_storage_id", next(_storage_id_counter))
        object.__setattr__(self, "_bound_fact", initial_fact)

    @property
    def storage_id(self) -> int:
        """Unique persistent identifier of this storage location."""
        return self._storage_id

    @property
    def bound_fact(self) -> AtomicFact:
        """The atomic fact currently bound to this storage location."""
        return self._bound_fact

    def read(self) -> AtomicFact:
        """Observe the fact identity currently bound to this location."""
        return self._bound_fact

    def rebind(self, new_fact: AtomicFact) -> AtomicFact:
        """Rebind this storage location to a new atomic fact identity.

        Preserves storage identity while replacing the current fact binding.
        Returns the previously bound fact.
        """
        if not isinstance(new_fact, AtomicFact):
            raise TypeError(
                f"Rebinding requires an AtomicFact instance, got {type(new_fact).__name__}"
            )
        previous = self._bound_fact
        object.__setattr__(self, "_bound_fact", new_fact)
        return previous

    def __copy__(self) -> "StorageLocation":
        raise TypeError(
            "StorageLocation cannot be duplicated; mutable storage identity is unique and non-copyable"
        )

    def __deepcopy__(self, memo: Any) -> "StorageLocation":
        raise TypeError(
            "StorageLocation cannot be duplicated; mutable storage identity is unique and non-copyable"
        )

    def __reduce__(self) -> Any:
        raise TypeError(
            "StorageLocation serialization is unsupported; persistent or cross-process semantic identity is not defined"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(
            f"Direct assignment to StorageLocation attribute '{name}' is forbidden; use rebind() for fact updates"
        )

    def __delattr__(self, name: str) -> None:
        raise AttributeError(
            f"StorageLocation attributes are permanent; cannot delete '{name}'"
        )

    def __repr__(self) -> str:
        return f"StorageLocation(storage_id={self._storage_id}, bound_fact={self._bound_fact!r})"


class CompoundFact:
    """An immutable compound unresolved fact occurrence with a unique semantic identity.

    Identity is determined strictly by its internally generated unique identifier,
    never by caller assignment, internal structure, or payload equivalence.
    """
    __slots__ = ("_identity", "_payload")

    def __init__(self, payload: Any = None) -> None:
        object.__setattr__(self, "_identity", next(_compound_id_counter))
        object.__setattr__(self, "_payload", payload)

    @property
    def identity(self) -> int:
        """Unique semantic identifier of this compound fact occurrence."""
        return self._identity

    @property
    def payload(self) -> Any:
        """Descriptive occurrence payload (non-semantic)."""
        return self._payload

    def project(
        self,
        selector_or_path: Union["SemanticSelector", "CanonicalPath"],
        is_defined: bool = False,
    ) -> "DerivedProjectionFact":
        """Project a semantic selector or canonical path from this compound fact."""
        if isinstance(selector_or_path, SemanticSelector):
            path = CanonicalPath((selector_or_path,))
        elif isinstance(selector_or_path, CanonicalPath):
            path = selector_or_path
        else:
            raise TypeError(
                f"project requires SemanticSelector or CanonicalPath, got {type(selector_or_path).__name__}"
            )
        return DerivedProjectionFact(self, path, is_defined=is_defined)

    def __copy__(self) -> "CompoundFact":
        return self

    def __deepcopy__(self, memo: Any) -> "CompoundFact":
        return self

    def __reduce__(self) -> Any:
        raise TypeError(
            "CompoundFact serialization is unsupported; persistent or cross-process semantic identity is not defined"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(
            f"CompoundFact attributes are immutable; cannot modify '{name}'"
        )

    def __delattr__(self, name: str) -> None:
        raise AttributeError(
            f"CompoundFact attributes are immutable; cannot delete '{name}'"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CompoundFact):
            return False
        return self._identity == other._identity

    def __hash__(self) -> int:
        return hash(self._identity)

    def __repr__(self) -> str:
        if self._payload is not None:
            return f"CompoundFact(identity={self._identity}, payload={self._payload!r})"
        return f"CompoundFact(identity={self._identity})"


class SemanticSelector:
    """An opaque semantic field selector.

    Equality is determined strictly by its unique semantic identifier, never by
    syntactic or display name labels.
    """
    __slots__ = ("_selector_id", "_display_name")

    def __init__(self, display_name: str = "") -> None:
        object.__setattr__(self, "_selector_id", next(_selector_id_counter))
        object.__setattr__(self, "_display_name", str(display_name))

    @property
    def selector_id(self) -> int:
        """Unique identifier of this semantic field selector."""
        return self._selector_id

    @property
    def display_name(self) -> str:
        """Descriptive field label (non-semantic)."""
        return self._display_name

    def __copy__(self) -> "SemanticSelector":
        return self

    def __deepcopy__(self, memo: Any) -> "SemanticSelector":
        return self

    def __reduce__(self) -> Any:
        raise TypeError(
            "SemanticSelector serialization is unsupported; persistent or cross-process semantic identity is not defined"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(
            f"SemanticSelector attributes are immutable; cannot modify '{name}'"
        )

    def __delattr__(self, name: str) -> None:
        raise AttributeError(
            f"SemanticSelector attributes are immutable; cannot delete '{name}'"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemanticSelector):
            return False
        return self._selector_id == other._selector_id

    def __hash__(self) -> int:
        return hash(self._selector_id)

    def __repr__(self) -> str:
        if self._display_name:
            return f"SemanticSelector(id={self._selector_id}, name={self._display_name!r})"
        return f"SemanticSelector(id={self._selector_id})"


class CanonicalPath:
    """An immutable, canonical sequence of semantic field selectors."""
    __slots__ = ("_selectors",)

    def __init__(self, selectors: Sequence[SemanticSelector] = ()) -> None:
        for idx, s in enumerate(selectors):
            if not isinstance(s, SemanticSelector):
                raise TypeError(
                    f"CanonicalPath element at index {idx} must be a SemanticSelector, got {type(s).__name__}"
                )
        object.__setattr__(self, "_selectors", tuple(selectors))

    @property
    def selectors(self) -> Tuple[SemanticSelector, ...]:
        """Sequence of semantic field selectors forming this path."""
        return self._selectors

    def extend(
        self,
        selector_or_path: Union[SemanticSelector, "CanonicalPath", Sequence[SemanticSelector]],
    ) -> "CanonicalPath":
        """Extend this canonical path with a selector or path segment."""
        if isinstance(selector_or_path, SemanticSelector):
            return CanonicalPath(self._selectors + (selector_or_path,))
        elif isinstance(selector_or_path, CanonicalPath):
            return CanonicalPath(self._selectors + selector_or_path.selectors)
        elif isinstance(selector_or_path, (list, tuple)):
            return CanonicalPath(self._selectors + tuple(selector_or_path))
        raise TypeError(
            f"Cannot extend CanonicalPath with {type(selector_or_path).__name__}"
        )

    def __copy__(self) -> "CanonicalPath":
        return self

    def __deepcopy__(self, memo: Any) -> "CanonicalPath":
        return self

    def __reduce__(self) -> Any:
        raise TypeError(
            "CanonicalPath serialization is unsupported; persistent or cross-process semantic identity is not defined"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(
            f"CanonicalPath attributes are immutable; cannot modify '{name}'"
        )

    def __delattr__(self, name: str) -> None:
        raise AttributeError(
            f"CanonicalPath attributes are immutable; cannot delete '{name}'"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CanonicalPath):
            return False
        return self._selectors == other._selectors

    def __hash__(self) -> int:
        return hash(self._selectors)

    def __repr__(self) -> str:
        return f"CanonicalPath({list(self._selectors)!r})"


class DerivedProjectionFact:
    """An immutable derived fact occurrence representing a defined field projection.

    Identity is uniquely determined by the pair (root_compound_identity, canonical_path).
    Identity formation strictly requires prior verification that projection definedness
    holds across all admissible execution trajectories in W_factive.
    """
    __slots__ = ("_root_fact", "_path")

    def __init__(
        self,
        root_fact: CompoundFact,
        path: CanonicalPath,
        is_defined: bool = False,
        witness: Optional["DefinednessWitness"] = None,
        world_state_id: Optional[Union[int, "WorldStateID"]] = None,
    ) -> None:
        if not isinstance(root_fact, CompoundFact):
            raise TypeError(
                f"DerivedProjectionFact root_fact must be a CompoundFact, got {type(root_fact).__name__}"
            )
        if not isinstance(path, CanonicalPath):
            raise TypeError(
                f"DerivedProjectionFact path must be a CanonicalPath, got {type(path).__name__}"
            )
        if witness is not None:
            if not isinstance(witness, DefinednessWitness):
                raise TypeError(
                    f"witness must be a DefinednessWitness instance, got {type(witness).__name__}"
                )
            if world_state_id is None:
                raise ValueError("world_state_id is required when validating against a DefinednessWitness.")
            witness.verify(root_fact, path, world_state_id)
        elif not is_defined:
            raise DefinednessPreconditionError(
                "Cannot form derived projection fact identity: projection definedness has not been established across all admissible trajectories in W_factive."
            )
        object.__setattr__(self, "_root_fact", root_fact)
        object.__setattr__(self, "_path", path)

    @property
    def root_fact(self) -> CompoundFact:
        """The root compound fact occurrence."""
        return self._root_fact

    @property
    def path(self) -> CanonicalPath:
        """The canonical semantic projection path."""
        return self._path

    @property
    def identity(self) -> Tuple[int, Tuple[SemanticSelector, ...]]:
        """Composite semantic identity pair (root_fact_id, canonical_path)."""
        return (self._root_fact.identity, self._path.selectors)

    def project(
        self,
        selector: SemanticSelector,
        is_defined: bool = False,
        witness: Optional["DefinednessWitness"] = None,
        world_state_id: Optional[Union[int, "WorldStateID"]] = None,
    ) -> "DerivedProjectionFact":
        """Extend this projection with an additional semantic field selector."""
        new_path = self._path.extend(selector)
        return DerivedProjectionFact(
            self._root_fact, new_path, is_defined=is_defined, witness=witness, world_state_id=world_state_id
        )

    def __copy__(self) -> "DerivedProjectionFact":
        return self

    def __deepcopy__(self, memo: Any) -> "DerivedProjectionFact":
        return self

    def __reduce__(self) -> Any:
        raise TypeError(
            "DerivedProjectionFact serialization is unsupported; persistent or cross-process semantic identity is not defined"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(
            f"DerivedProjectionFact attributes are immutable; cannot modify '{name}'"
        )

    def __delattr__(self, name: str) -> None:
        raise AttributeError(
            f"DerivedProjectionFact attributes are immutable; cannot delete '{name}'"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DerivedProjectionFact):
            return False
        return self.identity == other.identity

    def __hash__(self) -> int:
        return hash(self.identity)

    def __repr__(self) -> str:
        return f"DerivedProjectionFact(root={self._root_fact!r}, path={self._path!r})"


class WorldStateID:
    """An immutable identifier for a specific factive context/world state, bound to its sealed trajectory universe.

    State mutations produce a new WorldStateID, rendering prior witnesses stale.
    Direct caller instantiation with authorized_constraints or authorized_resolutions is prohibited.
    """
    __slots__ = ("_state_id", "_trajectories", "_authorized_constraints", "_authorized_resolutions")

    def __init__(
        self,
        trajectories: Optional[Sequence[Union["FactiveTrajectory", Callable[..., SemanticOutcome]]]] = None,
        authorized_constraints: Optional[Sequence[Union["ConstraintContentIdentity", int]]] = None,
        authorized_resolutions: Optional[Sequence[Any]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        if authorized_constraints or authorized_resolutions or kwargs:
            raise PermissionError(
                "Direct construction of WorldStateID with authorized_constraints or authorized_resolutions is prohibited; authorized state sealing requires an authorized host environment."
            )

        object.__setattr__(self, "_state_id", next(_world_state_id_counter))
        if trajectories is None:
            norm = (FactiveTrajectory(),)
        else:
            norm_list = []
            for t in trajectories:
                if isinstance(t, FactiveTrajectory):
                    norm_list.append(t)
                elif callable(t):
                    norm_list.append(FactiveTrajectory(t))
                else:
                    raise TypeError(
                        f"Trajectories must be FactiveTrajectory instances or callables, got {type(t).__name__}"
                    )
            norm = tuple(norm_list)
        object.__setattr__(self, "_trajectories", norm)
        object.__setattr__(self, "_authorized_constraints", ())
        object.__setattr__(self, "_authorized_resolutions", ())

    @classmethod
    def create_authorized_state(cls, *args: Any, **kwargs: Any) -> "WorldStateID":
        """Authoritative creation boundary for WorldStateID sealed with authorized constraints."""
        raise PermissionError(
            "Direct invocation of WorldStateID.create_authorized_state is prohibited; authorized state sealing requires an authorized host environment."
        )

    @property
    def state_id(self) -> int:
        """Unique persistent identifier of this world state."""
        return self._state_id

    @property
    def trajectories(self) -> Tuple["FactiveTrajectory", ...]:
        """The sealed factive trajectory universe for this world state."""
        return self._trajectories

    @property
    def authorized_constraints(self) -> Tuple[int, ...]:
        """The sealed authorized constraint IDs for this world state."""
        return self._authorized_constraints

    @property
    def authorized_resolutions(self) -> Tuple[Tuple["ProvenanceSet", str, int], ...]:
        """The sealed authorized resolution policies for this world state."""
        return self._authorized_resolutions

    def create_evaluator(
        self, profile: Optional["EvaluatorSemanticProfile"] = None
    ) -> "FactiveEvaluator":
        """Create an authorized FactiveEvaluator for this world state."""
        evaluator = object.__new__(FactiveEvaluator)
        object.__setattr__(evaluator, "_world_state", self)
        object.__setattr__(
            evaluator,
            "_profile",
            profile if profile is not None else EvaluatorSemanticProfile(),
        )
        return evaluator

    def __copy__(self) -> "WorldStateID":
        return self

    def __deepcopy__(self, memo: Any) -> "WorldStateID":
        return self

    def __reduce__(self) -> Any:
        raise TypeError(
            "WorldStateID serialization is unsupported; persistent or cross-process semantic identity is not defined"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"WorldStateID attributes are immutable; cannot modify '{name}'")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"WorldStateID attributes are immutable; cannot delete '{name}'")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WorldStateID):
            return False
        return self._state_id == other._state_id

    def __hash__(self) -> int:
        return hash(self._state_id)

    def __repr__(self) -> str:
        return f"WorldStateID(id={self._state_id})"


class DefinednessWitness:
    """An unforgeable evaluator-issued capability certifying definedness only.

    Binds strictly to (RootID, SemanticPath, WorldStateID).
    Holds zero authority to restrict W_factive or create ontological constraints.
    """
    __slots__ = ("_root_id", "_semantic_path", "_world_state_id", "_witness_id")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise PermissionError(
            "Direct construction of DefinednessWitness is prohibited; witnesses must be issued by an authorized factive evaluator via certify_definedness()."
        )

    @classmethod
    def _issue_from_evaluator(cls, *args: Any, **kwargs: Any) -> "DefinednessWitness":
        """Internal evaluator issuance boundary is prohibited; witnesses are issued via certify_definedness()."""
        raise PermissionError(
            "Direct invocation of DefinednessWitness._issue_from_evaluator is prohibited; witnesses must be issued by an authorized factive evaluator via certify_definedness()."
        )

    @property
    def root_id(self) -> int:
        """The RootID bound to this witness."""
        return self._root_id

    @property
    def semantic_path(self) -> Tuple[SemanticSelector, ...]:
        """The SemanticPath bound to this witness."""
        return self._semantic_path

    @property
    def world_state_id(self) -> int:
        """The WorldStateID bound to this witness."""
        return self._world_state_id

    @property
    def witness_id(self) -> int:
        """Internal unique witness capability token."""
        return self._witness_id

    def matches(
        self,
        root_id: Union[int, CompoundFact, AtomicFact],
        semantic_path: Union[CanonicalPath, Tuple[SemanticSelector, ...]],
        world_state_id: Union[int, WorldStateID],
    ) -> bool:
        """Verify exact 3-tuple binding match."""
        r_id = root_id.identity if isinstance(root_id, (CompoundFact, AtomicFact)) else root_id
        path_tuple = semantic_path.selectors if isinstance(semantic_path, CanonicalPath) else semantic_path
        w_id = world_state_id.state_id if isinstance(world_state_id, WorldStateID) else world_state_id
        return (self._root_id == r_id and self._semantic_path == path_tuple and self._world_state_id == w_id)

    def verify(
        self,
        root_id: Union[int, CompoundFact, AtomicFact],
        semantic_path: Union[CanonicalPath, Tuple[SemanticSelector, ...]],
        world_state_id: Union[int, WorldStateID],
    ) -> None:
        """Verify exact match or fail closed with DefinednessPreconditionError."""
        if not self.matches(root_id, semantic_path, world_state_id):
            raise DefinednessPreconditionError(
                f"DefinednessWitness mismatch: witness issued for (root_id={self._root_id}, "
                f"path={self._semantic_path!r}, world_state_id={self._world_state_id}) "
                f"does not match requested target."
            )

    def __copy__(self) -> "DefinednessWitness":
        return self

    def __deepcopy__(self, memo: Any) -> "DefinednessWitness":
        return self

    def __reduce__(self) -> Any:
        raise TypeError(
            "DefinednessWitness serialization is unsupported; persistent or cross-process semantic identity is not defined"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"DefinednessWitness attributes are immutable; cannot modify '{name}'")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"DefinednessWitness attributes are immutable; cannot delete '{name}'")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DefinednessWitness):
            return False
        return self._witness_id == other._witness_id

    def __hash__(self) -> int:
        return hash(self._witness_id)

    def __repr__(self) -> str:
        return f"DefinednessWitness(root_id={self._root_id}, path={self._semantic_path!r}, world_state_id={self._world_state_id})"


class FactiveTrajectory:
    """An immutable factive execution trajectory within a world state."""
    __slots__ = ("_trajectory_id", "_resolver")

    def __init__(
        self,
        resolver: Optional[Callable[[Union[int, CompoundFact, AtomicFact], Union[CanonicalPath, Tuple[SemanticSelector, ...]]], SemanticOutcome]] = None,
    ) -> None:
        object.__setattr__(self, "_trajectory_id", next(_trajectory_id_counter))
        object.__setattr__(self, "_resolver", resolver)

    @property
    def trajectory_id(self) -> int:
        return self._trajectory_id

    def evaluate(
        self,
        root: Union[int, CompoundFact, AtomicFact],
        path: Union[CanonicalPath, Tuple[SemanticSelector, ...]],
    ) -> SemanticOutcome:
        if self._resolver is not None:
            return self._resolver(root, path)
        return SemanticOutcome.defined(None)

    def __repr__(self) -> str:
        return f"FactiveTrajectory(id={self._trajectory_id})"


class EvaluatorSemanticProfile:
    """An immutable, closed semantic profile identity.

    Defines the closed evaluation environment (transitive closure of DSDG rules).
    Distinct profile identities never mutate; ecosystem evolution produces distinct profile IDs.
    """
    __slots__ = ("_profile_id", "_label")

    def __init__(
        self,
        label: Optional[str] = None,
    ) -> None:
        object.__setattr__(self, "_profile_id", next(_profile_id_counter))
        object.__setattr__(
            self,
            "_label",
            str(label) if label is not None else f"Profile_{self._profile_id}",
        )

    @property
    def profile_id(self) -> int:
        """Unique persistent identifier of this evaluator semantic profile."""
        return self._profile_id

    @property
    def label(self) -> str:
        """Descriptive label for this profile."""
        return self._label

    def __copy__(self) -> "EvaluatorSemanticProfile":
        return self

    def __deepcopy__(self, memo: Any) -> "EvaluatorSemanticProfile":
        return self

    def __reduce__(self) -> Any:
        raise TypeError(
            "EvaluatorSemanticProfile serialization is unsupported; persistent or cross-process semantic identity is not defined"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"EvaluatorSemanticProfile attributes are immutable; cannot modify '{name}'")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"EvaluatorSemanticProfile attributes are immutable; cannot delete '{name}'")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EvaluatorSemanticProfile):
            return False
        return self._profile_id == other._profile_id

    def __hash__(self) -> int:
        return hash(self._profile_id)

    def __repr__(self) -> str:
        return f"EvaluatorSemanticProfile(id={self._profile_id}, label={self._label!r})"


class ConstraintContentIdentity:
    """An immutable canonical structural semantic identity of an authorized constraint.

    Identifies the exact canonical structural AST with resolved referents and operand order.
    Logical equivalence alone does not authorize constraint substitution.
    """
    __slots__ = ("_constraint_id", "_structural_digest")

    def __init__(
        self,
        structural_digest: Optional[str] = None,
    ) -> None:
        object.__setattr__(self, "_constraint_id", next(_constraint_id_counter))
        object.__setattr__(
            self,
            "_structural_digest",
            str(structural_digest)
            if structural_digest is not None
            else f"Constraint_{self._constraint_id}",
        )

    @property
    def constraint_id(self) -> int:
        """Unique persistent identifier of this canonical constraint identity."""
        return self._constraint_id

    @property
    def structural_digest(self) -> str:
        """Canonical semantic structure digest."""
        return self._structural_digest

    def __copy__(self) -> "ConstraintContentIdentity":
        return self

    def __deepcopy__(self, memo: Any) -> "ConstraintContentIdentity":
        return self

    def __reduce__(self) -> Any:
        raise TypeError(
            "ConstraintContentIdentity serialization is unsupported; persistent or cross-process semantic identity is not defined"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"ConstraintContentIdentity attributes are immutable; cannot modify '{name}'")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"ConstraintContentIdentity attributes are immutable; cannot delete '{name}'")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ConstraintContentIdentity):
            return False
        return self._constraint_id == other._constraint_id

    def __hash__(self) -> int:
        return hash(self._constraint_id)

    def __repr__(self) -> str:
        return f"ConstraintContentIdentity(id={self._constraint_id}, digest={self._structural_digest!r})"


class OntologicalConstraintToken:
    """An unforgeable evaluator-issued capability authorizing exactly one hard constraint to restrict W_factive.

    Binds strictly to the 5-tuple:
    (RootID, SemanticPath, WorldStateID, EvaluatorSemanticProfile, ConstraintContentIdentity).
    Non-inheritable across roots, paths, world states, evaluator profiles, or constraint identities.
    Does not prove empirical truth; authorizes participation in defining W_factive.
    """
    __slots__ = (
        "_root_id",
        "_semantic_path",
        "_world_state_id",
        "_profile_id",
        "_constraint_id",
        "_token_id",
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise PermissionError(
            "Direct construction of OntologicalConstraintToken is prohibited; tokens must be issued by an authorized factive evaluator via authorize_ontological_constraint()."
        )

    @classmethod
    def _issue_from_evaluator(cls, *args: Any, **kwargs: Any) -> "OntologicalConstraintToken":
        """Internal evaluator issuance boundary is prohibited; tokens are issued via authorize_ontological_constraint()."""
        raise PermissionError(
            "Direct invocation of OntologicalConstraintToken._issue_from_evaluator is prohibited; tokens must be issued by an authorized factive evaluator via authorize_ontological_constraint()."
        )

    @property
    def root_id(self) -> int:
        """The RootID bound to this token."""
        return self._root_id

    @property
    def semantic_path(self) -> Tuple[SemanticSelector, ...]:
        """The SemanticPath bound to this token."""
        return self._semantic_path

    @property
    def world_state_id(self) -> int:
        """The WorldStateID bound to this token."""
        return self._world_state_id

    @property
    def profile_id(self) -> int:
        """The EvaluatorSemanticProfile ID bound to this token."""
        return self._profile_id

    @property
    def constraint_id(self) -> int:
        """The ConstraintContentIdentity ID bound to this token."""
        return self._constraint_id

    @property
    def token_id(self) -> int:
        """Internal unique token capability token."""
        return self._token_id

    def matches(
        self,
        root_id: Union[int, CompoundFact, AtomicFact],
        semantic_path: Union[CanonicalPath, Tuple[SemanticSelector, ...]],
        world_state_id: Union[int, WorldStateID],
        profile: Union[int, EvaluatorSemanticProfile],
        constraint_identity: Union[int, ConstraintContentIdentity],
    ) -> bool:
        """Verify exact 5-tuple binding match."""
        r_id = root_id.identity if isinstance(root_id, (CompoundFact, AtomicFact)) else root_id
        path_tuple = semantic_path.selectors if isinstance(semantic_path, CanonicalPath) else semantic_path
        w_id = world_state_id.state_id if isinstance(world_state_id, WorldStateID) else world_state_id
        p_id = profile.profile_id if isinstance(profile, EvaluatorSemanticProfile) else profile
        c_id = (
            constraint_identity.constraint_id
            if isinstance(constraint_identity, ConstraintContentIdentity)
            else constraint_identity
        )
        return (
            self._root_id == r_id
            and self._semantic_path == path_tuple
            and self._world_state_id == w_id
            and self._profile_id == p_id
            and self._constraint_id == c_id
        )

    def verify(
        self,
        root_id: Union[int, CompoundFact, AtomicFact],
        semantic_path: Union[CanonicalPath, Tuple[SemanticSelector, ...]],
        world_state_id: Union[int, WorldStateID],
        profile: Union[int, EvaluatorSemanticProfile],
        constraint_identity: Union[int, ConstraintContentIdentity],
    ) -> None:
        """Verify exact 5-tuple match or fail closed with DefinednessPreconditionError."""
        if not self.matches(root_id, semantic_path, world_state_id, profile, constraint_identity):
            r_id = root_id.identity if isinstance(root_id, (CompoundFact, AtomicFact)) else root_id
            path_tuple = semantic_path.selectors if isinstance(semantic_path, CanonicalPath) else semantic_path
            w_id = world_state_id.state_id if isinstance(world_state_id, WorldStateID) else world_state_id
            p_id = profile.profile_id if isinstance(profile, EvaluatorSemanticProfile) else profile
            c_id = (
                constraint_identity.constraint_id
                if isinstance(constraint_identity, ConstraintContentIdentity)
                else constraint_identity
            )
            mismatches = []
            if self._root_id != r_id:
                mismatches.append(f"RootID (expected {self._root_id}, got {r_id})")
            if self._semantic_path != path_tuple:
                mismatches.append(f"SemanticPath (expected {self._semantic_path!r}, got {path_tuple!r})")
            if self._world_state_id != w_id:
                mismatches.append(f"WorldStateID (expected {self._world_state_id}, got {w_id})")
            if self._profile_id != p_id:
                mismatches.append(f"EvaluatorSemanticProfile (expected {self._profile_id}, got {p_id})")
            if self._constraint_id != c_id:
                mismatches.append(f"ConstraintContentIdentity (expected {self._constraint_id}, got {c_id})")
            raise DefinednessPreconditionError(
                f"OntologicalConstraintToken mismatch: token authority does not match requested target on: {', '.join(mismatches)}."
            )

    def __copy__(self) -> "OntologicalConstraintToken":
        return self

    def __deepcopy__(self, memo: Any) -> "OntologicalConstraintToken":
        return self

    def __reduce__(self) -> Any:
        raise TypeError(
            "OntologicalConstraintToken serialization is unsupported; persistent or cross-process semantic identity is not defined"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"OntologicalConstraintToken attributes are immutable; cannot modify '{name}'")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"OntologicalConstraintToken attributes are immutable; cannot delete '{name}'")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, OntologicalConstraintToken):
            return False
        return self._token_id == other._token_id

    def __hash__(self) -> int:
        return hash(self._token_id)

    def __repr__(self) -> str:
        return (
            f"OntologicalConstraintToken(root_id={self._root_id}, path={self._semantic_path!r}, "
            f"world_state_id={self._world_state_id}, profile_id={self._profile_id}, "
            f"constraint_id={self._constraint_id})"
        )


class FactiveEvaluator:
    """Trusted factive evaluator managing trajectory space and certifying definedness for a specific WorldStateID.

    Direct caller instantiation is prohibited; evaluators are created via WorldStateID.create_evaluator().
    """
    __slots__ = ("_world_state", "_profile")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise PermissionError(
            "Direct construction of FactiveEvaluator is prohibited; obtain an evaluator via WorldStateID.create_evaluator()."
        )

    @classmethod
    def _create_from_world_state(cls, *args: Any, **kwargs: Any) -> "FactiveEvaluator":
        raise PermissionError("Direct invocation is prohibited; create evaluators via WorldStateID.create_evaluator().")

    @property
    def world_state(self) -> WorldStateID:
        """The authoritative WorldStateID managed by this evaluator."""
        return self._world_state

    @property
    def profile(self) -> EvaluatorSemanticProfile:
        """The active EvaluatorSemanticProfile of this evaluator."""
        return self._profile

    @property
    def trajectories(self) -> Tuple[FactiveTrajectory, ...]:
        """Admissible factive execution trajectories sealed in this world state."""
        return self._world_state.trajectories

    def certify_definedness(
        self,
        root: Union[int, CompoundFact, AtomicFact],
        path: Union[CanonicalPath, Tuple[SemanticSelector, ...]],
    ) -> DefinednessWitness:
        """Evaluate the fact projection across all factive trajectories in this world state and issue a witness."""
        trajs = self._world_state.trajectories
        if not trajs:
            raise DefinednessPreconditionError(
                "Cannot certify definedness over an empty world space: vacuous truth has zero epistemic authority."
            )

        for idx, traj in enumerate(trajs):
            outcome = traj.evaluate(root, path)
            if not getattr(outcome, "is_defined", True):
                raise DefinednessPreconditionError(
                    f"Cannot certify definedness: trajectory at index {idx} has undefined semantic behavior in W_factive."
                )

        # Normalize root
        if isinstance(root, (CompoundFact, AtomicFact)):
            r_id = root.identity
        elif isinstance(root, int):
            r_id = root
        else:
            raise TypeError(f"root must be int, CompoundFact, or AtomicFact, got {type(root).__name__}")

        # Normalize path
        if isinstance(path, CanonicalPath):
            path_tuple = path.selectors
        elif isinstance(path, tuple) and all(isinstance(s, SemanticSelector) for s in path):
            path_tuple = path
        else:
            raise TypeError("path must be CanonicalPath or tuple of SemanticSelectors")

        witness = object.__new__(DefinednessWitness)
        object.__setattr__(witness, "_root_id", r_id)
        object.__setattr__(witness, "_semantic_path", path_tuple)
        object.__setattr__(witness, "_world_state_id", self._world_state.state_id)
        object.__setattr__(witness, "_witness_id", next(_witness_id_counter))
        return witness

    def authorize_ontological_constraint(
        self,
        root: Union[int, CompoundFact, AtomicFact],
        path: Union[CanonicalPath, Tuple[SemanticSelector, ...]],
        constraint_identity: Union[int, ConstraintContentIdentity],
        profile: Optional[Union[int, EvaluatorSemanticProfile]] = None,
    ) -> OntologicalConstraintToken:
        """Issue an OntologicalConstraintToken authorizing exactly one hard constraint to restrict W_factive."""
        active_profile = profile if profile is not None else self._profile
        p_id = (
            active_profile.profile_id
            if isinstance(active_profile, EvaluatorSemanticProfile)
            else active_profile
        )
        if p_id != self._profile.profile_id:
            raise DefinednessPreconditionError(
                f"Cannot authorize constraint under mismatched profile: evaluator is bound to profile {self._profile.profile_id}, got {p_id}."
            )

        c_id = (
            constraint_identity.constraint_id
            if isinstance(constraint_identity, ConstraintContentIdentity)
            else constraint_identity
        )
        if c_id not in self._world_state.authorized_constraints:
            raise DefinednessPreconditionError(
                f"Cannot authorize constraint {c_id}: constraint is not authorized in WorldStateID {self._world_state.state_id}."
            )

        # Normalize root
        if isinstance(root, (CompoundFact, AtomicFact)):
            r_id = root.identity
        elif isinstance(root, int):
            r_id = root
        else:
            raise TypeError(f"root must be int, CompoundFact, or AtomicFact, got {type(root).__name__}")

        # Normalize path
        if isinstance(path, CanonicalPath):
            path_tuple = path.selectors
        elif isinstance(path, tuple) and all(isinstance(s, SemanticSelector) for s in path):
            path_tuple = path
        else:
            raise TypeError("path must be CanonicalPath or tuple of SemanticSelectors")

        token = object.__new__(OntologicalConstraintToken)
        object.__setattr__(token, "_root_id", r_id)
        object.__setattr__(token, "_semantic_path", path_tuple)
        object.__setattr__(token, "_world_state_id", self._world_state.state_id)
        object.__setattr__(token, "_profile_id", p_id)
        object.__setattr__(token, "_constraint_id", c_id)
        object.__setattr__(token, "_token_id", next(_token_id_counter))
        return token

    def evaluate_projection(
        self,
        root: Union[int, CompoundFact, AtomicFact],
        path: Optional[Union[CanonicalPath, Tuple[SemanticSelector, ...]]] = None,
    ) -> Union[Any, "UnknownValue"]:
        """Evaluate fact projection across trajectories, returning authentic UnknownValue on genuine variance."""
        trajs = self._world_state.trajectories
        if not trajs:
            raise DefinednessPreconditionError(
                "Cannot evaluate over an empty world space: vacuous truth has zero epistemic authority."
            )

        if isinstance(root, (CompoundFact, AtomicFact)):
            r_id = root.identity
        elif isinstance(root, int):
            r_id = root
        else:
            raise TypeError(f"root must be int, CompoundFact, or AtomicFact, got {type(root).__name__}")

        if path is None:
            path_tuple = ()
        elif isinstance(path, CanonicalPath):
            path_tuple = path.selectors
        elif isinstance(path, tuple) and all(isinstance(s, SemanticSelector) for s in path):
            path_tuple = path
        else:
            raise TypeError("path must be CanonicalPath or tuple of SemanticSelectors")

        outcomes = []
        for idx, traj in enumerate(trajs):
            outcome = traj.evaluate(root, path_tuple)
            if not getattr(outcome, "is_defined", True):
                raise DefinednessPreconditionError(
                    f"Cannot evaluate: trajectory at index {idx} has undefined semantic behavior in W_factive."
                )
            outcomes.append(outcome.value)

        first_val = outcomes[0]
        if all(val == first_val for val in outcomes[1:]):
            return first_val

        # Distinguishable outcomes -> Authentic UnknownValue bound to this WorldStateID
        prov = ProvenanceSet([r_id])
        val = object.__new__(UnknownValue)
        object.__setattr__(val, "_provenance_set", prov)
        object.__setattr__(val, "_world_state_id", self._world_state.state_id)
        return val






def certify_factive_definedness(
    evaluator: FactiveEvaluator,
    root: Union[int, CompoundFact, AtomicFact],
    path: Union[CanonicalPath, Tuple[SemanticSelector, ...]],
) -> DefinednessWitness:
    """Factive evaluator issuance boundary for DefinednessWitness.

    Requires an authorized FactiveEvaluator to evaluate and certify definedness across W_factive.
    Arbitrary caller-provided behavior lists or forged evaluators are strictly rejected.
    """
    if not isinstance(evaluator, FactiveEvaluator):
        raise TypeError(
            f"certify_factive_definedness requires a trusted FactiveEvaluator instance, got {type(evaluator).__name__}"
        )
    return evaluator.certify_definedness(root, path)


def authorize_ontological_constraint(
    evaluator: FactiveEvaluator,
    root: Union[int, CompoundFact, AtomicFact],
    path: Union[CanonicalPath, Tuple[SemanticSelector, ...]],
    constraint_identity: Union[int, ConstraintContentIdentity],
    profile: Optional[Union[int, EvaluatorSemanticProfile]] = None,
) -> OntologicalConstraintToken:
    """Factive evaluator issuance boundary for OntologicalConstraintToken.

    Requires an authorized FactiveEvaluator to issue an OntologicalConstraintToken for exact 5-tuple.
    Arbitrary caller construction without evaluator capability is strictly rejected.
    """
    if not isinstance(evaluator, FactiveEvaluator):
        raise TypeError(
            f"authorize_ontological_constraint requires a trusted FactiveEvaluator instance, got {type(evaluator).__name__}"
        )
    return evaluator.authorize_ontological_constraint(
        root, path, constraint_identity, profile=profile
    )


class ProvenanceSet:
    """An immutable non-empty set of authentic unresolved fact identities.

    Originates strictly from trusted factive evaluation over authentic unresolved facts.
    """
    __slots__ = ("_facts",)

    def __init__(
        self,
        facts: Sequence[Union[int, "AtomicFact", "CompoundFact", "DerivedProjectionFact"]],
    ) -> None:
        if not facts:
            raise ValueError("ProvenanceSet cannot be empty; Unknown must carry non-empty unresolved provenance.")
        norm_list = []
        for f in facts:
            if isinstance(f, int):
                norm_list.append(f)
            elif isinstance(f, (AtomicFact, CompoundFact, DerivedProjectionFact)):
                norm_list.append(f.identity)
            else:
                raise TypeError(f"Provenance elements must be int, AtomicFact, CompoundFact, or DerivedProjectionFact, got {type(f).__name__}")
        norm_tuple = tuple(sorted(set(norm_list)))
        if not norm_tuple:
            raise ValueError("ProvenanceSet cannot be empty.")
        object.__setattr__(self, "_facts", norm_tuple)


    @property
    def facts(self) -> Tuple[int, ...]:
        """Canonical sorted tuple of fact identities in this provenance set."""
        return self._facts

    def union(self, other: "ProvenanceSet") -> "ProvenanceSet":
        """Compute the exact set union of two provenance sets."""
        if not isinstance(other, ProvenanceSet):
            raise TypeError(f"Union requires ProvenanceSet, got {type(other).__name__}")
        combined = set(self._facts) | set(other._facts)
        return ProvenanceSet(tuple(combined))

    def __or__(self, other: "ProvenanceSet") -> "ProvenanceSet":
        return self.union(other)

    def __len__(self) -> int:
        return len(self._facts)

    def __iter__(self) -> Any:
        return iter(self._facts)

    def __contains__(self, item: Any) -> bool:
        if isinstance(item, (AtomicFact, DerivedProjectionFact)):
            return item.identity in self._facts
        return item in self._facts

    def is_subset(self, other: "ProvenanceSet") -> bool:
        if not isinstance(other, ProvenanceSet):
            raise TypeError(f"is_subset requires ProvenanceSet, got {type(other).__name__}")
        return set(self._facts).issubset(set(other._facts))

    def __copy__(self) -> "ProvenanceSet":
        return self

    def __deepcopy__(self, memo: Any) -> "ProvenanceSet":
        return self

    def __reduce__(self) -> Any:
        raise TypeError("ProvenanceSet serialization is unsupported; persistent or cross-process semantic identity is not defined")

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"ProvenanceSet attributes are immutable; cannot modify '{name}'")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"ProvenanceSet attributes are immutable; cannot delete '{name}'")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ProvenanceSet):
            return False
        return self._facts == other._facts

    def __hash__(self) -> int:
        return hash(self._facts)

    def __repr__(self) -> str:
        return f"ProvenanceSet({list(self._facts)})"


class UnknownValue:
    """An authentic Unknown semantic outcome carrying an immutable non-empty ProvenanceSet bound to a specific WorldStateID.

    Direct caller instantiation is prohibited; UnknownValue originates exclusively from trusted factive evaluation or K3 propagation.
    """
    __slots__ = ("_provenance_set", "_world_state_id")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise PermissionError(
            "Direct construction of UnknownValue is prohibited; authentic Unknown values must originate from trusted factive evaluation."
        )

    @property
    def provenance_set(self) -> ProvenanceSet:
        return self._provenance_set

    @property
    def world_state_id(self) -> int:
        return self._world_state_id

    def __copy__(self) -> "UnknownValue":
        return self

    def __deepcopy__(self, memo: Any) -> "UnknownValue":
        return self

    def __reduce__(self) -> Any:
        raise TypeError("UnknownValue serialization is unsupported; persistent or cross-process semantic identity is not defined")

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"UnknownValue attributes are immutable; cannot modify '{name}'")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"UnknownValue attributes are immutable; cannot delete '{name}'")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UnknownValue):
            return False
        return self._provenance_set == other._provenance_set and self._world_state_id == other._world_state_id

    def __hash__(self) -> int:
        return hash((self._provenance_set, self._world_state_id))

    def __repr__(self) -> str:
        return f"Unknown[{self._provenance_set}, ws={self._world_state_id}]"


def _create_propagated_unknown(provenance_set: ProvenanceSet, world_state_id: int) -> UnknownValue:
    val = object.__new__(UnknownValue)
    object.__setattr__(val, "_provenance_set", provenance_set)
    object.__setattr__(val, "_world_state_id", world_state_id)
    return val


def k3_not_with_provenance(val: Any) -> Any:
    """Strong Kleene K3 logical NOT with provenance preservation."""
    from xoxlang.runtime import XoX
    if isinstance(val, UnknownValue):
        return _create_propagated_unknown(val.provenance_set, val.world_state_id)
    if val is True or val is XoX.TRUE:
        return XoX.FALSE
    if val is False or val is XoX.FALSE:
        return XoX.TRUE
    if val is XoX.UNKNOWN:
        return XoX.UNKNOWN
    raise TypeError(f"Unsupported operand for k3_not: {type(val).__name__}")


def k3_and_with_provenance(left: Any, right_fn_or_val: Any) -> Any:
    """Strong Kleene K3 logical AND with short-circuiting and provenance combination."""
    from xoxlang.runtime import XoX
    # Left evaluation
    if left is False or left is XoX.FALSE:
        # Short-circuit: right is skipped completely (zero right provenance)
        return XoX.FALSE

    # Right evaluation (lazy)
    right = right_fn_or_val() if callable(right_fn_or_val) else right_fn_or_val

    if right is False or right is XoX.FALSE:
        # Determinate False: K3 semantic independence eliminates left provenance
        return XoX.FALSE

    if (left is True or left is XoX.TRUE) and (right is True or right is XoX.TRUE):
        return XoX.TRUE

    if isinstance(left, UnknownValue) and isinstance(right, UnknownValue):
        if left.world_state_id != right.world_state_id:
            raise DefinednessPreconditionError(
                f"Cannot combine Unknown values across distinct WorldStateIDs ({left.world_state_id} vs {right.world_state_id})."
            )
        return _create_propagated_unknown(left.provenance_set | right.provenance_set, left.world_state_id)

    if isinstance(left, UnknownValue):
        return _create_propagated_unknown(left.provenance_set, left.world_state_id)

    if isinstance(right, UnknownValue):
        return _create_propagated_unknown(right.provenance_set, right.world_state_id)

    return XoX.UNKNOWN


def k3_or_with_provenance(left: Any, right_fn_or_val: Any) -> Any:
    """Strong Kleene K3 logical OR with short-circuiting and provenance combination."""
    from xoxlang.runtime import XoX
    # Left evaluation
    if left is True or left is XoX.TRUE:
        # Short-circuit: right is skipped completely (zero right provenance)
        return XoX.TRUE

    # Right evaluation (lazy)
    right = right_fn_or_val() if callable(right_fn_or_val) else right_fn_or_val

    if right is True or right is XoX.TRUE:
        # Determinate True: K3 semantic independence eliminates left provenance
        return XoX.TRUE

    if (left is False or left is XoX.FALSE) and (right is False or right is XoX.FALSE):
        return XoX.FALSE

    if isinstance(left, UnknownValue) and isinstance(right, UnknownValue):
        if left.world_state_id != right.world_state_id:
            raise DefinednessPreconditionError(
                f"Cannot combine Unknown values across distinct WorldStateIDs ({left.world_state_id} vs {right.world_state_id})."
            )
        return _create_propagated_unknown(left.provenance_set | right.provenance_set, left.world_state_id)

    if isinstance(left, UnknownValue):
        return _create_propagated_unknown(left.provenance_set, left.world_state_id)

    if isinstance(right, UnknownValue):
        return _create_propagated_unknown(right.provenance_set, right.world_state_id)

    return XoX.UNKNOWN








