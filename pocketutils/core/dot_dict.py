from __future__ import annotations

import pickle
import sys
from collections.abc import ByteString, Callable, Collection, Mapping, Sequence
from copy import copy
from datetime import date, datetime
from typing import Any, TypeVar

import orjson
import tomlkit

from pocketutils.core.exceptions import XKeyError, XTypeError, XValueError

T = TypeVar("T")
PICKLE_PROTOCOL = 5


def _json_encode_default(obj: Any) -> Any:
    if isinstance(obj, NestedDotDict):
        # noinspection PyProtectedMember
        return dict(obj._x)


class NestedDotDict(Mapping):
    """
    A thin wrapper around a nested dict to make getting values easier.
    This was designed as a wrapper for TOML, but it works more generally too.

    Keys must be strings that do not contain a dot (.).
    A dot is reserved for splitting values to traverse the tree.
    For example, ``dotdict["pet.species.name"]``.
    """

    @classmethod
    def parse_toml(cls, data: str) -> NestedDotDict:
        return cls(tomlkit.loads(data))

    @classmethod
    def parse_json(cls, data: str) -> NestedDotDict:
        """
        Parses JSON from a string, into a NestedDotDict.
        If the JSON data is a list type, converts into a dict with the key ``data``.
        """
        data = orjson.loads(data.encode(encoding="utf-8"))
        if isinstance(data, list):
            data = dict(enumerate(data))
        return cls(data)

    @classmethod
    def parse_pickle(cls, data: ByteString) -> NestedDotDict:
        if not isinstance(data, bytes):
            data = bytes(data)
        return NestedDotDict(pickle.loads(data))

    def to_pickle(self, protocol: int = PICKLE_PROTOCOL) -> bytes:
        """
        Writes to a pickle file.
        """
        return pickle.dumps(self._x, protocol=PICKLE_PROTOCOL)

    def __init__(self, x: Mapping[str, Any]) -> None:
        """
        Constructor.

        Raises:
            XValueError: If a key (in this dict or a sub-dict) is not a str or contains a dot
        """
        if not (hasattr(x, "items") and hasattr(x, "keys") and hasattr(x, "values")):
            raise XTypeError(
                f"Type {type(x)} for value {x} appears not to be dict-like", actual=str(type(x))
            )
        bad = [k for k in x if not isinstance(k, str)]
        if len(bad) > 0:
            raise XValueError(f"Keys were not strings for these values: {bad}", value=bad)
        bad = [k for k in x if "." in k]
        if len(bad) > 0:
            raise XValueError(f"Keys contained dots (.) for these values: {bad}", value=bad)
        self._x = x
        # Let's make sure this constructor gets called on sub-dicts:
        self.leaves()

    def to_json(self, *, indent: bool = False) -> str:
        """
        Returns JSON text.
        """
        kwargs = dict(option=orjson.OPT_INDENT_2) if indent else {}
        encoded = orjson.dumps(self._x, default=_json_encode_default, **kwargs)
        return encoded.decode(encoding="utf-8")

    def to_toml(self) -> str:
        """
        Returns TOML text.
        """
        return tomlkit.dumps(self._x)

    def n_elements_total(self) -> int:
        return len(self._all_elements())

    def n_bytes_total(self) -> int:
        return sum([sys.getsizeof(x) for x in self._all_elements()])

    def _all_elements(self) -> Sequence[Any]:
        i = []
        for key, value in self._x.items():
            if value is not None and isinstance(value, Mapping):
                i += NestedDotDict(value)._all_elements()
            elif (
                value is not None
                and isinstance(value, Collection)
                and not isinstance(value, str)
                and not isinstance(value, ByteString)
            ):
                i += list(value)
            else:
                i.append(value)
        return i

    def leaves(self) -> Mapping[str, Any]:
        """
        Gets the leaves in this tree.

        Returns:
            A dict mapping dot-joined keys to their values
        """
        mp = {}
        for key, value in self._x.items():
            if value is not None and isinstance(value, Mapping):
                mp.update({key + "." + k: v for k, v in NestedDotDict(value).leaves().items()})
            else:
                mp[key] = value
        return mp

    def sub(self, items: str) -> NestedDotDict:
        """
        Returns the dictionary under (dotted) keys ``items``.

        See Also:
            :meth:`sub_opt`
        """
        return NestedDotDict(self[items])

    def sub_opt(self, items: str) -> NestedDotDict:
        """
        Returns the dictionary under (dotted) keys ``items``, or empty if a key is not found.

        See Also:
            :meth:`sub`
        """
        try:
            return NestedDotDict(self[items])
        except XKeyError:
            return NestedDotDict({})

    def exactly(self, items: str, astype: type[T]) -> T:
        """
        Gets the key ``items`` from the dict if it has type ``astype``.

        Args:
            items: The key hierarchy, with a dot (.) as a separator
            astype: The type, which will be checked using ``isinstance``

        Returns:
            The value in the required type

        Raises:
            XTypeError: If not ``isinstance(value, astype)``
        """
        z = self[items]
        if not isinstance(z, astype):
            raise XTypeError(
                f"Value {z} from {items} is a {type(z)}, not {astype}",
                actual=str(type(z)),
                expected=str(astype),
            )
        return z

    def get_as(self, items: str, astype: Callable[[Any], T], default: T | None = None) -> T | None:
        """
        Gets the value of an *optional* key, or ``default`` if it doesn't exist.
        Calls ``astype(value)`` on the value before returning.

        See Also:
            :meth:`req_as`
            :meth:`exactly`

        Args:
            items: The key hierarchy, with a dot (.) as a separator.
                   Ex: ``animal.species.name``.
            astype: Any function that converts the found value to type ``T``.
                    Can be a ``Type``, such as ``int``.
                    Despite the annotated type, this function only needs to accept the actual value of the key
                    as input, not ``Any``.
            default: Return this value if the key is not found (at any level)

        Returns:
            The value of found key in this dot-dict, or ``default``.

        Raises:
            XValueError: Likely exception raised if calling ``astype`` fails
        """
        x = self.get(items)
        if x is None:
            return default
        if astype is date:
            return self._to_date(x)
        if astype is datetime:
            return self._to_datetime(x)
        return astype(x)

    def req_as(self, items: str, astype: Callable[[Any], T] | None) -> T:
        """
        Gets the value of a *required* key.
        Calls ``astype(value)`` on the value before returning.

        See Also:
            :meth:`req_as`
            :meth:`exactly`

        Args:
            items: The key hierarchy, with a dot (.) as a separator.
                   Ex: ``animal.species.name``.
            astype: Any function that converts the found value to type ``T``.
                    Can be a ``Type``, such as ``int``.
                    Despite the annotated type, this function only needs to accept the actual value of the key
                    as input, not ``Any``.

        Returns:
            The value of found key in this dot-dict.

        Raises:
            XKeyError: If the key is not found (at any level).
            XValueError: Likely exception raised if calling ``astype`` fails
        """
        x = self[items]
        return astype(x)

    def get_list_as(
        self, items: str, astype: Callable[[Any], T], default: Sequence[T] | None = None
    ) -> Sequence[T] | None:
        """
        Gets list values from an *optional* key.
        Note that ``astype`` here converts elements *within* the list, not the whole list.
        Also see ``req_list_as``.

        Args:
            items: The key hierarchy, with a dot (.) as a separator. Ex: ``animal.species.name``.
            astype: Any function that converts the found value to type ``T``. Ex: ``int``.
            default: Return this value if the key wasn't found

        Returns:
            ``[astype(v) for v in self[items]]``, or ``default`` if ``items`` was not found.

        Raises:
            XValueError: Likely exception raised if calling ``astype`` fails
            XTypeError: If the found value is not a (non-``str``) ``Sequence``
        """
        x = self.get(items)
        if x is None:
            return default
        if not isinstance(x, Sequence) or isinstance(x, str):
            raise XTypeError(f"Value {x} is not a list for lookup {items}", actual=str(type(x)))
        return [astype(y) for y in x]

    def req_list_as(self, items: str, astype: Callable[[Any], T] | None) -> Sequence[T]:
        """
        Gets list values from a *required* key.
        Note that ``astype`` here converts elements *within* the list, not the whole list.
        Also see ``get_list_as``.

        Args:
            items: The key hierarchy, with a dot (.) as a separator. Ex: ``animal.species.name``.
            astype: Any function that converts the found value to type ``T``. Ex: ``int``.

        Returns:
            ``[astype(v) for v in self[items]]``

        Raises:
            XValueError: Likely exception raised if calling ``astype`` fails
            XTypeError: If the found value is not a (non-``str``) ``Sequence``
            XKeyError: If the key was not found (at any level)
        """
        x = self[items]
        if not isinstance(x, Sequence) or isinstance(x, str):
            raise XTypeError(f"Value {x} is not a list for lookup {items}", actual=str(type(x)))
        return [astype(y) for y in x]

    def get(self, items: str, default: Any = None) -> Any:
        """
        Gets a value from an optional key.
        Also see ``__getitem__``.
        """
        try:
            return self[items]
        except KeyError:
            return default

    def __getitem__(self, items: str) -> Any:
        """
        Gets a value from a required key.
        Analogous to ``dict.__getitem__``, but this can operate on dot-joined strings.

        **NOTE:** The number of keys for which this returns a value can be different from ``len(self)``.

        Example:
            >>> d = NestedDotDict(dict(a=dict(b=1)))
            >>> assert d["a.b"] == 1
        """
        at = self._x
        for item in items.split("."):
            if item not in at:
                raise XKeyError(f"{items} not found: {item} does not exist")
            at = at[item]
        return NestedDotDict(at) if isinstance(at, dict) else copy(at)

    def items(self) -> Sequence[tuple[str, Any]]:
        return list(self._x.items())

    def keys(self) -> Sequence[str]:
        return list(self._x.keys())

    def values(self) -> Sequence[Any]:
        return list(self._x.values())

    def pretty_str(self) -> str:
        """
        Pretty-prints the leaves of this dict using ``json.dumps``.

        Returns:
            A multi-line string
        """
        return orjson.dumps(
            self.leaves(), option=orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2 | orjson.OPT_UTC_Z
        ).decode(encoding="utf-8")

    def __len__(self) -> int:
        """
        Returns the number of values in this dict.
        Does **NOT** include nested values.
        """
        return len(self._x)

    def is_empty(self) -> bool:
        return len(self._x) == 0

    def __iter__(self):
        """
        Iterates over values in this dict.
        Does **NOT** include nested items.
        """
        return iter(self._x)

    def __repr__(self):
        return repr(self._x)

    def __str__(self):
        return str(self._x)

    def __eq__(self, other):
        return str(self) == str(other)

    def _to_date(self, s) -> date:
        if isinstance(s, date):
            return s
        elif isinstance(s, str):
            # This is MUCH faster than tomlkit's
            return date.fromisoformat(s)
        else:
            raise XTypeError(f"Invalid type {type(s)} for {s}", actual=str(type(s)))

    def _to_datetime(self, s) -> datetime:
        if isinstance(s, datetime):
            return s
        elif isinstance(s, str):
            # This is MUCH faster than tomlkit's
            if s.count(":") < 2:
                raise XValueError(
                    f"Datetime {s} does not contain hours, minutes, and seconds", value=s
                )
            return datetime.fromisoformat(s.upper().replace("Z", "+00:00"))
        else:
            raise XTypeError(f"Invalid type {type(s)} for {s}", actual=str(type(s)))


__all__ = ["NestedDotDict"]
