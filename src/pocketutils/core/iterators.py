# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
"""

"""

import abc
import math
from collections.abc import Iterable, Iterator, Sequence
from typing import Self, TypeVar

T_co = TypeVar("T_co", covariant=True)
IX = TypeVar("IX")


class SizedIterator(Iterator[T_co], metaclass=abc.ABCMeta):
    """
    An iterator with size and progress.
    """

    def __len__(self: Self) -> int:
        return self.total

    def __str__(self: Self) -> str:
        return repr(self)

    def __repr__(self: Self) -> str:
        return f"It({self.position}/{self.total})"

    @property
    def position(self: Self) -> int:
        raise NotImplementedError()

    @property
    def total(self: Self) -> int:
        raise NotImplementedError()

    @property
    def remaining(self: Self) -> int:
        return self.total - self.position

    @property
    def has_next(self: Self) -> bool:
        return self.position < self.total


class SeqIterator(SizedIterator[T_co]):
    """
    A concrete SizedIterator backed by a list.
    """

    def __init__(self: Self, it: Iterable[T_co]) -> None:
        self.__seq, self.__i, self.__current = list(it), 0, None

    def __next__(self: Self) -> T_co:
        try:
            self.__current = self.__seq[self.__i]
        except IndexError:
            msg = f"Size is {len(self)}"
            raise StopIteration(msg)
        self.__i += 1
        return self.__current

    @property
    def seq(self: Self) -> Sequence[T_co]:
        return self.__seq

    @property
    def position(self: Self) -> int:
        return self.__i

    @property
    def total(self: Self) -> int:
        return len(self.__seq)

    def reset(self: Self) -> None:
        self.__i, self.__current = 0, None

    def peek(self: Self) -> T_co:
        return self.__seq[self.__i]


class TieredIterator(SeqIterator[tuple[IX]]):
    """
    A SizedIterator that iterates over every tuples of combination from multiple sequences.

    Example:

        >>> it = TieredIterator([[1, 2, 3], [5, 6]])
        >>> list(it)
        [(1,5), (1,6), (2,5), (2,6), (3,5), (3,6)]
    """

    # noinspection PyMissingConstructor
    def __init__(self: Self, sequence: Sequence[Sequence[IX]]) -> None:
        self.__seqs = [SeqIterator(s) for s in reversed(sequence)]
        if len(self.seqs) == 0:
            self.__total = 0
        else:
            self.__total = math.prod([it.total for it in self.seqs])
        self.__i = 0

    def __next__(self: Self) -> tuple[IX]:
        if not self.has_next:
            msg = f"Length is {self.total}"
            raise StopIteration(msg)
        t = tuple(seq.peek() for seq in reversed(self.seqs))
        self.__set(0)
        self.__i += 1
        return t

    def __str__(self: Self) -> str:
        return repr(self)

    def __repr__(self: Self) -> str:
        sizes = ", ".join([f"{it.__current}/{it.total}" for it in self.seqs])
        return f"Iter({sizes})"

    @property
    def seqs(self: Self) -> Sequence[SeqIterator[IX]]:
        return self.__seqs

    @property
    def position(self: Self) -> int:
        return self.__i

    @property
    def total(self: Self) -> int:
        return self.__total

    def __set(self: Self, i: int) -> None:
        seq = self.seqs[i]
        if seq.remaining > 1:
            next(seq)
        else:
            seq.reset()
            # to avoid index error for last case, after which self.has_next is False
            if i < len(self.seqs) - 1:
                self.__set(i + 1)  # recurse


__all__ = ["SizedIterator", "SeqIterator", "TieredIterator"]
