from __future__ import annotations

import io
import pickle
import sys
from collections import UserDict, defaultdict
from configparser import ConfigParser
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, ClassVar, Self, TypeVar, Unpack

import tomlkit
from orjson import orjson
from ruamel.yaml import YAML

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Mapping

yaml = YAML(typ="safe")
TomlLeaf = None | list | int | str | float | date | datetime
TomlBranch = dict[str, TomlLeaf]
T = TypeVar("T")


def _json_encode_default(obj: Any) -> Any:
    if isinstance(obj, NestedDotDict):
        # noinspection PyProtectedMember
        return dict(obj)


def _check(dct: TomlBranch | TomlLeaf) -> None:
    if isinstance(dct, dict):
        bad = [k for k in dct if "." in k]
        if len(bad) > 0:
            msg = f"Key(s) contain '.': {bad}"
            raise ValueError(msg)
        for v in dct.values():
            _check(v)


class NestedDotDict(UserDict):
    """
    A thin wrapper around a nested dict, a wrapper for TOML.

    Keys must be strings that do not contain a dot (.).
    A dot is reserved for splitting values to traverse the tree.
    For example, `wrapped["pet.species.name"]`.
    """

    PICKLE_PROTOCOL: ClassVar[int] = 5

    def __init__(self: Self, x: dict[str, TomlLeaf | TomlBranch] | Self) -> None:
        """
        Constructor.

        Raises:
            ValueError: If a key (in this dict or a sub-dict) is not a str or contains a dot
        """
        if not isinstance(x, NestedDotDict | dict):
            msg = f"Not a dict; actually {type(x)} (value: '{x}')"
            raise TypeError(msg)
        _check(x)
        super().__init__(x)

    @classmethod
    def from_toml(cls: type[Self], data: str) -> Self:
        return cls(tomlkit.loads(data))

    @classmethod
    def from_yaml(cls: type[Self], data: str) -> Self:
        return cls(yaml.load(data))

    @classmethod
    def from_ini(cls: type[Self], data: str) -> Self:
        parser = ConfigParser()
        parser.read_string(data)
        return cls(parser)

    @classmethod
    def from_json(cls: type[Self], data: str) -> Self:
        return cls(orjson.loads(data))

    @classmethod
    def parse_pickle(cls: type[Self], data: bytes) -> Self:
        if not isinstance(data, bytes):
            data = bytes(data)
        return cls(pickle.loads(data))

    def to_json(self: Self, *, indent: bool = False) -> str:
        """
        Returns JSON text.
        """
        kwargs = {"option": orjson.OPT_INDENT_2} if indent else {}
        encoded = orjson.dumps(self, default=_json_encode_default, **kwargs)
        return encoded.decode(encoding="utf-8")

    def to_yaml(self: Self, **kwargs: Unpack[Mapping[str, Any]]) -> str:
        """
        Returns JSON text.
        """
        return yaml.dump(self, **kwargs)

    def to_ini(self: Self) -> str:
        """
        Returns TOML text.
        """
        config = ConfigParser()
        config.read_dict(self)
        writer = io.StringIO()
        config.write(writer)
        return writer.getvalue()

    def to_toml(self: Self) -> str:
        """
        Returns TOML text.
        """
        return tomlkit.dumps(self)

    def to_pickle(self: Self) -> bytes:
        """
        Writes to a pickle file.
        """
        return pickle.dumps(self, protocol=self.PICKLE_PROTOCOL)

    def n_elements_total(self: Self) -> int:
        i = 0
        for _ in self.walk():
            i += 1
        return i

    def n_bytes_total(self: Self) -> int:
        return sum([sys.getsizeof(x) for x in self.walk()])

    def transform_leaves(self: Self, fn: Callable[[str, TomlLeaf], TomlLeaf]) -> Self:
        x = {k: fn(k, v) for k, v in self.leaves()}
        return self.__class__(x)

    def walk(self: Self) -> Generator[TomlLeaf | TomlBranch, None, None]:
        for value in self.values():
            if isinstance(value, dict):
                yield from self.__class__(value).walk()
            elif isinstance(value, list):
                yield from value
            else:
                yield value

    def branches(self: Self) -> dict[str, TomlBranch]:
        """
        Maps each lowest-level branch to a dict of its values.

        Note:
            Leaves directly under the root are assigned to key `''`.

        Returns:
            `dotted-key:str -> (non-dotted-key:str -> value)`
        """
        dicts = defaultdict()
        for k, v in self.leaves():
            k0, _, k1 = str(k).rpartition(".")
            dicts[k0][k1] = v
        return dicts

    def leaves(self: Self) -> dict[str, TomlLeaf]:
        """
        Gets the leaves in this tree.

        Returns:
            `dotted-key:str -> value`
        """
        dct = {}
        for key, value in self.items():
            if isinstance(value, dict):
                dct.update({key + "." + k: v for k, v in self.__class__(value).leaves().items()})
            else:
                dct[key] = value
        return dct

    def sub(self: Self, items: str) -> Self:
        """
        Returns the dictionary under (dotted) keys `items`.
        """
        # noinspection PyTypeChecker
        return self.__class__(self[items])

    def get_as(self: Self, items: str, as_type: type[T], default: T | None = None) -> T:
        """
        Gets the key `items` from the dict, or `default` if it does not exist

        Args:
            items: The key hierarchy, with a dot (.) as a separator
            as_type: The type, which will be checked using `isinstance`
            default: Default to return the key is not found

        Returns:
            The value in the required type

        Raises:
            XTypeError: If not `isinstance(value, as_type)`
        """
        z = self.get(items, default)
        if not isinstance(z, as_type):
            msg = f"Value {z} from {items} is a {type(z)}, not {as_type}"
            raise TypeError(msg)
        return z

    def req_as(self: Self, items: str, as_type: type[T]) -> T | None:
        """
        Gets the key `items` from the dict.

        Args:
            items: The key hierarchy, with a dot (.) as a separator
            as_type: The type, which will be checked using `isinstance`

        Returns:
            The value in the required type

        Raises:
            XTypeError: If not `isinstance(value, as_type)`
        """
        z = self[items]
        if not isinstance(z, as_type):
            msg = f"Value {z} from {items} is a {type(z)}, not {as_type}"
            raise TypeError(msg)
        return z

    def get_list(self: Self, items: str, default: list[T] | None = None) -> list[T]:
        try:
            return self[items]
        except KeyError:
            return [] if default is None else default

    def get_list_as(self: Self, items: str, as_type: type[T], default: list[T] | None = None) -> list[T]:
        """
        Gets list values from an *optional* key.
        """
        try:
            x = self[items]
        except KeyError:
            return [] if default is None else default
        if not isinstance(x, list) or isinstance(x, str):
            msg = f"Value {x} is not a list for lookup {items}"
            raise TypeError(msg)
        bad = [y for y in x if not isinstance(y, as_type)]
        if len(bad) > 0:
            msg = f"Value(s) from {items} are not {as_type}: {bad}"
            raise TypeError(msg)
        return x

    def req_list_as(self: Self, items: str, as_type: type[T]) -> list[T]:
        """
        Gets list values from a *required* key.
        """
        x = self[items]
        if not isinstance(x, list) or isinstance(x, str):
            msg = f"Value {x} is not a list for lookup {items}"
            raise TypeError(msg)
        if not all(isinstance(y, as_type) for y in x):
            msg = f"Value {x} from {items} is a {type(x)}, not {as_type}"
            raise TypeError(msg)
        return x

    def req(self: Self, items: str) -> TomlLeaf | dict:
        return self[items]

    def get(self: Self, items: str, default: TomlLeaf | dict = None) -> TomlLeaf | dict:
        """
        Gets a value from an optional key.
        Also see `__getitem__`.
        """
        try:
            return self[items]
        except KeyError:
            return default

    def __getitem__(self: Self, items: str) -> TomlLeaf | dict:
        """
        Gets a value from a required key, operating on `.`-joined strings.

        Example:
            d = WrappedToml(dict(a=dict(b=1)))
            assert d["a.b"] == 1
        """
        if "." in items:
            i0, _, i_ = items.partition(".")
            z = self[i0]
            if not isinstance(z, dict | NestedDotDict):
                msg = f"No key {items} (ends at {i0})"
                raise KeyError(msg)
            return self.__class__(z)[i_]
        return super().__getitem__(items)

    def __rich_repr__(self: Self) -> str:
        """
        Pretty-prints the leaves of this dict using `json.dumps`.

        Returns:
            A multi-line string
        """
        option = orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2 | orjson.OPT_UTC_Z
        return orjson.dumps(self.leaves(), option=option).decode(encoding="utf-8")

    def _to_date(self: Self, s) -> date:
        if isinstance(s, date):
            return s
        elif isinstance(s, str):
            # This is MUCH faster than tomlkit's
            return date.fromisoformat(s)
        else:
            msg = f"Invalid type {type(s)} for {s}"
            raise TypeError(msg)

    def _to_datetime(self: Self, s: str | datetime) -> datetime:
        if isinstance(s, datetime):
            return s
        elif isinstance(s, str):
            # This is MUCH faster than tomlkit's
            if s.count(":") < 2:
                msg = f"Datetime {s} does not contain hours, minutes, and seconds"
                raise ValueError(msg)
            return datetime.fromisoformat(s.upper().replace("Z", "+00:00"))
        else:
            msg = f"Invalid type {type(s)} for {s}"
            raise TypeError(msg)


__all__ = ["NestedDotDict", "TomlLeaf", "TomlBranch"]
