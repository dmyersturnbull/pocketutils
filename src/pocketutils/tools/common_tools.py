import logging
import operator
import sys
from collections import defaultdict, deque
from collections.abc import ByteString, Callable, Generator, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import Any, Literal, Self, TypeVar

from pocketutils import FrozeDict, FrozeList, FrozeSet
from pocketutils.core.exceptions import (
    MultipleMatchesError,
    RefusingRequestError,
    XKeyError,
    XTypeError,
)
from pocketutils.core.input_output import Writeable, return_none_1_param

Y = TypeVar("Y")
T = TypeVar("T")
Z = TypeVar("Z")
Q = TypeVar("Q")
logger = logging.getLogger("pocketutils")


class CommonTools:
    @classmethod
    def freeze(cls: type[Self], v: Any) -> Any:
        """
        Returns `v` or a hashable view of it.
        Note that the returned types must be hashable but might not be ordered.
        You can generally add these values as DataFrame elements, but you might not
        be able to sort on those columns.

        Args:
            v: Any value

        Returns:
            Either `v` itself,
            a :class:`typeddfs.utils.FrozeSet` (subclass of :class:`collections.abc.Set`),
            a :class:`typeddfs.utils.FrozeList` (subclass of :class:`collections.abc.Sequence`),
            or a :class:`typeddfs.utils.FrozeDict` (subclass of :class:`collections.abc.Mapping`).
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
            case FrozeSet():
                return FrozeList(v)
            case Mapping():
                return FrozeDict(v)
            case _:
                hash(v)  # raise an AttributeError if not hashable
                return v

    @classmethod
    def nice_size(cls: type[Self], n_bytes: int, *, space: str = "") -> str:
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

    @classmethod
    def limit(cls: type[Self], items: Iterable[Q], n: int) -> Generator[Q, None, None]:
        for _i, x in zip(range(n), items):
            yield x

    @classmethod
    def is_float(cls: type[Self], s: Any) -> bool:
        """
        Returns whether `float(s)` succeeds.
        """
        try:
            float(s)
            return True
        except ValueError:
            return False

    @classmethod
    def try_none(
        cls: type[Self],
        function: Callable[[], T],
        fail_val: T | None = None,
        exception=Exception,
    ) -> T | None:
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
    def succeeds(cls: type[Self], function: Callable[[], Any], exception=Exception) -> bool:
        """Returns True iff `function` does not raise an error."""
        return cls.try_none(function, exception=exception) is not None

    @classmethod
    def or_null(cls: type[Self], x: Any, dtype=lambda s: s, or_else: Any = None) -> Any | None:
        """
        Return `None` if the operation `dtype` on `x` failed; returns the result otherwise.
        """
        return or_else if cls.is_null(x) else dtype(x)

    @classmethod
    def or_raise(
        cls: type[Self],
        x: Any,
        dtype=lambda s: s,
        or_else: BaseException | type[BaseException] | None = None,
    ) -> Any:
        """
        Returns `dtype(x)` if `x` is not None, or raises `or_else`.
        """
        if or_else is None:
            or_else = LookupError(f"Value is {x}")
        elif isinstance(or_else, type):
            or_else = or_else(f"Value is {x}")
        if cls.is_null(x):
            raise or_else
        return dtype(x)

    @classmethod
    def iterator_has_elements(cls: type[Self], x: Iterator[Any]) -> bool:
        """
        Returns False iff `next(x)` raises a `StopIteration`.
        WARNING: Tries to call `next(x)`, progressing iterators. Don't use `x` after calling this.
        Note that calling `iterator_has_elements([5])` will raise a `TypeError`

        Args:
            x: Must be an Iterator
        """
        return cls.succeeds(lambda: next(x), StopIteration)

    @classmethod
    def is_null(cls: type[Self], x: Any) -> bool:
        """
        Returns True for None, NaN, and NaT (not a time) values from Numpy, Pandas, and Python.
        Not perfect; may return false positive True for types declared outside Numpy and Pandas.
        """
        if x is None:
            return True
        if isinstance(x, str):
            return False
        return str(x) in [
            "nan",  # float('NaN') and Numpy float NaN
            "NaN",  # Pandas NaN and decimal.Decimal NaN
            "<NA>",  # Pandas pd.NA
            "NaT",  # Numpy datetime and timedelta NaT
        ]

    @classmethod
    def is_empty(cls: type[Self], x: Any) -> bool:
        """
        Returns True if x is None, NaN according to Pandas, or contains 0 items.

        That is, if and only if:
            - :meth:`is_null`
            - x is something with 0 length
            - x is iterable and has 0 elements (will call `__iter__`)

        Raises:
            RefusingRequestError If `x` is an Iterator. Calling this would empty the iterator, which is dangerous.
        """
        if isinstance(x, Iterator):
            msg = "Do not call is_empty on an iterator."
            raise RefusingRequestError(msg)
        try:
            if cls.is_null(x):
                return True
        except (ValueError, TypeError):
            pass
        return hasattr(x, "__len__") and len(x) == 0 or hasattr(x, "__iter__") and len(list(iter(x))) == 0

    @classmethod
    def is_probable_null(cls: type[Self], x: Any) -> bool:
        """
        Returns True if `x` is None, NaN according to Pandas, 0 length, or a string representation.

        Specifically, returns True if and only if:
            - :meth:`is_null`
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
        return cls.is_empty(x) or str(x).lower() in ["nan", "n/a", "na", "null", "none"]

    @classmethod
    def unique(cls: type[Self], sequence: Iterable[T]) -> Sequence[T]:
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
    def first(cls: type[Self], collection: Iterable[Any], attr: str | None = None) -> Any:
        """
        Gets the first element.

        Warning: Tries to call `next(x)`, progressing iterators.

        Args:
            collection: Any iterable
            attr: The name of the attribute that might be defined on the elements,
                or None to indicate the elements themselves should be used

        Returns:
            Either `None` or the value, according to the rules:
                - The attribute of the first element if `attr` is defined on an element
                - None if the sequence is empty
                - None if the sequence has no attribute `attr`
        """
        try:
            # note: calling iter on an iterator creates a view only
            x = next(iter(collection))
            return x if attr is None else cls.look(x, attr)
        except StopIteration:
            return None

    @classmethod
    def iter_rowcol(cls: type[Self], n_rows: int, n_cols: int) -> Generator[tuple[int, int], None, None]:
        """
        An iterator over (row column) pairs for a row-first grid traversal.

        Example:
            .. code-block::
                it = CommonTools.iter_rowcol(5, 3)
                [next(it) for _ in range(5)]  # [(0,0),(0,1),(0,2),(1,0),(1,1)]
        """
        for i in range(n_rows * n_cols):
            yield i // n_cols, i % n_cols

    @classmethod
    def multidict(
        cls: type[Self],
        sequence: Iterable[Z],
        key_attr: str | Iterable[str] | Callable[[Y], Z],
        skip_none: bool = False,
    ) -> Mapping[Y, Sequence[Z]]:
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
            v = cls.look(item, key_attr)
            if not skip_none and v is None:
                msg = f"No {key_attr} in {item}"
                raise XKeyError(msg, key=key_attr)
            if v is not None:
                dct[v].append(item)
        return dct

    @classmethod
    def parse_bool(cls: type[Self], s: str) -> bool:
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
        raise ValueError(msg)

    @classmethod
    def parse_bool_flex(cls: type[Self], s: str) -> bool:
        """
        Parses a 'true'/'false'/'yes'/'no'/... string to a bool, ignoring case.

        Allowed:
            - "true", "t", "yes", "y", "1"
            - "false", "f", "no", "n", "0"

        Raises:
            XValueError: If neither true nor false
        """
        mp = {
            **{v: True for v in {"true", "t", "yes", "y", "1"}},
            **{v: False for v in {"false", "f", "no", "n", "0"}},
        }
        v = mp.get(s.lower())
        if v is None:
            msg = f"{s.lower()} is not in {','.join(mp.keys())}"
            raise ValueError(msg)
        return v

    @classmethod
    def is_lambda(cls, function: Any) -> bool:
        """
        Returns whether this is a lambda function. Will return False for non-callables.
        """
        # noinspection PyPep8Naming
        LAMBDA = lambda: 0  # noqa: E731
        if not hasattr(function, "__name__"):
            return False  # not a function
        return (
            isinstance(function, type(LAMBDA))
            and function.__name__ == LAMBDA.__name__
            or str(function).startswith("<function <lambda> at ")
            and str(function).endswith(">")
        )

    @classmethod
    def only(
        cls: type[Self],
        sequence: Iterable[Any],
        condition: str | Callable[[Any], bool] | None = None,
        *,
        name: str = "collection",
    ) -> Any:
        """
        Returns either the SINGLE (ONLY) UNIQUE ITEM in the sequence or raises an exception.
        Each item must have __hash__ defined on it.

        Args:
            sequence: A list of any items (untyped)
            condition: If nonnull, consider only those matching this condition
            name: Just a name for the collection to use in an error message

        Returns:
            The first item the sequence.

        Raises:
            LookupError If the sequence is empty
            MultipleMatchesError If there is more than one unique item.
        """

        def _only(sq):
            st = set(sq)
            if len(st) > 1:
                raise MultipleMatchesError("More then 1 item in " + str(name))
            if len(st) == 0:
                raise LookupError("Empty " + str(name))
            return next(iter(st))

        if condition and isinstance(condition, str):
            return _only(
                [
                    s
                    for s in sequence
                    if (not getattr(s, condition[1:]) if condition.startswith("!") else getattr(s, condition))
                ],
            )
        elif condition:
            return _only([s for s in sequence if condition(s)])
        else:
            return _only(sequence)

    @classmethod
    def forever(cls: type[Self]) -> Iterator[int]:
        """
        Yields i for i in range(0, infinity).
        Useful for simplifying a i = 0; while True: i += 1 block.
        """
        i = 0
        while True:
            yield i
            i += 1

    @classmethod
    def to_true_iterable(cls: type[Self], s: Any) -> Iterable[Any]:
        """
        See :meth:`is_true_iterable`.

        Examples:
            - `to_true_iterable('abc')         # ['abc']`
            - `to_true_iterable(['ab', 'cd')]  # ['ab', 'cd']`
        """
        if cls.is_true_iterable(s):
            return s
        else:
            return [s]

    @classmethod
    def is_true_iterable(cls: type[Self], s: Any) -> bool:
        """
        Returns whether `s` is a probably "proper" iterable.
        In other words, iterable but not a string or bytes.

        Warning:
            This is not fully reliable.
            Types that do not define `__iter__` but are iterable
            via `__getitem__` will not be included.
        """
        return s is not None and isinstance(s, Iterable) and not isinstance(s, str) and not isinstance(s, ByteString)

    @classmethod
    @contextmanager
    def null_context(cls: type[Self]) -> Generator[None, None, None]:
        """
        Returns an empty context (literally just yields).
        Useful to simplify when a generator needs to be used depending on a switch.
        Ex::
            if verbose_flag:
                do_something()
            else:
                with Tools.silenced():
                    do_something()
        Can become::
            with (Tools.null_context() if verbose else Tools.silenced()):
                do_something()
        """
        yield

    @classmethod
    def look(cls: type[Self], obj: Y, attrs: str | Iterable[str] | Callable[[Y], Z]) -> Z | None:
        """
        Follows a dotted syntax for getting an item nested in class attributes.
        Returns the value of a chain of attributes on object `obj`,
        or None any object in that chain is None or lacks the next attribute.

        Example:
            Get a kitten's breed::

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

        Raises:
            TypeError:
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

    @classmethod
    def make_writer(cls: type[Self], writer: Writeable | Callable[[str], Any]) -> Writeable:
        if Writeable.isinstance(writer):
            return writer
        elif callable(writer):

            class W_(Writeable):
                def write(self: Self, msg):
                    writer(msg)

                def flush(self: Self):
                    pass

                def close(self: Self):
                    pass

            return W_()
        msg = f"{type(writer)} cannot be wrapped into a Writeable"
        raise XTypeError(msg)

    @classmethod
    def get_log_function(
        cls: type[Self],
        log: (
            Literal["stdout"]
            | Literal["stderr"]
            | Literal["DEBUG"]
            | Literal["INFO"]
            | Literal["WARNING"]
            | Literal["ERROR"]
            | Literal["FATAL"]
            | Literal["debug"]
            | Literal["info"]
            | Literal["warning"]
            | Literal["error"]
            | Literal["fatal"]
            | Literal[10]
            | Literal[20]
            | Literal[30]
            | Literal[40]
            | Literal[50]
            | Writeable
            | Callable[[str], Any]
            | None
        ),
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
        raise XTypeError(msg, actual=str(type(log)))

    @classmethod
    def sentinel(cls: type[Self], name: str) -> Any:
        class _Sentinel:
            def __eq__(self: Self, other):
                return self is other

            def __reduce__(self: Self):
                return name  # returning string is for singletons

            def __str__(self: Self) -> str:
                return name

            def __repr__(self: Self) -> str:
                return name

        return _Sentinel()

    def __repr__(self: Self) -> str:
        return self.__class__.__name__

    def __str__(self: Self) -> str:
        return self.__class__.__name__


__all__ = ["CommonTools", "Writeable"]
