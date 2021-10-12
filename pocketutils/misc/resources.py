import logging
import typing
from datetime import datetime, timedelta
from pathlib import Path
from typing import MutableMapping, Optional, Union

import orjson

from pocketutils.core import PathLike
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

    def contains(self, *nodes: PathLike, suffix: Optional[str] = None) -> bool:
        """Returns whether a resource file (or dir) exists."""
        return self.path(*nodes, suffix=suffix).exists()

    def path(self, *nodes: PathLike, suffix: Optional[str] = None, exists: bool = False) -> Path:
        """
        Gets a path of a test resource file under ``resources/``.

        Raises:
            MissingResourceError: If the path is not found
        """
        path = Path(self._dir, "resources", *nodes)
        path = path.with_suffix(path.suffix if suffix is None else suffix)
        if exists and not path.exists():
            raise MissingResourceError(f"Resource {path} missing")
        return path

    def file(self, *nodes: PathLike, suffix: Optional[str] = None) -> Path:
        """
        Gets a path of a test resource file under ``resources/``.

        Raises:
            MissingResourceError: If the path is not found
            PathExistsError: If the path is not a file or symlink to a file,
                             or is not readable
        """
        path = self.path(*nodes, suffix=suffix)
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

    def a_file(self, *nodes: PathLike, suffixes: Optional[typing.Set[str]] = None) -> Path:
        """
        Gets a path of a test resource file under ``resources/``, ignoring suffix.

        Args:
            nodes: Path nodes under ``resources/``
            suffixes: Set of acceptable suffixes; if None, all are accepted
        """
        path = Path(self._dir, "resources", *nodes)
        options = [
            p
            for p in path.parent.glob(path.stem + "*")
            if p.is_file() and (suffixes is None or p.suffix in suffixes)
        ]
        try:
            return CommonTools.only(options)
        except LookupError:
            raise MissingResourceError(f"Resource {path} missing") from None

    def json(self, *nodes: PathLike, suffix: Optional[str] = None) -> NestedDotDict:
        """Reads a JSON file under ``resources/``."""
        path = self.path(*nodes, suffix=suffix)
        data = orjson.loads(Path(path).read_text(encoding="utf8", errors="strict"))
        return NestedDotDict(data)

    def json_dict(self, *nodes: PathLike, suffix: Optional[str] = None) -> MutableMapping:
        """Reads a JSON file under ``resources/``."""
        path = self.path(*nodes, suffix=suffix)
        data = orjson.loads(Path(path).read_text(encoding="utf8", errors="strict"))
        return data

    def check_expired(
        self, path: PathLike, max_sec: Union[timedelta, float], *, what: Optional[str] = None
    ) -> bool:
        """
        Warns and returns True if ``path`` mod date is more than ``max_sec`` in the past.

        Args:
            path: A specific path to check
            max_sec: Max seconds, or a timedelta
            what: Substitute the path with this string in logging
        """
        path = Path(path)
        what = str(path) if what is None else what
        limit = max_sec if isinstance(max_sec, timedelta) else timedelta(seconds=max_sec)
        now = datetime.now().astimezone()
        then = FilesysTools.get_info(path).mod_or_create_dt
        delta = now - then
        if delta > limit:
            delta_str = UnitTools.delta_time_to_str(delta, space=Chars.narrownbsp)
            then_str = UnitTools.approx_time_wrt(now, then)
            self._logger.warning(f"{what} may be {delta_str} out of date. [{then_str}]")
            return True
        return False


__all__ = ["Resources"]
