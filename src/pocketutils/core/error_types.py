from __future__ import annotations

from dataclasses import dataclass, fields as dc_fields
from typing import Callable, TypeVar, overload

TExc = TypeVar("TExc", bound=BaseException)


@overload
def exception_type(
    *,
    message: Callable[..., str] | None = None,
    order: bool = False,
) -> Callable[[type[TExc]], type[TExc]]: ...
@overload
def exception_type(cls: type[TExc], /) -> type[TExc]: ...


def exception_type(
    cls: type[TExc] | None = None,
    /,
    *,
    message: Callable[..., str] | str | None = None,
    slots: bool | None = None,
    order: bool = False,
):
    """Modifies an exception subclass to behave like a dataclass.

    Does the following to `cls`:

    - Applies `@dataclass(frozen=True, slots=True, kw_only=True, order=order)`.
    - Calls `BaseException.__init__(msg)` (setting `BaseException.args` to `(msg,)`).
    - Fixes pickling (overrides `__reduce_ex__`).

    You can still define `__post_init__` and/or `__init__` like in a regular dataclass.

    Arguments:
        cls: The type to modify; must explicitly subclass an exception class.
        message: A template for the message; one of:
            - An f-string (called via `.format`) with the dataclass fields as parameters
            - A function of the exception instance
            - `None` (default), which will use a fallback that shows all the field values
        slots: Passed to `@dataclass`; if `None`, set to `True` unless `__post_init__` is defined.
            You probably don't need to change this.
        order: Passed to `@dataclass`.

    Example:
        ```
        @exception_type(message=f"Invalid name: {name}")
        class InvalidNameError(ValueError):
            name: str


        @exception_type(
            message=lambda self: f"{self.explanation}: {self.reason}"
        )
        class BadKeyError(KeyError):
            key: str | None
            count: int

            def __post_init__(self) -> None:
                self.explanation = "Malformed key '{key}'" if self.key else "Missing key"
        ```
    """

    def wrap(tp: type[TExc]) -> type[TExc]:
        user_post_init = tp.__dict__.get("__post_init__")
        # If `__post_init__` is defined, it's probably to define a field.
        slots_ = slots or (slots is None and user_post_init is None)
        tp = dataclass(frozen=True, slots=slots_, kw_only=True, order=order)(tp)

        def __post_init__(self) -> None:
            # Call user hook first so derived values exist before message formatting, if desired.
            if callable(user_post_init):
                user_post_init(self)
            fields = [f for f in dc_fields(self) if f.init]
            values = {f.name: getattr(self, f.name) for f in fields}
            if callable(message):
                msg = message(self, **values)
            elif isinstance(message, str):
                msg = message.format(**values)
            elif message is None:
                msg = f"{type(self).__name__}({', '.join(f'{k}={v}' for k, v in values.items())})"
            else:
                raise TypeError(f"Invalid type {type(message)} of message '{message}")
            # Normal exception behavior: args == (message,)
            BaseException.__init__(self, msg)

        def __reduce_ex__(self, protocol: int):
            kwargs = {f.name: getattr(self, f.name) for f in dc_fields(self) if f.init}
            return type(self)(**kwargs)

        tp.__post_init__ = __post_init__
        tp.__reduce_ex__ = __reduce_ex__
        return tp

    return wrap if cls is None else wrap(cls)
