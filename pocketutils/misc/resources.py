import logging
import os
import typing
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import MutableMapping, Optional, Any, Union

import orjson
from pocketutils.core.chars import Chars
from pocketutils.core.dot_dict import NestedDotDict
from pocketutils.core.exceptions import FileDoesNotExistError, MissingResourceError, PathExistsError
from pocketutils.tools.common_tools import CommonTools
from pocketutils.tools.unit_tools import UnitTools


logger = logging.getLogger("pocketutils")


@dataclass(frozen=True, repr=True)
class MandosResources:
    resource_dir: Path
    logger: Any = logger

    def contains(self, *nodes: Union[Path, str], suffix: Optional[str] = None) -> bool:
        """Returns whether a resource file (or dir) exists."""
        return self.path(*nodes, suffix=suffix).exists()

    def path(
        self, *nodes: Union[Path, str], suffix: Optional[str] = None, exists: bool = False
    ) -> Path:
        """Gets a path of a test resource file under ``resources/``."""
        path = Path(self.resource_dir, "resources", *nodes)
        path = path.with_suffix(path.suffix if suffix is None else suffix)
        if exists and not path.exists():
            raise MissingResourceError(f"Resource {path} missing")
        return path

    def file(self, *nodes: Union[Path, str], suffix: Optional[str] = None) -> Path:
        """Gets a path of a test resource file under ``resources/``."""
        path = self.path(*nodes, suffix=suffix)
        if not path.is_file():
            raise PathExistsError(f"Resource {path} is not a file!")
        if not os.access(path, os.R_OK):
            raise FileDoesNotExistError(f"Resource {path} is not readable")
        return path

    def dir(self, *nodes: Union[Path, str]) -> Path:
        """Gets a path of a test resource file under ``resources/``."""
        path = self.path(*nodes)
        if not path.is_dir() and not path.is_mount():
            raise PathExistsError(f"Resource {path} is not a directory!")
        return path

    def a_file(self, *nodes: Union[Path, str], suffixes: Optional[typing.Set[str]] = None) -> Path:
        """Gets a path of a test resource file under ``resources/``, ignoring suffix."""
        path = Path(self.resource_dir, "resources", *nodes)
        options = [
            p
            for p in path.parent.glob(path.stem + "*")
            if p.is_file() and (suffixes is None or p.suffix in suffixes)
        ]
        try:
            return CommonTools.only(options)
        except LookupError:
            raise MissingResourceError(f"Resource {path} missing") from None

    def json(self, *nodes: Union[Path, str], suffix: Optional[str] = None) -> NestedDotDict:
        """Reads a JSON file under ``resources/``."""
        path = self.path(*nodes, suffix=suffix)
        data = orjson.loads(Path(path).read_text(encoding="utf8"))
        return NestedDotDict(data)

    def json_dict(self, *nodes: Union[Path, str], suffix: Optional[str] = None) -> MutableMapping:
        """Reads a JSON file under ``resources/``."""
        path = self.path(*nodes, suffix=suffix)
        data = orjson.loads(Path(path).read_text(encoding="utf8"))
        return data

    def check_expired(self, path: Path, max_sec: Union[timedelta, int], what: str) -> bool:
        if isinstance(max_sec, timedelta):
            max_sec = max_sec.total_seconds()
        # getting the mod date because creation dates are iffy cross-platform
        # (in fact the Linux kernel doesn't bother to expose them)
        when = datetime.fromtimestamp(path.stat().st_mtime)
        delta_sec = (datetime.now() - when).total_seconds()
        if delta_sec > max_sec:
            delta_str = UnitTools.delta_time_to_str(Chars.narrownbsp)
            if delta_sec > 60 * 60 * 24 * 2:
                self.logger.warning(
                    f"{what} may be {delta_str} out of date. [downloaded: {when.strftime('%Y-%m-%d')}]"
                )
            else:
                self.logger.warning(
                    f"{what} may be {delta_str} out of date. [downloaded: {when.strftime('%Y-%m-%d %H:%M:%s')}]"
                )
            return True
        return False


__all__ = ["MandosResources"]
