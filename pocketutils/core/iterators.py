import abc
from collections.abc import Iterator as _Iterator
from typing import Iterable, Sequence, Tuple, TypeVar

import numpy as np

T = TypeVar("T")
IX = TypeVar("IX")


class SizedIterator(_Iterator[T], metaclass=abc.ABCMeta):
    """
    An iterator with size and progress.
    """

    def position(self) -> int:
        raise NotImplementedError()

    def total(self) -> int:
        raise NotImplementedError()

    def remaining(self) -> int:
        return self.total() - self.position()

    def has_next(self) -> bool:
        return self.position() < self.total()

    def __len__(self) -> int:
        return self.total()

    def __repr__(self):
        return f"It({self.position()}/{self.total()})"

    def __str__(self):
        return repr(self)


class SeqIterator(SizedIterator[T]):
    """
    A concrete SizedIterator backed by a list.
    """

    def __init__(self, it: Iterable[T]):
        self.__seq, self.__i, self.__current = list(it), 0, None

    @property
    def seq(self) -> Sequence[T]:
        return self.__seq

    def reset(self) -> None:
        self.__i, self.__current = 0, None

    def peek(self) -> T:
        return self.__seq[self.__i]

    def position(self) -> int:
        return self.__i

    def total(self) -> int:
        return len(self.__seq)

    def __next__(self) -> T:
        try:
            self.current = self.__seq[self.__i]
        except IndexError:
            raise StopIteration(f"Size is {len(self)}")
        self.__i += 1
        return self.current


class TieredIterator(SeqIterator[Tuple[IX]]):
    """
    A SizedIterator that iterates over every tuples of combination from multiple sequences.

    Example:
        >>> it = TieredIterator([[1, 2, 3], [5, 6]])
        >>> list(it)
        [(1,5), (1,6), (2,5), (2,6), (3,5), (3,6)]
    """

    # noinspection PyMissingConstructor
    def __init__(self, sequence: Sequence[Sequence[IX]]):
        self.__seqs = list([SeqIterator(s) for s in reversed(sequence)])
        self.__total = 0 if len(self.seqs) == 0 else int(np.product([i.total() for i in self.seqs]))
        self.__i = 0

    @property
    def seqs(self) -> Sequence[SeqIterator[IX]]:
        return self.__seqs

    def position(self) -> int:
        return self.__i

    def total(self) -> int:
        return self.__total

    def __next__(self) -> Tuple[IX]:
        if not self.has_next():
            raise StopIteration(f"Length is {self.total()}")
        t = tuple((seq.peek() for seq in reversed(self.seqs)))
        self.__set(0)
        self.__i += 1
        return t

    def __set(self, i: int):
        seq = self.seqs[i]
        if seq.remaining() > 1:
            next(seq)
        else:
            seq.reset()
            # to avoid index error for last case, after which self.has_next() is False
            if i < len(self.seqs) - 1:
                self.__set(i + 1)  # recurse

    def __repr__(self):
        sizes = ", ".join([f"{it.current}/{it.total()}" for it in self.seqs])
        return f"Iter({sizes})"

    def __str__(self):
        return repr(self)


__all__ = ["SizedIterator", "SeqIterator", "TieredIterator"]
