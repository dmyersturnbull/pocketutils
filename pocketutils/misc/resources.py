import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import AbstractSet, MutableMapping, Optional, Tuple, Union, Any

import orjson

from pocketutils.core import PathLike
from pocketutils.core._internal import read_txt_or_gz, JSON_SUFFIXES, TOML_SUFFIXES, GZ_BZ2_SUFFIXES
from pocketutils.core.chars import Chars
from pocketutils.core.dot_dict import NestedDotDict
from pocketutils.core.exceptions import (
    DirDoesNotExistError,
    FileDoesNotExistError,
    MissingResourceError,
    PathExistsError,
)
from pocketutils.tools.common_tools import CommonTools
from pocketutils.tools.filesys_tools import FilesysTools
from pocketutils.tools.unit_tools import UnitTools

_logger = logging.getLogger("pocketutils")


class Resources:
    def __init__(self, path: PathLike, *, logger=_logger):
        self._dir = Path(path)
        self._logger = logger
        self._in_memory: MutableMapping[str, Any] = {}

    @property
    def home(self) -> Path:
        return self._dir

    def to_memory(self, key: str, data: Any):
        self._in_memory[key] = data

    def from_memory(self, key: str) -> Any:
        return self._in_memory[key]

    def contains(self, *nodes: PathLike) -> bool:
        """Returns whether a resource file (or dir) exists."""
        return self.path(*nodes).exists()

    def contains_a_file(
        self, *nodes: PathLike, suffixes: Optional[AbstractSet[str]] = None
    ) -> bool:
        try:
            self.a_file(*nodes, suffixes=suffixes)
            return True
        except MissingResourceError:
            return False

    def path(self, *nodes: PathLike, exists: bool = False) -> Path:
        """
        Gets a path of a test resource file under ``resources/``.

        Raises:
            MissingResourceError: If the path is not found
        """
        if len(nodes) == 1 and isinstance(nodes[0], Path) and nodes[0].is_absolute():
            path = nodes[0]
        else:
            path = Path(self._dir, *nodes)
            path = path.with_suffix(path.suffix)
        if exists and not path.exists():
            raise MissingResourceError(f"Resource {path} missing")
        return path

    def file(self, *nodes: PathLike) -> Path:
        """
        Gets a path of a test resource file under ``resources/``.

        Raises:
            MissingResourceError: If the path is not found
            PathExistsError: If the path is not a file or symlink to a file or is not readable
        """
        path = self.path(*nodes)
        info = FilesysTools.get_info(path)
        if not info.is_file:
            raise PathExistsError(f"Resource {path} is not a file!")
        if not info.is_readable_file:
            raise FileDoesNotExistError(f"Resource {path} is not readable")
        return path

    def dir(self, *nodes: PathLike) -> Path:
        """
        Gets a path of a test resource file under ``resources/``.

        Raises:
            MissingResourceError: If the path is not found and ``not missing_ok``
            PathExistsError: If the path is not a dir, symlink to a dir, or mount,
                             or lacks 'R' or 'X' permissions
        """
        path = self.path(*nodes)
        info = FilesysTools.get_info(path)
        if not info.exists:
            raise DirDoesNotExistError(f"Resource {path} does not exist")
        if not info.is_dir:
            raise PathExistsError(f"Resource {path} is not a directory")
        if info.is_readable_dir:
            raise FileDoesNotExistError(f"Resource {path} is not readable")
        return path

    def a_file(self, *nodes: PathLike, suffixes: Optional[AbstractSet[str]] = None) -> Path:
        """
        Gets a path of a test resource file under ``resources/``, ignoring suffix.

        Args:
            nodes: Path nodes under ``resources/``
            suffixes: Set of acceptable suffixes; if None, only the exact file is accepted
        """
        path = self.path(*nodes)
        if path.is_file():
            return path
        options = [
            p
            for p in path.parent.glob(path.stem + "*")
            if p.is_file() and (suffixes is None or p.suffix in suffixes)
        ]
        try:
            return CommonTools.only(options)
        except LookupError:
            raise MissingResourceError(f"Resource {path} missing") from None

    def toml(self, *nodes: PathLike) -> NestedDotDict:
        """Reads a TOML file under ``resources/``."""
        path = self.a_file(*nodes, suffixes=GZ_BZ2_SUFFIXES)
        return NestedDotDict.read_toml(path)

    def json(self, *nodes: PathLike) -> NestedDotDict:
        """Reads a JSON file under ``resources/``."""
        path = self.a_file(*nodes, suffixes=GZ_BZ2_SUFFIXES)
        return NestedDotDict.read_json(path)

    def json_dict(self, *nodes: PathLike) -> MutableMapping:
        """Reads a JSON file under ``resources/``."""
        path = self.a_file(*nodes, suffixes=GZ_BZ2_SUFFIXES)
        return orjson.loads(read_txt_or_gz(path))


__all__ = ["Resources"]
