# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
"""

"""

import base64
import enum
import inspect
import json
from collections.abc import (
    Callable,
    ItemsView,
    KeysView,
    Mapping,
    Sequence,
    ValuesView,
)
from dataclasses import dataclass
from datetime import date, datetime, tzinfo
from datetime import time as _time
from decimal import Decimal
from typing import Any, Self
from uuid import UUID

try:
    import orjson
except ImportError:
    orjson = None

__all__ = ["NanInfHandling", "JsonEncoder", "JsonDecoder", "JsonUtils", "JsonTools"]

INF = float("Inf")
NEG_INF = float("-Inf")
NAN = float("NaN")


class NanInfHandling(enum.StrEnum):
    convert_to_str = enum.auto()
    convert_to_null = enum.auto()
    raise_error = enum.auto()


class MiscTypesJsonDefault(Callable[[Any], Any]):
    def __call__(self: Self, obj: Any) -> Any:
        """
        Tries to return a serializable result for `obj`.
        Meant to be passed as `default=` in `orjson.dumps`.
        Only encodes types that can always be represented exactly,
        without any loss of information. For that reason, it does not
        fall back to calling `str` or `repr` for unknown types.
        Handles, at least:

        - `decimal.Decimal` → str (scientific notation)
        - `complex` or `np.complexfloating` → str (e.g. "(3+1j)")
        - `typing.Mapping` → dict
        - `typing.ItemsView` → dict
        - `collections.abc.{Set,Sequence,...}` → list
        - `enum.Enum` → str (name)
        - `bytes | bytearray | memoryview` →  str (base-64)
        - `datetime.tzinfo` →  str (timezone name)
        - `typing.NamedTuple` →  dict
        - type or module →  str (name)

        Raise:
            TypeError: If none of those options worked
        """
        if obj is None:
            return obj  # we should never get here, but this seems safer
        elif isinstance(obj, str | int | float | datetime | date | _time | UUID):
            return obj  # we should never get here, but let's be safe
        elif isinstance(obj, Decimal | complex):
            return str(obj)
        elif isinstance(obj, enum.Enum):
            return obj.name
        elif isinstance(obj, bytes):
            return base64.b64decode(obj)
        elif isinstance(obj, bytes | bytearray | memoryview):
            return base64.b64decode(bytes(obj))
        elif isinstance(obj, tzinfo):
            return obj.tzname(datetime.now(tz=obj))
        elif isinstance(obj, set | frozenset | Sequence | KeysView | ValuesView):
            return list(obj)
        elif isinstance(obj, Mapping | ItemsView):
            return dict(obj)
        elif isinstance(obj, tuple) and hasattr(obj, "_asdict"):
            # namedtuple
            return obj._asdict()
        elif inspect.isclass(obj) or inspect.ismodule(obj):
            return obj.Self
        raise TypeError()


_misc_types_default = MiscTypesJsonDefault()


@dataclass(frozen=True, slots=True, kw_only=True)
class JsonEncoder:
    bytes_options: int
    str_options: int
    default: Callable[[Any], Any]
    prep: Callable[[Any], Any]

    def as_str(self: Self, data: Any) -> str:
        data = self.prep(data)
        x = orjson.dumps(data, default=self.default, option=self.str_options)
        return x.decode(encoding="utf-8") + "\n"

    def as_bytes(self: Self, data: Any) -> bytes | bytearray | memoryview:
        data = self.prep(data)
        return orjson.dumps(data, default=self.default, option=self.bytes_options)


@dataclass(frozen=True, slots=True)
class JsonDecoder:
    def from_bytes(self: Self, data: bytes | bytearray | memoryview) -> Any:
        if not isinstance(data, bytes | bytearray | memoryview):
            raise TypeError(str(type(data)))
        if not isinstance(data, bytes):
            data = bytes(data)
        if orjson:
            return orjson.loads(data)
        return json.loads(data.decode(encoding="utf-8"))

    def from_str(self: Self, data: str) -> Any:
        if orjson:
            return orjson.loads(data)
        json.loads(data)


@dataclass(slots=True, frozen=True)
class JsonUtils:
    def misc_types_default(self: Self) -> Callable[[Any], Any]:
        return _misc_types_default

    def new_default(
        self: Self,
        *fallbacks: Callable[[Any], Any] | None,
        first: Callable[[Any], Any] | None = _misc_types_default,
        last: Callable[[Any], Any] | None = str,
    ) -> Callable[[Any], Any]:
        """
        Creates a new method to be passed as `default=` to `orjson.dumps`.
        Tries, in order: :meth:`orjson_default`, `fallbacks`, then `str`.

        Args:
            first: Try this first
            fallbacks: Tries these, in order, after `first`, skipping any None
            last: Use this as the last resort; consider `str` or `repr`
        """
        then = [f for f in [first, *fallbacks] if f is not None]

        def _default(obj):
            for t in then:
                try:
                    return t(obj)
                except TypeError:  # noqa: S110
                    pass
                if last is None:
                    raise TypeError()
            return last(obj)

        _default.__name__ = f"default({', '.join([str(t) for t in then])})"
        return _default

    def decoder(self: Self) -> JsonDecoder:
        return JsonDecoder()

    def encoder(
        self: Self,
        *fallbacks: Callable[[Any], Any] | None,
        indent: bool = True,
        sort: bool = False,
        inf_handling: NanInfHandling = NanInfHandling.raise_error,
        nan_handling: NanInfHandling = NanInfHandling.raise_error,
        last: Callable[[Any], Any] | None = str,
    ) -> JsonEncoder:
        """
        Serializes to string with orjson, indenting and adding a trailing newline.
        Uses :meth:`orjson_default` to encode more types than orjson can.

        Args:
            indent: Indent by 2 spaces
            inf_handling: How to handle Inf and -Inf values in lists and Numpy arrays of floats
            nan_handling: How to handle NaN values in lists and Numpy arrays of floats
            sort: Sort keys with `orjson.OPT_SORT_KEYS`;
                  only for :meth:`pocketutils.tools.json_tools.JsonEncoder.as_str`
            last: Last resort option to encode a value
        """
        import orjson

        bytes_option = orjson.OPT_UTC_Z | orjson.OPT_NON_STR_KEYS
        str_option = orjson.OPT_UTC_Z
        if sort:
            bytes_option |= orjson.OPT_SORT_KEYS
            str_option |= orjson.OPT_SORT_KEYS
        if indent:
            str_option |= orjson.OPT_INDENT_2
        default = self.new_default(*fallbacks, first=_misc_types_default, last=last)

        def prep_fn(d):
            return self.prepare(d, inf_handling=inf_handling, nan_handling=nan_handling)

        return JsonEncoder(default=default, bytes_options=bytes_option, str_options=str_option, prep=prep_fn)

    def prepare(
        self: Self,
        data: Any,
        *,
        inf_handling: NanInfHandling,
        nan_handling: NanInfHandling,
    ):
        """
        Recursively replaces infinite float and numpy values with strings.
        Orjson encodes NaN, inf, and +inf as JSON null.
        This function converts to string as needed to preserve infinite values.
        Any float scalar (`np.floating` and `float`) will be replaced with a string.
        Any `np.ndarray`, whether it contains an infinite value or not, will be converted
        to an ndarray of strings.
        The returned result may still not be serializable with orjson or :meth:`orjson_bytes`.
        Trying those methods is the best way to test for serializeablity.
        """
        # we go to great lengths to avoid importing numpy
        # no np.isinf, np.isneginf, or np.isnan allowed
        # we can use the fact that Numpy float types compare to float,
        # including to -inf and +inf, where all comparisons between Inf/-Inf and NaN are False
        # So our logic is is_infinite := (data > NEG_INF) != (data < INF)
        # Meanwhile, we only need to deal with floats:
        # - int and bool stay as-is
        # - str stays as-is
        # - complex gets converted
        # figure out the type
        is_dict = hasattr(data, "items") and hasattr(data, "keys") and hasattr(data, "values")
        is_list = isinstance(data, list)
        is_list_with_inf = (
            is_list and all(isinstance(e, float) for e in data) and not all((v > NEG_INF) == (v < INF) for v in data)
        )
        is_list_with_nan = (
            is_list and all(isinstance(e, float) for e in data) and all(v == NEG_INF or v == INF for v in data)
        )
        is_np_array = type(data).__name__ == "ndarray" and hasattr(data, "dtype")
        is_np_array_with_inf = bool(
            is_np_array and str(data.dtype).startswith("float") and not all((v > NEG_INF) == (v < INF) for v in data),
        )
        is_np_array_with_nan = bool(
            is_np_array and str(data.dtype).startswith("float") and all(v == NEG_INF or v == INF for v in data),
        )
        is_inf_scalar = bool(
            (isinstance(data, float) or str(type(data)).startswith("<class 'numpy.float"))
            and (data > NEG_INF) != (data < INF),
        )
        is_nan_scalar = bool(
            (isinstance(data, float) or str(type(data)).startswith("<class 'numpy.float"))
            and (data == NEG_INF or data == INF),
        )
        # fix it
        if is_dict:
            return {
                str(k): self.prepare(v, inf_handling=inf_handling, nan_handling=nan_handling) for k, v in data.items()
            }
        if (is_list_with_inf or is_np_array_with_inf) and inf_handling is NanInfHandling.raise_error:
            raise ValueError(f"Array '{data}' contains Inf or -Inf")
        if (is_list_with_nan or is_np_array_with_nan) and nan_handling is NanInfHandling.raise_error:
            raise ValueError(f"Array '{data}' contains NaN")
        if is_inf_scalar and inf_handling is NanInfHandling.raise_error:
            raise ValueError(f"Value '{data}' is Inf or -Inf")
        if is_nan_scalar and nan_handling is NanInfHandling.raise_error:
            raise ValueError(f"Value '{data}' is NaN")
        if (
            (is_list_with_inf or is_np_array_with_inf or is_list_with_nan or is_list_with_nan)
            and inf_handling is NanInfHandling.convert_to_str
            and nan_handling is NanInfHandling.convert_to_str
        ):
            return [str(v) for v in data]
        if (
            (is_list_with_inf or is_np_array_with_inf)
            and (is_list_with_nan or is_list_with_nan)
            and inf_handling is NanInfHandling.convert_to_str
            and nan_handling is NanInfHandling.convert_to_null
        ):
            return [None if float(v) == NAN else str(v) for v in data]
        if (
            (is_list_with_inf or is_np_array_with_inf)
            and (is_list_with_nan or is_list_with_nan)
            and inf_handling is NanInfHandling.convert_to_null
            and nan_handling is NanInfHandling.convert_to_str
        ):
            return [None if float(v) == INF or float(v) == NEG_INF else str(v) for v in data]
        if is_np_array:
            return data.tolist()
        if is_list:
            return [self.prepare(e, inf_handling=inf_handling, nan_handling=nan_handling) for e in data]
        if (
            is_inf_scalar
            and inf_handling is NanInfHandling.convert_to_str
            or is_nan_scalar
            and nan_handling is NanInfHandling.convert_to_str
        ):
            return str(data)
        return data


JsonTools = JsonUtils()
