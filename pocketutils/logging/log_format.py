from __future__ import annotations

import logging
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
        [20191228:14:20:06] kale⟩    datasets      :77    INFO    | Downloading QC-DR...
        [20191228:14:20:08] numexp…⟩ utils         :141   INFO    | NumExpr defaulting to 8 threads.
        [20191228:14:21:01] kale⟩    __init__      :185   NOTICE  | Downloaded QC-DR with 8 runs, 85 names, and 768 wells.
        [20191229:14:26:04] kale⟩    __init__      :202   INFO    | Registered new type RandomForestClassifier:n_jobs=4,n_estimators=8000
        [20191229:14:26:36] kale⟩    __init__      :185   NOTICE  | Using: treatment selector ⟨keep_all⟩, control selector ⟨keep_all⟩, subsampler ⟨keep_8_balanced⟩, and should_proceed ⟨if_at_least_0_req2_fail⟩
        [20191229:14:26:36] kale⟩    multi_traine… :193   DEBUG   | Logging every 50 iterations.
        [20191229:14:26:36] kale⟩    timing        :83    INFO    | Started processing 504 items at 2019-12-28 14:26:36.
        [20191229:14:26:39] kale⟩    timing        :91    INFO    | Processed 1/504 in 2.8s. Estimated 23.57min left.
        [20191229:14:26:41] kale⟩    classifiers   :211   INFO    | Training on 2 labels and 101997 features using 16 examples, 8 runs, and 2000 estimators on 4 core(s).
        [20191229:14:26:46] kale⟩    classifiers   :230   INFO    | Finished training. Took 5s. oob_score=0.188
        [20191229:14:27:07] kale⟩    __init__      :185   NOTICE  | Ignoring future classifier output...
        [20191229:14:39:13] kale⟩    timing        :91    INFO    | Processed 201/504 in 12.61min. Estimated 19.01min left.
        [20191229:14:51:12] kale⟩    timing        :91    INFO    | Processed 401/504 in 24.6min. Estimated 6.32min left.
        [20191229:14:57:10] kale⟩    timing        :94    INFO    | Processed 504/504 in 30.58min. Done at 2019-12-28 14:57:10.
    """

    def __init__(self, max_name: int, max_module: int, max_line: int):
        self.max_name, self.max_module, self.max_line = max_name, max_module, max_line
        self.old_factory = deepcopy(logging.getLogRecordFactory())

    def factory(self, *args, **kwargs):
        def ltrunc(s, n, before="", after=""):
            return (before + (s if len(s) <= n else s[: n - 1] + "…") + after).ljust(
                n + len(before) + len(after)
            )

        record = self.old_factory(*args, **kwargs)
        record.abbrev = (
            ltrunc(record.name, self.max_name, after="⟩")
            + " "
            + ltrunc(record.module, self.max_module)
            + " "
            + ":"
            + str(record.lineno).ljust(self.max_line)
        )
        return record

    @property
    def approx_max_len(self) -> int:
        return self.max_name + 2 + self.max_module + 2 + self.max_line

    @property
    def format(self) -> str:
        return "[%(asctime)s] %(abbrev)s %(levelname)-8s| %(message)s"

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
