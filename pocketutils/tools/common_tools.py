import sys
from collections import defaultdict
from typing import (
    Any,
    Callable,
    Generator,
    Iterable,
    Iterator,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import numpy as np

from pocketutils.core.exceptions import RefusingRequestError
from pocketutils.core.input_output import DevNull
from pocketutils.core.internal import nicesize
from pocketutils.tools.base_tools import BaseTools

Y = TypeVar("Y")
T = TypeVar("T")
Z = TypeVar("Z")
Q = TypeVar("Q")


class CommonTools(BaseTools):
    @classmethod
    def limit(cls, items: Iterable[Q], n: int) -> Generator[Q, None, None]:
        for i, x in zip(range(n), items):
            yield x

    @classmethod
    def try_none(
        cls,
        function: Callable[[], T],
        fail_val: Optional[T] = None,
        exception=Exception,
    ) -> Optional[T]:
        """
        Returns the value of a function or None if it raised an exception.

        Args:
            function: Try calling this function
            fail_val: Return this value
            exception: Restrict caught exceptions to subclasses of this type
        """
        # noinspection PyBroadException
        try:
            return function()
        except exception:
            return fail_val

    @classmethod
    def succeeds(cls, function: Callable[[], Any], exception=Exception) -> bool:
        """Returns True iff `function` does not raise an error."""
        return cls.try_none(function, exception=exception) is not None

    @classmethod
    def or_null(cls, x: Any, dtype=lambda s: s, or_else: Any = None) -> Optional[Any]:
        """
        Return ``None`` if the operation ``dtype`` on ``x`` failed; returns the result otherwise.
        """
        return or_else if cls.is_null(x) else dtype(x)

    @classmethod
    def or_raise(
        cls,
        x: Any,
        dtype=lambda s: s,
        or_else: Union[None, BaseException, Type[BaseException]] = None,
    ) -> Any:
        """
        Returns ``dtype(x)`` if ``x`` is not None, or raises ``or_else``.
        """
        if or_else is None:
            or_else = LookupError(f"Value is {x}")
        elif isinstance(or_else, type):
            or_else = or_else(f"Value is {x}")
        if cls.is_null(x):
            raise or_else
        return dtype(x)

    @classmethod
    def iterator_has_elements(cls, x: Iterator[Any]) -> bool:
        """
        Returns False iff ``next(x)`` raises a ``StopIteration``.
        WARNING: Tries to call ``next(x)``, progressing iterators. Don't use ``x`` after calling this.
        Note that calling ``iterator_has_elements([5])`` will raise a `TypeError`

        Args:
            x: Must be an Iterator
        """
        return cls.succeeds(lambda: next(x), StopIteration)

    @classmethod
    def is_null(cls, x: Any) -> bool:
        """
        Returns True if x is either:
            - None
            - NaN
        """
        try:
            if np.isnan(x):
                return True
        except (ValueError, TypeError):
            pass
        return x is None or x == float("nan")

    @classmethod
    def is_empty(cls, x: Any) -> bool:
        """
        Returns True iff either:
            - x is None
            - np.is_nan(x)
            - x is something with 0 length
            - x is iterable and has 0 elements (will call ``__iter__``)

        Raises:
            RefusingRequestError If ``x`` is an Iterator. Calling this would empty the iterator, which is dangerous.
        """
        if isinstance(x, Iterator):
            raise RefusingRequestError("Do not call is_empty on an iterator.")
        try:
            if np.isnan(x):
                return True
        except (ValueError, TypeError):
            pass
        return (
            x is None
            or x == float("nan")
            or hasattr(x, "__len__")
            and len(x) == 0
            or hasattr(x, "__iter__")
            and len(list(iter(x))) == 0
        )

    @classmethod
    def is_probable_null(cls, x: Any) -> bool:
        """
        Returns True iff either:
            - x is None
            - np.is_nan(x)
            - x is something with 0 length
            - x is iterable and has 0 elements (will call ``__iter__``)
            - a str(x) is 'nan', 'n/a', 'null', or 'none'; case-insensitive

        Things that are **NOT** probable nulls:
            - "na"
            - 0
            - [None]

        Raises:
            TypeError If ``x`` is an Iterator. Calling this would empty the iterator, which is dangerous.
        """
        return cls.is_empty(x) or str(x).lower() in ["nan", "n/a", "null", "none"]

    @classmethod
    def unique(cls, sequence: Iterable[T]) -> Sequence[T]:
        """
        Returns the unique items in `sequence`, in the order they appear in the iteration.

        Args:
            sequence: Any once-iterable sequence

        Returns:
            An ordered List of unique elements
        """
        seen = set()
        return [x for x in sequence if not (x in seen or seen.add(x))]

    @classmethod
    def first(cls, collection: Iterable[Any], attr: Optional[str] = None) -> Optional[Any]:
        """
        Gets the first element.

        WARNING: Tries to call ``next(x)``, progressing iterators.

        Args:
            collection: Any iterable
            attr: The name of the attribute that might be defined on the elements,
                or None to indicate the elements themselves should be used

        Returns:
            - The attribute of the first element if ``attr`` is defined on an element
            - None if the the sequence is empty
            - None if the sequence has no attribute ``attr``
        """
        try:
            # note: calling iter on an iterator creates a view only
            x = next(iter(collection))
            return x if attr is None else cls.look(x, attr)
        except StopIteration:
            return None

    @classmethod
    def iter_rowcol(cls, n_rows: int, n_cols: int) -> Generator[Tuple[int, int], None, None]:
        """
        An iterator over (row column) pairs for a row-first traversal of a grid with ``n_cols`` columns.

        Example:
            >>> it = CommonTools.iter_rowcol(5, 3)
            >>> [next(it) for _ in range(5)]  # [(0,0),(0,1),(0,2),(1,0),(1,1)]
        """
        for i in range(n_rows * n_cols):
            yield i // n_cols, i % n_cols

    @classmethod
    def multidict(
        cls,
        sequence: Iterable[Z],
        key_attr: Union[str, Iterable[str], Callable[[Y], Z]],
        skip_none: bool = False,
    ) -> Mapping[Y, Sequence[Z]]:
        """
        Builds a mapping of some attribute in `sequence` to the containing elements of ``sequence``.

        Args:
            sequence: Any iterable
            key_attr: Usually string like 'attr1.attr2'; see `look`
            skip_none: If None, raises a `KeyError` if the key is missing for any item; otherwise, skips it
        """
        dct = defaultdict(lambda: [])
        for item in sequence:
            v = CommonTools.look(item, key_attr)
            if not skip_none and v is None:
                raise KeyError(f"No {key_attr} in {item}")
            if v is not None:
                dct[v].append(item)
        return dct

    @classmethod
    def mem_size(cls, obj) -> str:
        """
        Returns the size of the object in memory as a human-readable string.

        Args:
            obj: Any Python object

        Returns:
            A human-readable size with units
        """
        return nicesize(sys.getsizeof(obj))

    @classmethod
    def devnull(cls):
        """
        Yields a 'writer' that does nothing.

        Example:
            >>> with CommonTools.devnull() as devnull:
            >>>     devnull.write('hello')
        """
        yield DevNull()

    @classmethod
    def parse_bool(cls, s: str) -> bool:
        """
        Parses a 'true'/'false' string to a bool, ignoring case.

        Raises:
            ValueError: If neither true nor false
        """
        if isinstance(s, bool):
            return s
        if s.lower() == "false":
            return False
        if s.lower() == "true":
            return True
        raise ValueError(f"{s} is not true/false")

    @classmethod
    def parse_bool_flex(cls, s: str) -> bool:
        """
        Parses a 'true'/'false'/'yes'/'no'/... string to a bool, ignoring case.

        Allowed:
            - "true", "t", "yes", "y", "1", "+"
            - "false", "f", "no", "n", "0", "-"

        Raises:
            ValueError: If neither true nor false
        """
        mp = {
            **{v: True for v in {"true", "t", "yes", "y", "1", "+"}},
            **{v: False for v in {"false", "f", "no", "n", "0", "-"}},
        }
        v = mp.get(s.lower())
        if v is None:
            raise ValueError(f"{s.lower()} is not in {','.join(mp.keys())}")
        return v


__all__ = ["CommonTools"]
