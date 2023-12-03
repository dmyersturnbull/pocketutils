# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
"""

"""

import inspect
import sys
import typing
from collections.abc import Callable, Generator, Mapping
from dataclasses import dataclass
from inspect import Parameter
from types import MappingProxyType
from typing import Any, Self, TypeVar

__all__ = ["ReflectionUtils", "ReflectionTools"]

T_co = TypeVar("T_co", covariant=True)


@dataclass(slots=True, frozen=True)
class ReflectionUtils:
    def get_generic_arg(self: Self, clazz: type[T_co], bound: type[T_co] | None = None) -> type[T_co]:
        """
        Finds the generic argument (specific TypeVar) of a `typing.Generic` class.
        **Assumes that `clazz` only has one type parameter. Always returns the first.**

        Args:
            clazz: The Generic class
            bound: If non-None, requires the returned type to be a subclass of `bound` (or equal to it)

        Returns:
            The class

        Raises:
            AssertionError: For most errors
        """
        bases = clazz.__orig_bases__
        try:
            param = typing.get_args(bases[0])[0]
        except KeyError:
            msg = f"Failed to get generic type on {clazz}"
            raise AssertionError(msg)
        if not issubclass(param, bound):
            msg = f"{param} is not a {bound}"
            raise AssertionError(msg)
        return param

    def subclass_dict(self: Self, clazz: type[T_co], concrete: bool = False) -> Mapping[str, type[T_co]]:
        return {c.__name__: c for c in self.subclasses(clazz, concrete=concrete)}

    def subclasses(self: Self, clazz: type[T_co], concrete: bool = False) -> Generator[type[T_co], None, None]:
        for subclass in clazz.__subclasses__():
            yield from self.subclasses(subclass, concrete=concrete)
            if not concrete or not inspect.isabstract(subclass) and not subclass.__name__.startswith("_"):
                yield subclass

    def default_arg_values(self: Self, func: Callable[..., Any]) -> Mapping[str, Any | None]:
        return {k: v.default for k, v in self.optional_args(func).items()}

    def required_args(self: Self, func: Callable[..., Any]) -> Mapping[str, MappingProxyType]:
        """
        Finds parameters that lack default values.

        Args:
            func: A function or method

        Returns:
            A dict mapping parameter names to instances of `MappingProxyType`,
            just as `inspect.signature(func).parameters` does.
        """
        return self._args(func, True)

    def optional_args(self: Self, func: Callable[..., Any]) -> Mapping[str, Parameter]:
        """
        Finds parameters that have default values.

        Args:
            func: A function or method

        Returns:
            A dict mapping parameter names to instances of `MappingProxyType`,
            just as `inspect.signature(func).parameters` does.
        """
        return self._args(func, False)

    def injection(self: Self, fully_qualified: str, clazz: type[T_co]) -> type[T_co]:
        """
        Gets a **class** by its fully-resolved class name.

        Args:
            fully_qualified: Dotted syntax
            clazz: Class

        Returns:
            The Type

        Raises:
            InjectionError: If the class was not found
        """
        s = fully_qualified
        mod = s[: s.rfind(".")]
        clz = s[s.rfind(".") :]
        try:
            return getattr(sys.modules[mod], clz)
        except AttributeError:
            msg = f"Did not find {clazz} by fully-qualified class name {fully_qualified}"
            raise LookupError(msg) from None

    def _args(self: Self, func: Callable[..., Any], req: bool) -> dict[str, Parameter]:
        signature = inspect.signature(func)
        return {
            k: v
            for k, v in signature.parameters.items()
            if req and v.default is Parameter.empty or not req and v.default is not Parameter.empty
        }


ReflectionTools = ReflectionUtils()
