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

__all__ = ["JsonEncoder", "JsonDecoder", "JsonUtils", "JsonTools"]

INF = float("Inf")
NEG_INF = float("-Inf")
NAN = float("NaN")


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
    prep: Callable[[Any], Any] | None

    def as_bytes(self: Self, data: Any) -> bytes | bytearray | memoryview:
        if self.prep is not None:
            data = self.prep(data)
        return orjson.dumps(data, default=self.default, option=self.bytes_options)

    def as_str(self: Self, data: Any) -> str:
        if self.prep is not None:
            data = self.prep(data)
        x = orjson.dumps(data, default=self.default, option=self.str_options)
        return x.decode(encoding="utf-8") + "\n"


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
                except TypeError:
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
        preserve_inf: bool = True,
        last: Callable[[Any], Any] | None = str,
    ) -> JsonEncoder:
        """
        Serializes to string with orjson, indenting and adding a trailing newline.
        Uses :meth:`orjson_default` to encode more types than orjson can.

        Args:
            indent: Indent by 2 spaces
            preserve_inf: Preserve infinite values with :meth:`preserve_inf`
            sort: Sort keys with `orjson.OPT_SORT_KEYS`;
                  only for :meth:`typeddfs.json_utils.JsonEncoder.as_str`
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
        prep = self.preserve_inf if preserve_inf else None
        return JsonEncoder(default=default, bytes_options=bytes_option, str_options=str_option, prep=prep)

    def preserve_inf(self: Self, data: Any) -> Any:
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
        # - complex gets converted to
        if isinstance(data, Mapping):
            return {str(k): self.preserve_inf(v) for k, v in data.items()}
        elif (
            (isinstance(data, Sequence) or type(data).__name__ == "ndarray")
            and not isinstance(data, str)
            and not isinstance(data, bytes | bytearray | memoryview)
        ):
            is_np_float_array = hasattr(data, "dtype") and str(data.dtype).startswith("dtype(float")
            if (
                is_np_float_array
                or all(isinstance(v, float) for v in data)
                and all((v > NEG_INF) != (v < INF) for v in data)
            ):
                # it's a list or array of floats containing -Inf or +Inf
                # ==> convert to str to preserve
                return [str(v) for v in data]
            elif is_np_float_array:
                # it's an array of other types, or of floats containing neither -Inf nor +Inf
                # ==> convert to list (faster than recursing)
                # noinspection PyUnresolvedReferences
                return data.tolist()
            else:
                # it's an array of other types, or of floats containing neither -Inf nor +Inf
                # ==> return float list as-is
                return data
        elif (isinstance(data, float) or (hasattr(data, "dtype") and str(data.dtype).startswith("dtype(float"))) and (
            data > NEG_INF
        ) != (data < INF):
            # single float value with -Inf or +Inf
            # ==> preserve inf
            return str(data)
        elif type(data).__name__ == "ndarray" and hasattr(data, "dtype"):
            # it's a non-float Numpy array
            # ==> convert to list
            return data.astype(str).tolist()
        return data


JsonTools = JsonUtils()
