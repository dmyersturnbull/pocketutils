"""
Low-level tools (e.g. memory management).
"""
import atexit
import importlib
import locale
import logging
import os
import platform
import socket
import signal
import struct
import sys
import traceback
from collections import Callable
from dataclasses import dataclass, asdict
from datetime import timezone, datetime
from getpass import getuser
from typing import Any, Union, Sequence, Mapping, Optional, NamedTuple

from pocketutils.core.input_output import Writeable
from pocketutils.tools.base_tools import BaseTools

logger = logging.getLogger("pocketutils")


@dataclass(frozen=True, repr=True, order=True)
class Frame:
    depth: int
    filename: str
    line: int
    name: str
    repeats: int

    def as_dict(self) -> Mapping[str, Union[int, str]]:
        return asdict(self)


class SerializedException(NamedTuple):
    message: Sequence[str]
    stacktrace: Sequence[Frame]


@dataclass(frozen=True, repr=True)
class SignalHandler:
    name: str
    code: int
    desc: str
    sink: Union[Writeable, Callable[[str], Any]]

    def __call__(self):
        self.sink.write(f"~~{self.name}[{self.code}] ({self.desc})~~")
        traceback.print_stack(file=self.sink)
        for line in traceback.format_stack():
            self.sink.write(line)


@dataclass(frozen=True, repr=True)
class ExitHandler:
    sink: Writeable

    def __call__(self):
        self.sink.write(f"~~EXIT~~")
        traceback.print_stack(file=self.sink)
        for line in traceback.format_stack():
            self.sink.write(line)


class SystemTools(BaseTools):
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
        lang_code, encoding = locale.getlocale()
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
                lang_code=lang_code,
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
    def serialize_exception(cls, e: Optional[BaseException]) -> SerializedException:
        tbe = traceback.TracebackException.from_exception(e)
        msg = [] if e is None else list(tbe.format_exception_only())
        tb = SystemTools.build_traceback(e)
        return SerializedException(msg, tb)

    @classmethod
    def serialize_exception_msg(cls, e: Optional[BaseException]) -> Sequence[str]:
        tbe = traceback.TracebackException.from_exception(e)
        return [] if e is None else list(tbe.format_exception_only())

    @classmethod
    def build_traceback(cls, e: Optional[BaseException]) -> Sequence[Frame]:
        if e is None:
            return []
        tb = []
        current = None
        tbe = traceback.TracebackException.from_exception(e)
        last, repeats = None, 0
        for i, s in enumerate(tbe.stack):
            current = Frame(depth=i, filename=s.filename, line=s.line, name=s.name, repeats=-1)
            if current == last:
                repeats += 1
            else:
                current = Frame(
                    depth=current.depth,
                    filename=current.filename,
                    line=current.line,
                    name=current.name,
                    repeats=repeats,
                )
                tb.append(current)
                repeats = 0
            last = current
        if current is not None and current == last:
            tb.append(current)
        return tb

    @classmethod
    def trace_signals(cls, sink: Writeable = sys.stderr) -> None:
        """
        Registers signal handlers for all signals that log the traceback.
        Uses ``signal.signal``.
        """
        for sig in signal.valid_signals():
            handler = SignalHandler(sig.name, sig.value, signal.strsignal(sig), sink)
            signal.signal(sig.value, handler)

    @classmethod
    def trace_exit(cls, sink: Writeable = sys.stderr) -> None:
        """
        Registers an exit handler via ``atexit.register`` that logs the traceback.
        """
        atexit.register(ExitHandler(sink))


__all__ = ["SignalHandler", "ExitHandler", "SystemTools"]
