# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
"""

"""

import logging
import operator
import re
import sys
from collections import defaultdict, deque
from collections.abc import Callable, Generator, Hashable, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from types import LambdaType
from typing import Any, Literal, Self, TypeVar

from pocketutils import FrozeDict, FrozeList, FrozeSet
from pocketutils.core.exceptions import MultipleMatchesError, NoMatchesError, ValueIllegalError
from pocketutils.core.input_output import Writeable, return_none_1_param

__all__ = ["CommonUtils", "CommonTools", "Writeable"]

T = TypeVar("T")
V_co = TypeVar("V_co", covariant=True)
K_contra = TypeVar("K_contra", contravariant=True)
logger = logging.getLogger("pocketutils")
lambda_regex = re.compile(r"^<function (?:[A-Za-z_][A-Za-z0-9_.]*)?(?:<locals>\.)?<lambda> at 0x[A-F0-9]+>$")


@dataclass(slots=True, frozen=True)
class CommonUtils:
    def freeze(
        self: Self,
        v: Sequence[V_co] | set[V_co] | dict[K_contra, V_co] | frozenset[V_co] | Hashable,
    ) -> FrozeList[V_co] | FrozeSet[V_co] | FrozeDict[K_contra, V_co] | Hashable:
        """
        Returns `v` or a hashable view of it.
        Note that the returned types must be hashable but might not be ordered.
        You can generally add these values as DataFrame elements, but you might not
        be able to sort on those columns.

        Args:
            v: Any value

        Returns:
            Either `v` itself,
            [`FrozeSet`](pocketutils.core.frozen_types.FrozeSet) (subclass of `collections.abc.Set`),
            a [`FrozeList`](pocketutils.core.frozen_types.FrozeList) (subclass of `collections.abc.Sequence`),
            or a [`FrozeDict`](pocketutils.core.frozen_types.FrozeDict) (subclass of `collections.abc.Mapping`).
            int, float, str, np.generic, and tuple are always returned as-is.

        Raises:
            AttributeError: If `v` is not hashable and could not be converted to
                            a FrozeSet, FrozeList, or FrozeDict, *or* if one of the elements for
                            one of the above types is not hashable.
            TypeError: If `v` is an `Iterator` or `deque`
        """
        if isinstance(v, int | float | str | tuple | frozenset):
            return v  # short-circuit
        if str(type(v)).startswith("<class 'numpy."):
            return v
        match v:
            case Iterator():  # let's not ruin their iterator by traversing
                msg = "Type is an iterator"
                raise TypeError(msg)
            case deque():  # the only other major built-in type we won't accept
                msg = "Type is a deque"
                raise TypeError(msg)
            case Sequence():
                return FrozeList(v)
            case set():
                return FrozeSet(v)
            case frozenset():
                return FrozeSet(v)
            case Mapping():
                return FrozeDict(v)
            case _:
                hash(v)  # raise an AttributeError if not hashable
                return v

    def nice_size(self: Self, n_bytes: int, *, space: str = "") -> str:
        """
        Uses IEC 1998 units, such as KiB (1024).
            n_bytes: Number of bytes
            space: Separator between digits and units

            Returns:
                Formatted string
        """
        data = {
            "PiB": 1024**5,
            "TiB": 1024**4,
            "GiB": 1024**3,
            "MiB": 1024**2,
            "KiB": 1024**1,
        }
        for suffix, scale in data.items():
            if n_bytes >= scale:
                break
        else:
            scale, suffix = 1, "B"
        return str(n_bytes // scale) + space + suffix

    def limit(self: Self, items: Iterable[V_co], n: int) -> Iterator[V_co]:
        for _i, x in zip(range(n), items):
            yield x

    def is_float(self: Self, s: Any) -> bool:
        """
        Returns whether `float(s)` succeeds.
        """
        try:
            float(s)
            return True
        except ValueError:
            return False

    def try_or_none(
        self: Self,
        function: Callable[[], V_co],
        or_else: V_co | None = None,
        exception: type[Exception] = Exception,
    ) -> V_co | None:
        """
        Returns the value of a function or None if it raised an exception.

        Args:
            function: Try calling this function
            or_else: Return this value
            exception: Restrict caught exceptions to subclasses of this type
        """
        # noinspection PyBroadException
        try:
            return function()
        except exception:
            return or_else

    def succeeds(self: Self, function: Callable[[], Any], exception: type[BaseException] = Exception) -> bool:
        """Returns True iff `function` does not raise an error."""
        try:
            function()
        except exception:
            return False
        return True

    def iterator_has_elements(self: Self, it: Iterator) -> bool:
        """
        Returns False iff `next(x)` raises a `StopIteration`.
        WARNING: Tries to call `next(x)`, progressing iterators. Don't use `x` after calling this.
        Note that calling `iterator_has_elements([5])` will raise a `TypeError`

        Args:
            it: Must be an Iterator
        """
        return self.succeeds(lambda: next(it), StopIteration)

    def is_null(self: Self, v: V_co) -> bool:
        """
        Returns True for None, NaN, and NaT (not a time) values from Numpy, Pandas, and Python.
        Not perfect; may return false positive True for types declared outside Numpy and Pandas.
        """
        if v is None:
            return True
        if isinstance(v, str):
            return False
        return str(v) in [
            "nan",  # float('NaN') and Numpy float NaN
            "NaN",  # Pandas NaN and decimal.Decimal NaN
            "<NA>",  # Pandas pd.NA
            "NaT",  # Numpy datetime and timedelta NaT
        ]

    def is_empty(self: Self, v: V_co) -> bool:
        """
        Returns True if x is None, NaN according to Pandas, or contains 0 items.

        That is, if and only if:
            - `self.is_null(x)`
            - x is something with 0 length
            - x is iterable and has 0 elements (will call `__iter__`)

        Raises:
            RefusingRequestError If `x` is an Iterator. Calling this would empty the iterator, which is dangerous.
        """
        if isinstance(v, Iterator):
            msg = "Do not call is_empty on an iterator."
            raise TypeError(msg)
        try:
            if self.is_null(v):
                return True
        except (ValueError, TypeError):
            pass
        return hasattr(v, "__len__") and len(v) == 0 or hasattr(v, "__iter__") and len(list(iter(v))) == 0

    def is_probable_null(self: Self, v: V_co) -> bool:
        """
        Returns True if `x` is None, NaN according to Pandas, 0 length, or a string representation.

        Specifically, returns True if and only if:
            - `is_null`
            - x is something with 0 length
            - x is iterable and has 0 elements (will call `__iter__`)
            - a str(x) is 'nan', 'na', 'n/a', 'null', or 'none'; case-insensitive

        Things that are **NOT** probable nulls:
            - `0`
            - `[None]`

        Raises:
            TypeError If `x` is an Iterator.
                      Calling this would empty the iterator, which is dangerous.
        """
        return self.is_empty(v) or str(v).lower() in {"nan", "n/a", "na", "null", "none", "<NA>", "NaT"}

    def unique(self: Self, sequence: Iterable[V_co]) -> Sequence[V_co]:
        """
        Returns the unique items in `sequence`, in the order they appear in the iteration.

        Args:
            sequence: Any once-iterable sequence

        Returns:
            An ordered List of unique elements
        """
        seen = set()
        return [x for x in sequence if not (x in seen or seen.add(x))]

    def first(self: Self, collection: Iterable[V_co]) -> V_co:
        """
        Gets the first element.

        Warning: Tries to call `next(x)`, progressing iterators.

        Args:
            collection: Any iterable

        Returns:
            Either `None` or the value, according to the rules:
                - The attribute of the first element if `attr` is defined on an element
                - None if the sequence is empty
                - None if the sequence has no attribute `attr`
        """
        try:
            # note: calling iter on an iterator creates a view only
            return next(iter(collection))
        except StopIteration:
            return None

    def iter_row_col(self: Self, rows: int, cols: int) -> Iterator[tuple[int, int]]:
        """
        An iterator over (row column) pairs for a row-first grid traversal.

        Example:

            it = CommonTools.iter_rowcol(5, 3)
            [next(it) for _ in range(5)]  # [(0,0),(0,1),(0,2),(1,0),(1,1)]
        """
        for i in range(rows * cols):
            yield i // cols, i % cols

    def multidict(
        self: Self,
        sequence: Iterable[V_co],
        key_attr: str | Iterable[str] | Callable[[K_contra], V_co],
        skip_none: bool = False,
    ) -> Mapping[K_contra, Sequence[V_co]]:
        """
        Builds a mapping from keys to multiple values.
        Builds a mapping of some attribute in `sequence` to
        the containing elements of `sequence`.

        Args:
            sequence: Any iterable
            key_attr: Usually string like 'attr1.attr2'; see `look`
            skip_none: If None, raises a `KeyError` if the key is missing for any item; otherwise, skips it
        """
        dct = defaultdict(list)
        for item in sequence:
            v = self.look(item, key_attr)
            if not skip_none and v is None:
                msg = f"No {key_attr} in {item}"
                raise KeyError(msg)
            if v is not None:
                dct[v].append(item)
        return dct

    def parse_bool(self: Self, s: str) -> bool:
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
        msg = f"{s} is not true/false"
        raise ValueIllegalError(msg, value=s)

    def parse_bool_flex(self: Self, s: str) -> bool:
        """
        Parses a 'true'/'false'/'yes'/'no'/... string to a bool, ignoring case.

        Allowed:
            - "true", "t", "yes", "y", "1"
            - "false", "f", "no", "n", "0"

        Raises:
            XValueError: If neither true nor false
        """
        mp = {
            **{v: True for v in ("true", "t", "yes", "y", "1")},
            **{v: False for v in ("false", "f", "no", "n", "0")},
        }
        v = mp.get(s.lower())
        if v is None:
            msg = f"{s.lower()} is not in {','.join(mp.keys())}"
            raise ValueIllegalError(msg, value=s)
        return v

    def is_lambda(self: Self, function: Any) -> bool:
        """
        Returns whether this is a lambda function. Will return False for non-callables.
        """
        return isinstance(function, LambdaType)

    def only(
        self: Self,
        sequence: Iterable[T],
        condition: str | Callable[[T], bool] | None = None,
        *,
        exception_if_none: Exception = NoMatchesError(),
        exception_if_multiple: Exception = MultipleMatchesError(),
    ) -> T:
        """
        Returns either the SINGLE (ONLY) UNIQUE ITEM in the sequence or raises an exception.
        Each item must have __hash__ defined on it.

        Args:
            sequence: A list of any items (untyped)
            condition: If nonnull, consider only those matching this condition (using `self.look`)
            exception_if_none: Exception to raise if none match
            exception_if_multiple: Exception to raise if multiple match

        Returns:
            The first item the sequence.

        Raises:
            LookupError If the sequence is empty
            MultipleMatchesError If there is more than one unique item.
        """

        def _only(sq: Iterable[T]):
            st = set(sq)
            if len(st) > 1:
                raise exception_if_multiple
            if len(st) == 0:
                raise exception_if_none
            return next(iter(st))

        if condition and isinstance(condition, str):
            return _only(
                [
                    s
                    for s in sequence
                    if (not self.look(s, condition[1:]) if condition.startswith("!") else self.look(s, condition))
                ],
            )
        elif condition:
            return _only([s for s in sequence if condition(s)])
        return _only(sequence)

    def forever(self: Self) -> Iterator[int]:
        """
        Yields i for i in range(0, infinity).
        Useful for simplifying a i = 0; while True: i += 1 block.
        """
        i = 0
        while True:
            yield i
            i += 1

    def is_true_iterable(self: Self, v: Any) -> bool:
        """
        Returns whether `s` is an iterable but not `str` and not `bytes`.

        Warning:
            Types that do not define `__iter__` but are iterable
            via `__getitem__` will not be included.
        """
        return (
            v is not None
            and isinstance(v, Iterable)
            and not isinstance(v, str)
            and not isinstance(v, bytes | bytearray | memoryview)
        )

    @contextmanager
    def null_context(self: Self) -> Generator[None, None, None]:
        """
        Returns an empty context (literally just yields).
        Useful to simplify when a generator needs to be used depending on a switch.

        Example:

            if verbose_flag:
                do_something()
            else:
                with Tools.silenced():
                    do_something()

        Can become:

        ```python
        with (Tools.null_context() if verbose else Tools.silenced()):
            do_something()
        ```
        """
        yield

    def look(self: Self, obj: T, attrs: str | Iterable[str] | Callable[[T], V_co]) -> V_co | None:
        """
        Follows a dotted syntax for getting an item nested in class attributes.
        Returns the value of a chain of attributes on object `obj`,
        or None any object in that chain is None or lacks the next attribute.

        Example:

            # Get a kitten's breed
            BaseTools.look(kitten), 'breed.name')  # either None or a string

        Args:
            obj: Any object
            attrs: One of:
                - A string in the form attr1.attr2, translating to `obj.attr1`
                - An iterable of strings of the attributes
                - A function that maps `obj` to its output;
                   equivalent to calling `attrs(obj)` but returning None on `AttributeError`.

        Returns:
            Either None or the type of the attribute
        """
        if attrs is None:
            return obj
        if not isinstance(attrs, str) and hasattr(attrs, "__len__") and len(attrs) == 0:
            return obj
        if isinstance(attrs, str):
            attrs = operator.attrgetter(attrs)
        elif isinstance(attrs, Iterable) and all(isinstance(a, str) for a in attrs):
            attrs = operator.attrgetter(".".join(attrs))
        elif not callable(attrs):
            msg = f"Type {type(attrs)} unrecognized for key/attrib. Must be a function, string, or sequence of strings"
            raise TypeError(msg)
        try:
            return attrs(obj)
        except AttributeError:
            return None

    def make_writer(self: Self, writer: Writeable | Callable[[str], Any]) -> Writeable:
        if Writeable.isinstance(writer):
            return writer
        elif callable(writer):

            class W(Writeable[V_co]):
                def write(self: Self, msg: V_co) -> int:
                    writer(msg)
                    return len(msg)

                def flush(self: Self) -> None:
                    pass

                def close(self: Self) -> None:
                    pass

            return W()
        msg_ = f"{type(writer)} cannot be wrapped into a Writeable"
        raise TypeError(msg_)

    def get_log_fn(
        self: Self,
        log: (Literal["stdout"] | str | int | Writeable | Callable[[str], Any] | None),
    ) -> Callable[[str], Any]:
        """
        Gets a logging function from user input.

        The rules are:
            - If None, uses logger.info
            - If 'print' or 'stdout',  use sys.stdout.write
            - If 'stderr', use sys.stderr.write
            - If another str or int, try using that logger level (raises an error if invalid)
            - If callable, returns it
            - If it has a callable method called 'write', uses that

        Returns:
            A function of the log message that returns None
        """
        if log is None:
            return return_none_1_param
        elif isinstance(log, str) and log.lower() == "stdout":
            # noinspection PyTypeChecker
            return sys.stdout.write
        elif log == "stderr":
            # noinspection PyTypeChecker
            return sys.stderr.write
        elif isinstance(log, int):
            return getattr(logger, logging.getLevelName(log).lower())
        elif isinstance(log, str):
            return getattr(logger, log.lower())
        elif callable(log):
            return log
        elif hasattr(log, "write"):
            return log.write
        msg = f"Log type {type(log)} not known"
        raise ValueIllegalError(msg, value=log)

    def sentinel(self: Self, name: str) -> Any:
        class _Sentinel:
            def __eq__(self: Self, other: Self) -> bool:
                return self is other

            def __reduce__(self: Self) -> str:
                return name  # returning string is for singletons

            def __hash__(self: Self) -> int:
                return hash(name)

            def __str__(self: Self) -> str:
                return name

            def __repr__(self: Self) -> str:
                return name

        return _Sentinel()

    def longest(self: Self, parts: Iterable[V_co]) -> V_co:
        """
        Returns an element with the highest `len`.
        """
        mx = ""
        for _i, x in enumerate(parts):
            if len(x) > len(mx):
                mx = x
        return mx


CommonTools = CommonUtils()
