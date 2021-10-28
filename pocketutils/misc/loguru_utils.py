"""
Loguru logging extension that, configurably:
- redirects built-in logging to your loguru logger
- remembers the handlers added
- auto-detects compression and serialization from filenames
- includes extras in non-serializing handlers
- has a few alternative (possibly better) choices for colors, icons, and levels
- will complain when you do really stupid things
- has a convenient notation for configuring from a CLI
  (e.g. ``--stderr debug --log :INFO:run.log.gz``)
- mandates utf-8
"""
from __future__ import annotations

import abc
import logging
import os
import sys
import traceback
from collections import deque
from dataclasses import dataclass
from functools import partialmethod
from inspect import cleandoc
from pathlib import Path
from typing import (
    AbstractSet,
    Any,
    Callable,
    Deque,
    Generic,
    Iterable,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    TextIO,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import loguru._defaults as _defaults

# noinspection PyProtectedMember
import loguru._logger
import regex
from loguru import logger as _logger

# noinspection PyProtectedMember
from loguru._logger import Logger

from pocketutils.core import PathLike
from pocketutils.core.exceptions import IllegalStateError, XValueError

_levels = loguru.logger._core.levels
Formatter = Union[str, Callable[[Mapping[str, Any]], str]]
DEFAULT_FMT_STRING = cleandoc(
    r"""
    <bold>{time:YYYY-MM-DD HH:mm:ss.SSS} | </bold>
    <level>{level: <7}</level><bold> | </bold>
    <cyan>({thread.id}){name}</cyan><bold>:</bold>
    <cyan>{function}</cyan><bold>:</bold>
    <cyan>{line}</cyan><bold> — </bold>
    <level>{message}{{EXTRA}}</level>
    {exception}
    """
).replace("\n", "")


class _SENTINEL:
    pass


T = TypeVar("T", covariant=True, bound=Logger)
Z = TypeVar("Z", covariant=True, bound=Logger)


def _add_traceback(record):
    extra = record["extra"]
    if extra.get("traceback", False):
        extra["traceback"] = "\n" + "".join(traceback.format_stack())
    else:
        extra["traceback"] = ""


_LOGGER_ARG_PATTERN = regex.compile(r"(?:([a-zA-Z]+):)?(.*)", flags=regex.V1)
log_compressions = {
    ".xz",
    ".lzma",
    ".gz",
    ".zip",
    ".bz2",
    ".tar",
    ".tar.gz",
    ".tar.bz2",
    ".tar.xz",
}
valid_log_suffixes = {
    *{f".log{c}" for c in log_compressions},
    *{f".txt{c}" for c in log_compressions},
    *{f".json{c}" for c in log_compressions},
}


class _Defaults:
    def wrap_extended_fmt(
        self,
        *,
        fmt: str = DEFAULT_FMT_STRING,
        sep: str = "; ",
        eq_sign: str = " ",
    ) -> Callable[[Mapping[str, Any]], str]:
        def FMT(record: Mapping[str, Any]) -> str:
            extra = sep.join([e + eq_sign + "{extra[" + e + "]}" for e in record["extra"].keys()])
            if len(extra) > 0:
                extra = f" [ {extra} ]"
            return fmt.replace("{{EXTRA}}", extra) + os.linesep

        return FMT

    def wrap_plain_fmt(
        self, *, fmt: str = DEFAULT_FMT_STRING
    ) -> Callable[[Mapping[str, Any]], str]:
        def FMT(record: Mapping[str, Any]) -> str:
            return fmt.replace("{{EXTRA}}", "") + os.linesep

        return FMT

    @property
    def levels_current(self):
        ell = loguru.logger._core.levels
        return {e.name: e.no for e in ell.values()}

    @property
    def colors_current(self):
        ell = loguru.logger._core.levels
        return {e.name: e.color for e in ell.values()}

    @property
    def icons_current(self):
        ell = loguru.logger._core.levels
        return {e.name: e.icon for e in ell.values()}

    @property
    def levels_built_in(self):
        return {e.name: e.no for e in _levels.values()}

    @property
    def colors_built_in(self):
        return {e.name: e.color for e in _levels.values()}

    @property
    def icons_built_in(self):
        return {e.name: e.icon for e in _levels.values()}

    # the levels for caution and notice are DEFINED here
    # trace and success must match loguru's
    # and the rest must match logging's
    # note that most of these alternate between informative and problematic
    # i.e. info (ok), caution (bad), success (ok), warning (bad), notice (ok), error (bad)
    @property
    def levels_extended(self) -> Mapping[str, int]:
        ell = loguru.logger._core.levels
        levels = {k.name: k.no for k in ell.values()}
        levels.setdefault("CAUTION", 23)
        levels.setdefault("NOTICE", 37)
        return levels

    @property
    def colors_extended(self) -> Mapping[str, str]:
        ell = loguru.logger._core.levels
        colors = {k.name: k.color for k in ell.values()}
        colors.setdefault("CAUTION", ell["WARNING"].color)
        colors.setdefault("NOTICE", ell["INFO"].color)
        return colors

    @property
    def colors_red_green_safe(self) -> Mapping[str, str]:
        return dict(
            TRACE="<dim>",
            DEBUG="<dim>",
            INFO="<bold>",
            CAUTION="<yellow>",
            SUCCESS="<blue>",
            WARNING="<yellow>",
            NOTICE="<blue>",
            ERROR="<red>",
            CRITICAL="<red>",
        )

    @property
    def icons_extended(self) -> Mapping[str, str]:
        ell = loguru.logger._core.levels
        icons = {k.name: k.icon for k in ell.values()}
        icons.setdefault("CAUTION", "⚐")
        icons.setdefault("NOTICE", "★")
        return icons

    @property
    def level(self) -> str:
        return _defaults.LOGURU_LEVEL

    @property
    def fmt_simplified(self):
        return self.wrap_plain_fmt()

    @property
    def fmt_built_in(self):
        return self.wrap_extended_fmt()

    @property
    def fmt_built_in_raw(self):
        return _defaults.LOGURU_FORMAT

    @property
    def fmt_extended_raw(self):
        return DEFAULT_FMT_STRING

    @property
    def aliases(self):
        return dict(NONE=None, NO=None, OFF=None, VERBOSE="INFO", QUIET="ERROR")

    def new_log_fn(self, level: str, logger: Logger = _logger):
        """
        Generates functions to attach to a ``loguru._logger.Logger``.
        For example, ``LogMethodFactory.new("caution")`` will return
        a function that delegates (essentially) to ``logger.log("CAUTION", ...)``.
        """

        def _x(__message: str, *args, **kwargs):
            logger._log(level.upper(), None, False, logger._options, __message, args, kwargs)

        _x.__name__ = level.lower()
        return _x


@dataclass(frozen=True, repr=True, order=True)
class HandlerInfo:
    """
    Information about a loguru handler.
    """

    hid: int
    path: Optional[Path]
    level: Optional[str]
    fmt: Formatter


@dataclass(frozen=False, repr=True)
class _HandlerInfo:
    hid: int
    sink: Any
    level: Optional[int]
    fmt: Formatter

    @property
    def to_friendly(self):
        return HandlerInfo(hid=self.hid, level=self.level, fmt=self.fmt, path=self.sink)


@dataclass(frozen=True, repr=True, order=True)
class LogSinkInfo:
    """
    Information about a loguru sink, before it has been added.
    """

    path: Path
    base: Path
    suffix: str
    serialize: bool
    compression: Optional[str]


class InterceptHandler(logging.Handler):
    """
    Redirects standard logging to loguru.
    """

    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = _logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        _logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


class Rememberer:
    """
    A handler that stores recent messages in a deque.
    """

    def __init__(self, n_messages: int):
        self.hid: int = -1
        self._messages: Deque[str] = deque(maxlen=n_messages)

    def __call__(self, msg: str):
        self._messages.append(msg)


class LoggerWithCautionAndNotice(Logger, metaclass=abc.ABCMeta):
    """
    A wrapper that has fake methods to trick static analysis.
    """

    def caution(self, __message: str, *args, **kwargs):
        raise NotImplementedError()  # not real

    def notice(self, __message: str, *args, **kwargs):
        raise NotImplementedError()  # not real


class FancyLoguru(Generic[T]):
    """
    See :module:`pocketutils.misc.fancy_loguru`.
    """

    def __init__(self, logger: T = _logger):
        self._defaults = _Defaults()
        self._logger = logger
        # noinspection PyTypeChecker
        self._main: _HandlerInfo = None
        self._rememberer: Rememberer = None
        self._paths: MutableMapping[Path, _HandlerInfo] = {}
        self._aliases = dict(self._defaults.aliases)
        self._control_enabled = True

    @staticmethod
    def new(t: Type[Z]) -> FancyLoguru[Z]:
        ell = _logger.patch(_add_traceback)
        logger = t(ell._core, *ell._options)
        return FancyLoguru[Z](logger)

    @property
    def defaults(self) -> _Defaults:
        return self._defaults

    @property
    def logger(self) -> T:
        """
        Returns the stored logger.
        """
        return self._logger

    @property
    def levels(self) -> Mapping[str, int]:
        """
        Returns the global loguru levels.
        """
        return {e.name: e.no for e in _levels.values()}

    @property
    def aliases(self) -> Mapping[str, Optional[str]]:
        """
        Returns the aliases to levels.
        A ``None`` means no logging ("OFF").
        """
        return self._aliases

    @property
    def recent_messages(self) -> Sequence[str]:
        """
        Returns some number of recent messages, if recording.

        See Also:
            :meth:`remember`
        """
        if self._rememberer is None:
            return []
        return list(self._rememberer._messages)

    @property
    def main(self) -> Optional[HandlerInfo]:
        """
        Returns the main handler info, if configured.
        """
        if self._main is None:
            return None
        return HandlerInfo(
            hid=self._main.hid, level=self._main.level, fmt=self._main.fmt, path=None
        )

    @property
    def paths(self) -> AbstractSet[HandlerInfo]:
        """
        Lists all path handlers configured in this object.
        """
        return {h.to_friendly for h in self._paths.values()}

    def get_path(self, p: PathLike) -> Optional[HandlerInfo]:
        """
        Returns a path handler to this path, or None if it does not exist.
        The path is resolved, following symlinks, via ``pathlib.Path.resolve``.
        """
        p = Path(p)
        p = self._paths.get(p.resolve())
        return None if p is None else p.to_friendly

    def set_control(self, enabled: bool) -> __qualname__:
        """
        Enables/disables handler control.
        If control is disabled, subsequent calls to
        methods like :meth:`from_cli` and :meth:`add_path` do nothing.
        """
        self._control_enabled = enabled
        return self

    @property
    def is_control_enabled(self) -> bool:
        return self._control_enabled

    def config_levels(
        self,
        *,
        levels: Mapping[str, int] = _SENTINEL,
        colors: Mapping[str, str] = _SENTINEL,
        icons: Mapping[str, str] = _SENTINEL,
        aliases: Mapping[str, str] = _SENTINEL,
    ) -> __qualname__:
        """
        Modify loguru's levels.
        This is a global operation and will run regardless of :attr:`is_control_enabled`.
        """
        levels = self._defaults.levels_extended if levels is _SENTINEL else levels
        colors = self._defaults.colors_extended if colors is _SENTINEL else colors
        icons = self._defaults.icons_extended if icons is _SENTINEL else icons
        aliases = self._defaults.aliases if aliases is _SENTINEL else aliases
        for k, v in levels.items():
            self.config_level(
                k,
                v,
                color=colors.get(k, _SENTINEL),
                icon=icons.get(k, _SENTINEL),
            )
        self._aliases = dict(aliases)
        return self

    def config_level(
        self,
        name: str,
        level: int,
        *,
        color: Union[None, str, _SENTINEL] = _SENTINEL,
        icon: Union[None, str, _SENTINEL] = _SENTINEL,
        replace: bool = True,
    ) -> __qualname__:
        """
        Add a new loguru level.
        This is a global operation and will run regardless of :attr:`is_control_enabled`.
        """
        try:
            data = self._logger.level(name)
        except ValueError:
            data = None
        if data is None:
            self._logger.level(
                name,
                no=level,
                color=None if color is _SENTINEL else color,
                icon=None if icon is _SENTINEL else icon,
            )
        elif replace:
            if level != data.no:  # loguru doesn't check whether they're eq; it just errors
                raise IllegalStateError(f"Cannot set level={level}!={data.no} for {name}")
            self._logger.level(
                name,
                color=data.color if color is _SENTINEL else color,
                icon=data.icon if icon is _SENTINEL else icon,
            )
        return self

    def add_log_methods(self, *, replace: bool = True) -> __qualname__:
        levels = [level.lower() for level in self.levels.keys()]
        for level in levels:
            _x = self._defaults.new_log_fn(level, self._logger)
            if replace or not hasattr(self._logger, level):
                setattr(self._logger, level, _x)
        return self

    def enable(self, *names: str) -> __qualname__:
        """
        Calls ``loguru.logger.enable`` on multiple items.
        """
        if not self._control_enabled:
            return self
        for name in names:
            _logger.enable(name)
        return self

    def disable(self, *names: str) -> __qualname__:
        """
        Calls ``loguru.logger.disable`` on multiple items.
        """
        if not self._control_enabled:
            return self
        for name in names:
            _logger.disable(name)
        return self

    def intercept_std(self, *, warnings: bool = True) -> __qualname__:
        """
        Sets python builtin ``logging`` to redirect to loguru.
        Uses :class:`InterceptHandler`.

        Args:
            warnings: Call ``logging.captureWarnings(True)`` to intercept builtin ``warnings``
        """
        # noinspection PyArgumentList
        logging.basicConfig(handlers=[InterceptHandler()], level=0, encoding="utf-8")
        if warnings:
            logging.captureWarnings(True)

    def config_main(
        self,
        *,
        sink: TextIO = _SENTINEL,
        level: Optional[str] = _SENTINEL,
        fmt: Formatter = _SENTINEL,
    ) -> __qualname__:
        """
        Sets the logging level for the main handler (normally stderr).
        """
        if not self._control_enabled:
            if self._main is not None:
                self._main.level = self._main.level if level is _SENTINEL else level
                self._main.sink = self._main.sink if sink is _SENTINEL else sink
                self._main.fmt = self._main.fmt if fmt is _SENTINEL else fmt
            return self
        if level is not None and level is not _SENTINEL:
            level = level.upper()
        if self._main is None:
            self._main = _HandlerInfo(
                hid=-1,
                sink=sys.stderr,
                level=self.levels[self._defaults.level],
                fmt=self._defaults.fmt_built_in,
            )
        else:
            try:
                self._logger.remove(self._main.hid)
            except ValueError:
                self._logger.error(f"Cannot remove handler {self._main.hid}")
        self._main.level = self._main.level if level is _SENTINEL else level
        self._main.sink = self._main.sink if sink is _SENTINEL else sink
        self._main.fmt = self._main.fmt if fmt is _SENTINEL else fmt
        self._main.hid = self._logger.add(
            self._main.sink, level=self._main.level, format=self._main.fmt
        )
        return self

    def remember(self, *, n_messages: int = 100) -> __qualname__:
        """
        Adds a handler that stores the last ``n_messages``.
        Retrieve the stored messages with :meth:`recent_messages`.
        """
        if n_messages == 0 and self._rememberer is None:
            return
        if n_messages == 0:
            self._logger.remove(self._rememberer.hid)
            return
        extant = self.recent_messages
        self._rememberer = Rememberer(n_messages)
        self._rememberer.hid = self._logger.add(
            self._rememberer, level="TRACE", format=self._main.fmt
        )
        for msg in extant:
            self._rememberer(msg)
        return self

    def add_path(
        self,
        path: PathLike,
        level: str = _SENTINEL,
        *,
        fmt: str = _SENTINEL,
        filter=None,
    ) -> __qualname__:
        """
        Adds a handler to a file.

        See Also:
            :meth:`remove_path`

        Args:
            path: If it ends with .gz, .zip, .etc., will use compression
                  If (ignoring compression) ends with .json, will serialize as JSON.
                  Calls ``pathlib.Path.resolve``, meaning that symlinks are followed
            level: Min log level
            fmt: Formatting string; will wrap into a :class:`Formatter`
                 Include ``{{EXTRA}}`` to include all extras
                 See: :class:`FormatFactory`
            filter: Filtration function of records
        """
        if not self._control_enabled:
            return self
        path = Path(path).resolve()
        level, ell, fmt = self._get_info(level, fmt)
        info = self.guess_file_sink_info(path)
        hid = self._logger.add(
            str(info.base),
            format=fmt,
            level=level,
            compression=info.compression,
            serialize=info.serialize,
            backtrace=True,
            diagnose=True,
            enqueue=True,
            filter=filter,
            encoding="utf-8",
        )
        self._paths[path] = _HandlerInfo(hid=hid, sink=info.base, level=ell, fmt=fmt)
        return self

    def remove_paths(self) -> __qualname__:
        """
        Removes **all** path handlers stored here.

        See Also:
            :meth:`remove_path`
        """
        if not self._control_enabled:
            return self
        for p in dict(self._paths).keys():
            self.remove_path(p)
        return self

    def remove_path(self, path: Path) -> __qualname__:
        """
        Removes a path handler (limited to those stored here).
        Will log an error and continue if the path is not found.

        See Also:
            :meth:`remove_paths`
        """
        if not self._control_enabled:
            return self
        path = path.resolve()
        p = self._paths.get(path)
        if p is not None:
            try:
                self._logger.remove(p.hid)
                del self._paths[path]
            except ValueError:
                self._logger.exception(f"Cannot remove handler {p.hid} to {path}")
        return self

    def from_cli(
        self,
        path: Union[None, str, Path] = None,
        main: Optional[str] = None,
        _msg_level: str = "OFF",
    ) -> __qualname__:
        """
        This function controls logging set via command-line.
        Deletes any existing path handlers.

        Args:
            main: The level for stderr; if None, does not modify
            path: If set, the path to a file. Can be prefixed with ``:level:`` to set the level
                  (e.g. ``:INFO:mandos-run.log.gz``). Can serialize to JSON if .json is used
                  instead of .log or .txt.
            _msg_level: Level for messages about this logging change
        """
        _msg_level = self._aliases.get(_msg_level.upper(), _msg_level.upper())
        if not self._control_enabled:
            if self._main is not None:
                self._main.level = _msg_level
            return self
        if main is _SENTINEL:
            main = None
        if main is None and self._main is None:
            main = self._defaults.level
        elif main is None:
            main = self._main.level
        main = self._aliases.get(main.upper(), main.upper())
        if main not in self._defaults.levels_extended:
            _permitted = ", ".join(
                [*self._defaults.levels_extended, *self._defaults.aliases.keys()]
            )
            raise XValueError(
                f"{main.lower()} not a permitted log level (allowed: {_permitted}", value=main
            )
        self.config_main(level=main)
        self.remove_paths()
        if path is not None and len(str(path)) > 0:
            match = _LOGGER_ARG_PATTERN.match(str(path))
            path_level = "DEBUG" if match.group(1) is None else match.group(1)
            path = Path(match.group(2))
            self.add_path(path, path_level)
            if _msg_level is not None:
                self._logger.log(_msg_level, f"Added path handler {path} (level {path_level})")
        if _msg_level is not None:
            self._logger.log(_msg_level, f"Set main log level to {main}")
        return self

    __call__ = from_cli

    def rewire_streams_to_utf8(self) -> __qualname__:
        """
        Calls ``reconfigure`` on ``sys.stderr``, ``sys.stdout``, and ``sys.stdin`` to use utf-8.
        Use at your own risk.
        """
        sys.stderr.reconfigure(encoding="utf-8")
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
        return self

    @classmethod
    def guess_file_sink_info(cls, path: Union[str, Path]) -> LogSinkInfo:
        path = Path(path)
        base, compression = path.name, None
        for c in log_compressions:
            if path.name.endswith(c):
                base, compression = path.name[: -len(c)], c
        if not [base.endswith(s) for s in [".json", ".log", ".txt"]]:
            raise XValueError(
                f"Log filename {path.name} is not .json, .log, .txt, or a compressed variant",
                value=path.name,
            )
        return LogSinkInfo(
            path=path,
            base=path.parent / base,
            suffix=compression,
            serialize=base.endswith(".json"),
            compression=compression,
        )

    def _get_info(self, level: str = _SENTINEL, fmt: str = _SENTINEL) -> Tuple[str, int, Formatter]:
        if level is _SENTINEL and self._main is None:
            level = self._defaults.level
        elif level is _SENTINEL:
            level = self._main.level
        level = level.upper()
        if fmt is _SENTINEL and self._main is None:
            fmt = self._defaults.fmt_built_in
        elif fmt is _SENTINEL:
            fmt = self._main.fmt
        if isinstance(fmt, str):
            fmt = self._defaults.wrap_extended_fmt(fmt=fmt)
        ell = self.levels[level]
        return level, ell, fmt

    @classmethod
    def built_in(
        cls,
        *,
        enable_control: bool = True,
        sink=sys.stderr,
        level: str = _SENTINEL,
    ) -> FancyLoguru[Logger]:
        """
        Creates a new FancyLoguru using standard loguru levels, etc.

        Args:
            enable_control: If False, all calls to add/remove handlers (except :meth:`remember`)
                            will be ignored. :meth:`rewire_streams` will also be ignored.
                            This is provided so that you can configure both an "application"
                            and a library that works for the same code
                            with ``enable_control=<is-command-line>``.
            sink: The *main* sink to start with
            level: The min log level for the main sink
        """
        return (
            FancyLoguru.new(Logger)
            .set_control(enable_control)
            .config_levels()
            .remember()
            .config_main(level=level, sink=sink)
        )

    @classmethod
    def extended(
        cls,
        *,
        enable_control: bool = True,
        sink=sys.stderr,
        level: str = _SENTINEL,
        simplify_fmt: bool = True,
        red_green_safe: bool = True,
    ) -> FancyLoguru[LoggerWithCautionAndNotice]:
        """
        Creates a new FancyLoguru with extra levels "caution" and "notice".
        - *CAUTION*: Bad, but between levels *INFO* and *SUCCESS*
        - *NOTICE*: Good/neutral, but between levels *WARNING* and *ERROR*

        Args:
            enable_control: See :meth:`built_in`
            sink: See :meth:`built_in`
            level: See :meth:`built_in`
            simplify_fmt: Use ``DEFAULT_FMT_STRING``
            red_green_safe: Modify the standard colors to use blue instead of green
        """
        defaults = _Defaults()
        levels = defaults.levels_extended
        icons = defaults.icons_extended
        colors = defaults.colors_red_green_safe if red_green_safe else defaults.colors_extended
        fmt = defaults.fmt_simplified if simplify_fmt else defaults.fmt_built_in
        return (
            FancyLoguru.new(LoggerWithCautionAndNotice)
            .set_control(enable_control)
            .config_levels(levels=levels, colors=colors, icons=icons)
            .remember()
            .config_main(level=level, sink=sink, fmt=fmt)
        )


FANCY_LOGURU_DEFAULTS = _Defaults()


__all__ = [
    "FancyLoguru",
    "FANCY_LOGURU_DEFAULTS",
    "InterceptHandler",
    "HandlerInfo",
    "Logger",
    "LoggerWithCautionAndNotice",
]
