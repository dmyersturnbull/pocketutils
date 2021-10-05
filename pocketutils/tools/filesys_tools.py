import gzip
import hashlib
import json
import logging
import os
import platform
import shutil
import socket
import stat
import sys
import tempfile
import warnings
from contextlib import contextmanager
from datetime import datetime, timezone
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
)

import numpy as np
import pandas as pd
import regex

from pocketutils.core import JsonEncoder
from pocketutils.core.exceptions import (
    AlreadyUsedError,
    ContradictoryRequestError,
    FileDoesNotExistError,
    ParsingError,
)
from pocketutils.core.hashers import *
from pocketutils.core.input_output import OpenMode, PathLike, Writeable
from pocketutils.core.web_resource import *
from pocketutils.tools.base_tools import BaseTools
from pocketutils.tools.path_tools import PathTools

logger = logging.getLogger("pocketutils")
COMPRESS_LEVEL = 9
ENCODING = "utf8"

try:
    import dill
except ImportError:
    dill = None
    logger.debug("Could not import dill", exc_info=True)

try:
    import jsonpickle
    import jsonpickle.ext.numpy as jsonpickle_numpy

    jsonpickle_numpy.register_handlers()
    import jsonpickle.ext.pandas as jsonpickle_pandas

    jsonpickle_pandas.register_handlers()
except ImportError:
    # zero them all out
    jsonpickle, jsonpickle_numpy, jsonpickle_pandas = None, None, None
    logger.debug("Could not import jsonpickle", exc_info=True)


try:
    from defusedxml import ElementTree
except ImportError:
    logger.warning("Could not import defusedxml; falling back to xml")
    from xml.etree import ElementTree


class FilesysTools(BaseTools):
    """
    Tools for file/directory creation, etc.

    Security concerns
    -----------------

    Please note that several of these functions expose security concerns.
    In particular, ``pkl``, ``unpkl``, and any others that involve pickle or its derivatives.
    """

    @classmethod
    def pkl(cls, stuff: Any, path: PathLike) -> None:
        """Save to a file with dill."""
        warnings.warn("pkl will be removed", DeprecationWarning)
        data = dill.dumps(stuff, protocol=5)  # nosec
        Path(path).write_bytes(data)

    @classmethod
    def unpkl(cls, path: PathLike):
        """Load a file with dill."""
        warnings.warn("unpkl will be removed", DeprecationWarning)
        # ignore encoding param, which is only useful for unpickling Python 2-generated
        data = Path(path).read_bytes()
        return dill.loads(data)  # nosec

    @classmethod
    def new_hasher(cls, algorithm: str = "sha1") -> Hasher:
        return Hasher(algorithm)

    @classmethod
    def new_webresource(
        cls, url: str, archive_member: Optional[str], local_path: PathLike
    ) -> WebResource:
        return WebResource(url, archive_member, local_path)

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

        now = datetime.now(timezone.utc).astimezone().isoformat()
        data = {}

        def _try(os_fn, k: str, *args):
            if any((a is None for a in args)):
                return None
            try:
                v = os_fn(*args)
                data[k] = v
                return v
            except OSError:
                return None

        data.update(
            dict(
                os_release=platform.platform(),
                python_version=sys.version,
                environment_info_capture_datetime=now,
            )
        )
        if "SHELL" in os.environ:
            data["shell"] = os.environ["SHELL"]
        if include_insecure:
            data.update(
                dict(
                    hostname=socket.gethostname(),
                    username=getuser(),
                    cwd=os.getcwd(),
                    login=os.getlogin(),
                )
            )
            pid = _try(os.getpid, "pid")
            ppid = _try(os.getppid, "parent_pid", pid)
            _try(os.getpriority, "priority", os.PRIO_PROCESS, pid)
            _try(os.getpriority, "parent_priority", os.PRIO_PROCESS, ppid)
        try:
            import psutil
        except ImportError:
            psutil = None
            logger.warning("psutil is not installed, so cannot get extended env info")
        if psutil is not None:
            data.update(
                dict(
                    disk_used=psutil.disk_usage(".").used,
                    disk_free=psutil.disk_usage(".").free,
                    memory_used=psutil.virtual_memory().used,
                    memory_available=psutil.virtual_memory().available,
                )
            )
        return data

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
    def read_lines_file(cls, path: PathLike, ignore_comments: bool = False) -> Sequence[str]:
        """
        Returns a list of lines in the file.
        Optionally skips lines starting with '#' or that only contain whitespace.
        """
        warnings.warn(
            "read_lines_file will be removed; use typeddfs's read_lines instead", DeprecationWarning
        )
        lines = []
        with FilesysTools.open_file(path, "r") as f:
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

        Args:
            path: Read the file at this local path

        Returns:
            A dict mapping keys to values, both with surrounding whitespace stripped
        """
        warnings.warn(
            "read_properties_file will be removed; use typeddfs's read_properties instead",
            DeprecationWarning,
        )
        dct = {}
        with FilesysTools.open_file(path, "r") as f:
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
    ):
        warnings.warn(
            "write_properties_file will be removed; use typeddfs's write_properties instead",
            DeprecationWarning,
        )
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
    def make_dirs(cls, s: PathLike) -> None:
        """
        Make a directory (ok if exists, will make parents).
        Avoids a bug on Windows where the path '' breaks. Just doesn't make the path '' (assumes it means '.').
        """
        warnings.warn("make_dirs will be removed; the upstream bug was fixed", DeprecationWarning)
        # '' can break on Windows
        if str(s) != "":
            Path(s).mkdir(exist_ok=True, parents=True)

    @classmethod
    def save_json(cls, data: Any, path: PathLike, mode: str = "w") -> None:
        warnings.warn("save_json will be removed; use orjson instead", DeprecationWarning)
        with cls.open_file(path, mode) as f:
            json.dump(data, f, ensure_ascii=False, cls=JsonEncoder)

    @classmethod
    def load_json(cls, path: PathLike):
        warnings.warn("save_json will be removed; use orjson instead", DeprecationWarning)
        return json.loads(Path(path).read_text(encoding="utf8"))

    @classmethod
    def save_jsonpkl(cls, data, path: PathLike, mode: str = "w") -> None:
        warnings.warn("save_jsonpickle will be removed; wrap orjson instead", DeprecationWarning)
        if jsonpickle is None:
            raise ImportError("No jsonpickle")
        FilesysTools.write_text(jsonpickle.encode(data), path, mode=mode)

    @classmethod
    def load_jsonpkl(cls, path: PathLike) -> dict:
        warnings.warn("load_jsonpkl will be removed; wrap orjson instead", DeprecationWarning)
        if jsonpickle is None:
            raise ImportError("No jsonpickle")
        return jsonpickle.decode(FilesysTools.read_text(path))

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
        Reads a variety of simple formats based on filename extension, including '.txt', 'csv', .xml', '.properties', '.json'.
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
            return FilesysTools.read_lines_file(path)
        elif ext == "txt":
            return path.read_text("utf-8")
        elif ext == "data":
            return path.read_bytes()
        elif ext == "json":
            return FilesysTools.load_json(path)
        elif ext == "pkl":
            return FilesysTools.unpkl(path)
        elif ext in ["npy", "npz"]:
            return np.load(str(path), allow_pickle=True)
        elif ext == "properties":
            return FilesysTools.read_properties_file(path)
        elif ext == "csv":
            return pd.read_csv(path)
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
    def read_bytes(cls, path: PathLike) -> bytes:
        warnings.warn("read_bytes will be removed; use pathlib instead", DeprecationWarning)
        return Path(path).read_bytes()

    @classmethod
    def read_text(cls, path: PathLike) -> str:
        warnings.warn("read_text will be removed; use pathlib instead", DeprecationWarning)
        return Path(path).read_text(encoding="utf-8")

    @classmethod
    def write_bytes(cls, data: Any, path: PathLike, mode: str = "wb") -> None:
        warnings.warn("write_bytes will be removed; use pathlib instead", DeprecationWarning)
        if not OpenMode(mode).write or not OpenMode(mode).binary:
            raise ContradictoryRequestError(f"Cannot write bytes to {path} in mode {mode}")
        with cls.open_file(path, mode) as f:
            f.write(data)

    @classmethod
    def write_text(cls, data: Any, path: PathLike, mode: str = "w"):
        warnings.warn("write_text will be removed; use pathlib instead", DeprecationWarning)
        if not OpenMode(mode).write or OpenMode(mode).binary:
            raise ContradictoryRequestError(f"Cannot write text to {path} in mode {mode}")
        with cls.open_file(path, mode) as f:
            f.write(str(data))

    @classmethod
    @contextmanager
    def open_file(cls, path: PathLike, mode: str):
        """
        Opens a file in a safer way, always using the encoding set in Kale (utf8) by default.
        This avoids the problems of accidentally overwriting, forgetting to set mode, and not setting the encoding.
        Note that the default encoding on open() is not UTF on Windows.
        Raises specific informative errors.
        Cannot set overwrite in append mode.
        """
        warnings.warn("open_file will be removed", DeprecationWarning)
        path = Path(path)
        mode = OpenMode(mode)
        if mode.write and mode.safe and path.exists():
            raise FileDoesNotExistError(f"Path {path} already exists")
        if not mode.read:
            PathTools.prep_file(path, exist_ok=mode.overwrite or mode.append)
        if mode.gzipped:
            yield gzip.open(path, mode.internal, compresslevel=COMPRESS_LEVEL)
        elif mode.binary:
            yield open(path, mode.internal)
        else:
            yield open(path, mode.internal, encoding=ENCODING)

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
        warnings.warn(
            "write_lines will be removed; use typeddfs's write_lines instead", DeprecationWarning
        )
        path = Path(path)
        mode = OpenMode(mode)
        if not mode.overwrite or mode.binary:
            raise ContradictoryRequestError(f"Wrong mode for writing a text file: {mode}")
        if not cls.is_true_iterable(iterable):
            raise TypeError("Not a true iterable")  # TODO include iterable if small
        PathTools.prep_file(path, exist_ok=mode.overwrite or mode.append)
        n = 0
        with cls.open_file(path, mode) as f:
            for x in iterable:
                f.write(str(x) + "\n")
            n += 1
        return n

    @classmethod
    def sha1(cls, x: SupportsBytes) -> str:
        warnings.warn(
            "sha1 will be removed; use hash_hex(x, algorithm='sha1') instead", DeprecationWarning
        )
        return cls.hash_hex(x, "sha1")

    @classmethod
    def sha256(cls, x: SupportsBytes) -> str:
        warnings.warn(
            "sha1 will be removed; use hash_hex(x, algorithm='sha256') instead", DeprecationWarning
        )
        return cls.hash_hex(x, "sha256")

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
        Simple wrapper around tempfile.TemporaryFile, tempfile.NamedTemporaryFile, and tempfile.SpooledTemporaryFile.
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


__all__ = ["FilesysTools"]
