import logging
import os
import stat
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Self

logger = logging.getLogger("pocketutils")
COMPRESS_LEVEL = 9


@dataclass(frozen=True, slots=True, kw_only=True)
class PathInfo:
    """
    Info about an extant or nonexistent path as it was at some time.
    Use this to avoid making repeated filesystem calls (e.g. `.is_dir()`):
    None of the properties defined here make OS calls.

    Attributes:
        source: The original path used for lookup; may be a symlink
        resolved: The fully resolved path, or None if it does not exist
        as_of: A datetime immediately before the system calls (system timezone)
        real_stat: `os.stat_result`, or None if the path does not exist
        link_stat: `os.stat_result`, or None if the path is not a symlink
        has_access: Path exists and has the 'a' flag set
        has_read: Path exists and has the 'r' flag set
        has_write: Path exists and has the 'w' flag set

    All the additional properties refer to the resolved path,
    except for :meth:`is_symlink`, :meth:`is_valid_symlink`,
    and :meth:`is_broken_symlink`.
    """

    source: Path
    resolved: Path | None
    as_of: datetime
    real_stat: os.stat_result | None
    link_stat: os.stat_result | None
    has_access: bool
    has_read: bool
    has_write: bool

    @property
    def mod_or_create_dt(self: Self) -> datetime | None:
        """
        Returns the modification or access datetime.
        Uses whichever is available: creation on Windows and modification on Unix-like.
        """
        if os.name == "nt":
            return self._get_dt("st_ctime")
        # will work on posix; on java try anyway
        return self._get_dt("st_mtime")

    @property
    def mod_dt(self: Self) -> datetime | None:
        """
        Returns the modification datetime, if known.
        Returns None on Windows or if the path does not exist.
        """
        if os.name == "nt":
            return None
        return self._get_dt("st_mtime")

    @property
    def create_dt(self: Self) -> datetime | None:
        """
        Returns the creation datetime, if known.
        Returns None on Unix-like systems or if the path does not exist.
        """
        if os.name == "posix":
            return None
        return self._get_dt("st_ctime")

    @property
    def access_dt(self: Self) -> datetime | None:
        """
        Returns the access datetime.
        *Should* never return None if the path exists, but not guaranteed.
        """
        return self._get_dt("st_atime")

    @property
    def exists(self: Self) -> bool:
        """
        Returns whether the resolved path exists.
        """
        return self.real_stat is not None

    @property
    def is_file(self: Self) -> bool:
        return self.exists and stat.S_ISREG(self.real_stat.st_mode)

    @property
    def is_dir(self: Self) -> bool:
        return self.exists and stat.S_ISDIR(self.real_stat.st_mode)

    @property
    def is_readable_dir(self: Self) -> bool:
        return self.is_file and self.has_access and self.has_read

    @property
    def is_writeable_dir(self: Self) -> bool:
        return self.is_dir and self.has_access and self.has_write

    @property
    def is_readable_file(self: Self) -> bool:
        return self.is_file and self.has_access and self.has_read

    @property
    def is_writeable_file(self: Self) -> bool:
        return self.is_file and self.has_access and self.has_write

    @property
    def is_block_device(self: Self) -> bool:
        return self.exists and stat.S_ISBLK(self.real_stat.st_mode)

    @property
    def is_char_device(self: Self) -> bool:
        return self.exists and stat.S_ISCHR(self.real_stat.st_mode)

    @property
    def is_socket(self: Self) -> bool:
        return self.exists and stat.S_ISSOCK(self.real_stat.st_mode)

    @property
    def is_fifo(self: Self) -> bool:
        return self.exists and stat.S_ISFIFO(self.real_stat.st_mode)

    @property
    def is_symlink(self: Self) -> bool:
        return self.link_stat is not None

    @property
    def is_valid_symlink(self: Self) -> bool:
        return self.is_symlink and self.exists

    @property
    def is_broken_symlink(self: Self) -> bool:
        return self.is_symlink and not self.exists

    def _get_dt(self: Self, attr: str) -> datetime | None:
        if self.real_stat is None:
            return None
        sec = getattr(self.real_stat, attr)
        return datetime.fromtimestamp(sec).astimezone()


__all__ = ["PathInfo"]
