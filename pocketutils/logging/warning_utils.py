from __future__ import annotations

import os
import warnings

from pocketutils.core.exceptions import NotConstructableError


class GlobalWarningUtils:
    """
    Convenient API to add warning filters.
    Also provides ``init``, which sets a less-verbose warning formatter.

    Example:
        >>> GlobalWarningUtils.init()\
            .filter_common_numeric()\
            .substring_once('Number of features differ')
    """

    def __init__(self):
        raise NotConstructableError(f"Do not instantiate {self.__class__.__name__}")

    @classmethod
    def init(cls) -> __qualname__:
        """
        Common initialization, including setting a better formatter that doesn't say "WARNING:py.warnings:".
        """

        def new_formatter(message, category, filename, lineno, line=None):
            return (
                "%s:%s: %s: %s\n" % (os.path.basename(filename), lineno, category.__name__, message)
            ).replace("WARNING:py.warnings:", "")

        warnings.formatwarning = new_formatter
        return cls

    @classmethod
    def filter(cls, **kwargs) -> __qualname__:
        """Same as warnings.filterwarnings."""
        warnings.filterwarnings(**kwargs)
        return cls

    @classmethod
    def substring_never(cls, substring: str) -> __qualname__:
        """Adds a filter containing this substring, never showing the warning."""
        warnings.filterwarnings(message=".*" + substring + ".*", action="ignore")
        return cls

    @classmethod
    def substring_once(cls, substring: str) -> __qualname__:
        """Adds a filter containing this substring, warning only once."""
        warnings.filterwarnings(message=".*" + substring + ".*", action="once")
        return cls

    @classmethod
    def filter_common_numeric(cls) -> __qualname__:
        """
        Adds filters for common unavoidable warnings from numpy, pandas, scikit-learn, etc.

        See ``common_never_substrings`` and ``common_once_substrings``.
        """
        for v in cls.common_never_substrings():
            cls.substring_never(v)
        for v in cls.common_once_substrings():
            cls.substring_once(v)
        return cls

    @classmethod
    def common_never_substrings(cls):
        return [
            "libuv only supports millisecond timer resolution",
            "or '1type' as a synonym of type is deprecated",
            "Series.nonzero() is deprecated and will be removed in a future version",
            "Monkey-patching ssl after ssl has already been imported may lead to errors",
            "your performance may suffer as PyTables will pickle object types that it cannot map directly to c-types",
        ]

    @classmethod
    def common_once_substrings(cls):
        return [
            "Trying to unpickle estimator",
        ]


__all__ = ["GlobalWarningUtils"]
