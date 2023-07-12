from __future__ import annotations

import abc
import contextlib
import logging
from pathlib import Path, PurePath
from typing import Any, TypeVar
from urllib import request

T = TypeVar("T", covariant=True)
Y = TypeVar("Y")
Z = TypeVar("Z")
logger = logging.getLogger("pocketutils")


class Writeable(metaclass=abc.ABCMeta):
    @classmethod
    def isinstance(cls, value: Any):
        return hasattr(value, "write") and hasattr(value, "flush") and hasattr(value, "close")

    def write(self, msg):
        raise NotImplementedError()

    def flush(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class DevNull(Writeable):
    """Pretends to write but doesn't."""

    def write(self, msg):
        pass

    def flush(self):
        pass

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class LogWriter:
    """
    A call to a logger at some level, pretending to be a writer.
    Has a write method, as well as flush and close methods that do nothing.
    """

    def __init__(self, level: int | str):
        if isinstance(level, str):
            level = level.upper()
        self.level = logging.getLevelName(level)

    def write(self, msg: str):
        getattr(logger, self.level)(msg)

    def flush(self):
        pass

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class DelegatingWriter:
    # we CANNOT override TextIOBase: It causes hangs
    def __init__(self, *writers):
        self._writers = writers

    def write(self, s):
        for writer in self._writers:
            writer.write(s)

    def flush(self):
        for writer in self._writers:
            writer.flush()

    def close(self):
        for writer in self._writers:
            writer.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class Capture:
    """
    A lazy string-like object that wraps around a StringIO result.
    It's too hard to fully subclass a string while keeping it lazy.
    """

    def __init__(self, cio):
        self.__cio = cio

    @property
    def lines(self):
        return self.split("\n")

    @property
    def value(self):
        return self.__cio.getvalue()

    def __repr__(self):
        return self.__cio.getvalue()

    def __str__(self):
        return self.__cio.getvalue()

    def __len__(self):
        return len(repr(self))

    def split(self, x: str):
        return self.__cio.getvalue().split(x)


class OpenMode(str):
    """
    Python file open modes (``open()``-compatible).
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

    @property
    def read(self) -> bool:
        return "w" not in self and "x" not in self and "a" not in self

    @property
    def write(self) -> bool:
        return "w" in self or "x" in self or "a" in self

    @property
    def overwrite(self) -> bool:
        return "w" in self

    @property
    def safe(self) -> bool:
        return "x" in self

    @property
    def append(self) -> bool:
        return "a" in self

    @property
    def text(self) -> bool:
        return "b" not in self

    @property
    def binary(self) -> bool:
        return "b" in self

    def normalize(self) -> str:
        s = self.replace("U", "")
        if "r" not in self and "w" not in self and "x" not in self and "a" not in self:
            s = "r" + self
        if "t" not in self and "b" not in self:
            s = "t" + self
        return s

    def __eq__(self, other):
        if isinstance(other, OpenMode):
            return self.normalize() == other.normalize()
        elif isinstance(other, str):
            return self.normalize() == OpenMode(other).normalize()
        raise TypeError(f"Wrong type {type(other)} of '{other}'")

    def __ne__(self, other):
        if isinstance(other, OpenMode):
            return self.normalize() != other.normalize()
        elif isinstance(other, str):
            return self.normalize() != OpenMode(other).normalize()
        raise TypeError(f"Wrong type {type(other)} of '{other}'")

    def __lt__(self, other):
        if isinstance(other, OpenMode):
            return self.normalize() < other.normalize()
        elif isinstance(other, str):
            return self.normalize() < OpenMode(other).normalize()
        raise TypeError(f"Wrong type {type(other)} of '{other}'")

    def __gt__(self, other):
        if isinstance(other, OpenMode):
            return self.normalize() > other.normalize()
        elif isinstance(other, str):
            return self.normalize() > OpenMode(other).normalize()
        raise TypeError(f"Wrong type {type(other)} of '{other}'")

    def __le__(self, other):
        if isinstance(other, OpenMode):
            return self.normalize() <= other.normalize()
        elif isinstance(other, str):
            return self.normalize() <= OpenMode(other).normalize()
        raise TypeError(f"Wrong type {type(other)} of '{other}'")

    def __ge__(self, other):
        if isinstance(other, OpenMode):
            return self.normalize() >= other.normalize()
        elif isinstance(other, str):
            return self.normalize() >= OpenMode(other).normalize()
        raise TypeError(f"Wrong type {type(other)} of '{other}'")


def null_context():
    yield


@contextlib.contextmanager
def silenced(no_stdout: bool = True, no_stderr: bool = True):
    with contextlib.redirect_stdout(DevNull()) if no_stdout else null_context():
        with contextlib.redirect_stderr(DevNull()) if no_stderr else null_context():
            yield


def stream_download(url: str, path: PurePath | str):
    with request.urlopen(url) as stream:
        with Path(path).open("wb") as out:
            data = stream.read(1024 * 1024)
            while data:
                out.write(data)
                data = data.read(1024 * 1024)


__all__ = [
    "Writeable",
    "DevNull",
    "LogWriter",
    "DelegatingWriter",
    "Capture",
    "OpenMode",
]
