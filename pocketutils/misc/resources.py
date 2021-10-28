import logging
import typing
from datetime import datetime, timedelta
from pathlib import Path
from typing import MutableMapping, Optional, Tuple, Union

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
            PathExistsError: If the path is not a file or symlink to a file or is not readable
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
        self,
        path: PathLike,
        max_sec: Union[timedelta, float],
        *,
        warn_expired_fmt: str = "{path_rel} is {delta} out of date [{mod_rel}]",
        warn_unknown_fmt: str = "{path_rel} mod date is unknown [created: {create_rel}]",
    ) -> Optional[bool]:
        """
        Warns and returns True if ``path`` mod date is more than ``max_sec`` in the past.
        Returns None if it could not be determined.

        The formatting strings can refer to any of these (will be empty if unknown):
        - path: Full path
        - name: File/dir name
        - path_rel: Path relative to ``self._dir``, or full path if not under
        - now: formatted current datetime
        - [mod/create]_dt: Formatted mod/creation datetime
        - [mod/create]_rel: Mod/create datetime in terms of offset from now
        - [mod/create]_delta: Formatted timedelta from now
        - [mod/create]_delta_sec: Number of seconds from now (negative if now < mod/create dt)

        Args:
            path: A specific path to check
            max_sec: Max seconds, or a timedelta
            warn_expired_fmt: Formatting string in terms of the variables listed above
            warn_unknown_fmt: Formatting string in terms of the variables listed above

        Returns:
            Whether it is expired, or None if it could not be determined
        """
        path = Path(path)
        limit = max_sec if isinstance(max_sec, timedelta) else timedelta(seconds=max_sec)
        now = datetime.now().astimezone()
        info = FilesysTools.get_info(path)
        if not info.mod_dt and now - info.mod_dt > limit:
            self._warn_expired(now, info.mod_dt, info.create_dt, path, warn_expired_fmt)
            return True
        elif not info.mod_dt and (not info.create_dt or (now - info.create_dt) > limit):
            self._warn_expired(now, info.mod_dt, info.create_dt, path, warn_unknown_fmt)
            return None
        return False

    def _warn_expired(
        self,
        now: datetime,
        mod: Optional[datetime],
        created: Optional[datetime],
        path: Path,
        fmt: Optional[str],
    ):
        if isinstance(fmt, str):
            fmt = fmt.format
        if path.is_relative_to(self._dir):
            path_rel = str(path.relative_to(self._dir))
        else:
            path_rel = str(path)
        now_str, mod_str, mod_rel, mod_delta, mod_delta_sec = self._pretty(now, mod)
        _, create_str, create_rel, create_delta, create_delta_sec = self._pretty(now, created)
        msg = fmt(
            path=path,
            path_rel=path_rel,
            name=path.name,
            now=now_str,
            mod_dt=mod_str,
            mod_rel=mod_rel,
            mod_delta=mod_delta,
            mod_sec=mod_delta_sec,
            create_dt=create_str,
            create_rel=create_rel,
            create_delta=create_delta,
            create_sec=create_delta_sec,
        )
        self._logger.warning(msg)

    def _pretty(self, now: datetime, then: Optional[datetime]) -> Tuple[str, str, str, str, str]:
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        delta = now - then
        if then is None:
            return now_str, "", "", "", ""
        then_str = then.strftime("%Y-%m-%d %H:%M:%S")
        then_rel = UnitTools.approx_time_wrt(now, then)
        delta_str = UnitTools.delta_time_to_str(delta, space=Chars.narrownbsp)
        return now_str, then_str, then_rel, delta_str, str(delta.total_seconds())


__all__ = ["Resources"]
