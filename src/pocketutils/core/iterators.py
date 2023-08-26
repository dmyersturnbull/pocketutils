import abc
import math
from collections.abc import Iterable, Iterator, Sequence
from typing import Self, TypeVar

T = TypeVar("T")
IX = TypeVar("IX")


class SizedIterator(Iterator[T], metaclass=abc.ABCMeta):
    """
    An iterator with size and progress.
    """

    def position(self: Self) -> int:
        raise NotImplementedError()

    def total(self: Self) -> int:
        raise NotImplementedError()

    def remaining(self: Self) -> int:
        return self.total() - self.position()

    def has_next(self: Self) -> bool:
        return self.position() < self.total()

    def __len__(self: Self) -> int:
        return self.total()

    def __repr__(self: Self) -> str:
        return f"It({self.position()}/{self.total()})"

    def __str__(self: Self) -> str:
        return repr(self)


class SeqIterator(SizedIterator[T]):
    """
    A concrete SizedIterator backed by a list.
    """

    def __init__(self: Self, it: Iterable[T]) -> None:
        self.__seq, self.__i, self.__current = list(it), 0, None

    @property
    def seq(self: Self) -> Sequence[T]:
        return self.__seq

    def reset(self: Self) -> None:
        self.__i, self.__current = 0, None

    def peek(self: Self) -> T:
        return self.__seq[self.__i]

    def position(self: Self) -> int:
        return self.__i

    def total(self: Self) -> int:
        return len(self.__seq)

    def __next__(self: Self) -> T:
        try:
            self.current = self.__seq[self.__i]
        except IndexError:
            msg = f"Size is {len(self)}"
            raise StopIteration(msg)
        self.__i += 1
        return self.current


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
            self.__total = math.prod([it.total() for it in self.seqs])
        self.__i = 0

    @property
    def seqs(self: Self) -> Sequence[SeqIterator[IX]]:
        return self.__seqs

    def position(self: Self) -> int:
        return self.__i

    def total(self: Self) -> int:
        return self.__total

    def __next__(self: Self) -> tuple[IX]:
        if not self.has_next():
            msg = f"Length is {self.total()}"
            raise StopIteration(msg)
        t = tuple(seq.peek() for seq in reversed(self.seqs))
        self.__set(0)
        self.__i += 1
        return t

    def __set(self: Self, i: int) -> None:
        seq = self.seqs[i]
        if seq.remaining() > 1:
            next(seq)
        else:
            seq.reset()
            # to avoid index error for last case, after which self.has_next() is False
            if i < len(self.seqs) - 1:
                self.__set(i + 1)  # recurse

    def __repr__(self: Self) -> str:
        sizes = ", ".join([f"{it.current}/{it.total()}" for it in self.seqs])
        return f"Iter({sizes})"

    def __str__(self: Self) -> str:
        return repr(self)


__all__ = ["SizedIterator", "SeqIterator", "TieredIterator"]
