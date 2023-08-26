import inspect
import sys
import typing
from collections.abc import Callable, Generator, Mapping
from types import MappingProxyType
from typing import Any, Self, TypeVar

from pocketutils.core.exceptions import InjectionError

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class ReflectionTools:
    @classmethod
    def get_generic_arg(cls: type[Self], clazz: type[T_co], bound: type[T_co] | None = None) -> type[T_co]:
        """
        Finds the generic argument (specific TypeVar) of a :class:`~typing.Generic` class.
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
            msg = f"Failed to get generic type on {cls}"
            raise AssertionError(msg)
        if not issubclass(param, bound):
            msg = f"{param} is not a {bound}"
            raise AssertionError(msg)
        return param

    @classmethod
    def subclass_dict(cls: type[Self], clazz: type[T_co], concrete: bool = False) -> Mapping[str, type[T_co]]:
        return {c.__name__: c for c in cls.subclasses(clazz, concrete=concrete)}

    @classmethod
    def subclasses(cls: type[Self], clazz: type[T_co], concrete: bool = False) -> Generator[type[T_co], None, None]:
        for subclass in clazz.__subclasses__():
            yield from cls.subclasses(subclass, concrete=concrete)
            if not concrete or not inspect.isabstract(subclass) and not subclass.__name__.startswith("_"):
                yield subclass

    @classmethod
    def default_arg_values(cls: type[Self], func: Callable[..., Any]) -> Mapping[str, Any | None]:
        return {k: v.default for k, v in cls.optional_args(func).items()}

    @classmethod
    def required_args(cls: type[Self], func: Callable[..., Any]) -> Mapping[str, MappingProxyType]:
        """
        Finds parameters that lack default values.

        Args:
            func: A function or method

        Returns:
            A dict mapping parameter names to instances of `MappingProxyType`,
            just as `inspect.signature(func).parameters` does.
        """
        return cls._args(func, True)

    @classmethod
    def optional_args(cls: type[Self], func: Callable[..., Any]) -> Mapping[str, MappingProxyType]:
        """
        Finds parameters that have default values.

        Args:
            func: A function or method

        Returns:
            A dict mapping parameter names to instances of `MappingProxyType`,
            just as `inspect.signature(func).parameters` does.
        """
        return cls._args(func, False)

    @classmethod
    def injection(cls: type[Self], fully_qualified: str, clazz: type[T]) -> type[T]:
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
            raise InjectionError(
                msg,
            ) from None

    @classmethod
    def _args(cls: type[Self], func: Callable[..., Any], req: bool) -> dict[str, inspect.Parameter]:
        signature = inspect.signature(func)
        return {
            k: v
            for k, v in signature.parameters.items()
            if req and v.default is inspect.Parameter.empty or not req and v.default is not inspect.Parameter.empty
        }


__all__ = ["ReflectionTools"]
