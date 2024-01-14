# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
"""

"""

from __future__ import annotations

import abc
import io
import json
import pickle
from collections import defaultdict
from configparser import ConfigParser
from dataclasses import dataclass
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Self, TypeVar, Unpack

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, MutableMapping

_Single = None | str | int | float | date | datetime
TomlLeaf = list[_Single] | _Single
# TomlBranch = dict[str, TomlLeaf | "TomlBranch"]
TomlBranch = dict[str, TomlLeaf | dict]
T = TypeVar("T", bound=TomlLeaf | TomlBranch)


class _Utils:
    @classmethod
    def json_encode_default(cls: type[Self], obj: Any) -> Any:
        if isinstance(obj, NestedDotDict):
            return dict(obj)

    @classmethod
    def dots_to_dict(cls: type[Self], items: Mapping[str, TomlLeaf]) -> dict[str, TomlLeaf | TomlBranch]:
        """
        Make sub-dictionaries from substrings in `items` delimited by `.`.
        Used for TOML.

        Example:

            Utils.dots_to_dict({"genus.species": "fruit bat"}) == {"genus": {"species": "fruit bat"}}

        See Also:
            [`dict_to_dots`](pocketutils.core.dot_dict._Utils.dicts_to_dots)
        """
        dct = {}
        cls._un_leaf(dct, items)
        return dct

    @classmethod
    def dict_to_dots(cls: type[Self], items: Mapping[str, TomlLeaf | TomlBranch]) -> dict[str, TomlLeaf]:
        """
        Performs the inverse of [`dict_to_dots`](pocketutils.core.dot_dict._Utils.dots_to_dicts].

        Example:

            Utils.dict_to_dots({"genus": {"species": "fruit bat"}}) == {"genus.species": "fruit bat"}
        """
        return dict(cls._re_leaf("", items))

    @classmethod
    def _un_leaf(cls: type[Self], to: MutableMapping[str, Any], items: Mapping[str, Any]) -> None:
        for k, v in items.items():
            if "." not in k:
                to[k] = v
            else:
                k0, k1 = k.split(".", 1)
                if k0 not in to:
                    to[k0] = {}
                cls._un_leaf(to[k0], {k1: v})

    @classmethod
    def _re_leaf(cls: type[Self], at: str, items: Mapping[str, Any]) -> Iterable[tuple[str, Any]]:
        for k, v in items.items():
            me = at + "." + k if len(at) > 0 else k
            if hasattr(v, "items") and hasattr(v, "keys") and hasattr(v, "values"):
                yield from cls._re_leaf(me, v)
            else:
                yield me, v

    @classmethod
    def check(cls: type[Self], dct: Mapping | TomlBranch | TomlLeaf) -> TomlLeaf | TomlBranch:
        if hasattr(dct, "items") and hasattr(dct, "keys") and hasattr(dct, "values"):
            bad = [k for k in dct if "." in k]
            if len(bad) > 0:
                msg = f"Key(s) contain '.': {bad}"
                raise ValueError(msg)
            return dict({k: cls.check(v) for k, v in dct.items()})
        return dct


@dataclass(frozen=True, slots=True)
class AbstractYamlMixin(metaclass=abc.ABCMeta):
    @classmethod
    def from_yaml(cls: type[Self], data: str) -> Self:
        raise NotImplementedError()

    def to_yaml(self: Self, **kwargs: Unpack[Mapping[str, Any]]) -> str:
        """
        Returns YAML text.
        """
        raise NotImplementedError()


@dataclass(frozen=True, slots=True)
class RuamelYamlMixin(AbstractYamlMixin):
    @classmethod
    def from_yaml(cls: type[Self], data: str) -> Self:
        from ruamel.yaml import YAML

        yaml = YAML(typ="safe")
        return cls(yaml.load(data))

    def to_yaml(self: Self, **kwargs: Unpack[Mapping[str, Any]]) -> str:
        from ruamel.yaml import YAML

        yaml = YAML(typ="safe")
        return yaml.dump(self, **kwargs)


@dataclass(frozen=True, slots=True)
class AbstractJsonMixin(metaclass=abc.ABCMeta):
    @classmethod
    def from_json(cls: type[Self], data: str) -> Self:
        raise NotImplementedError()

    def to_json(self: Self) -> str:
        """
        Returns JSON text.
        """
        raise NotImplementedError()


@dataclass(frozen=True, slots=True)
class OrjsonJsonMixin(AbstractJsonMixin):
    @classmethod
    def from_json(cls: type[Self], data: str) -> Self:
        import orjson

        return cls(orjson.loads(data))

    def to_json(self: Self) -> str:
        import orjson

        encoded = orjson.dumps(self, default=_Utils.json_encode_default)
        return encoded.decode(encoding="utf-8")


@dataclass(frozen=True, slots=True)
class AbstractTomlMixin(metaclass=abc.ABCMeta):
    @classmethod
    def from_toml(cls: type[Self], data: str) -> Self:
        raise NotImplementedError()

    def to_toml(self: Self) -> str:
        """
        Returns TOML text.
        """
        raise NotImplementedError()


@dataclass(frozen=True, slots=True)
class TomllibTomlMixin(AbstractTomlMixin):
    @classmethod
    def from_toml(cls: type[Self], data: str) -> Self:
        import tomllib

        return cls(tomllib.loads(data))

    def to_toml(self: Self) -> str:
        raise NotImplementedError()


@dataclass(frozen=True, slots=True)
class TomlkitTomlMixin(AbstractTomlMixin):
    @classmethod
    def from_toml(cls: type[Self], data: str) -> Self:
        import tomlkit

        return cls(tomlkit.loads(data))

    def to_toml(self: Self) -> str:
        import tomlkit

        return tomlkit.dumps(self)


@dataclass(frozen=True, slots=True)
class BuiltinJsonMixin(AbstractJsonMixin):
    @classmethod
    def from_json(cls: type[Self], data: str) -> Self:
        import json

        return cls(json.loads(data))

    def to_json(self: Self) -> str:
        import json

        return json.dumps(self, ensure_ascii=False)


@dataclass(frozen=True, slots=True)
class PickleMixin(metaclass=abc.ABCMeta):
    @classmethod
    def from_pickle(cls: type[Self], data: bytes) -> Self:
        if not isinstance(data, bytes):
            data = bytes(data)
        return cls(pickle.loads(data))  # noqa: S301

    def to_pickle(self: Self) -> bytes:
        """
        Writes to a pickle file.
        """
        return pickle.dumps(self, protocol=self.PICKLE_PROTOCOL)


@dataclass(frozen=True, slots=True)
class AbstractIniMixin(metaclass=abc.ABCMeta):
    @classmethod
    def from_ini(cls: type[Self], data: str) -> Self:
        raise NotImplementedError()

    def to_ini(self: Self) -> str:
        """
        Returns INI text.
        """
        raise NotImplementedError()


@dataclass(frozen=True, slots=True)
class BuiltinIniMixin(AbstractIniMixin):
    @classmethod
    def from_ini(cls: type[Self], data: str) -> Self:
        parser = ConfigParser()
        parser.read_string(data)
        return cls(parser)

    def to_ini(self: Self) -> str:
        config = ConfigParser()
        config.read_dict(self)
        writer = io.StringIO()
        config.write(writer)
        return writer.getvalue()


class AbstractDotDict(dict[str, TomlLeaf | TomlBranch]):
    """
    A thin wrapper around a nested dict, a wrapper for TOML.

    Keys must be strings that do not contain a dot (.).
    A dot is reserved for splitting values to traverse the tree.
    For example, `wrapped["pet.species.name"]`.
    """

    def __init__(self: Self, x: dict[str, TomlLeaf | TomlBranch] | Self) -> None:
        """
        Constructor.

        Raises:
            ValueError: If a key (in this dict or a sub-dict) is not a str or contains a dot
        """
        if not isinstance(x, AbstractDotDict | dict):
            msg = f"Not a dict; actually {type(x)} (value: '{x}')"
            raise TypeError(msg)
        _Utils.check(x)
        super().__init__(x)

    @classmethod
    def from_leaves(cls: type[Self], x: Mapping[str, TomlLeaf] | Self) -> Self:
        return cls(_Utils.dots_to_dict(x))

    def transform_leaves(self: Self, fn: Callable[[str, TomlLeaf], TomlLeaf]) -> Self:
        x = {k: fn(k, v) for k, v in self.leaves()}
        return self.__class__(x)

    def walk(self: Self) -> Iterable[TomlLeaf | TomlBranch]:
        for value in self.values():
            if isinstance(value, dict):
                yield from self.__class__(value).walk()
            else:
                yield value

    def nodes(self: Self) -> dict[str, TomlBranch | TomlLeaf]:
        return {**self.branches(), **self.leaves()}

    def branches(self: Self) -> dict[str, TomlBranch]:
        """
        Maps each lowest-level branch to a dict of its values.

        Note:
            Leaves directly under the root are assigned to key `''`.

        Returns:
            `dotted-key:str -> (non-dotted-key:str -> value)`
        """
        dicts = defaultdict(dict)
        for k, v in self.leaves().items():
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

    def req_as(self: Self, items: str, as_type: type[T]) -> T:
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
            if not isinstance(z, dict | AbstractDotDict):
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
        return json.dumps(self, ensure_ascii=True, indent=2)

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


try:
    import orjson

    _Json = OrjsonJsonMixin
except ImportError:
    _Json = BuiltinJsonMixin

try:
    import orjson

    _Toml = TomlkitTomlMixin
except ImportError:
    _Toml = TomllibTomlMixin

try:
    import ruamel

    _Yaml = RuamelYamlMixin
except ImportError:
    _Yaml = None

if _Yaml is None:

    class NestedDotDict(AbstractDotDict, _Json, _Toml, BuiltinIniMixin, PickleMixin):
        pass
else:

    class NestedDotDict(AbstractDotDict, _Json, _Toml, _Yaml, BuiltinIniMixin, PickleMixin):
        pass


__all__ = ["NestedDotDict", "TomlLeaf", "TomlBranch"]
