import gzip
import hashlib
import importlib.metadata
import locale
import logging
import os
import pathlib
import platform
import shutil
import socket
import stat
import struct
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from getpass import getuser
from pathlib import Path, PurePath
from typing import (
    Any,
    Generator,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    SupportsBytes,
    Type,
    Union,
    Tuple,
    Callable,
)

import numpy as np
import orjson
import pandas as pd
import regex
from defusedxml import ElementTree
from pocketutils.core.chars import Chars

from pocketutils.tools.unit_tools import UnitTools

from pocketutils.core.exceptions import (
    AlreadyUsedError,
    ContradictoryRequestError,
    DirDoesNotExistError,
    FileDoesNotExistError,
    ParsingError,
)
from pocketutils.core._internal import read_txt_or_gz, write_txt_or_gz
from pocketutils.core.input_output import OpenMode, PathLike, Writeable
from pocketutils.core.web_resource import *
from pocketutils.tools.base_tools import BaseTools
from pocketutils.tools.path_tools import PathTools

logger = logging.getLogger("pocketutils")
COMPRESS_LEVEL = 9


@dataclass(frozen=True, repr=True)
class PathInfo:
    """
    Info about an extant or nonexistent path as it was at some time.
    Use this to avoid making repeated filesystem calls (e.g. ``.is_dir()``):
    None of the properties defined here make OS calls.

    Attributes:
        source: The original path used for lookup; may be a symlink
        resolved: The fully resolved path, or None if it does not exist
        as_of: A datetime immediately before the system calls (system timezone)
        real_stat: ``os.stat_result``, or None if the path does not exist
        link_stat: ``os.stat_result``, or None if the path is not a symlink
        has_access: Path exists and has the 'a' flag set
        has_read: Path exists and has the 'r' flag set
        has_write: Path exists and has the 'w' flag set

    All of the additional properties refer to the resolved path,
    except for :meth:`is_symlink`, :meth:`is_valid_symlink`,
    and :meth:`is_broken_symlink`.
    """

    source: Path
    resolved: Optional[Path]
    as_of: datetime
    real_stat: Optional[os.stat_result]
    link_stat: Optional[os.stat_result]
    has_access: bool
    has_read: bool
    has_write: bool

    @property
    def mod_or_create_dt(self) -> Optional[datetime]:
        """
        Returns the modification or access datetime.
        Uses whichever is available: creation on Windows and modification on Unix-like.
        """
        if os.name == "nt":
            return self._get_dt("st_ctime")
        # will work on posix; on java try anyway
        return self._get_dt("st_mtime")

    @property
    def mod_dt(self) -> Optional[datetime]:
        """
        Returns the modification datetime, if known.
        Returns None on Windows or if the path does not exist.
        """
        if os.name == "nt":
            return None
        return self._get_dt("st_mtime")

    @property
    def create_dt(self) -> Optional[datetime]:
        """
        Returns the creation datetime, if known.
        Returns None on Unix-like systems or if the path does not exist.
        """
        if os.name == "posix":
            return None
        return self._get_dt("st_ctime")

    @property
    def access_dt(self) -> Optional[datetime]:
        """
        Returns the access datetime.
        *Should* never return None if the path exists, but not guaranteed.
        """
        return self._get_dt("st_atime")

    @property
    def exists(self) -> bool:
        """
        Returns whether the resolved path exists.
        """
        return self.real_stat is not None

    @property
    def is_file(self) -> bool:
        return self.exists and stat.S_ISREG(self.real_stat.st_mode)

    @property
    def is_dir(self) -> bool:
        return self.exists and stat.S_ISDIR(self.real_stat.st_mode)

    @property
    def is_readable_dir(self) -> bool:
        return self.is_file and self.has_access and self.has_read

    @property
    def is_writeable_dir(self) -> bool:
        return self.is_dir and self.has_access and self.has_write

    @property
    def is_readable_file(self) -> bool:
        return self.is_file and self.has_access and self.has_read

    @property
    def is_writeable_file(self) -> bool:
        return self.is_file and self.has_access and self.has_write

    @property
    def is_block_device(self) -> bool:
        return self.exists and stat.S_ISBLK(self.real_stat.st_mode)

    @property
    def is_char_device(self) -> bool:
        return self.exists and stat.S_ISCHR(self.real_stat.st_mode)

    @property
    def is_socket(self) -> bool:
        return self.exists and stat.S_ISSOCK(self.real_stat.st_mode)

    @property
    def is_fifo(self) -> bool:
        return self.exists and stat.S_ISFIFO(self.real_stat.st_mode)

    @property
    def is_symlink(self) -> bool:
        return self.link_stat is not None

    @property
    def is_valid_symlink(self) -> bool:
        return self.is_symlink and self.exists

    @property
    def is_broken_symlink(self) -> bool:
        return self.is_symlink and not self.exists

    def _get_dt(self, attr: str) -> Optional[datetime]:
        if self.real_stat is None:
            return None
        sec = getattr(self.real_stat, attr)
        return datetime.fromtimestamp(sec).astimezone()


class FilesysTools(BaseTools):
    """
    Tools for file/directory creation, etc.

    .. caution::
        Some functions may be insecure.
    """

    @classmethod
    def read_compressed_text(cls, path: PathLike) -> str:
        """
        Reads text from a text file, optionally gzipped or bz2-ed.
        Recognized suffixes for compression are ``.gz``, ``.gzip``, ``.bz2``, and ``.bzip2``.
        """
        return read_txt_or_gz(path)

    @classmethod
    def write_compressed_text(cls, txt: str, path: PathLike, *, mkdirs: bool = False) -> None:
        """
        Writes text to a text file, optionally gzipped or bz2-ed.
        Recognized suffixes for compression are ``.gz``, ``.gzip``, ``.bz2``, and ``.bzip2``.
        """
        write_txt_or_gz(txt, path, mkdirs=mkdirs)

    @classmethod
    def new_webresource(
        cls, url: str, archive_member: Optional[str], local_path: PathLike
    ) -> WebResource:
        return WebResource(url, archive_member, local_path)

    @classmethod
    def is_linux(cls) -> bool:
        return sys.platform == "linux"

    @classmethod
    def is_windows(cls) -> bool:
        return sys.platform == "win32"

    @classmethod
    def is_macos(cls) -> bool:
        return sys.platform == "darwin"

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
        If exist_ok is False, calls logger.warning it already exists
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
    def get_env_info(cls, *, include_insecure: bool = False) -> Mapping[str, str]:
        """
        Get a dictionary of some system and environment information.
        Includes os_release, hostname, username, mem + disk, shell, etc.

        Args:
            include_insecure: Include data like hostname and username

        .. caution ::
            Even with ``include_insecure=False``, avoid exposing this data to untrusted
            sources. For example, this includes the specific OS release, which could
            be used in attack.
        """
        try:
            import psutil
        except ImportError:
            psutil = None
            logger.warning("psutil is not installed, so cannot get extended env info")

        now = datetime.now(timezone.utc).astimezone().isoformat()
        uname = platform.uname()
        language_code, encoding = locale.getlocale()
        # build up this dict:
        data = {}

        def _try(os_fn, k: str, *args):
            if any((a is None for a in args)):
                return None
            try:
                v = os_fn(*args)
                data[k] = v
                return v
            except (OSError, ImportError):
                return None

        data.update(
            dict(
                platform=platform.platform(),
                python=".".join(str(i) for i in sys.version_info),
                os=uname.system,
                os_release=uname.release,
                os_version=uname.version,
                machine=uname.machine,
                byte_order=sys.byteorder,
                processor=uname.processor,
                build=sys.version,
                python_bits=8 * struct.calcsize("P"),
                environment_info_capture_datetime=now,
                encoding=encoding,
                locale=locale,
                recursion_limit=sys.getrecursionlimit(),
                float_info=sys.float_info,
                int_info=sys.int_info,
                flags=sys.flags,
                hash_info=sys.hash_info,
                implementation=sys.implementation,
                switch_interval=sys.getswitchinterval(),
                filesystem_encoding=sys.getfilesystemencoding(),
            )
        )
        if "LANG" in os.environ:
            data["lang"] = os.environ["LANG"]
        if "SHELL" in os.environ:
            data["shell"] = os.environ["SHELL"]
        if "LC_ALL" in os.environ:
            data["lc_all"] = os.environ["LC_ALL"]
        if hasattr(sys, "winver"):
            data["win_ver"] = sys.getwindowsversion()
        if hasattr(sys, "mac_ver"):
            data["mac_ver"] = sys.mac_ver()
        if hasattr(sys, "linux_distribution"):
            data["linux_distribution"] = sys.linux_distribution()
        if include_insecure:
            _try(getuser, "username")
            _try(os.getlogin, "login")
            _try(socket.gethostname, "hostname")
            _try(os.getcwd, "cwd")
            pid = _try(os.getpid, "pid")
            ppid = _try(os.getppid, "parent_pid")
            if hasattr(os, "getpriority"):
                _try(os.getpriority, "priority", os.PRIO_PROCESS, pid)
                _try(os.getpriority, "parent_priority", os.PRIO_PROCESS, ppid)
        if psutil is not None:
            data.update(
                dict(
                    disk_used=psutil.disk_usage(".").used,
                    disk_free=psutil.disk_usage(".").free,
                    memory_used=psutil.virtual_memory().used,
                    memory_available=psutil.virtual_memory().available,
                )
            )
        return {k: str(v) for k, v in dict(data).items()}

    @classmethod
    def list_package_versions(cls) -> Mapping[str, str]:
        """
        Returns installed packages and their version numbers.
        Reliable; uses importlib (Python 3.8+).
        """
        # calling .metadata reads the metadata file
        # and .version is an alias to .metadata["version"]
        # so make sure to only read once
        # TODO: get installed extras?
        dct = {}
        for d in importlib.metadata.distributions():
            meta = d.metadata
            dct[meta["name"]] = meta["version"]
        return dct

    @classmethod
    def delete_surefire(cls, path: PathLike) -> Optional[Exception]:
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
            except IOError:
                pass  # almost definitely because it doesn't exist
        else:
            path.unlink(missing_ok=True)
        logger.debug(f"Permanently deleted {path}")
        return chmod_err

    @classmethod
    def trash(cls, path: PathLike, trash_dir: Optional[PathLike] = None) -> None:
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
    def try_cleanup(cls, path: Path, *, bound: Type[Exception] = PermissionError) -> None:
        """
        Try to delete a file (probably temp file), if it exists, and log any PermissionError.
        """
        path = Path(path)
        # noinspection PyBroadException
        try:
            path.unlink(missing_ok=True)
        except bound:
            logger.error(f"Permission error preventing deleting {path}")

    @classmethod
    def read_lines_file(cls, path: PathLike, *, ignore_comments: bool = False) -> Sequence[str]:
        """
        Returns a list of lines in the file.
        Optionally skips lines starting with '#' or that only contain whitespace.
        """
        lines = []
        with cls.open_file(path, "r") as f:
            for line in f.readlines():
                line = line.strip()
                if not ignore_comments or not line.startswith("#") and not len(line.strip()) == 0:
                    lines.append(line)
        return lines

    @classmethod
    def read_properties_file(cls, path: PathLike) -> Mapping[str, str]:
        """
        Reads a .properties file.
        A list of lines with key=value pairs (with an equals sign).
        Lines beginning with # are ignored.
        Each line must contain exactly 1 equals sign.

        .. caution::
            The escaping is not compliant with the standard

        Args:
            path: Read the file at this local path

        Returns:
            A dict mapping keys to values, both with surrounding whitespace stripped
        """
        dct = {}
        with cls.open_file(path, "r") as f:
            for i, line in enumerate(f.readlines()):
                line = line.strip()
                if len(line) == 0 or line.startswith("#"):
                    continue
                if line.count("=") != 1:
                    raise ParsingError(f"Bad line {i} in {path}", resource=path)
                k, v = line.split("=")
                k, v = k.strip(), v.strip()
                if k in dct:
                    raise AlreadyUsedError(f"Duplicate property {k} (line {i})", key=k)
                dct[k] = v
        return dct

    @classmethod
    def write_properties_file(
        cls, properties: Mapping[Any, Any], path: Union[str, PurePath], mode: str = "o"
    ) -> None:
        """
        Writes a .properties file.

        .. caution::
            The escaping is not compliant with the standard
        """
        if not OpenMode(mode).write:
            raise ContradictoryRequestError(f"Cannot write text to {path} in mode {mode}")
        with FilesysTools.open_file(path, mode) as f:
            bads = []
            for k, v in properties.items():
                if "=" in k or "=" in v or "\n" in k or "\n" in v:
                    bads.append(k)
                f.write(
                    str(k).replace("=", "--").replace("\n", "\\n")
                    + "="
                    + str(v).replace("=", "--").replace("\n", "\\n")
                    + "\n"
                )
            if 0 < len(bads) <= 10:
                logger.warning(
                    "At least one properties entry contains an equals sign or newline (\\n)."
                    f"These were escaped: {', '.join(bads)}"
                )
            elif len(bads) > 0:
                logger.warning(
                    "At least one properties entry contains an equals sign or newline (\\n),"
                    "which were escaped."
                )

    @classmethod
    def save_json(cls, data: Any, path: PathLike, mode: str = "w") -> None:
        with cls.open_file(path, mode) as f:
            f.write(orjson.dumps(data).decode(encoding="utf8"))

    @classmethod
    def load_json(cls, path: PathLike) -> Union[dict, list]:
        return orjson.loads(Path(path).read_text(encoding="utf8"))

    @classmethod
    def read_any(
        cls, path: PathLike
    ) -> Union[
        str,
        bytes,
        Sequence[str],
        pd.DataFrame,
        Sequence[int],
        Sequence[float],
        Sequence[str],
        Mapping[str, str],
    ]:
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
        elif ext == "data":
            return path.read_bytes()
        elif ext == "json":
            return cls.load_json(path)
        elif ext in ["npy", "npz"]:
            return np.load(str(path), allow_pickle=False, encoding="utf8")
        elif ext == "properties":
            return cls.read_properties_file(path)
        elif ext == "csv":
            return pd.read_csv(path, encoding="utf8")
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
    def open_file(cls, path: PathLike, mode: Union[OpenMode, str], *, mkdir: bool = False):
        """
        Opens a text file, always using utf8, optionally gzipped.

        See Also:
            :class:`pocketutils.core.input_output.OpenMode`
        """
        path = Path(path)
        mode = OpenMode(mode)
        if mode.write and mkdir:
            path.parent.mkdir(exist_ok=True, parents=True)
        if not mode.read:
            cls.prep_file(path, exist_ok=mode.overwrite or mode.append)
        if mode.gzipped:
            yield gzip.open(path, mode.internal, compresslevel=COMPRESS_LEVEL, encoding="utf8")
        elif mode.binary:
            yield open(path, mode.internal, encoding="utf8")
        else:
            yield open(path, mode.internal, encoding="utf8")

    @classmethod
    def write_lines(cls, iterable: Iterable[Any], path: PathLike, mode: str = "w") -> int:
        """
        Just writes an iterable line-by-line to a file, using '\n'.
        Makes the parent directory if needed.
        Checks that the iterable is a "true iterable" (not a string or bytes).

        Returns:
            The number of lines written (the same as len(iterable) if iterable has a length)

        Raises:
            FileExistsError: If the path exists and append is False
            PathIsNotFileError: If append is True, and the path exists but is not a file
        """
        if not cls.is_true_iterable(iterable):
            raise TypeError("Not a true iterable")  # TODO include iterable if small
        n = 0
        with cls.open_file(path, mode) as f:
            for x in iterable:
                f.write(str(x) + "\n")
            n += 1
        return n

    @classmethod
    def hash_hex(cls, x: SupportsBytes, algorithm: str) -> str:
        """
        Returns the hex-encoded hash of the object (converted to bytes).
        """
        m = hashlib.new(algorithm)
        m.update(bytes(x))
        return m.hexdigest()

    @classmethod
    def replace_in_file(cls, path: PathLike, changes: Mapping[str, str]) -> None:
        """
        Uses re.sub repeatedly to modify (AND REPLACE) a file's content.
        """
        path = Path(path)
        data = path.read_text(encoding="utf-8")
        for key, value in changes.items():
            data = regex.sub(key, value, data, flags=regex.V1 | regex.MULTILINE | regex.DOTALL)
        path.write_text(data, encoding="utf-8")

    @classmethod
    def tmppath(cls, path: Optional[PathLike] = None, **kwargs) -> Generator[Path, None, None]:
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
    def tmpfile(
        cls, path: Optional[PathLike] = None, *, spooled: bool = False, **kwargs
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
    def tmpdir(cls, **kwargs) -> Generator[Path, None, None]:
        with tempfile.TemporaryDirectory(**kwargs) as x:
            yield Path(x)

    @classmethod
    def check_expired(
        cls,
        path: PathLike,
        max_sec: Union[timedelta, float],
        *,
        parent: Optional[PathLike] = None,
        warn_expired_fmt: str = "{path_rel} is {delta} out of date [{mod_rel}]",
        warn_unknown_fmt: str = "{path_rel} mod date is unknown [created: {create_rel}]",
        log: Optional[Callable[[str], Any]] = logger.warning,
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
            parent: If provided, path_rel is relative to this directory (to simplify warnings)
            warn_expired_fmt: Formatting string in terms of the variables listed above
            warn_unknown_fmt: Formatting string in terms of the variables listed above
            log: Log about problems

        Returns:
            Whether it is expired, or None if it could not be determined
        """
        path = Path(path)
        if log is None:
            log = lambda _: None
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
        mod: Optional[datetime],
        created: Optional[datetime],
        path: Path,
        parent: Optional[Path],
        fmt: Optional[str],
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
        cls, now: datetime, then: Optional[datetime]
    ) -> Tuple[str, str, str, str, str]:
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        if then is None:
            return now_str, "", "", "", ""
        delta = now - then
        then_str = then.strftime("%Y-%m-%d %H:%M:%S")
        then_rel = UnitTools.approx_time_wrt(now, then)
        delta_str = UnitTools.delta_time_to_str(delta, space=Chars.narrownbsp)
        return now_str, then_str, then_rel, delta_str, str(delta.total_seconds())

    @classmethod
    def __stat_raw(cls, path: Path) -> Optional[os.stat_result]:
        try:
            return path.lstat()
        except OSError as e:
            if hasattr(pathlib, "_ignore_error") and not pathlib._ignore_error(e):
                raise
        return None


__all__ = ["FilesysTools", "PathInfo"]
