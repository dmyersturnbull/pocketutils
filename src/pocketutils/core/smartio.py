# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
"""
Compression-aware reading and writing of files.
"""

from __future__ import annotations

import abc
import bz2
import gzip
import lzma
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any, Self, TypeVar

from pocketutils.core.exceptions import AccessDeniedError, KeyReusedError, PathExistsError

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping


PathLike = str | PurePath
T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class CompressedPath:
    parent: Path
    stem: str
    suffix: str


@dataclass(frozen=True, slots=True)
class Compression:
    name: str
    suffixes: list[str]
    compress: Callable[[bytes], bytes]
    decompress: Callable[[bytes], bytes]

    def split_path(self: Self, path: PurePath | str) -> CompressedPath:
        path = Path(path)
        for suffix in self.suffixes:
            if path.suffix == suffix:
                return CompressedPath(path.parent, path.stem, suffix)
        return CompressedPath(path.parent, path.stem, "")

    def compress_file(self: Self, source: PurePath | str, dest: PurePath | str, atomic: bool = False) -> None:
        source = Path(source)
        dest = Path(dest)
        temp = dest.parent / ("~" + dest.name + ".part") if atomic else dest
        data = self.compress(source.read_bytes())
        temp.write_bytes(data)
        if atomic:
            temp.rename(dest)

    def decompress_file(self: Self, source: PurePath | str, dest: PurePath | str, atomic: bool = False) -> None:
        source = Path(source)
        dest = Path(dest)
        temp = dest.parent / ("~" + dest.name + ".part") if atomic else dest
        data = self.decompress(source.read_bytes())
        temp.write_bytes(data)
        if atomic:
            temp.rename(dest)


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
            raise KeyReusedError(msg, key=fmt.name, original_value=already)
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

            Compression.of("gzip").suffix  # ".gz"
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


@dataclass(frozen=True, slots=True)
class AbstractSmartIo(metaclass=abc.ABCMeta):
    _compressions: CompressionSet | None = None

    @property
    def mapping(self: Self) -> Mapping[str, Compression]:
        return self.compressions.mapping

    @property
    def compressions(self: Self) -> CompressionSet:
        if self._compressions is None:
            self._compressions = self._new_compression_list()
        return self._compressions

    @property
    def all_suffixes(self: Self) -> Iterable[str]:
        for c in self.compressions:
            yield from c.suffixes

    def _new_compression_list(self: Self) -> CompressionSet:
        raise NotImplementedError()

    def write(
        self: Self,
        data: Any,
        path: PathLike,
        *,
        atomic: bool = False,
        mkdirs: bool = False,
        exist_ok: bool = False,
    ) -> None:
        path = Path(path)
        compressed = self.compressions.guess(path).compress(data)
        if path.exists() and not path.is_file():
            raise PathExistsError(filename=str(path))
        if path.exists() and not exist_ok:
            raise PathExistsError(filename=str(path))
        if path.exists() and not os.access(path, os.W_OK):
            raise AccessDeniedError(filename=str(path))
        if mkdirs:
            path.parent.mkdir(parents=True, exist_ok=True)
        if atomic:
            tmp = self.tmp_path(path)
            path.write_bytes(compressed)
            tmp.rename(path)
        else:
            path.write_bytes(compressed)

    def read_text(self: Self, path: PathLike, encoding: str = "utf-8") -> str:
        """
        Similar to :meth:`read_bytes`, but then converts to UTF-8.
        """
        return self.read_bytes(path).decode(encoding=encoding)

    def read_bytes(self: Self, path: PathLike) -> bytes:
        """
        Reads, decompressing according to the filename suffix.
        """
        data = Path(path).read_bytes()
        return self.compressions.guess(path).decompress(data)

    def tmp_path(self: Self, path: PathLike, extra: str = "tmp") -> Path:
        now = datetime.now(tz=UTC).isoformat(timespec="microsecond")
        now = now.replace(":", "").replace("-", "")
        path = Path(path)
        suffix = "".join(path.suffixes)
        return path.parent / f".part_{extra}.{now}{suffix}"


@dataclass(frozen=True, slots=True)
class SmartIoUtil(AbstractSmartIo, metaclass=abc.ABCMeta):
    def _new_compression_list(self: Self) -> CompressionSet:
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


SmartIo = SmartIoUtil()

__all__ = ["Compression", "CompressionSet", "SmartIo", "SmartIoUtil"]
