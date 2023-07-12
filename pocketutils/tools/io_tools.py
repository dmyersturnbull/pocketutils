import abc
import base64
import binascii
import hashlib
from typing import Literal, SupportsBytes

from pocketutils import DevNull

try:
    import base2048
except ImportError:
    base2048 = None


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


class Enc(metaclass=abc.ABCMeta):
    @property
    def name(self) -> str:
        return self.__class__.__name__.lower()

    def encode(self, d: bytes) -> str:
        raise NotImplementedError()

    def decode(self, d: str) -> bytes:
        raise NotImplementedError()


class Base16(Enc):
    def encode(self, d: bytes) -> str:
        return base64.b16encode(d).decode(encoding="ascii")

    def decode(self, d: str) -> bytes:
        return base64.b16decode(d)


class Base32(Enc):
    def encode(self, d: bytes) -> str:
        return base64.b32encode(d).decode(encoding="ascii")

    def decode(self, d: str) -> bytes:
        return base64.b32decode(d)


class Base64(Enc):
    def encode(self, d: bytes) -> str:
        return base64.standard_b64encode(d).decode(encoding="ascii")

    def decode(self, d: str) -> bytes:
        return base64.standard_b64decode(d)


class Base64Url(Enc):
    def encode(self, d: bytes) -> str:
        return base64.urlsafe_b64encode(d).decode(encoding="ascii")

    def decode(self, d: str) -> bytes:
        return base64.urlsafe_b64decode(d)


class Base32Hex(Enc):
    def encode(self, d: bytes) -> str:
        return base64.b32hexencode(d).decode(encoding="ascii")

    def decode(self, d: str) -> bytes:
        return base64.b32hexdecode(d)


class Base32HexTilde(Enc):
    def encode(self, d: bytes) -> str:
        return base64.b32hexencode(d).decode(encoding="ascii").replace("=", "~")

    def decode(self, d: str) -> bytes:
        return base64.b32hexdecode(d.replace("=", "~"))


class Base2048(Enc):
    def encode(self, d: bytes) -> str:
        return base2048.encode(d).decode(encoding="ascii")

    def decode(self, d: str) -> bytes:
        return base2048.decode(d)


class _Alphabet32Enc(Enc):
    _base32_alphabet = ""
    _to_alphabet = ""

    def encode(self, d: bytes) -> str:
        encoded = base64.b32encode(d).decode(encoding="ascii")
        alphabet = dict(zip(self._base32_alphabet, self._to_alphabet))
        return "".join([alphabet[v] for v in encoded])

    def decode(self, d: str) -> bytes:
        alphabet = dict(zip(self._to_alphabet, self._base32_alphabet))
        d = "".join([alphabet[v] for v in d])
        return base64.b32hexdecode(d)


class Base32Bech(_Alphabet32Enc):
    _base32_alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567="
    _to_alphabet = "qpzry9x8gf2tvdw0s3jn54khce6mua7l="

    @property
    def name(self) -> str:
        return "base32-bech"


class Base32BechTilde(_Alphabet32Enc):
    _base32_alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567="
    _to_alphabet = "qpzry9x8gf2tvdw0s3jn54khce6mua7l~"

    @property
    def name(self) -> str:
        return "base32-bech-tilde"


class Base32HexBech(_Alphabet32Enc):
    _base32_alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUV="
    _to_alphabet = "023456789acdefghjklmnpqrstuvwxyz="

    @property
    def name(self) -> str:
        return "base32hex-bech"


class Base32HexBechTilde(_Alphabet32Enc):
    _base32_alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUV="
    _to_alphabet = "023456789acdefghjklmnpqrstuvwxyz~"

    @property
    def name(self) -> str:
        return "base32hex-bech-tilde"


class Base64UrlTilde(Enc):
    @property
    def name(self) -> str:
        return "base64url-tilde"

    def encode(self, d: bytes) -> str:
        return base64.urlsafe_b64encode(d).decode(encoding="ascii").replace("=", "~")

    def decode(self, d: str) -> bytes:
        return base64.urlsafe_b64decode(d.replace("~", "="))


class Base85(Enc):
    def encode(self, d: bytes) -> str:
        return base64.b85encode(d).decode(encoding="ascii")

    def decode(self, d: str) -> bytes:
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


class IoTools:
    @classmethod
    def hash_digest(
        cls,
        data: SupportsBytes | str,
        algorithm: HashAlgorithm,
        *,
        digest_length: int | None = None,
        **kwargs,
    ) -> bytes:
        kwargs = dict(usedforsecurity=False) | kwargs
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

    @classmethod
    def encode(cls, d: bytes, to: Encoding = "base64"):
        if to not in ENCODINGS:
            raise ValueError(f"Unknown encoding {to}")
        return ENCODINGS[to].encode(d)

    @classmethod
    def decode(cls, d: bytes, to: Encoding = "base64"):
        if to not in ENCODINGS:
            raise ValueError(f"Unknown encoding {to}")
        return ENCODINGS[to].decode(d)

    @classmethod
    def devnull(cls):
        """
        Yields a 'writer' that does nothing.

        Example:
            .. code-block::

                with CommonTools.devnull() as devnull:
                    devnull.write('hello')
        """
        yield DevNull()


__all__ = ["IoTools"]
