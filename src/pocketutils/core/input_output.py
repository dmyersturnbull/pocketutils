from __future__ import annotations

import abc
import contextlib
import functools
import logging
from typing import TYPE_CHECKING, Any, Generic, Self, TypeVar, final

if TYPE_CHECKING:
    from io import StringIO

T_co = TypeVar("T_co", covariant=True)
Y = TypeVar("Y")
Z = TypeVar("Z")
logger = logging.getLogger("pocketutils")


class Writeable(Generic[T_co], metaclass=abc.ABCMeta):
    @classmethod
    def isinstance(cls: type[Self], value: T_co) -> bool:
        return hasattr(value, "write") and hasattr(value, "flush") and hasattr(value, "close")

    def write(self: Self, msg: T_co) -> int:
        raise NotImplementedError()

    def flush(self: Self) -> None:
        raise NotImplementedError()

    def close(self: Self) -> bool:
        raise NotImplementedError()

    def __enter__(self: Self) -> Self:
        return self

    def __exit__(self: Self, exc_type, exc_value, traceback) -> None:
        self.close()


@final
class DevNull(Writeable[T_co]):
    """Pretends to write but doesn't."""

    def write(self: Self, msg: T_co) -> int:
        return 0

    def flush(self: Self) -> None:
        pass

    def close(self: Self) -> None:
        pass

    def __enter__(self: Self) -> Self:
        return self

    def __exit__(self: Self, exc_type, exc_value, traceback) -> None:
        pass


class LogWriter(Writeable[str]):
    """
    A call to a logger at some level, pretending to be a writer.
    Has a write method, as well as flush and close methods that do nothing.
    """

    def __init__(self: Self, level: int | str) -> None:
        if isinstance(level, str):
            level = level.upper()
        self.level = logging.getLevelName(level)

    def write(self: Self, msg: str) -> int:
        getattr(logger, self.level)(msg)
        return len(msg)

    def flush(self: Self) -> None:
        pass

    def close(self: Self) -> None:
        pass

    def __enter__(self: Self) -> Self:
        return self

    def __exit__(self: Self, exc_type, exc_value, traceback) -> None:
        self.close()


class DelegatingWriter(Writeable):
    # we CANNOT override TextIOBase: It causes hangs
    def __init__(self: Self, *writers: Writeable) -> None:
        self._writers = writers

    def write(self: Self, s: T_co) -> int:
        x = 0
        for writer in self._writers:
            x += writer.write(s)
        return x

    def flush(self: Self) -> None:
        for writer in self._writers:
            writer.flush()

    def close(self: Self) -> None:
        for writer in self._writers:
            writer.close()

    def __enter__(self: Self) -> Self:
        return self

    def __exit__(self: Self, exc_type, exc_value, traceback) -> None:
        self.close()


class Capture:
    """
    A lazy string-like object that wraps around a StringIO result.
    It's too hard to fully subclass a string while keeping it lazy.
    """

    def __init__(self: Self, cio: StringIO) -> None:
        self.__cio = cio

    @property
    def lines(self: Self) -> list[str]:
        return self.split("\n")

    @property
    def value(self: Self) -> str:
        return self.__cio.getvalue()

    def __repr__(self: Self) -> str:
        return self.__cio.getvalue()

    def __str__(self: Self) -> str:
        return self.__cio.getvalue()

    def __len__(self: Self) -> int:
        return len(repr(self))

    def split(self: Self, x: str) -> list[str]:
        return self.__cio.getvalue().split(x)


@functools.total_ordering
class OpenMode(str):
    """
    Python file open modes (`open()`-compatible).
    Contains method :meth:`normalize` and properties :meth:`read`.

    Here are the flags:
        - 'r' means read
        - 'w' means overwrite
        - 'x' means exclusive write; complain if it exists
        - 'a' means append
        - 't' means text (default)
        - 'b' means binary
        - '+' means open for updating
    """

    def __new__(cls, s: str):
        for c in s:
            if c not in {"r", "w", "x", "a", "t", "b", "+", "U"}:
                msg = f"Invalid flag '{c}' in open mode '{s}'"
                raise ValueError(msg)
        if ("r" in s) + ("w" in s) + ("x" in s) + ("a" in s) > 1:
            raise ValueError(f"Too many 'r'/'w'/'x'/'a' flags in '{s}'")
        return str.__new__(cls, s)

    @property
    def read(self: Self) -> bool:
        return "w" not in self and "x" not in self and "a" not in self and "+" not in self

    @property
    def write(self: Self) -> bool:
        return ("w" in self or "x" in self or "a" in self) and "+" not in self

    @property
    def update(self: Self) -> bool:
        return "+" in self

    @property
    def overwrite(self: Self) -> bool:
        return "w" in self

    @property
    def safe(self: Self) -> bool:
        return "x" in self

    @property
    def append(self: Self) -> bool:
        return "a" in self

    @property
    def text(self: Self) -> bool:
        return "b" not in self

    @property
    def binary(self: Self) -> bool:
        return "b" in self

    def normalize(self: Self) -> Self:
        s = ""
        if self.append:
            s += "a"
        elif self.safe:
            s += "x"
        elif self.overwrite:
            s += "w"
        elif self.read:
            s += "r"
        if self.binary:
            s += "b"
        else:
            s += "t"
        if self.update:
            s += "+"
        return self.__class__(s)


def null_context():
    yield


def return_none_1_param(a: Any) -> None:
    return None


def return_none_2_params(a: Any, b: Any) -> None:
    return None


def return_none_3_params(a: Any, b: Any, c: Any) -> None:
    return None


@contextlib.contextmanager
def silenced(no_stdout: bool = True, no_stderr: bool = True):
    with contextlib.redirect_stdout(DevNull()) if no_stdout else null_context():
        with contextlib.redirect_stderr(DevNull()) if no_stderr else null_context():
            yield


__all__ = [
    "Writeable",
    "DevNull",
    "LogWriter",
    "DelegatingWriter",
    "Capture",
    "OpenMode",
]
