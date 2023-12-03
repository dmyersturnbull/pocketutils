# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
"""

"""

from __future__ import annotations

import abc
import logging
from collections import UserDict
from typing import TYPE_CHECKING, Any, Generic, Self, TypeVar, Unpack

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping


T_co = TypeVar("T_co", covariant=True)

logger = logging.getLogger("pocketutils")


def null_context():
    yield


class Sentinel:
    """
    A sentinel value tied to nothing more than a memory address.
    """

    @classmethod
    def new(cls: type[Self]) -> Sentinel:
        return Sentinel()

    def __init__(self: Self) -> None:
        pass


V = TypeVar("V")


class LazyWrapped(Generic[V], metaclass=abc.ABCMeta):
    def __init__(self: Self) -> None:
        self._v, self._exists = None, False

    def get(self: Self) -> V:
        if not self._exists:
            self._v = self._generate()
            self._exists = True
        return self._v

    @property
    def raw_value(self: Self) -> V:
        return self._v

    @property
    def is_defined(self: Self) -> bool:
        return self._exists

    @property
    def _name(self: Self) -> str:
        raise NotImplementedError()

    def _generate(self: Self) -> V:
        raise NotImplementedError()

    def __repr__(self: Self) -> str:
        return self._name + "[" + (repr(self._v) if self.is_defined else "⌀") + "]"

    def __str__(self: Self) -> str:
        return self._name + "[" + (str(self._v) if self.is_defined else "⌀") + "]"

    def __eq__(self: Self, other: Self) -> bool:
        return type(self) == type(other) and self.is_defined == other.is_defined and self.raw_value == other.raw_value


class PlainLazyWrapped(LazyWrapped, metaclass=abc.ABCMeta):
    pass


class ClearableLazyWrapped(LazyWrapped, metaclass=abc.ABCMeta):
    def clear(self: Self) -> None:
        self._exists = False


class LazyWrap:
    @classmethod
    def new_type(cls: type[Self], dtype: str, generator: Callable[[], V]) -> type[PlainLazyWrapped]:
        # noinspection PyTypeChecker
        return cls._new_type(dtype, generator, PlainLazyWrapped)

    @classmethod
    def new_clearable_type(
        cls: type[Self],
        dtype: str,
        generator: Callable[[], V],
    ) -> type[ClearableLazyWrapped]:
        # noinspection PyTypeChecker
        return cls._new_type(dtype, generator, ClearableLazyWrapped)

    @classmethod
    def _new_type(
        cls: type[Self],
        dtype: str,
        generator: Callable[[], V],
        superclass: type[LazyWrapped],
    ) -> type[LazyWrapped]:
        """
        Creates a new mutable wrapped type.

        Example:
            >>> LazyRemoteTime = LazyWrap.new_type('RemoteTime', lambda: ...)
            >>> dt = LazyRemoteTime()  # nothing happens
            >>> dt.get()  # has a value

        Args:
            dtype: The name of the data type, such as 'datetime' if generator=datetime.now
            generator: This is called to (lazily) initialize an instance of the LazyWrapped

        Returns:
            A new class subclassing LazyWrapped
        """

        class X(superclass):
            @property
            def _name(self: Self):
                return dtype

            def _generate(self: Self):
                return generator()

        X.__name__ = superclass.__name__ + dtype
        return X


class DictNamespace(UserDict):
    """
    Behaves like a dict and a `SimpleNamespace`.
    This means it has a length, can be iterated over, etc., and can be accessed via `.`.
    """

    def __init__(self: Self, **kwargs: Unpack[Mapping[str, Any]]) -> None:
        super().__init__(**kwargs)
        self.__dict__.update(kwargs)

    def __eq__(self: Self, other: Self | DictNamespace) -> bool:
        if isinstance(self, DictNamespace) and isinstance(other, DictNamespace):
            return self.__dict__ == other.__dict__
        return NotImplemented


class OptRow:
    """
    Short for 'optional row'.
    A wrapper around a NamedTuple that returns None if the key doesn't exist.
    This is intended for Pandas itertuples().
    """

    def __init__(self: Self, row) -> None:
        self._row = row

    def __getattr__(self: Self, item: str) -> Any:
        try:
            return getattr(self._row, item)
        except AttributeError:
            return None

    def opt(self: Self, item: str) -> Any:
        return getattr(self, item)

    def req(self: Self, item: str) -> Any:
        return getattr(self._row, item)

    def __contains__(self: Self, item) -> bool:
        try:
            getattr(self._row, item)
            return True
        except AttributeError:
            return False

    def items(self: Self) -> Iterable[Any]:
        # noinspection PyProtectedMember
        return self._row._asdict()

    def keys(self: Self) -> Iterable[Any]:
        # noinspection PyProtectedMember
        return self._row._asdict().keys()

    def values(self: Self) -> Iterable[Any]:
        # noinspection PyProtectedMember
        return self._row._asdict().values()

    def __repr__(self: Self) -> str:
        return self.__class__.__name__ + "@" + hex(id(self))

    def __str__(self: Self) -> str:
        return self.__class__.__name__

    def __eq__(self: Self, other: Self) -> bool:
        # noinspection PyProtectedMember
        return self._row == other._row


__all__ = [
    "Sentinel",
    "OptRow",
    "LazyWrap",
    "DictNamespace",
]
