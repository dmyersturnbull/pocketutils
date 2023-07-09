"""
Compression-aware reading and writing of files.
"""
from __future__ import annotations

import abc
import bz2
import gzip
import lzma
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePath
from typing import Any, Self

from pocketutils import WritePermissionsError

PathLike = str | PurePath


@dataclass(frozen=True)
class Compression(metaclass=abc.ABCMeta):
    name: str
    suffixes: set[str]
    compress: Callable[[bytes], bytes]
    decompress: Callable[[bytes], bytes]


def identity(x):
    return x


@dataclass(frozen=True)
class CompressionSet:
    mapping: dict[str, Compression]

    @classmethod
    def empty(cls) -> Self:
        return CompressionSet({"": Compression("", set(), identity, identity)})

    def __add__(self, fmt: Compression):
        new = {fmt.name: fmt} | {s: fmt for s in fmt.suffixes}
        already = {v for k, v in self.mapping.items() if k in new}
        if len(already) > 1 or len(already) == 1 and already != {fmt}:
            raise ValueError(f"Keys from {fmt} already mapped to {already}")
        return CompressionSet(self.mapping | new)

    def __sub__(self, fmt: Compression):
        return CompressionSet(
            {k: v for k, v in self.mapping.items() if k != fmt.name and k not in fmt.suffixes}
        )

    def __or__(self, fmt: CompressionSet):
        return CompressionSet(self.mapping | fmt.mapping)

    def __getitem__(self, t: Compression | str) -> Compression:
        """
        Returns a FileFormat from a name (e.g. "gz" or "gzip").
        Case-insensitive.

        Example:
            ``Compression.of("gzip").suffix  # ".gz"``
        """
        if isinstance(t, Compression):
            return t
        return self.mapping[t]

    def guess(self, path: PathLike) -> Compression:
        if "." not in path.name:
            return self[""]
        try:
            return self[path.suffix]
        except KeyError:
            return self[""]


def _get_compressions():
    import brotli
    import lz4.frame
    import snappy
    import zstandard

    return (
        CompressionSet.empty()
        + Compression("gzip", {".gz", ".gzip"}, gzip.compress, gzip.decompress)
        + Compression("brotli", {".bro", ".brotli"}, brotli.compress, brotli.decompress)
        + Compression("zstandard", {".zst", ".zstd"}, zstandard.compress, zstandard.decompress)
        + Compression("lz4", {".lz4"}, lz4.frame.compress, lz4.frame.decompress)
        + Compression("snappy", {".snappy"}, snappy.compress, snappy.decompress)
        + Compression("bzip2", {".bz2", ".bzip2"}, bz2.compress, bz2.decompress)
        + Compression("xz", {".xz"}, lzma.compress, lzma.decompress)
    )


@dataclass(slots=True, frozen=True)
class SmartIo:
    _COMPRESSIONS = None

    @classmethod
    def compressions(cls) -> CompressionSet:
        if cls._COMPRESSIONS is None:
            _COMPRESSIONS = _get_compressions()
        return cls._COMPRESSIONS

    @classmethod
    def write(
        cls, data: Any, path: PathLike, *, atomic: bool = False, mkdirs: bool = False
    ) -> None:
        path = Path(path)
        compressed = cls.compressions().guess(path).compress(data)
        if path.exists() and not path.is_file():
            raise WritePermissionsError(f"Path {path} is not a file", path=path)
        if path.exists() and not os.access(path, os.W_OK):
            raise WritePermissionsError(f"Cannot write to {path}", path=path)
        if mkdirs:
            path.parent.mkdir(parents=True, exist_ok=True)
        if atomic:
            tmp = cls.tmp_path(path)
            path.write_bytes(compressed)
            tmp.rename(path)
        else:
            path.write_bytes(compressed)

    @classmethod
    def read_text(cls, path: PathLike) -> str:
        """
        Similar to :meth:`read_bytes`, but then converts to UTF-8.
        """
        return cls.read_bytes(path).decode(encoding="utf-8")

    @classmethod
    def read_bytes(cls, path: PathLike) -> bytes:
        """
        Reads, decompressing according to the filename suffix.
        """
        data = Path(path).read_bytes()
        return cls.compressions().guess(path).decompress(data)

    @classmethod
    def tmp_path(cls, path: PathLike, extra: str = "tmp") -> Path:
        now = datetime.now().isoformat(timespec="microsecond").replace(":", "").replace("-", "")
        path = Path(path)
        suffix = "".join(path.suffixes)
        return path.parent / f".part_{extra}.{now}{suffix}"


__all__ = ["Compression", "CompressionSet", "SmartIo"]
