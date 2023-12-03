# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
"""
Decorations.
"""
from __future__ import annotations

import enum
import html as _html
from abc import abstractmethod
from collections.abc import Callable, Collection, Generator, Iterable
from functools import total_ordering, wraps
from typing import Any, Literal, Self, TypeVar, final
from warnings import warn

T = TypeVar("T", bound=type)


def reserved(cls: T) -> T:
    """
    Empty but is declared for future use.
    """
    return cls


class CodeIncompleteError(NotImplementedError):
    """The code is not finished."""


class CodeRemovedError(NotImplementedError):
    """The code was removed."""


class PreviewWarning(UserWarning):
    """The code being called is a preview, unstable. or immature."""


@enum.unique
class CodeStatus(enum.Enum):
    """
    An enum for the quality/maturity of code,
    ranging from incomplete to deprecate.
    """

    INCOMPLETE = -2
    PREVIEW = -1
    STABLE = 0
    PENDING_DEPRECATION = 1
    DEPRECATED = 2
    REMOVED = 3

    @classmethod
    def of(cls: type[Self], x: int | str | CodeStatus) -> CodeStatus:
        if isinstance(x, str):
            return cls[x.lower().strip()]
        if isinstance(x, CodeStatus):
            return x
        if isinstance(x, int):
            return cls(x)
        msg = f"Invalid type {type(x)} for {x}"
        raise TypeError(msg)


def status(level: int | str | CodeStatus, vr: str | None = "", msg: str | None = None) -> Callable[..., Any]:
    """
    Annotate code quality. Emits a warning if bad code is called.

    Args:
        level: The quality / maturity
        vr: First version the status / warning applies to
        msg: Explanation and/or when it will be removed or completed
    """

    level = CodeStatus.of(level)

    @wraps(status)
    def dec(func):
        func.__status__ = level
        if level is CodeStatus.STABLE:
            return func
        elif level is CodeStatus.REMOVED:

            def my_fn(*_, **__):
                raise CodeRemovedError(f"{func.__name__} was removed (as of version: {vr}). {msg}")

            return wraps(func)(my_fn)

        elif level is CodeStatus.INCOMPLETE:

            def my_fn(*_, **__):
                error_msg = f"{func.__name__} is incomplete (as of version: {vr}). {msg}"
                raise CodeIncompleteError(error_msg)

            return wraps(func)(my_fn)
        elif level is CodeStatus.PREVIEW:

            def my_fn(*args, **kwargs):
                preview_msg = f"{func.__name__} is a preview or immature (as of version: {vr}). {msg}"
                warn(preview_msg, PreviewWarning)
                return func(*args, **kwargs)

            return wraps(func)(my_fn)
        elif level is CodeStatus.PENDING_DEPRECATION:

            def my_fn(*args, **kwargs):
                pending_dep_msg = f"{func.__name__} is pending deprecation (as of version: {vr}). {msg}"
                warn(pending_dep_msg, PendingDeprecationWarning)
                return func(*args, **kwargs)

            # noinspection PyDeprecation
            return wraps(func)(my_fn)
        elif level is CodeStatus.DEPRECATED:

            def my_fn(*args, **kwargs):
                dep_msg = f"{func.__name__} is deprecated (as of version: {vr}). {msg}"
                warn(dep_msg, DeprecationWarning)
                return func(*args, **kwargs)

            # noinspection PyDeprecation
            return wraps(func)(my_fn)
        raise AssertionError(f"What is {level}?")

    return dec


def incomplete(vr: str | None = "", msg: str | None = None) -> Callable[..., Any]:
    return status(CodeStatus.INCOMPLETE, vr, msg)


def preview(vr: str | None = "", msg: str | None = None) -> Callable[..., Any]:
    return status(CodeStatus.PREVIEW, vr, msg)


def pending_deprecation(vr: str | None = "", msg: str | None = None) -> Callable[..., Any]:
    return status(CodeStatus.PENDING_DEPRECATION, vr, msg)


def deprecated(vr: str | None = "", msg: str | None = None) -> Callable[..., Any]:
    return status(CodeStatus.DEPRECATED, vr, msg)


def removed(vr: str | None = "", msg: str | None = None) -> Callable[..., Any]:
    return status(CodeStatus.REMOVED, vr, msg)


class _Utils:
    @classmethod
    def exclude_fn(cls: type[Self], *items) -> Callable[str, bool]:
        fns = [cls._exclude_fn(x) for x in items]

        def exclude(s: str):
            return any(fn(s) for fn in fns)

        return exclude

    @classmethod
    def _exclude_fn(cls: type[Self], exclude) -> Callable[str, bool]:
        if exclude is None or exclude is False:
            return lambda s: False
        if isinstance(exclude, str):
            return lambda s: s == exclude
        elif isinstance(exclude, Collection):
            return lambda s: s in exclude
        elif callable(exclude):
            return exclude
        else:
            raise TypeError(str(exclude))

    @classmethod
    def gen_str(
        cls: type[Self],
        obj,
        fields: Collection[str] | None = None,
        *,
        exclude: Callable[[str], bool] = lambda _: False,
        address: bool = False,
    ) -> str:
        _name = obj.__class__.__name__
        _fields = ", ".join(
            k + "=" + ('"' + v + '"' if isinstance(v, str) else str(v))
            for k, v in cls.gen_list(obj, fields, exclude=exclude, address=address)
        )
        return f"{_name}({_fields})"

    @classmethod
    def gen_html(
        cls: type[Self],
        obj,
        fields: Collection[str] | None = None,
        *,
        exclude: Callable[[str], bool] = lambda _: False,
        address: bool = True,
    ) -> str:
        _name = obj.__class__.__name__
        _fields = ", ".join(
            f"{k}={_html.escape(v)}" for k, v in cls.gen_list(obj, fields, exclude=exclude, address=address)
        )
        return f"{_name}({_fields})"

    @classmethod
    def gen_list(
        cls: type[Self],
        obj: Any,
        fields: Collection[str] | None = None,
        *,
        exclude: Callable[[str], bool] = lambda _: False,
        address: bool = False,
    ) -> str:
        yield from _Utils.var_items(obj, fields, exclude=exclude)
        if address:
            yield "@", str(hex(id(obj)))

    @classmethod
    def var_items(
        cls: type[Self],
        obj: Any,
        fields: Collection[str] | None,
        exclude: Callable[[str], bool],
    ) -> Generator[tuple[str, Any], None, None]:
        yield from [
            (key, value)
            for key, value in vars(obj).items()
            if (fields is None) or (key in fields)
            if not key.startswith(f"_{obj.__class__.__name__}__") and not exclude(key)  # imperfect exclude mangled
        ]


def add_reprs(
    fields: Collection[str] | None = None,
    *,
    exclude: Collection[str] | Callable[[str], bool] | None | Literal[False] = None,
    exclude_from_str: Collection[str] | Callable[[str], bool] | None = None,
    exclude_from_repr: Collection[str] | Callable[[str], bool] | None = None,
    exclude_from_html: Collection[str] | Callable[[str], bool] | None = None,
    exclude_from_rich: Collection[str] | Callable[[str], bool] | None = None,
    address: bool = False,
    html: bool = True,
    rich: bool = True,
) -> Callable[..., Any]:
    """
    Auto-adds `__repr__`, `__str__`, `_repr_html`, and `__rich_repr__`
    that use instances' attributes (`vars`).
    """
    exclude_from_repr = _Utils.exclude_fn(exclude, exclude_from_repr)
    exclude_from_str = _Utils.exclude_fn(exclude, exclude_from_str)
    exclude_from_html = _Utils.exclude_fn(exclude, exclude_from_html)
    exclude_from_rich = _Utils.exclude_fn(exclude, exclude_from_rich)

    def __repr(self) -> str:
        return _Utils.gen_str(self, fields, exclude=exclude_from_repr, address=address)

    def __str(self) -> str:
        return _Utils.gen_str(self, fields, exclude=exclude_from_str)

    def __html(self) -> str:
        return _Utils.gen_html(self, fields, exclude=exclude_from_html)

    def __rich(self) -> Iterable[Any | tuple[Any] | tuple[str, Any] | tuple[str, Any, Any]]:
        yield from _Utils.gen_list(self, fields, exclude=exclude_from_rich)

    @wraps(add_reprs)
    def dec(cls: type) -> type:
        if cls.__str__ is object.__str__:
            cls.__str__ = __str
        if cls.__repr__ is object.__repr__:
            cls.__repr__ = __repr
        if html and not hasattr(cls, "_repr_html") and html:
            cls._repr_html_ = __html
        if rich and not hasattr(cls, "__rich_repr__") and rich:
            cls.__rich_repr__ = __rich
        return cls

    return dec


__all__ = [
    "abstractmethod",
    "total_ordering",
    "final",
    "CodeStatus",
    "status",
    "CodeIncompleteError",
    "PreviewWarning",
    "CodeRemovedError",
    "add_reprs",
    "deprecated",
    "pending_deprecation",
    "incomplete",
    "preview",
    "removed",
]
