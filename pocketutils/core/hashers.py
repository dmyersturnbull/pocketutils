from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional, Union

from pocketutils.core.exceptions import (
    FileDoesNotExistError,
    HashValidationFailedError,
    IllegalStateError,
)


@dataclass(frozen=True, unsafe_hash=True, repr=True)
class HashableFile:
    """
    A file ``path`` with an associated hash file named ``path.with_suffix(path.suffix + "." + suffix)``.
    For example, the path might be ``x.tar.gz`` and the hash file ``x.tar.gz.sha1``.

    There are three valid states:
        - non-hashed (HashableFile)
        - post-hashed (PostHashedFile)
        - pre-hashed (PreHashedFile)

        file_path: The path of the file
        hash_path: The path of the hash
    """

    file_path: Path
    hash_path: Path
    actual: Optional[str]
    expected: Optional[str]
    algorithm: Callable[[], Any]
    buffer_size: int = 16 * 1024

    def __post_init__(self):
        if not self.file_path.exists():
            raise FileDoesNotExistError(f"File {self.file_path} not found", path=self.file_path)

    @property
    def files_exist(self) -> bool:
        return self.file_path.exists() and self.hash_path.exists()

    def computed(self) -> PostHashedFile:
        return PostHashedFile(
            file_path=self.file_path,
            hash_path=self.hash_path,
            actual=self._get_or_compute(),
            expected=self.expected,
            algorithm=self.algorithm,
            buffer_size=self.buffer_size,
        )

    def precomputed(self) -> PreHashedFile:
        if not self.hash_path.exists():
            raise IllegalStateError(f"Hash file {self.hash_path} does not exist")
        return PreHashedFile(
            file_path=self.file_path,
            hash_path=self.hash_path,
            expected=self._read_hash(),
            actual=self.actual,
            algorithm=self.algorithm,
            buffer_size=self.buffer_size,
        )

    def compute(self) -> str:
        alg = self.algorithm()
        with self.file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(self.buffer_size), b""):
                alg.update(chunk)
        return alg.hexdigest()

    def _read_hash(self) -> str:
        return self.hash_path.read_text(encoding="utf8").strip()

    def _write_hash(self) -> None:
        self.hash_path.write_text(self.actual, encoding="utf8")

    def _get_or_compute(self) -> str:
        if self.actual is not None:
            return self.actual
        return self.compute()


@dataclass(frozen=True, unsafe_hash=True, repr=True)
class NonHashedFile(HashableFile):
    def __post_init__(self):
        super().__post_init__()
        if self.hash_path.exists():
            raise IllegalStateError(f"Hash file {self.hash_path} already exists")


@dataclass(frozen=True, unsafe_hash=True, repr=True)
class PostHashedFile(HashableFile):
    def precomputed(self) -> PrePostHashedFile:
        if not self.hash_path.exists():
            raise IllegalStateError(f"Hash file {self.hash_path} does not exist")
        return PrePostHashedFile(
            file_path=self.file_path,
            hash_path=self.hash_path,
            expected=self._read_hash(),
            actual=self.actual,
            algorithm=self.algorithm,
            buffer_size=self.buffer_size,
        )

    def write(self) -> None:
        """
        Writes the actual (computed) hash to the file.
        Does not affect the state, except that the file will exist.

        Raises:
            IllegalStateError: If the hash file already exists.
                               This can only be true if it was written after instantiating this.
        """
        if self.hash_path.exists():
            raise IllegalStateError(f"Hash file {self.hash_path} already exists")
        self._write_hash()

    def __post_init__(self):
        super().__post_init__()
        if self.hash_path.exists():
            raise IllegalStateError(f"Hash file {self.hash_path} already exists")
        if self.actual is None:
            raise IllegalStateError(f"Actual hash value does not exist for path {self.file_path}")


@dataclass(frozen=True, unsafe_hash=True, repr=True)
class PreHashedFile(HashableFile):
    def __post_init__(self):
        super().__post_init__()
        if self.expected is None:
            raise IllegalStateError(f"Expected hash value does not exist for path {self.file_path}")

    def computed(self) -> PrePostHashedFile:
        return PrePostHashedFile(
            file_path=self.file_path,
            hash_path=self.hash_path,
            actual=self._get_or_compute(),
            expected=self.expected,
            algorithm=self.algorithm,
            buffer_size=self.buffer_size,
        )


@dataclass(frozen=True, unsafe_hash=True, repr=True)
class PrePostHashedFile(HashableFile):
    def __post_init__(self):
        super().__post_init__()
        if self.expected is None:
            raise ValueError(f"Expected hash value does not exist for path {self.file_path}")
        if self.actual is None:
            raise ValueError(f"Actual hash value does not exist for path {self.file_path}")

    def match_or_raise(self) -> str:
        if not self.matches:
            raise HashValidationFailedError(
                f"Hash for file {self.file_path} does not match",
                key=self.file_path,
                expected=self.expected,
                actual=self.actual,
            )
        return self.expected

    @property
    def matches(self) -> bool:
        return self.actual == self.expected


class Hasher:
    """
    Makes and reads .sha1 / .sha256 files next to existing paths.
    """

    def __init__(
        self,
        algorithm: str = "sha1",
        buffer_size: int = 16 * 1024,
    ):
        self._algorithm = algorithm
        if isinstance(algorithm, str):
            self._algorithm_class = getattr(hashlib, algorithm)
            self._suffix = algorithm
        self._buffer_size = buffer_size

    @property
    def algorithm(self) -> str:
        return self._algorithm

    def to_write(self, path: Union[Path, str]) -> PostHashedFile:
        """
        Gets a HashableFile that has an already-existing
        Computes the actual hash from the file.
        Complains if the hash file already exists.
        """
        return self._new(path).computed()

    def to_verify(self, path: Union[Path, str]) -> PrePostHashedFile:
        """
        Gets a HashableFile that has an existing hash file.
        Computes the actual hash from the file.
        Complains if the hash file does not exist.
        """
        return self._new(path).precomputed().computed()

    def any(
        self, path: Union[Path, str], computed: bool = False, precomputed: Optional[bool] = False
    ) -> HashableFile:
        new = self._new(path)
        if computed and (precomputed or (precomputed is None and new.hash_path.exists())):
            return new.precomputed().computed()
        elif precomputed or (precomputed is None and new.hash_path.exists()):
            return new.precomputed()
        elif computed:
            return new.computed()
        else:
            return new

    def _new(self, path: Path):
        path = Path(path)
        hash_path = path.with_suffix(path.suffix + "." + self._suffix)
        return HashableFile(
            file_path=path,
            hash_path=hash_path,
            expected=None,
            actual=None,
            algorithm=self._algorithm_class,
            buffer_size=self._buffer_size,
        )


__all__ = [
    "Hasher",
    "HashableFile",
    "NonHashedFile",
    "PreHashedFile",
    "PostHashedFile",
    "PrePostHashedFile",
]
