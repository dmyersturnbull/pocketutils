from __future__ import annotations

import logging
from collections import Mapping
from dataclasses import dataclass
from typing import AbstractSet, Any, Callable, Sequence, Union

from notifiers import notify
from notifiers.core import Response, get_notifier

from pocketutils.core import PathLike
from pocketutils.core.dot_dict import NestedDotDict
from pocketutils.core.exceptions import XValueError

logger = logging.getLogger("pocketutils")


@dataclass(frozen=True)
class Notifier:
    """
    A simple config for notifiers from a .json or .toml file.
    """

    __config: Mapping[str, Mapping[str, Union[int, str, bool]]]
    _warn: Union[bool, Callable[[Response], Any]] = True

    @property
    def services(self) -> AbstractSet[str]:
        return self.__config.keys()

    @classmethod
    def from_json_file(
        cls, path: PathLike, *, warn: Union[bool, Callable[[Response], Any]] = True
    ) -> Notifier:
        return cls.from_dict(NestedDotDict.read_json(path), warn=warn)

    @classmethod
    def from_toml_file(
        cls, path: PathLike, *, warn: Union[bool, Callable[[Response], Any]] = True
    ) -> Notifier:
        return cls.from_dict(NestedDotDict.read_toml(path), warn=warn)

    @classmethod
    def from_dict(
        cls, dct: Sequence[Any], *, warn: Union[bool, Callable[[Response], Any]] = True
    ) -> Notifier:
        return Notifier({x["services"]: x["defaults"] for x in dct}, _warn=warn)

    def __post_init__(self):
        for k, v in self.__config.items():
            if "message" in v:
                raise XValueError(f"Do not include message in defaults")
            get_notifier(provider_name=k, strict=True)  # test

    def notify(self, message: str) -> Mapping[str, Response]:
        returns = {}
        for service, defaults in self.__config.items():
            r = notify(service, message=message, **defaults)
            returns[service] = r
            if self._warn and not r.ok and not defaults.get("raise_on_errors", False):
                if callable(self._warn):
                    self._warn(r)
                else:
                    logger.error(f"Error ({r.status}) notifying via {service}: {r.errors}")
        return returns

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(self.services)})"

    def __str__(self):
        return repr(self)


__all__ = ["Notifier"]
