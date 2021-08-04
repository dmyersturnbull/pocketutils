"""
Experimental replacement for fancy consoles.
"""
import abc
import logging
import sys
from typing import Callable, Optional, TypeVar, Generic, Sequence

from colorama import Style, Fore

from pocketutils.core.input_output import Writeable
from pocketutils.misc.messages import *


logger = logging.getLogger("pocketutils")
L = TypeVar("L", covariant=True)
M = TypeVar("M", covariant=True)


class AbstractColorConsole(Generic[L, M], metaclass=abc.ABCMeta):
    def print(self, *lines: str, level: L, mod: Optional[M] = None) -> None:
        for line in self.format(*lines, level=level, mod=mod):
            self._stream.write(line)

    @property
    def _stream(self) -> Writeable:
        raise NotImplementedError()

    @property
    def _reset(self) -> int:
        return Style.RESET_ALL

    def format(self, *lines: str, level: L, mod: Optional[M] = None) -> Sequence[str]:
        raise NotImplementedError()


class ColorConsole(AbstractColorConsole[MsgLevel, bool]):
    def __init__(
        self,
        stream: Writeable,
        top: str,
        bottom: str,
        left: str,
        right: str,
        pad_top: int,
        pad_bottom: int,
        width: int,
        mapping: Callable[[MsgLevel], int],
    ):
        self._the_stream = stream
        self._top, self._bottom, self._left, self._right = top, bottom, left, right
        self._pad_top, self._pad_bottom = pad_top, pad_bottom
        self._width = width
        self._mapping = mapping

    def format(self, *lines: str, level: MsgLevel, mod: Optional[bool] = None) -> Sequence[str]:
        color = str(self._mapping(level))
        width = self._width
        reset = str(self._reset)
        if mod:
            top, bottom, left, right = self._top, self._bottom, self._left, self._right
            pad_top = ["" for _ in range(self._pad_top)]
            pad_bottom = ["" for _ in range(self._pad_bottom)]
        else:
            top, bottom, left, right = "", "", "", ""
            pad_top, pad_bottom = [], []

        def cl(text: str):
            return color + left + text.center(width - len(left) - len(right)) + right + reset

        return [
            *pad_top,
            color + top * width + reset,
            *[cl(line) for line in lines],
            color + bottom * width + reset,
            *pad_bottom,
        ]

    @property
    def _stream(self) -> Writeable:
        return self._the_stream


class ColorConsoleBuilder:
    def __init__(self):
        self._mapping = {}
        self._width = 100
        self._top, self._bottom = "-", "-"
        self._left, self._right = "", ""
        self._pad_top, self._pad_bottom = 1, 1

    def add(self, level: MsgLevel, color: int) -> __qualname__:
        self._mapping[level] = color
        return self

    def width(self, w: int) -> __qualname__:
        self._width = w
        return self

    def top(self, top: str) -> __qualname__:
        self._top = top
        return self

    def bottom(self, bottom: str) -> __qualname__:
        self._bottom = bottom
        return self

    def left(self, left: str) -> __qualname__:
        self._left = left
        return self

    def right(self, right: str) -> __qualname__:
        self._right = right
        return self

    def pad_top(self, i: int) -> __qualname__:
        self._pad_top = i
        return self

    def pad_bottom(self, i: int) -> __qualname__:
        self._pad_bottom = i
        return self

    def build(self, sink: Optional[Writeable] = None) -> ColorConsole:
        if sink is None:
            sink = sys.stdout

        def fn(level: MsgLevel):
            return self._mapping[level]

        return ColorConsole(
            sink,
            self._top,
            self._bottom,
            self._left,
            self._right,
            self._pad_top,
            self._pad_bottom,
            self._width,
            fn,
        )


class ColorConsoles:
    @classmethod
    def new(cls) -> ColorConsoleBuilder:
        return ColorConsoleBuilder()

    @classmethod
    def default(cls) -> ColorConsoleBuilder:
        mapping = {
            MsgLevel.INFO: Style.BRIGHT,
            MsgLevel.NOTICE: Fore.BLUE,
            MsgLevel.SUCCESS: Fore.GREEN,
            MsgLevel.WARNING: Fore.MAGENTA,
            MsgLevel.FAILURE: Fore.RED,
        }
        builder = ColorConsoleBuilder()
        for k, v in mapping.items():
            builder.add(k, v)
        return builder


__all__ = ["AbstractColorConsole", "ColorConsole", "ColorConsoles"]
