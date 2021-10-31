from __future__ import annotations

import bz2
import gzip
import logging
import operator
import os
import sys
from pathlib import Path, PurePath
from typing import Any, Callable, Iterable, Optional, TypeVar, Union

T = TypeVar("T", covariant=True)
Y = TypeVar("Y")
Z = TypeVar("Z")
logger = logging.getLogger("pocketutils")

PathLike = Union[str, PurePath, os.PathLike]


class PathLikeUtils:
    @classmethod
    def isinstance(cls, value: Any):
        return (
            isinstance(value, str) or isinstance(value, os.PathLike) or isinstance(value, PurePath)
        )


class Pretty:
    @classmethod
    def condensed(cls, item, depth=1):
        if isinstance(item, dict):
            return (
                "{\n"
                + "\n".join(
                    [
                        "\t" * (depth + 1) + k + " = " + cls.condensed(v, depth + 1)
                        for k, v in item.items()
                    ]
                )
                + "\n"
                + "\t" * depth
                + "}"
            )
        else:
            return str(item)

    @classmethod
    def expanded(cls, item, depth=1):
        if isinstance(item, dict):
            return (
                "{\n"
                + "\n".join(
                    [
                        "\t" * (depth + 1) + k + " = " + cls.expanded(v, depth + 1)
                        for k, v in item.items()
                    ]
                )
                + "\n"
                + "\t" * depth
                + "}"
            )
        elif isinstance(item, (list, set)):
            return (
                "[\n"
                + "\n".join(["\t" * (depth + 1) + cls.expanded(v, depth + 1) for v in item])
                + "\n"
                + "\t" * depth
                + "]"
            )
        else:
            return str(item)


def nicesize(nbytes: int, space: str = "") -> str:
    """
    Uses IEC 1998 units, such as KiB (1024).
        nbytes: Number of bytes
        space: Separator between digits and units

        Returns:
            Formatted string
    """
    data = {
        "PiB": 1024 ** 5,
        "TiB": 1024 ** 4,
        "GiB": 1024 ** 3,
        "MiB": 1024 ** 2,
        "KiB": 1024 ** 1,
    }
    for suffix, scale in data.items():
        if nbytes >= scale:
            break
    else:
        scale, suffix = 1, "B"
    return str(nbytes // scale) + space + suffix


def look(obj: Y, attrs: Union[str, Iterable[str], Callable[[Y], Z]]) -> Optional[Z]:
    if attrs is None:
        return obj
    if not isinstance(attrs, str) and hasattr(attrs, "__len__") and len(attrs) == 0:
        return obj
    if isinstance(attrs, str):
        attrs = operator.attrgetter(attrs)
    elif isinstance(attrs, Iterable) and all((isinstance(a, str) for a in attrs)):
        attrs = operator.attrgetter(".".join(attrs))
    elif not callable(attrs):
        raise TypeError(
            f"Type {type(attrs)} unrecognized for key/attrib. Must be a function, string, or sequence of strings"
        )
    try:
        return attrs(obj)
    except AttributeError:
        return None


GZ_BZ2_SUFFIXES = {".gz", ".gzip", ".bz2", ".bzip2"}
JSON_SUFFIXES = {".json" + s for s in {"", *GZ_BZ2_SUFFIXES}}
TOML_SUFFIXES = {".toml" + s for s in {"", *GZ_BZ2_SUFFIXES}}


def read_txt_or_gz(path: PathLike) -> str:
    path = Path(path)
    if path.name.endswith(".bz2") or path.name.endswith(".bzip2"):
        return bz2.decompress(path.read_bytes()).decode(encoding="utf8")
    if path.name.endswith(".gz") or path.name.endswith(".gzip"):
        return gzip.decompress(path.read_bytes()).decode(encoding="utf8")
    return Path(path).read_text(encoding="utf8")


def write_txt_or_gz(txt: str, path: PathLike, *, mkdirs: bool = False) -> str:
    path = Path(path)
    if mkdirs:
        path.parent.mkdir(parents=True, exist_ok=True)
    if path.name.endswith(".bz2") or path.name.endswith(".bzip2"):
        data = bz2.compress(txt.encode(encoding="utf8"))
        path.write_bytes(data)
    elif path.name.endswith(".gz") or path.name.endswith(".gzip"):
        data = gzip.compress(txt.encode(encoding="utf8"))
        path.write_bytes(data)
    else:
        path.write_text(txt)
    return txt


def null_context():
    yield


__all__ = [
    "nicesize",
    "look",
    "logger",
    "Pretty",
    "PathLike",
    "PathLikeUtils",
    "read_txt_or_gz",
    "write_txt_or_gz",
    "GZ_SUFFIXES",
    "BZ2_SUFFIXES",
]
