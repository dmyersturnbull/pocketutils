import operator
from collections.abc import Callable, Iterable
from typing import Any, TypeVar

T = TypeVar("T", covariant=True)
Y = TypeVar("Y")
Z = TypeVar("Z")


def look(obj: Y, attrs: str | Iterable[str] | Callable[[Y], Z]) -> Z | None:
    if attrs is None:
        return obj
    if not isinstance(attrs, str) and hasattr(attrs, "__len__") and len(attrs) == 0:
        return obj
    if isinstance(attrs, str):
        attrs = operator.attrgetter(attrs)
    elif isinstance(attrs, Iterable) and all(isinstance(a, str) for a in attrs):
        attrs = operator.attrgetter(".".join(attrs))
    elif not callable(attrs):
        raise TypeError(
            f"Type {type(attrs)} unrecognized for key/attrib. Must be a function, string, or sequence of strings"
        )
    try:
        return attrs(obj)
    except AttributeError:
        return None


def null_context():
    yield


def is_lambda(function: Any) -> bool:
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


def parse_bool(s: str) -> bool:
    if isinstance(s, bool):
        return s
    if s.lower() == "false":
        return False
    if s.lower() == "true":
        return True
    raise ValueError(f"{s} is not true/false")


def parse_bool_flex(s: str) -> bool:
    mp = {
        **{v: True for v in {"true", "t", "yes", "y", "1"}},
        **{v: False for v in {"false", "f", "no", "n", "0"}},
    }
    v = mp.get(s.lower())
    if v is None:
        raise ValueError(f"{s.lower()} is not in {','.join(mp.keys())}")
    return v


__all__ = [
    "look",
    "null_context",
]
