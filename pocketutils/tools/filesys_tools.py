import csv
import gzip
import logging
import os
import pathlib
import shutil
import stat
import sys
import tempfile
from collections.abc import Callable, Generator, Iterable, Mapping, Sequence
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path, PurePath
from typing import Any

import orjson
import regex
from defusedxml import ElementTree

from pocketutils.core.chars import Chars
from pocketutils.core.exceptions import (
    AlreadyUsedError,
    DirDoesNotExistError,
    FileDoesNotExistError,
    ParsingError,
    ReadPermissionsError,
    WritePermissionsError,
)
from pocketutils.core.input_output import OpenMode, PathLike, Writeable
from pocketutils.tools.path_info import PathInfo
from pocketutils.tools.path_tools import PathTools
from pocketutils.tools.sys_tools import SystemTools
from pocketutils.tools.unit_tools import UnitTools

logger = logging.getLogger("pocketutils")


class FilesysTools:
    """
    Tools for file/directory creation, etc.

    .. caution::
        Some functions may be insecure.
    """

    def get_encoding(self, encoding: str = "utf-8") -> str:
        """
        Returns a text encoding from a more flexible string.
        Ignores hyphens and lowercases the string.
        Permits these nonstandard shorthands:

          - ``"platform"``: use ``sys.getdefaultencoding()`` on the fly
          - ``"utf8(bom)"``: use ``"utf-8-sig"`` on Windows; ``"utf-8"`` otherwise
          - ``"utf16(bom)"``: use ``"utf-16-sig"`` on Windows; ``"utf-16"`` otherwise
          - ``"utf32(bom)"``: use ``"utf-32-sig"`` on Windows; ``"utf-32"`` otherwise
        """
        encoding = encoding.lower().replace("-", "")
        if encoding == "platform":
            encoding = sys.getdefaultencoding()
        if encoding == "utf8(bom)":
            encoding = "utf-8-sig" if os.name == "nt" else "utf-8"
        if encoding == "utf16(bom)":
            encoding = "utf-16-sig" if os.name == "nt" else "utf-16"
        if encoding == "utf32(bom)":
            encoding = "utf-32-sig" if os.name == "nt" else "utf-32"
        return encoding

    def get_encoding_errors(self, errors: str | None) -> str | None:
        """
        Returns the value passed as``errors=`` in ``open``.
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
        raise ValueError(f"Invalid value {errors} for errors")

    @classmethod
    def get_info(
        cls, path: PathLike, *, expand_user: bool = False, strict: bool = False
    ) -> PathInfo:
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
        as_of = datetime.now().astimezone()
        if has_ignore_error or path.is_symlink() or path.exists():
            link_stat = cls.__stat_raw(path)
        if link_stat is not None:
            if expand_user:
                resolved = path.expanduser().resolve(strict=strict)
            else:
                resolved = path.resolve(strict=strict)
            if stat.S_ISLNK(link_stat.st_mode):
                real_stat = cls.__stat_raw(resolved)
            else:
                real_stat = link_stat
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

    @classmethod
    def prep_dir(cls, path: PathLike, *, exist_ok: bool = True) -> bool:
        """
        Prepares a directory by making it if it doesn't exist.
        If exist_ok is False, calls ``logger.warning`` if ``path`` already exists
        """
        path = Path(path)
        exists = path.exists()
        # On some platforms we get generic exceptions like permissions errors,
        # so these are better
        if exists and not path.is_dir():
            raise DirDoesNotExistError(f"Path {path} exists but is not a file")
        if exists and not exist_ok:
            logger.warning(f"Directory {path} already exists")
        if not exists:
            # NOTE! exist_ok in mkdir throws an error on Windows
            path.mkdir(parents=True)
        return exists

    @classmethod
    def prep_file(cls, path: PathLike, *, exist_ok: bool = True) -> None:
        """
        Prepares a file path by making its parent directory.
        Same as ``pathlib.Path.mkdir`` but makes sure ``path`` is a file if it exists.
        """
        # On some platforms we get generic exceptions like permissions errors, so these are better
        path = Path(path)
        # check for errors first; don't make the dirs and then fail
        if path.exists() and not path.is_file() and not path.is_symlink():
            raise FileDoesNotExistError(f"Path {path} exists but is not a file")
        Path(path.parent).mkdir(parents=True, exist_ok=exist_ok)

    @classmethod
    def dump_error(cls, e: BaseException | None, path: PathLike | datetime | None = None) -> Path:
        """
        Writes a .json file containing the error message, stack trace, and sys info.
        System info is from :meth:`get_env_info`.
        """
        if path is None:
            path = f"err-dump-{cls.dt_for_filesys(datetime.now().astimezone())}.json"
        elif isinstance(path, datetime):
            path = f"err-dump-{cls.dt_for_filesys(datetime.now().astimezone())}.json"
        path = Path(path)
        data = cls.dump_error_as_dict(e)
        data = orjson.dumps(data, option=orjson.OPT_INDENT_2)
        path.write_bytes(data)
        return path

    @classmethod
    def dump_error_as_dict(cls, e: BaseException | None) -> Mapping[str, Any]:
        try:
            system = SystemTools.get_env_info()
        except BaseException as e2:
            system = f"UNKNOWN << {e2} >>"
        msg, tb = SystemTools.serialize_exception(e)
        tb = [t.as_dict() for t in tb]
        return dict(message=msg, stacktrace=tb, system=system)

    @classmethod
    def dt_for_filesys(cls, dt: datetime, *, timespec: str = "milliseconds") -> str:
        return dt.isoformat(timespec=timespec).replace(":", "")

    @classmethod
    def verify_can_read_files(
        cls,
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
            ReadPermissionsError: If a path is not a file (modulo existence) or doesn't have 'W' set
        """
        paths = [Path(p) for p in paths]
        for path in paths:
            if path.exists() and not path.is_file():
                raise ReadPermissionsError(f"Path {path} is not a file", path=path)
            if (not missing_ok or path.exists()) and not os.access(path, os.R_OK):
                raise ReadPermissionsError(f"Cannot read from {path}", path=path)
            if attempt:
                try:
                    with open(path):
                        pass
                except OSError:
                    raise WritePermissionsError(f"Failed to open {path} for read", key=str(path))

    @classmethod
    def verify_can_write_files(
        cls,
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
            WritePermissionsError: If a path is not a file (modulo existence) or doesn't have 'W' set
        """
        paths = [Path(p) for p in paths]
        for path in paths:
            if path.exists() and not path.is_file():
                raise WritePermissionsError(f"Path {path} is not a file", path=path)
            if (not missing_ok or path.exists()) and not os.access(path, os.W_OK):
                raise WritePermissionsError(f"Cannot write to {path}", path=path)
            if attempt:
                try:
                    with open(path, "a"):  # or w
                        pass
                except OSError:
                    raise WritePermissionsError(f"Failed to open {path} for write", path=path)

    @classmethod
    def verify_can_write_dirs(cls, *paths: str | Path, missing_ok: bool = False) -> None:
        """
        Checks that all directories can be written to, to ensure atomicity before operations.

        Args:
            *paths: The directories
            missing_ok: Don't raise an error if a path doesn't exist

        Returns:
            WritePermissionsError: If a path is not a directory (modulo existence) or doesn't have 'W' set
        """
        paths = [Path(p) for p in paths]
        for path in paths:
            if path.exists() and not path.is_dir():
                raise WritePermissionsError(f"Path {path} is not a dir", path=(path))
            if missing_ok and not path.exists():
                continue
            if not os.access(path, os.W_OK):
                raise WritePermissionsError(f"{path} lacks write permission", path=path)
            if not os.access(path, os.X_OK):
                raise WritePermissionsError(f"{path} lacks access permission", path=path)

    @classmethod
    def delete_surefire(cls, path: PathLike) -> Exception | None:
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

    @classmethod
    def trash(cls, path: PathLike, trash_dir: PathLike | None = None) -> None:
        """
        Trash a file or directory.

        Args:
            path: The path to move to the trash
            trash_dir: If None, uses :meth:`pocketutils.tools.path_tools.PathTools.guess_trash`
        """
        if trash_dir is None:
            trash_dir = PathTools.guess_trash()
        logger.debug(f"Trashing {path} to {trash_dir} ...")
        shutil.move(str(path), str(trash_dir))
        logger.debug(f"Trashed {path} to {trash_dir}")

    @classmethod
    def try_cleanup(cls, path: Path, *, bound: type[Exception] = PermissionError) -> None:
        """
        Try to delete a file (probably temp file), if it exists, and log any ``PermissionError``.
        """
        path = Path(path)
        # noinspection PyBroadException
        try:
            path.unlink(missing_ok=True)
        except bound:
            logger.error(f"Permission error preventing deleting {path}")

    @classmethod
    def read_any(
        cls, path: PathLike
    ) -> (
        str
        | bytes
        | Sequence[str]
        | Sequence[int]
        | Sequence[float]
        | Sequence[str]
        | Mapping[str, str]
    ):
        """
        Reads a variety of simple formats based on filename extension.
        Includes '.txt', 'csv', .xml', '.properties', '.json'.
        Also reads '.data' (binary), '.lines' (text lines).
        And formatted lists: '.strings', '.floats', and '.ints' (ex: "[1, 2, 3]").
        """
        path = Path(path)
        ext = path.suffix.lstrip(".")

        def load_list(dtype):
            return [
                dtype(s)
                for s in FilesysTools.read_lines_file(path)[0]
                .replace(" ", "")
                .replace("[", "")
                .replace("]", "")
                .split(",")
            ]

        if ext == "lines":
            return cls.read_lines_file(path)
        elif ext == "txt":
            return path.read_text(encoding="utf-8")
        elif ext == "bytes":
            return path.read_bytes()
        elif ext == "json":
            return cls.load_json(path)
        elif ext == "properties":
            return cls.read_properties_file(path)
        elif ext == "csv":
            with path.open(encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return list(reader)
        elif ext == "ints":
            return load_list(int)
        elif ext == "floats":
            return load_list(float)
        elif ext == "strings":
            return load_list(str)
        elif ext == "xml":
            ElementTree.parse(path).getroot()
        else:
            raise TypeError(f"Did not recognize resource file type for file {path}")

    @classmethod
    @contextmanager
    def open_file(cls, path: PathLike, mode: OpenMode | str, *, mkdir: bool = False):
        """
        Opens a text file, always using utf-8, optionally gzipped.

        See Also:
            :class:`pocketutils.core.input_output.OpenMode`
        """
        path = Path(path)
        mode = OpenMode(mode)
        if mode.write and mkdir:
            path.parent.mkdir(exist_ok=True, parents=True)
        if not mode.read:
            cls.prep_file(path, exist_ok=mode.overwrite or mode.append)
        if path.suffix == ".gz" or path.suffix == ".gzip":
            yield gzip.open(path, mode, encoding="utf-8")
        elif mode.binary:
            yield open(path, mode, encoding="utf-8")
        else:
            yield open(path, mode, encoding="utf-8")

    @classmethod
    def write_lines(cls, iterable: Iterable[Any], path: PathLike, mode: str = "w") -> int:
        r"""
        Just writes an iterable line-by-line to a file, using '\n'.

        Makes the parent directory if needed.
        Checks that the iterable is a "true iterable" (not a string or bytes).

        Returns:
            The number of lines written (the same as len(iterable) if iterable has a length)

        Raises:
            FileExistsError: If the path exists and append is False
            PathIsNotFileError: If append is True, and the path exists but is not a file
        """
        n = 0
        with cls.open_file(path, mode) as f:
            for x in iterable:
                f.write(str(x) + "\n")
            n += 1
        return n

    @classmethod
    def replace_in_file(cls, path: PathLike, changes: Mapping[str, str]) -> None:
        """
        Uses ``regex.sub`` repeatedly to modify (AND REPLACE) a file's content.
        """
        path = Path(path)
        data = path.read_text(encoding="utf-8")
        for key, value in changes.items():
            data = regex.sub(key, value, data, flags=regex.V1 | regex.MULTILINE | regex.DOTALL)
        path.write_text(data, encoding="utf-8")

    @classmethod
    def tmp_path(cls, path: PathLike | None = None, **kwargs) -> Generator[Path, None, None]:
        """
        Makes a temporary Path. Won't create ``path`` but will delete it at the end.
        If ``path`` is None, will use ``tempfile.mkstemp``.
        """
        if path is None:
            _, path = tempfile.mkstemp()
        try:
            yield Path(path, **kwargs)
        finally:
            Path(path).unlink()

    @classmethod
    def tmp_file(
        cls, path: PathLike | None = None, *, spooled: bool = False, **kwargs
    ) -> Generator[Writeable, None, None]:
        """
        Simple wrapper around tempfile functions.
        Wraps ``TemporaryFile``, ``NamedTemporaryFile``, and ``SpooledTemporaryFile``.
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

    @classmethod
    def tmp_dir(cls, **kwargs) -> Generator[Path, None, None]:
        with tempfile.TemporaryDirectory(**kwargs) as x:
            yield Path(x)

    @classmethod
    def check_expired(
        cls,
        path: PathLike,
        max_sec: timedelta | float,
        *,
        parent: PathLike | None = None,
        warn_expired_fmt: str = "{path_rel} is {delta} out of date [{mod_rel}]",
        warn_unknown_fmt: str = "{path_rel} mod date is unknown [created: {create_rel}]",
        log: Callable[[str], Any] | None = logger.warning,
    ) -> bool | None:
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
            parent: If provided, path_rel is relative to this directory (to simplify warnings)
            warn_expired_fmt: Formatting string in terms of the variables listed above
            warn_unknown_fmt: Formatting string in terms of the variables listed above
            log: Log about problems

        Returns:
            Whether it is expired, or None if it could not be determined
        """
        path = Path(path)
        if log is None:

            def log(_):
                return None

        limit = max_sec if isinstance(max_sec, timedelta) else timedelta(seconds=max_sec)
        now = datetime.now().astimezone()
        info = FilesysTools.get_info(path)
        if info.mod_dt and now - info.mod_dt > limit:
            cls._warn_expired(now, info.mod_dt, info.create_dt, path, parent, warn_expired_fmt, log)
            return True
        elif not info.mod_dt and (not info.create_dt or (now - info.create_dt) > limit):
            cls._warn_expired(now, info.mod_dt, info.create_dt, path, parent, warn_unknown_fmt, log)
            return None
        return False

    @classmethod
    def _warn_expired(
        cls,
        now: datetime,
        mod: datetime | None,
        created: datetime | None,
        path: Path,
        parent: Path | None,
        fmt: str | None,
        log: Callable[[str], Any],
    ):
        if isinstance(fmt, str):
            fmt = fmt.format
        if parent is not None and path.is_relative_to(parent):
            path_rel = str(path.relative_to(parent))
        else:
            path_rel = str(path)
        now_str, mod_str, mod_rel, mod_delta, mod_delta_sec = cls._expire_warning_info(now, mod)
        _, create_str, create_rel, create_delta, create_delta_sec = cls._expire_warning_info(
            now, created
        )
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
        log(msg)

    @classmethod
    def _expire_warning_info(
        cls, now: datetime, then: datetime | None
    ) -> tuple[str, str, str, str, str]:
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        if then is None:
            return now_str, "", "", "", ""
        delta = now - then
        then_str = then.strftime("%Y-%m-%d %H:%M:%S")
        then_rel = UnitTools.approx_time_wrt(now, then)
        delta_str = UnitTools.delta_time_to_str(delta, space=Chars.narrownbsp)
        return now_str, then_str, then_rel, delta_str, str(delta.total_seconds())

    @classmethod
    def __stat_raw(cls, path: Path) -> os.stat_result | None:
        try:
            return path.lstat()
        except OSError as e:
            if hasattr(pathlib, "_ignore_error") and not pathlib._ignore_error(e):
                raise
        return None


__all__ = ["FilesysTools", "PathInfo"]
