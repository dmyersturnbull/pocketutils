from __future__ import annotations

import json
import pickle
from copy import copy
from datetime import date, datetime
from pathlib import Path, PurePath
from typing import Any, ByteString, Callable, Mapping, Optional, Sequence
from typing import Tuple as Tup
from typing import Type, TypeVar, Union

import orjson
import tomlkit

PICKLE_PROTOCOL = 5
T = TypeVar("T")


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

    def to_json(self, indent: bool = False) -> str:
        kwargs = dict(option=orjson.OPT_INDENT_2) if indent else {}
        encoded = orjson.dumps(dict(self), default=_json_encode_default, **kwargs)
        return encoded.decode(encoding="utf8")

    @classmethod
    def read_toml(cls, path: Union[PurePath, str]) -> NestedDotDict:
        return NestedDotDict(tomlkit.loads(Path(path).read_text(encoding="utf8")))

    @classmethod
    def read_json(cls, path: Union[PurePath, str]) -> NestedDotDict:
        """
        Reads JSON from a file, into a NestedDotDict.
        If the JSON data is a list type, converts into a dict with the key ``data``.
        """
        data = orjson.loads(Path(path).read_text(encoding="utf8"))
        if isinstance(data, list):
            data = {"data": data}
        data.__class__ = cls
        return data

    @classmethod
    def read_pickle(cls, path: Union[PurePath, str]) -> NestedDotDict:
        """

        Note that this function has potential security concerns.
        This is because it relies on the pickle module.
        """
        data = Path(path).read_bytes()
        data = pickle.loads(data)  # nosec
        return NestedDotDict(data)

    @classmethod
    def parse_toml(cls, data: str) -> NestedDotDict:
        return NestedDotDict(tomlkit.loads(data))

    @classmethod
    def parse_json(cls, data: str) -> NestedDotDict:
        """
        Parses JSON from a string, into a NestedDotDict.
        If the JSON data is a list type, converts into a dict with the key ``data``.
        """
        data = json.loads(data)
        if isinstance(data, list):
            data = {"data": data}
        data.__class__ = cls
        return NestedDotDict(data)

    @classmethod
    def parse_pickle(cls, data: ByteString) -> NestedDotDict:
        if not isinstance(data, bytes):
            data = bytes(data)
        return NestedDotDict(pickle.loads(data))

    def __init__(self, x: Mapping[str, Any]) -> None:
        """
        Constructor.

        Raises:
            ValueError: If a key (in this dict or a sub-dict) is not a str or contains a dot
        """
        if not (hasattr(x, "items") and hasattr(x, "keys") and hasattr(x, "values")):
            raise TypeError(f"Type {type(x)} for value {x} appears not to be dict-like")
        bad = [k for k in x if not isinstance(k, str)]
        if len(bad) > 0:
            raise ValueError(f"Keys were not strings for these values: {bad}")
        bad = [k for k in x if "." in k]
        if len(bad) > 0:
            raise ValueError(f"Keys contained dots (.) for these values: {bad}")
        self._x = x
        # Let's make sure this constructor gets called on subdicts:
        self.leaves()

    def write_json(self, path: Union[PurePath, str], indent: bool = False) -> None:
        kwargs = dict(option=orjson.OPT_INDENT_2) if indent else {}
        Path(path).write_bytes(orjson.dumps(dict(self), default=_json_encode_default, **kwargs))

    def write_pickle(self, path: Union[PurePath, str]) -> None:
        Path(path).write_bytes(pickle.dumps(self._x, protocol=PICKLE_PROTOCOL))

    def leaves(self) -> Mapping[str, Any]:
        """
        Gets the leaves in this tree.

        Returns:
            A dict mapping dot-joined keys to their values
        """
        mp = {}
        for key, value in self._x.items():
            if len(key) == 0:
                raise AssertionError(f"Key is empty (value=${value})")
            if isinstance(value, dict):
                mp.update({key + "." + k: v for k, v in NestedDotDict(value).leaves().items()})
            else:
                mp[key] = value
        return mp

    def sub(self, items: str) -> NestedDotDict:
        return NestedDotDict(self[items])

    def exactly(self, items: str, astype: Type[T]) -> T:
        """
        Gets the key ``items`` from the dict if it has type ``astype``.
        Calling ``dotdict.exactly(k, t) is equivalent to calling ``t(dotdict[k])``,
        but a raised ``TypeError`` will note the key, making this a useful shorthand for the above within a try-except.

        Args:
            items: The key hierarchy, with a dot (.) as a separator
            astype: The type, which will be checked using ``isinstance``

        Returns:
            The value in the required type

        Raises:
            TypeError: If not ``isinstance(value, astype)``
        """
        z = self[items]
        if not isinstance(z, astype):
            raise TypeError(f"Value {z} from {items} is a {type(z)}, not {astype}")
        return z

    def get_as(
        self, items: str, astype: Callable[[Any], T], default: Optional[T] = None
    ) -> Optional[T]:
        """
        Gets the value of an *optional* key, or ``default`` if it doesn't exist.
        Also see ``req_as``.

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
            ValueError: Likely exception raised if calling ``astype`` fails

        """
        x = self.get(items)
        if x is None:
            return default
        if astype is date:
            return self._to_date(x)
        if astype is datetime:
            return self._to_datetime(x)
        return astype(x)

    def req_as(self, items: str, astype: Optional[Callable[[Any], T]]) -> T:
        """
        Gets the value of a *required* key.
        Also see ``get_as`` and ``exactly``.

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
            KeyError: If the key is not found (at any level).
            ValueError: Likely exception raised if calling ``astype`` fails
        """
        x = self[items]
        return astype(x)

    def get_list_as(
        self, items: str, astype: Callable[[Any], T], default: Optional[Sequence[T]] = None
    ) -> Optional[Sequence[T]]:
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
            ValueError: Likely exception raised if calling ``astype`` fails
            TypeError: If the found value is not a (non-``str``) ``Sequence``
        """
        x = self.get(items)
        if x is None:
            return default
        if not isinstance(x, Sequence) or isinstance(x, str):
            raise TypeError(f"Value {x} is not a list for lookup {items}")
        return [astype(y) for y in x]

    def req_list_as(self, items: str, astype: Optional[Callable[[Any], T]]) -> Sequence[T]:
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
            ValueError: Likely exception raised if calling ``astype`` fails
            TypeError: If the found value is not a (non-``str``) ``Sequence``
            KeyError: If the key was not found (at any level)
        """
        x = self[items]
        if not isinstance(x, Sequence) or isinstance(x, str):
            raise TypeError(f"Value {x} is not a list for lookup {items}")
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
                raise KeyError(f"{items} not found: {item} does not exist")
            at = at[item]
        return NestedDotDict(at) if isinstance(at, dict) else copy(at)

    def items(self) -> Sequence[Tup[str, Any]]:
        return list(self._x.items())

    def keys(self) -> Sequence[str]:
        return list(self._x.keys())

    def values(self) -> Sequence[Any]:
        return list(self._x.values())

    def pretty_str(self) -> str:
        """
        Pretty-prints the leaves of this dict using ``json.dumps``.

        Returns:
            A multi-lined string
        """
        return json.dumps(
            self.leaves(),
            sort_keys=True,
            indent=4,
            ensure_ascii=False,
        )

    def __len__(self) -> int:
        """
        Returns the number of values in this dict.
        Does **NOT** include nested values.
        """
        return len(self._x)

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

    def _to_date(self, s):
        if isinstance(s, date):
            return s
        elif isinstance(s, str):
            # This is MUCH faster than tomlkit's
            return date.fromisoformat(s)
        else:
            raise TypeError(f"Invalid type ${type(s)} for {s}")

    def _to_datetime(self, s):
        if isinstance(s, datetime):
            return s
        elif isinstance(s, str):
            # This is MUCH faster than tomlkit's
            if s.count(":") < 2:
                raise ValueError(f"Datetime {s} does not contain hours, minutes, and seconds")
            return datetime.fromisoformat(s.upper().replace("Z", "+00:00"))
        else:
            raise TypeError(f"Invalid type ${type(s)} for {s}")


__all__ = ["NestedDotDict"]
