"""
Hashable and ordered collections.
"""


import functools
from collections.abc import Hashable, Iterator, Mapping, MutableMapping, Sequence, Set, ValuesView
from typing import Self, TypeVar

T_co = TypeVar("T_co", covariant=True)
K_contra = TypeVar("K_contra", contravariant=True)
V_co = TypeVar("V_co", covariant=True)


@functools.total_ordering
class FrozeList(Sequence[T_co], Hashable):
    """
    An immutable list.
    Hashable and ordered.
    """

    EMPTY: Self = NotImplemented  # delayed

    def __init__(self: Self, lst: Sequence[T_co]) -> None:
        self.__lst = lst if isinstance(lst, list) else list(lst)
        try:
            self.__hash = hash(tuple(lst))
        except AttributeError:
            self.__hash = 0

    @property
    def is_empty(self: Self) -> bool:  # pragma: no cover
        return len(self.__lst) == 0

    @property
    def length(self: Self) -> int:  # pragma: no cover
        return len(self.__lst)

    def __iter__(self: Self) -> Iterator[T_co]:  # pragma: no cover
        return iter(self.__lst)

    def __getitem__(self: Self, item: int) -> T_co:  # pragma: no cover
        return self.__lst[item]

    def __hash__(self: Self) -> int:
        return self.__hash

    def __eq__(self: Self, other: Sequence[T_co]) -> bool:
        return self.__lst == self.__make_other(other)

    def __lt__(self: Self, other: Sequence[T_co]) -> bool:
        return self.__lst < self.__make_other(other)

    def __len__(self: Self) -> int:
        return len(self.__lst)

    def __str__(self: Self) -> str:
        return str(self.__lst)

    def __repr__(self: Self) -> str:
        return repr(self.__lst)

    def to_list(self: Self) -> list[T_co]:
        return list(self.__lst)

    def get(self: Self, item: T_co, default: T_co | None = None) -> T_co | None:
        if item in self.__lst:
            return item
        return default

    def req(self: Self, item: T_co, default: T_co | None = None) -> T_co:
        """
        Returns the requested list item, falling back to a default.
        Short for "require".

        Raise:
            KeyError: If `item` is not in this list and `default` is `None`
        """
        if item in self.__lst:
            return item
        if default is None:
            msg = f"Item {item} not found"
            raise KeyError(msg)
        return default

    def __make_other(self: Self, other: Sequence[T_co]) -> list[T_co]:
        if isinstance(other, FrozeList):
            other = other.__lst
        if isinstance(other, list):
            return other
        elif isinstance(other, Sequence):
            return list(other)
        msg = f"Cannot compare to {type(other)}"
        raise TypeError(msg)


class FrozeSet(Set[T_co], Hashable):
    """
    An immutable set.
    Hashable and ordered.
    This is almost identical to `typing.FrozenSet`, but its behavior was made
    equivalent to those of FrozeDict and FrozeList.
    """

    EMPTY: Self = NotImplemented  # delayed

    def __init__(self: Self, lst: Set[T_co]) -> None:
        self.__lst = lst if isinstance(lst, set) else set(lst)
        try:
            self.__hash = hash(tuple(lst))
        except AttributeError:
            # the hashes will collide, making sets slow
            # but at least we'll have a hash and thereby not violate the constraint
            self.__hash = 0

    def get(self: Self, item: T_co, default: T_co | None = None) -> T_co | None:
        if item in self.__lst:
            return item
        return default

    def req(self: Self, item: T_co, default: T_co | None = None) -> T_co:
        """
        Returns `item` if it is in this set.
        Short for "require".
        Falls back to `default` if `default` is not `None`.

        Raises:
            KeyError: If `item` is not in this set and `default` is `None`
        """
        if item in self.__lst:
            return item
        if default is None:
            msg = f"Item {item} not found"
            raise KeyError(msg)
        return default

    def __getitem__(self: Self, item: T_co) -> T_co:
        if item in self.__lst:
            return item
        msg = f"Item {item} not found"
        raise KeyError(msg)

    def __contains__(self: Self, x: T_co) -> bool:  # pragma: no cover
        return x in self.__lst

    def __iter__(self: Self) -> Iterator[T_co]:  # pragma: no cover
        return iter(self.__lst)

    def __hash__(self: Self) -> int:
        return self.__hash

    def __eq__(self: Self, other: Set[T_co]) -> bool:
        return self.__lst == self.__make_other(other)

    def __lt__(self: Self, other: Set[T_co]) -> bool:
        """
        Compares `self` and `other` for partial ordering.
        Sorts `self` and `other`, then compares the two sorted sets.

        Approximately::
            return list(sorted(self: Self)) < list(sorted(other))
        """
        other = sorted(self.__make_other(other))
        me = sorted(self.__lst)
        return me < other

    @property
    def is_empty(self: Self) -> bool:  # pragma: no cover
        return len(self.__lst) == 0

    @property
    def length(self: Self) -> int:  # pragma: no cover
        return len(self.__lst)

    def __len__(self: Self) -> int:  # pragma: no cover
        return len(self.__lst)

    def __str__(self: Self) -> str:
        return str(self.__lst)

    def __repr__(self: Self) -> str:
        return repr(self.__lst)

    def to_set(self: Self) -> Set[T_co]:
        return set(self.__lst)

    def to_frozenset(self: Self) -> Set[T_co]:
        return frozenset(self.__lst)

    def __make_other(self: Self, other: Set[T_co]) -> set[T_co]:
        if isinstance(other, FrozeSet):
            other = other.__lst
        if isinstance(other, set):
            return other
        elif isinstance(other, Set):
            return set(other)
        msg = f"Cannot compare to {type(other)}"
        raise TypeError(msg)


class FrozeDict(Mapping[K_contra, V_co], Hashable):
    """
    An immutable dictionary/mapping.
    Hashable and ordered.
    """

    EMPTY: Self = NotImplemented  # delayed

    def __init__(self: Self, dct: Mapping[K_contra, V_co]) -> None:
        self.__dct = dct if isinstance(dct, dict) else dict(dct)
        self.__hash = hash(tuple(dct.items()))

    def get(self: Self, key: K_contra, default: V_co | None = None) -> V_co | None:  # pragma: no cover
        return self.__dct.get(key, default)

    def req(self: Self, key: K_contra, default: V_co | None = None) -> V_co:
        """
        Returns the value corresponding to `key`.
        Short for "require".
        Falls back to `default` if `default` is not None and `key` is not in this dict.

        Raise:
        KeyError: If `key` is not in this dict and `default` is `None`
        """
        if default is None:
            return self.__dct[key]
        return self.__dct.get(key, default)

    def items(self: Self) -> Set[tuple[K_contra, V_co]]:  # pragma: no cover
        return self.__dct.items()

    def keys(self: Self) -> Set[K_contra]:  # pragma: no cover
        return self.__dct.keys()

    def values(self: Self) -> ValuesView[V_co]:  # pragma: no cover
        return self.__dct.values()

    def __iter__(self: Self) -> Iterator[K_contra]:  # pragma: no cover
        return iter(self.__dct)

    def __contains__(self: Self, item: K_contra) -> bool:  # pragma: no cover
        return item in self.__dct

    def __getitem__(self: Self, item: K_contra) -> T_co:  # pragma: no cover
        return self.__dct[item]

    def __hash__(self: Self) -> int:
        return self.__hash

    def __eq__(self: Self, other: Mapping[K_contra, V_co]) -> bool:
        return self.__dct == self.__make_other(other)

    def __lt__(self: Self, other: Mapping[K_contra, V_co]) -> bool:
        """
        Compares this dict to another, with partial ordering.

        The algorithm is:
            1. Sort `self` and `other` by keys
            2. If `sorted_self < sorted_other`, return `False`
            3. If the reverse is true (`sorted_other < sorted_self`), return `True`
            4. (The keys are now known to be the same.)
               For each key, in order: If `self[key] < other[key]`, return `True`
            5. Return `False`
        """
        other = self.__make_other(other)
        me = self.__dct
        o_keys = sorted(other.keys())
        s_keys = sorted(me.keys())
        if o_keys < s_keys:
            return False
        if o_keys > s_keys:
            return True
        # keys are equal
        return any(other[k] > me[k] for k in o_keys)

    @property
    def is_empty(self: Self) -> bool:  # pragma: no cover
        return len(self.__dct) == 0

    @property
    def length(self: Self) -> int:  # pragma: no cover
        return len(self.__dct)

    def __len__(self: Self) -> int:
        return len(self.__dct)

    def __str__(self: Self) -> str:
        return str(self.__dct)

    def __repr__(self: Self) -> str:
        return repr(self.__dct)

    def to_dict(self: Self) -> MutableMapping[K_contra, V_co]:  # pragma: no cover
        return dict(self.__dct)

    def __make_other(self: Self, other: Mapping[K_contra, V_co]) -> dict[K_contra, V_co]:
        if isinstance(other, FrozeDict):
            other = other.__dct
        if isinstance(other, dict):
            return other
        elif isinstance(other, Mapping):
            return dict(other)
        msg = f"Cannot compare to {type(other)}"
        raise TypeError(msg)


# for performance, only make these once:
FrozeList.EMPTY = FrozeList([])
FrozeSet.EMPTY = FrozeSet(set())
FrozeDict.EMPTY = FrozeDict({})


__all__ = ["FrozeList", "FrozeSet", "FrozeDict"]
