from __future__ import annotations

import io
import pickle
import sys
from collections import UserDict, defaultdict
from collections.abc import Callable, Mapping
from configparser import ConfigParser
from copy import copy
from datetime import date, datetime
from pathlib import Path
from typing import Any, Self, TypeVar

import tomlkit
from orjson import orjson
from ruamel.yaml import YAML

yaml = YAML(typ="safe")
TomlLeaf = None | list | int | str | float | date | datetime
TomlBranch = dict[str, TomlLeaf]
T = TypeVar("T")


def _json_encode_default(obj: Any) -> Any:
    if isinstance(obj, NestedDotDict):
        # noinspection PyProtectedMember
        return dict(obj)


class NestedDotDict(UserDict):
    """
    A thin wrapper around a nested dict, a wrapper for TOML.

    Keys must be strings that do not contain a dot (.).
    A dot is reserved for splitting values to traverse the tree.
    For example, ``wrapped["pet.species.name"]``.
    """

    PICKLE_PROTOCOL = 5

    @classmethod
    def from_toml(cls, data: str) -> Self:
        return cls(tomlkit.loads(data))

    @classmethod
    def from_yaml(cls, data: str) -> Self:
        return cls(yaml.load(data))

    @classmethod
    def from_ini(cls, data: str) -> Self:
        parser = ConfigParser()
        parser.read_string(data)
        return cls(parser)

    @classmethod
    def from_json(cls, data: str) -> Self:
        return cls(orjson.loads(data))

    @classmethod
    def parse_pickle(cls, data: bytes) -> Self:
        if not isinstance(data, bytes):
            data = bytes(data)
        return cls(pickle.loads(data))

    def to_json(self, *, indent: bool = False) -> str:
        """
        Returns JSON text.
        """
        kwargs = dict(option=orjson.OPT_INDENT_2) if indent else {}
        encoded = orjson.dumps(self, default=_json_encode_default, **kwargs)
        return encoded.decode(encoding="utf-8")

    def to_yaml(self, **kwargs) -> str:
        """
        Returns JSON text.
        """
        return yaml.dump(self, **kwargs)

    def to_ini(self) -> str:
        """
        Returns TOML text.
        """
        config = ConfigParser()
        config.read_dict(self)
        writer = io.StringIO()
        config.write(writer)
        return writer.getvalue()

    def to_toml(self) -> str:
        """
        Returns TOML text.
        """
        return tomlkit.dumps(self)

    def to_pickle(self) -> bytes:
        """
        Writes to a pickle file.
        """
        return pickle.dumps(self, protocol=self.PICKLE_PROTOCOL)

    def n_elements_total(self) -> int:
        return len(self._all_elements())

    def n_bytes_total(self) -> int:
        return sum([sys.getsizeof(x) for x in self._all_elements()])

    def __init__(self, x: Mapping[str, TomlLeaf | dict]) -> None:
        """
        Constructor.

        Raises:
            ValueError: If a key (in this dict or a sub-dict) is not a str or contains a dot
        """
        super().__init__(x)
        if not (hasattr(x, "items") and hasattr(x, "keys") and hasattr(x, "values")):
            raise TypeError(f"Type {type(x)} for value {x} appears not to be dict-like")
        bad = [k for k in x if not isinstance(k, str)]
        if len(bad) > 0:
            raise ValueError(f"Keys were not strings for values {bad}")
        bad = [k for k in x if "." in k]
        if len(bad) > 0:
            raise ValueError(f"Keys contains '.' for values {bad}")
        # Let's make sure this constructor gets called on sub-dicts:
        self.leaves()

    def transform_leaves(self, fn: Callable[[str, TomlLeaf], TomlLeaf]) -> Self:
        x = {k: fn(k, v) for k, v in self.leaves()}
        return self.__class__(x)

    def branches(self) -> dict[str, TomlBranch]:
        """
        Maps each lowest-level branch to a dict of its values.

        Note:
            Leaves directly under the root are assigned to key ``''``.

        Returns:
            ``dotted-key:str -> (non-dotted-key:str -> value)``
        """
        dicts = defaultdict()
        for k, v in self.leaves():
            k0, _, k1 = str(k).rpartition(".")
            dicts[k0][k1] = v
        return dicts

    def leaves(self) -> dict[str, TomlLeaf]:
        """
        Gets the leaves in this tree.

        Returns:
            ``dotted-key:str -> value``
        """
        dct = {}
        for key, value in self.items():
            if isinstance(value, dict):
                dct.update({key + "." + k: v for k, v in self.__class__(value).leaves().items()})
            else:
                dct[key] = value
        return dct

    def sub(self, items: str) -> Self:
        """
        Returns the dictionary under (dotted) keys ``items``.
        """
        # noinspection PyTypeChecker
        return self.__class__(self[items])

    def get_as(self, items: str, as_type: type[T], default: T | None = None) -> T:
        """
        Gets the key ``items`` from the dict, or ``default`` if it does not exist

        Args:
            items: The key hierarchy, with a dot (.) as a separator
            as_type: The type, which will be checked using ``isinstance``
            default: Default to return the key is not found

        Returns:
            The value in the required type

        Raises:
            XTypeError: If not ``isinstance(value, as_type)``
        """
        z = self.get(items, default)
        if not isinstance(z, as_type):
            raise TypeError(f"Value {z} from {items} is a {type(z)}, not {as_type}")
        return z

    def req_as(self, items: str, as_type: type[T]) -> T | None:
        """
        Gets the key ``items`` from the dict.

        Args:
            items: The key hierarchy, with a dot (.) as a separator
            as_type: The type, which will be checked using ``isinstance``

        Returns:
            The value in the required type

        Raises:
            XTypeError: If not ``isinstance(value, as_type)``
        """
        z = self[items]
        if not isinstance(z, as_type):
            raise TypeError(f"Value {z} from {items} is a {type(z)}, not {as_type}")
        return z

    def get_list_as(self, items: str, as_type: type[T], default: list[T] | None = None) -> list[T]:
        """
        Gets list values from an *optional* key.
        """
        x = self.get(items, default)
        if not isinstance(x, list) or isinstance(x, str):
            raise TypeError(f"Value {x} is not a list for lookup {items}")
        if not all(isinstance(y, as_type) for y in x):
            raise TypeError(f"Value {x} from {items} is a {type(x)}, not {as_type}")
        return x

    def req_list_as(self, items: str, as_type: type[T]) -> list[T]:
        """
        Gets list values from a *required* key.
        """
        x = self[items]
        if not isinstance(x, list) or isinstance(x, str):
            raise TypeError(f"Value {x} is not a list for lookup {items}")
        if not all(isinstance(y, as_type) for y in x):
            raise TypeError(f"Value {x} from {items} is a {type(x)}, not {as_type}")
        return x

    def req(self, items: str) -> TomlLeaf | dict:
        return self[items]

    def get(self, items: str, default: TomlLeaf | dict = None) -> TomlLeaf | dict:
        """
        Gets a value from an optional key.
        Also see ``__getitem__``.
        """
        try:
            return self[items]
        except KeyError:
            return default

    def __getitem__(self, items: str) -> TomlLeaf | dict:
        """
        Gets a value from a required key, operating on ``.``-joined strings.

        Example:
            d = WrappedToml(dict(a=dict(b=1)))
            assert d["a.b"] == 1
        """
        at = self
        for item in items.split("."):
            if item not in at:
                raise KeyError(f"{items} not found: {item} does not exist")
            at = at[item]
        return self.__class__(at) if isinstance(at, dict) else copy(at)

    def __rich_repr__(self) -> str:
        """
        Pretty-prints the leaves of this dict using ``json.dumps``.

        Returns:
            A multi-line string
        """
        option = orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2 | orjson.OPT_UTC_Z
        return orjson.dumps(self.leaves(), option=option).decode(encoding="utf-8")

    def _to_date(self, s) -> date:
        if isinstance(s, date):
            return s
        elif isinstance(s, str):
            # This is MUCH faster than tomlkit's
            return date.fromisoformat(s)
        else:
            raise TypeError(f"Invalid type {type(s)} for {s}")

    def _to_datetime(self, s) -> datetime:
        if isinstance(s, datetime):
            return s
        elif isinstance(s, str):
            # This is MUCH faster than tomlkit's
            if s.count(":") < 2:
                raise ValueError(f"Datetime {s} does not contain hours, minutes, and seconds")
            return datetime.fromisoformat(s.upper().replace("Z", "+00:00"))
        else:
            raise TypeError(f"Invalid type {type(s)} for {s}")

    def _all_elements(self) -> list[TomlLeaf | TomlBranch]:
        i = []
        for key, value in self.items():
            if value is not None and isinstance(value, dict):
                i += NestedDotDict(value)._all_elements()
            elif (
                value is not None
                and isinstance(value, list)
                and not isinstance(value, str)
                and not isinstance(value, bytes)
            ):
                i += list(value)
            else:
                i.append(value)
        return i


__all__ = ["NestedDotDict", "TomlLeaf", "TomlBranch"]
