"""
Compression-aware reading and writing of files.
"""
from __future__ import annotations

import bz2
import gzip
import lzma
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any, Self, TypeVar

from pocketutils.core.exceptions import WritePermissionsError, XFileExistsError

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

PathLike = str | PurePath
T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Compression:
    name: str
    suffixes: list[str]
    compress: Callable[[bytes], bytes]
    decompress: Callable[[bytes], bytes]

    def compress_file(self: Self, source: PurePath | str, dest: PurePath | str | None = None) -> None:
        source = Path(source)
        dest = source.parent / (source.name + self.suffixes[0]) if dest is None else Path(dest)
        data = self.compress(source.read_bytes())
        dest.write_bytes(data)

    def decompress_file(self: Self, source: PurePath | str, dest: PurePath | str | None = None) -> None:
        source = Path(source)
        dest = source.with_suffix("") if dest is None else Path(dest)
        data = self.decompress(source.read_bytes())
        dest.write_bytes(data)


def identity(x: T) -> T:
    return x


@dataclass(frozen=True, slots=True)
class CompressionSet:
    mapping: dict[str, Compression]

    @classmethod
    def empty(cls: type[Self]) -> Self:
        return CompressionSet({"": Compression("", [], identity, identity)})

    def __add__(self: Self, fmt: Compression):
        new = {fmt.name: fmt} | {s: fmt for s in fmt.suffixes}
        already = {v for k, v in self.mapping.items() if k in new}
        if len(already) > 1 or len(already) == 1 and already != {fmt}:
            msg = f"Keys from {fmt} already mapped to {already}"
            raise ValueError(msg)
        return CompressionSet(self.mapping | new)

    def __sub__(self: Self, fmt: Compression) -> CompressionSet:
        return CompressionSet(
            {k: v for k, v in self.mapping.items() if k != fmt.name and k not in fmt.suffixes},
        )

    def __or__(self: Self, fmt: CompressionSet) -> CompressionSet:
        return CompressionSet(self.mapping | fmt.mapping)

    def __getitem__(self: Self, t: Compression | str) -> Compression:
        """
        Returns a FileFormat from a name (e.g. "gz" or "gzip").
        Case-insensitive.

        Example:
            `Compression.of("gzip").suffix  # ".gz"`
        """
        if isinstance(t, Compression):
            return t
        return self.mapping[t]

    def guess(self: Self, path: PathLike) -> Compression:
        if "." not in path.name:
            return self[""]
        try:
            return self[path.suffix]
        except KeyError:
            return self[""]


def _get_compressions() -> CompressionSet:
    import brotli
    import lz4.frame
    import snappy
    import zstandard

    return (
        CompressionSet.empty()
        + Compression("gzip", [".gz", ".gzip"], gzip.compress, gzip.decompress)
        + Compression("brotli", [".br", ".brotli"], brotli.compress, brotli.decompress)
        + Compression("zstandard", [".zst", ".zstd"], zstandard.compress, zstandard.decompress)
        + Compression("lz4", [".lz4"], lz4.frame.compress, lz4.frame.decompress)
        + Compression("snappy", [".snappy"], snappy.compress, snappy.decompress)
        + Compression("bzip2", [".bz2", ".bzip2"], bz2.compress, bz2.decompress)
        + Compression("xz", [".xz"], lzma.compress, lzma.decompress)
        + Compression("lzma", [".lzma"], lzma.compress, lzma.decompress)
    )


@dataclass(frozen=True, slots=True)
class SmartIo:
    __COMPRESSIONS = None

    @classmethod
    def mapping(cls: type[Self]) -> Mapping[str, Compression]:
        return cls.compressions().mapping

    @classmethod
    def compressions(cls: type[Self]) -> CompressionSet:
        if cls.__COMPRESSIONS is None:
            _COMPRESSIONS = _get_compressions()
        return cls.__COMPRESSIONS

    @classmethod
    def write(
        cls: type[Self],
        data: Any,
        path: PathLike,
        *,
        atomic: bool = False,
        mkdirs: bool = False,
        exist_ok: bool = False,
    ) -> None:
        path = Path(path)
        compressed = cls.compressions().guess(path).compress(data)
        if path.exists() and not path.is_file():
            msg = f"Path {path} is not a file"
            raise WritePermissionsError(msg, path=path)
        if path.exists() and not exist_ok:
            msg = f"Path {path} exists"
            raise XFileExistsError(msg, path=path)
        if path.exists() and not os.access(path, os.W_OK):
            msg = f"Cannot write to {path}"
            raise WritePermissionsError(msg, path=path)
        if mkdirs:
            path.parent.mkdir(parents=True, exist_ok=True)
        if atomic:
            tmp = cls.tmp_path(path)
            path.write_bytes(compressed)
            tmp.rename(path)
        else:
            path.write_bytes(compressed)

    @classmethod
    def read_text(cls: type[Self], path: PathLike, encoding: str = "utf-8") -> str:
        """
        Similar to :meth:`read_bytes`, but then converts to UTF-8.
        """
        return cls.read_bytes(path).decode(encoding=encoding)

    @classmethod
    def read_bytes(cls: type[Self], path: PathLike) -> bytes:
        """
        Reads, decompressing according to the filename suffix.
        """
        data = Path(path).read_bytes()
        return cls.compressions().guess(path).decompress(data)

    @classmethod
    def tmp_path(cls: type[Self], path: PathLike, extra: str = "tmp") -> Path:
        now = datetime.now().isoformat(timespec="microsecond")
        now = now.replace(":", "").replace("-", "")
        path = Path(path)
        suffix = "".join(path.suffixes)
        return path.parent / f".part_{extra}.{now}{suffix}"


__all__ = ["Compression", "CompressionSet", "SmartIo"]
