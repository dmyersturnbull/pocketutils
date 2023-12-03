# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
"""

"""

import logging
import os
import pathlib
import shutil
import stat
import tempfile
from collections.abc import Generator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePath
from typing import Any, Self, Unpack

from pocketutils.core.exceptions import PathMissingError, ReadFailedError, WriteFailedError
from pocketutils.core.input_output import Writeable

__all__ = ["FilesysUtils", "FilesysTools", "PathInfo"]

logger = logging.getLogger("pocketutils")


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
    except for [`is_symlink`](pocketutils.tools.filesys_tools.PathInfo.is_symlink),
    [`is_valid_symlink`](pocketutils.tools.filesys_tools.PathInfo.is_valid_symlink),
    and [`is_broken_symlink`](pocketutils.tools.filesys_tools.PathInfo.is_broken_symlink).
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


@dataclass(slots=True, frozen=True)
class FilesysUtils:
    """
    Tools for file/directory creation, etc.

    Warning:
        Some functions may be insecure.
    """

    @classmethod
    def verify_can_read_files(
        cls: type[Self],
        *paths: str | Path,
        missing_ok: bool = False,
        attempt: bool = False,
    ) -> None:
        """
        Checks that all files can be written to, to ensure atomicity before operations.

        Args:
            *paths: The files
            missing_ok: Don't raise an error if a path doesn't exist
            attempt: Actually try opening

        Returns:
            ReadFailedError: If a path is not a file (modulo existence) or doesn't have 'W' set
        """
        paths = [Path(p) for p in paths]
        for path in paths:
            if path.exists() and not path.is_file():
                raise ReadFailedError(f"Path {path} is not a file", filename=str(path))
            if (not missing_ok or path.exists()) and not os.access(path, os.R_OK):
                raise ReadFailedError(f"Cannot read from {path}", filename=str(path))
            if attempt:
                try:
                    with open(path):
                        pass
                except OSError:
                    raise WriteFailedError(f"Failed to open {path} for read", filename=str(path))

    @classmethod
    def verify_can_write_files(
        cls: type[Self],
        *paths: str | Path,
        missing_ok: bool = False,
        attempt: bool = False,
    ) -> None:
        """
        Checks that all files can be written to, to ensure atomicity before operations.

        Args:
            *paths: The files
            missing_ok: Don't raise an error if a path doesn't exist
            attempt: Actually try opening

        Returns:
            WriteFailedError: If a path is not a file (modulo existence) or doesn't have 'W' set
        """
        paths = [Path(p) for p in paths]
        for path in paths:
            if path.exists() and not path.is_file():
                raise WriteFailedError(f"Path {path} is not a file", filename=str(path))
            if (not missing_ok or path.exists()) and not os.access(path, os.W_OK):
                raise WriteFailedError(f"Cannot write to {path}", filename=str(path))
            if attempt:
                try:
                    with open(path, "a"):  # or w
                        pass
                except OSError:
                    raise WriteFailedError(f"Failed to open {path} for write", filename=str(path))

    @classmethod
    def verify_can_write_dirs(
        cls: type[Self],
        *paths: str | PurePath,
        missing_ok: bool = False,
    ) -> None:
        """
        Checks that all directories can be written to, to ensure atomicity before operations.

        Args:
            *paths: The directories
            missing_ok: Don't raise an error if a path doesn't exist

        Returns:
            WriteFailedError: If a path is not a directory (modulo existence) or doesn't have 'W' set
        """
        paths = [Path(p) for p in paths]
        for path in paths:
            if path.exists() and not path.is_dir():
                raise WriteFailedError(f"Path {path} is not a dir", filename=str(path))
            if missing_ok and not path.exists():
                continue
            if not os.access(path, os.W_OK):
                raise WriteFailedError(f"{path} lacks write permission", filename=str(path))
            if not os.access(path, os.X_OK):
                raise WriteFailedError(f"{path} lacks access permission", filename=str(path))

    def get_info(self: Self, path: PurePath | str, *, expand_user: bool = False, strict: bool = False) -> PathInfo:
        path = Path(path)
        has_ignore_error = hasattr(pathlib, "_ignore_error")
        if not has_ignore_error:
            logger.debug("No _ignore_error found; some OSErrors may be suppressed")
        resolved = None
        real_stat = None
        has_access = False
        has_read = False
        has_write = False
        link_stat = None
        as_of = datetime.now(tz=UTC).astimezone()
        if has_ignore_error or path.is_symlink() or path.exists():
            link_stat = self.__stat_raw(path)
        if link_stat is not None:
            resolved = path.expanduser().resolve(strict=strict) if expand_user else path.resolve(strict=strict)
            real_stat = self.__stat_raw(resolved) if stat.S_ISLNK(link_stat.st_mode) else link_stat
            has_access = os.access(path, os.X_OK, follow_symlinks=True)
            has_read = os.access(path, os.R_OK, follow_symlinks=True)
            has_write = os.access(path, os.W_OK, follow_symlinks=True)
            if not stat.S_ISLNK(link_stat.st_mode):
                link_stat = None
        return PathInfo(
            source=path,
            resolved=resolved,
            as_of=as_of,
            real_stat=real_stat,
            link_stat=link_stat,
            has_access=has_access,
            has_read=has_read,
            has_write=has_write,
        )

    def prep_dir(self: Self, path: PurePath | str, *, exist_ok: bool = True) -> bool:
        """
        Prepares a directory by making it if it doesn't exist.
        If `exist_ok` is False, calls `logger.warning` if `path` already exists
        """
        path = Path(path)
        exists = path.exists()
        # On some platforms we get generic exceptions like permissions errors,
        # so these are better
        if exists and not path.is_dir():
            raise PathMissingError(filename=str(path))
        if exists and not exist_ok:
            logger.warning(f"Directory {path} already exists")
        if not exists:
            # NOTE! exist_ok in mkdir throws an error on Windows
            path.mkdir(parents=True)
        return exists

    def prep_file(self: Self, path: PurePath | str, *, exist_ok: bool = True) -> None:
        """
        Prepares a file path by making its parent directory.
        Same as `pathlib.Path.mkdir` but makes sure `path` is a file if it exists.
        """
        # On some platforms we get generic exceptions like permissions errors, so these are better
        path = Path(path)
        # check for errors first; don't make the dirs and then fail
        if path.exists() and not path.is_file() and not path.is_symlink():
            raise PathMissingError(filename=str(path))
        Path(path.parent).mkdir(parents=True, exist_ok=exist_ok)

    def delete_surefire(self: Self, path: PurePath | str) -> Exception | None:
        """
        Deletes files or directories cross-platform, but working around multiple issues in Windows.

        Returns:
            None, or an Exception for minor warnings

        Raises:
            IOError: If it can't delete
        """
        # we need this because of Windows
        path = Path(path)
        logger.debug(f"Permanently deleting {path} ...")
        chmod_err = None
        try:
            os.chmod(str(path), stat.S_IRWXU)
        except Exception as e:
            chmod_err = e
        # another reason for returning exception:
        # We don't want to interrupt the current line being printed like in slow_delete
        if path.is_dir():
            shutil.rmtree(str(path), ignore_errors=True)  # ignore_errors because of Windows
            try:
                path.unlink(missing_ok=True)  # again, because of Windows
            except OSError:
                pass  # almost definitely because it doesn't exist
        else:
            path.unlink(missing_ok=True)
        logger.debug(f"Permanently deleted {path}")
        return chmod_err

    def trash(self: Self, path: PurePath | str, trash_dir: PurePath | str) -> None:
        """
        Trash a file or directory.

        Args:
            path: The path to move to the trash
            trash_dir: If None, uses
            [`guess_trash`](pocketutils.tools.path_tools.PathTools.guess_trash).
        """
        logger.debug(f"Trashing {path} to {trash_dir} ...")
        shutil.move(str(path), str(trash_dir))
        logger.debug(f"Trashed {path} to {trash_dir}")

    def try_delete(self: Self, path: Path, *, bound: type[Exception] = PermissionError) -> None:
        """
        Try to delete a file (probably temp file), if it exists, and log any `PermissionError`.
        """
        path = Path(path)
        # noinspection PyBroadException
        try:
            path.unlink(missing_ok=True)
        except bound:
            logger.error(f"Permission error preventing deleting {path}")

    def temp_path(self: Self, path: PurePath | str | None = None, **kwargs) -> Generator[Path, None, None]:
        """
        Makes a temporary Path. Won't create `path` but will delete it at the end.
        If `path` is None, will use `tempfile.mkstemp`.
        """
        if path is None:
            _, path = tempfile.mkstemp()
        try:
            yield Path(path, **kwargs)
        finally:
            Path(path).unlink()

    def temp_file(
        self: Self,
        path: PurePath | str | None = None,
        *,
        spooled: bool = False,
        **kwargs: Unpack[Mapping[str, Any]],
    ) -> Generator[Writeable, None, None]:
        """
        Simple wrapper around `tempfile` functions.
        Wraps `TemporaryFile`, `NamedTemporaryFile`, and `SpooledTemporaryFile`.
        """
        if spooled:
            with tempfile.SpooledTemporaryFile(**kwargs) as x:
                yield x
        elif path is None:
            with tempfile.TemporaryFile(**kwargs) as x:
                yield x
        else:
            with tempfile.NamedTemporaryFile(str(path), **kwargs) as x:
                yield x

    def temp_dir(self: Self, **kwargs: Unpack[Mapping[str, Any]]) -> Generator[Path, None, None]:
        with tempfile.TemporaryDirectory(**kwargs) as x:
            yield Path(x)

    def __stat_raw(self: Self, path: Path) -> os.stat_result | None:
        try:
            return path.lstat()
        except OSError as e:
            if hasattr(pathlib, "_ignore_error") and not pathlib._ignore_error(e):
                raise e
        return None


FilesysTools = FilesysUtils()
