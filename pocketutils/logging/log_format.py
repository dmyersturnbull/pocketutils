from __future__ import annotations

import logging
import textwrap
from copy import deepcopy


class LogFormatBuilder:
    """
    Builder for those of us who hate the Python logging Formatter syntax and can't remember the options.

    Example:
        >>> formatter = (
        >>>     LogFormatBuilder()
        >>>     .level_name_fixed_width()
        >>>     .asc_time()
        >>>     .thread_name(left=' [', right=':')
        >>>     .line_num(left='', right=']')
        >>>     .message(left=': ')
        >>> ).build()
    """

    _s = None

    def __init__(self) -> None:
        self._s = ""

    def __repr__(self) -> str:
        return "{}({})".format(self.__class__.__name__, self._s)

    def __str__(self) -> str:
        return repr(self)

    def level_num(self, left: str = " ", right: str = ""):
        self._s += left + "%(levelno)s" + right
        return self

    def level_name(self, left: str = " ", right: str = ""):
        self._s += left + "%(levelname)s" + right
        return self

    def level_name_fixed_width(self, left: str = " ", right: str = ""):
        self._s += left + "%(levelname)-8s" + right
        return self

    def name(self, left: str = " ", right: str = ""):
        self._s += left + "%(name)s" + right
        return self

    def module(self, left: str = " ", right: str = ""):
        self._s += left + "%(module)s" + right
        return self

    def message(self, left: str = " ", right: str = ""):
        self._s += left + "%(message)s" + right
        return self

    def thread_id(self, left: str = " ", right: str = ""):
        self._s += left + "%(thread)d" + right
        return self

    def thread_name(self, left: str = " ", right: str = ""):
        self._s += left + "%(threadName)s" + right
        return self

    def asc_time(self, left: str = " ", right: str = ""):
        self._s += left + "%(asctime)s" + right
        return self

    def line_num(self, left: str = " ", right: str = ""):
        self._s += left + "%(lineno)d" + right
        return self

    def other(self, fmt: str, left: str = " ", right: str = ""):
        self._s += left + fmt + right
        return self

    def build(self) -> logging.Formatter:
        return logging.Formatter(self._s[min(1, len(self._s)) :])


class PrettyRecordFactory:
    """
    A ``logging`` formatter
    Makes beautiful aligned log output.

    Example:
        logger = logging.getLogger('myproject')
        log_factory = KaleRecordFactory(7, 13, 5).modifying(logger)

    For example:
    •  ⟩20210302:17:33:14 :sauronlab  :environment  :150
       |Set global log level to INFO and sauronlab to MINOR.
    •  ⟩20210302:17:33:14 :sauronlab  :environment  :141
       |Read Csauronlab.config .
    •  ⟩20210302:17:33:14 :sauronlab  :environment  :142
       |Set 8 sauronlab config items. Run 'print(sauronlab_env.info())' for details.
    ⚠  ⟩20210302:17:33:22 :sauronlab  :startup      :26
       |Could not load sauronlab package info. Is it installed?
    •  ⟩20210302:17:33:26 :sauronlab  :_kvrc_utils  :989
       |Loaded 49 matplotlib RC settings from sauronlab.mplstyle
    •  ⟩20210302:17:33:26 :sauronlab  :_kvrc_utils  :1035
       |Loaded 37 Sauronlab viz settings from sauronlab_viz.properties
    •  ⟩20210302:17:33:26 :sauronlab  :_kvrc_utils  :1037
       |Set 10 reference widths and heights. Pad is (0.25, 0.25). Gutter is 0.25.
    ★  ⟩20210302:17:33:26 :sauronlab  :fancy_logger :203
       |Sauronlab version ??. Started in 12s.
    """

    def __init__(
        self, max_name: int, max_module: int, max_line: int, width: int = 100, symbols: bool = False
    ):
        self.max_name, self.max_module, self.max_line = max_name, max_module, max_line
        self.width = width
        self.old_factory = deepcopy(logging.getLogRecordFactory())
        if symbols:
            self.flags = dict(
                TRACE=".",
                DEBUG="-",
                MINOR="·",
                INFO="•",
                CAUTION="☡",
                WARNING="⚠",
                NOTICE="★",
                ERROR="⛔",
            )
        else:
            self.flags = {}

    def factory(self, *args, **kwargs):
        def ltrunc(s, n, before="", after=""):
            return (before + (s if len(s) <= n else s[: n - 1] + "…") + after).ljust(
                n + len(before) + len(after)
            )

        record = self.old_factory(*args, **kwargs)
        if record.name == "py.warnings":
            record.name = "warn"
        if record.module.startswith("<ipython-input"):
            record.module = "ipython"
        record.symbol = self.flags.get(record.levelname, record.levelname)
        record.abbrev = (
            ":"
            + ltrunc(record.name, self.max_name)
            + " :"
            + ltrunc(record.module, self.max_module)
            + " :"
            + str(record.lineno).ljust(self.max_line)
        )
        msg = str(record.getMessage())
        # TODO: 68
        if len(msg) < self.width - 64:
            record.wrapped = " " + msg
        else:
            # 18 from the timestamp
            hanging = " " * 3 + "|"
            record.wrapped = "\n" + "\n".join(
                textwrap.wrap(
                    msg, width=self.width, initial_indent=hanging, subsequent_indent=hanging
                )
            )
        return record

    @property
    def approx_max_len(self) -> int:
        return self.max_name + 2 + self.max_module + 2 + self.max_line

    @property
    def format(self) -> str:
        return "%(symbol)s  ⟩%(asctime)s %(abbrev)s%(wrapped)s"

    @property
    def time_format(self) -> str:
        return "%Y%m%d:%H:%M:%S"

    @property
    def formatter(self) -> logging.Formatter:
        return logging.Formatter(self.format, self.time_format)

    def modifying(self, ell) -> PrettyRecordFactory:
        """
        Set the log factory of a logger to this, and set all of its (current) handlers to use it.

        Args:
            ell: A logger (ex logging.getLogger(''))

        Returns:
            This instance
        """
        logging.setLogRecordFactory(self.factory)
        for handler in ell.handlers:
            handler.setFormatter(self.formatter)
        for handler in logging.getLogger().handlers:
            handler.setFormatter(self.formatter)
        return self


__all__ = ["LogFormatBuilder", "PrettyRecordFactory"]
