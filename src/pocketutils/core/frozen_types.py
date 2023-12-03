# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
"""
Hashable and ordered collections.
"""

from __future__ import annotations

import functools
import itertools
from collections.abc import Hashable, ItemsView, Iterator, KeysView, Mapping, MutableMapping, Sequence, ValuesView
from typing import Self, TypeVar

T_co = TypeVar("T_co", covariant=True)
K_contra = TypeVar("K_contra", contravariant=True)
V_co = TypeVar("V_co", covariant=True)


@functools.total_ordering
class FrozeList(Sequence[T_co], Hashable):
    """
    An immutable list, hashable and ordered.
    """

    EMPTY: Self = NotImplemented  # delayed

    def __init__(self: Self, lst: Sequence[T_co]) -> None:
        self.__lst = lst if isinstance(lst, list) else list(lst)
        try:
            self.__hash = hash(tuple(lst))
        except AttributeError:
            self.__hash = 0

    def __iter__(self: Self) -> Iterator[T_co]:  # nocov
        return iter(self.__lst)

    def __contains__(self: Self, x: T_co) -> bool:  # nocov
        return x in self.__lst

    def __len__(self: Self) -> int:
        return len(self.__lst)

    def __getitem__(self: Self, item: int | slice) -> T_co | Self:  # nocov
        if isinstance(item, slice):
            return FrozeList(self.__lst[item])
        return self.__lst[item]

    def __hash__(self: Self) -> int:
        return self.__hash

    def __eq__(self: Self, other: Sequence[T_co]) -> bool:
        return self.__lst == self.__make_other(other)

    def __lt__(self: Self, other: Sequence[T_co]) -> bool:
        return self.__lst < self.__make_other(other)

    def __add__(self, other: Sequence[T_co]) -> Self:
        return FrozeList(self.__lst + self.__make_other(other))

    def __sub__(self, other: Sequence[T_co]) -> Self:
        return FrozeList([v for v in self.__lst if v not in set(self.__make_other(other))])

    def __and__(self, other: Sequence[T_co]) -> Self:
        return FrozeList(
            [v for v in self.__lst if v in set(self.__make_other(other))]
            + [v for v in self.__make_other(other) if v not in set(self.__lst)],
        )

    def __or__(self, other: Sequence[T_co]) -> Self:
        return FrozeList(self.__lst + [v for v in self.__make_other(other) if v not in set(self.__lst)])

    def __str__(self: Self) -> str:
        return str(self.__lst)

    def __repr__(self: Self) -> str:
        return repr(self.__lst)

    @property
    def is_empty(self: Self) -> bool:  # nocov
        return len(self.__lst) == 0

    @property
    def length(self: Self) -> int:  # nocov
        return len(self.__lst)

    def get(self: Self, item: T_co, default: T_co | None = None) -> T_co | None:
        if item in self.__lst:
            return item
        return default

    def req(self: Self, item: T_co) -> T_co:
        """
        Returns the requested list item, falling back to a default.
        Short for "require".

        Raise:
            KeyError: If `item` is not in this list and `default` is `None`
        """
        if item in self.__lst:
            return item
        msg = f"No item {item} in list"
        raise KeyError(msg)

    def to_list(self: Self) -> list[T_co]:
        return list(self.__lst)

    def is_disjoint(self: Self, other: Sequence[T_co]) -> bool:
        return len(set(self.__lst) & set(self.__make_other(other))) == 0

    def is_superset(self: Self, other: Sequence[T_co]) -> bool:
        return all(v in set(self.__lst) for v in self.__make_other(other))

    def is_subset(self: Self, other: Sequence[T_co]) -> bool:
        return all(v in set(self.__make_other(other)) for v in self.__lst)

    def sublists(self: Self) -> FrozeList[FrozeList[T_co]]:
        sublists: list[FrozeList[T_co]] = []
        for start in range(len(self)):
            for end in range(start + 1, len(self) + 1):
                sublists.append(self[start:end])
        return FrozeList(sublists)

    def __make_other(self: Self, other: Sequence[T_co]) -> list[T_co]:
        if isinstance(other, FrozeList):
            other = other.__lst
        if isinstance(other, list):
            return other
        elif isinstance(other, Sequence):
            return list(other)
        msg = f"Cannot compare to {type(other)}"
        raise TypeError(msg)


class FrozeSet(frozenset[T_co], Hashable):
    """
    An immutable set.
    Hashable and ordered, and subclasses `set` and `frozenset`.
    This is almost identical to `frozenset`, but its behavior was made
    equivalent to those of FrozeDict and FrozeList.
    """

    EMPTY: Self = NotImplemented  # delayed

    def __init__(self: Self, lst: set[T_co] | frozenset[T_co]) -> None:
        self.__lst = lst if isinstance(lst, frozenset) else set(lst)
        try:
            self.__hash = hash(tuple(lst))
        except AttributeError:
            # the hashes will collide, making sets slow
            # but at least we'll have a hash and thereby not violate the constraint
            self.__hash = 0

    def __iter__(self: Self) -> Iterator[T_co]:  # nocov
        return iter(self.__lst)

    def __contains__(self: Self, x: T_co) -> bool:  # nocov
        return x in self.__lst

    def __len__(self: Self) -> int:  # nocov
        return len(self.__lst)

    def __getitem__(self: Self, item: T_co) -> T_co:
        if item in self.__lst:
            return item
        msg = f"Item {item} not found"
        raise KeyError(msg)

    def __hash__(self: Self) -> int:
        return self.__hash

    def __eq__(self: Self, other: set[T_co] | frozenset[T_co]) -> bool:
        return self.__lst == self.__make_other(other)

    def __lt__(self: Self, other: set[T_co] | frozenset[T_co]) -> bool:
        """
        Compares `self` and `other` for partial ordering.
        Sorts `self` and `other`, then compares the two sorted sets.

        Approximately::
            return list(sorted(self: Self)) < list(sorted(other))
        """
        other = sorted(self.__make_other(other))
        me = sorted(self.__lst)
        return me < other

    def __str__(self: Self) -> str:
        return str(self.__lst)

    def __repr__(self: Self) -> str:
        return repr(self.__lst)

    @property
    def is_empty(self: Self) -> bool:  # nocov
        return len(self.__lst) == 0

    @property
    def length(self: Self) -> int:  # nocov
        return len(self.__lst)

    def get(self: Self, item: T_co, default: T_co | None = None) -> T_co | None:
        if item in self.__lst:
            return item
        return default

    def req(self: Self, item: T_co) -> T_co:
        """
        Returns `item` if it is in this set.
        Short for "require".

        Raises:
            KeyError: If `item` is not in this set and `default` is `None`
        """
        if item in self.__lst:
            return item

    def to_set(self: Self) -> set[T_co]:
        return set(self.__lst)

    def to_frozenset(self: Self) -> frozenset[T_co]:
        return frozenset(self.__lst)

    def subsets(self: Self) -> FrozeSet[FrozeSet[T_co]]:
        sets: set[FrozeSet[T_co]] = set()
        for sl in itertools.product(*[[[], [i]] for i in self.__lst]):
            sets |= FrozeSet({j for i in sl for j in i})
        return FrozeSet(sets)

    def __make_other(self: Self, other: set[T_co]) -> set[T_co]:
        if isinstance(other, FrozeSet):
            other = other.__lst
        if isinstance(other, set):
            return other
        elif isinstance(other, set):
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

    def __iter__(self: Self) -> Iterator[K_contra]:  # nocov
        return iter(self.__dct)

    def __contains__(self: Self, item: K_contra) -> bool:  # nocov
        return item in self.__dct

    def __len__(self: Self) -> int:
        return len(self.__dct)

    def __getitem__(self: Self, item: K_contra) -> T_co:  # nocov
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

    def __and__(self: Self, other: Mapping[K_contra, V_co]):
        other = self.__make_other(other)
        return FrozeDict({k: v for k, v in self.__dct.items() if other.get(k) == v})

    def __or__(self: Self, other: Mapping[K_contra, V_co]):
        return FrozeDict(self.__dct | self.__make_other(other))

    def __str__(self: Self) -> str:
        return str(self.__dct)

    def __repr__(self: Self) -> str:
        return repr(self.__dct)

    @property
    def is_empty(self: Self) -> bool:  # nocov
        return len(self.__dct) == 0

    @property
    def length(self: Self) -> int:  # nocov
        return len(self.__dct)

    def get(self: Self, key: K_contra, default: V_co | None = None) -> V_co | None:  # nocov
        return self.__dct.get(key, default)

    def req(self: Self, key: K_contra) -> V_co:
        """
        Returns the value corresponding to `key`.
        Short for "require".

        Raise:
            KeyError: If `key` is not in this dict and `default` is `None`
        """
        return self.__dct[key]

    def item_set(self: Self) -> FrozeSet[tuple[K_contra, V_co]]:  # nocov
        return FrozeSet(set(self.__dct.items()))

    def key_set(self: Self) -> FrozeSet[K_contra]:  # nocov
        return FrozeSet(set(self.__dct.keys()))

    def value_set(self: Self) -> FrozeSet[V_co]:  # nocov
        return FrozeSet(set(self.__dct.values()))

    def items(self: Self) -> ItemsView[K_contra, V_co]:  # nocov
        return self.__dct.items()

    def keys(self: Self) -> KeysView[K_contra]:  # nocov
        return self.__dct.keys()

    def values(self: Self) -> ValuesView[V_co]:  # nocov
        return self.__dct.values()

    def to_dict(self: Self) -> MutableMapping[K_contra, V_co]:  # nocov
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
