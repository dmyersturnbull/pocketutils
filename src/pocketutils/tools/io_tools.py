# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
"""

"""

import abc
import base64
import binascii
import functools
import hashlib
import os
import sys
from dataclasses import dataclass
from typing import Literal, Self, SupportsBytes

from pocketutils.core.input_output import DevNull

try:
    import base2048
except ImportError:
    base2048 = None

__all__ = ["IoUtils", "IoTools"]


Encoding = (
    Literal["2048"]  # for fun
    | Literal["base85"]
    | Literal["base64"]
    | Literal["base64url"]
    | Literal["base64url-tilde"]
    | Literal["base32"]
    | Literal["base32-tilde"]
    | Literal["base32hex"]
    | Literal["base32hex-tilde"]
    | Literal["base32-bech32"]
    | Literal["base32-bech32-tilde"]
    | Literal["base32hex-bech32"]
    | Literal["base32hex-bech32-tilde"]
    | Literal["base16"]
    | Literal["hex"]
)

HashAlgorithm = (
    Literal["shake_256"]
    | Literal["shake_128"]
    | Literal["sha3_512"]
    | Literal["sha3_384"]
    | Literal["sha3_256"]
    | Literal["sha3_224"]
    | Literal["sha2_512"]
    | Literal["sha2_256"]
    | Literal["sha2_224"]
    | Literal["sha1"]
    | Literal["md5"]
    | Literal["crc32"]
)


@functools.total_ordering
class Enc(metaclass=abc.ABCMeta):
    def __reduce__(self: Self) -> str:
        return self.name

    def __hash__(self: Self) -> int:
        return hash(self.name)

    def __eq__(self: Self, other: Self) -> bool:
        return self.name == other.name

    def __lt__(self: Self, other: Self) -> bool:
        return self.name < other.name

    def __str__(self: Self) -> str:
        return self.name

    def __repr__(self: Self) -> str:
        return self.name

    @property
    def name(self: Self) -> str:
        return self.__class__.__name__.lower()

    def encode(self: Self, d: bytes) -> str:
        raise NotImplementedError()

    def decode(self: Self, d: str) -> bytes:
        raise NotImplementedError()


class Base16(Enc):
    def encode(self: Self, d: bytes) -> str:
        return base64.b16encode(d).decode(encoding="ascii")

    def decode(self: Self, d: str) -> bytes:
        return base64.b16decode(d)


class Base32(Enc):
    def encode(self: Self, d: bytes) -> str:
        return base64.b32encode(d).decode(encoding="ascii")

    def decode(self: Self, d: str) -> bytes:
        return base64.b32decode(d)


class Base64(Enc):
    def encode(self: Self, d: bytes) -> str:
        return base64.standard_b64encode(d).decode(encoding="ascii")

    def decode(self: Self, d: str) -> bytes:
        return base64.standard_b64decode(d)


class Base64Url(Enc):
    def encode(self: Self, d: bytes) -> str:
        return base64.urlsafe_b64encode(d).decode(encoding="ascii")

    def decode(self: Self, d: str) -> bytes:
        return base64.urlsafe_b64decode(d)


class Base32Hex(Enc):
    def encode(self: Self, d: bytes) -> str:
        return base64.b32hexencode(d).decode(encoding="ascii")

    def decode(self: Self, d: str) -> bytes:
        return base64.b32hexdecode(d)


class Base32HexTilde(Enc):
    def encode(self: Self, d: bytes) -> str:
        return base64.b32hexencode(d).decode(encoding="ascii").replace("=", "~")

    def decode(self: Self, d: str) -> bytes:
        return base64.b32hexdecode(d.replace("=", "~"))


class Base2048(Enc):
    def encode(self: Self, d: bytes) -> str:
        return base2048.encode(d)

    def decode(self: Self, d: str) -> bytes:
        return base2048.decode(d)


class _Alphabet32Enc(Enc):
    _base32_alphabet = ""
    _to_alphabet = ""

    def encode(self: Self, d: bytes) -> str:
        encoded = base64.b32encode(d).decode(encoding="ascii")
        alphabet = dict(zip(self._base32_alphabet, self._to_alphabet))
        return "".join([alphabet[v] for v in encoded])

    def decode(self: Self, d: str) -> bytes:
        alphabet = dict(zip(self._to_alphabet, self._base32_alphabet))
        d = "".join([alphabet[v] for v in d])
        return base64.b32hexdecode(d)


class Base32Bech(_Alphabet32Enc):
    _base32_alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567="
    _to_alphabet = "qpzry9x8gf2tvdw0s3jn54khce6mua7l="

    @property
    def name(self: Self) -> str:
        return "base32-bech"


class Base32BechTilde(_Alphabet32Enc):
    _base32_alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567="
    _to_alphabet = "qpzry9x8gf2tvdw0s3jn54khce6mua7l~"

    @property
    def name(self: Self) -> str:
        return "base32-bech-tilde"


class Base32HexBech(_Alphabet32Enc):
    _base32_alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUV="
    _to_alphabet = "023456789acdefghjklmnpqrstuvwxyz="

    @property
    def name(self: Self) -> str:
        return "base32hex-bech"


class Base32HexBechTilde(_Alphabet32Enc):
    _base32_alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUV="
    _to_alphabet = "023456789acdefghjklmnpqrstuvwxyz~"

    @property
    def name(self: Self) -> str:
        return "base32hex-bech-tilde"


class Base64UrlTilde(Enc):
    @property
    def name(self: Self) -> str:
        return "base64url-tilde"

    def encode(self: Self, d: bytes) -> str:
        return base64.urlsafe_b64encode(d).decode(encoding="ascii").replace("=", "~")

    def decode(self: Self, d: str) -> bytes:
        return base64.urlsafe_b64decode(d.replace("~", "="))


class Base85(Enc):
    def encode(self: Self, d: bytes) -> str:
        return base64.b85encode(d).decode(encoding="ascii")

    def decode(self: Self, d: str) -> bytes:
        return base64.b85decode(d)


ENCODINGS = {
    e.name: e
    for e in [
        Base16,
        Base32,
        Base32Hex,
        Base32HexTilde,
        Base32Bech,
        Base32HexBech,
        Base32BechTilde,
        Base32HexBechTilde,
        Base64,
        Base64Url,
        Base64UrlTilde,
        Base85,
        Base2048,
    ]
}


@dataclass(slots=True, frozen=True)
class IoUtils:
    def get_encoding(self: Self, encoding: str = "utf-8") -> str:
        """
        Returns a text encoding from a more flexible string.
        Ignores hyphens and lowercases the string.
        Permits these nonstandard shorthands:

          - `"platform"`: use `sys.getdefaultencoding()` on the fly
          - `"utf-8(bom)"`: use `"utf-8-sig"` on Windows; `"utf-8"` otherwise
          - `"utf-16(bom)"`: use `"utf-16-sig"` on Windows; `"utf-16"` otherwise
          - `"utf-32(bom)"`: use `"utf-32-sig"` on Windows; `"utf-32"` otherwise
        """
        encoding = encoding.lower().replace("-", "")
        if encoding == "platform":
            encoding = sys.getdefaultencoding()
        if encoding == "utf-8(bom)":
            encoding = "utf-8-sig" if os.name == "nt" else "utf-8"
        if encoding == "utf-16(bom)":
            encoding = "utf-16-sig" if os.name == "nt" else "utf-16"
        if encoding == "utf-32(bom)":
            encoding = "utf-32-sig" if os.name == "nt" else "utf-32"
        return encoding

    def get_encoding_errors(self: Self, errors: str | None) -> str | None:
        """
        Returns the value passed as`errors=` in `open`.

        Raises:
            ValueError: If invalid
        """
        if errors is None:
            return "strict"
        if errors in (
            "strict",
            "ignore",
            "replace",
            "xmlcharrefreplace",
            "backslashreplace",
            "namereplace",
            "surrogateescape",
            "surrogatepass",
        ):
            return errors
        msg = f"Invalid value {errors} for errors"
        raise ValueError(msg)

    def hash_digest(
        self: Self,
        data: SupportsBytes | str,
        algorithm: HashAlgorithm,
        *,
        digest_length: int | None = None,
        **kwargs,
    ) -> bytes:
        kwargs = {"usedforsecurity": False} | kwargs
        x = data.encode("utf-8") if isinstance(data, str) else bytes(data)
        if algorithm == "crc32":
            return bytes(binascii.crc32(x))
        elif algorithm.startswith("shake_"):
            m = getattr(hashlib, algorithm)(**kwargs)
            m.update(x)
            return m.digest(128 if digest_length is None else digest_length)
        else:
            m = hashlib.new(algorithm, **kwargs)
            m.update(x)
            return m.digest()

    def encode(self: Self, d: bytes, enc: Encoding = "base64") -> str:
        if enc not in ENCODINGS:
            msg = f"Unknown encoding {enc}"
            raise ValueError(msg)
        return ENCODINGS[enc].encode(d)

    def decode(self: Self, d: bytes, enc: Encoding = "base64") -> bytes:
        if enc not in ENCODINGS:
            msg = f"Unknown encoding {enc}"
            raise ValueError(msg)
        return ENCODINGS[enc].decode(d)

    def devnull(self: Self) -> DevNull:
        """
        Yields a 'writer' that does nothing.

        Example:

            with CommonTools.devnull() as devnull:
                devnull.write('hello')
        """
        yield DevNull()


IoTools = IoUtils()
