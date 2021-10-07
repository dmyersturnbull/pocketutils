from __future__ import annotations

import warnings
from pathlib import Path
from typing import AbstractSet

from pocketutils.core.exceptions import NotConstructableError


class WarningsConfig:
    """
    Convenient API to add warning filters.
    Also provides :meth:`simplify_format`, which sets a less-verbose warning formatter.

    Example:
        >>> (
                GlobalWarningUtils.simplify_format()
                .filter_common()
                .never("Number of features differ")
            )
    """

    def __init__(self):
        raise NotConstructableError(f"Do not instantiate {self.__class__.__name__}")

    @classmethod
    def simplify_format(cls) -> __qualname__:
        """
        Common initialization, including setting a better formatter that doesn't say "WARNING:py.warnings:".
        """

        def new_formatter(message, category, filename, lineno, line=None):
            cat = category.__name__.replace("Warning", "")
            s = f"{Path(filename).name}:{lineno}: {cat}: {message}"
            return s.replace("WARNING:py.warnings:", "")

        warnings.formatwarning = new_formatter
        return cls

    @classmethod
    def filter(cls, **kwargs) -> __qualname__:
        """Same as warnings.filterwarnings."""
        warnings.filterwarnings(**kwargs)
        return cls

    @classmethod
    def never(cls, *substrings: str) -> __qualname__:
        """Adds a filter containing this substring, never showing the warning."""
        for substring in substrings:
            warnings.filterwarnings(message=".*?" + substring + ".*", action="ignore")
        return cls

    @classmethod
    def once(cls, *substrings: str) -> __qualname__:
        """Adds a filter containing this substring, warning only once."""
        for substring in substrings:
            warnings.filterwarnings(message=".*?" + substring + ".*", action="once")
        return cls

    @classmethod
    def filter_common(cls) -> __qualname__:
        """
        Adds filters for common unavoidable warnings from numpy, pandas, scikit-learn, etc.

        See ``common_never_substrings`` and ``common_once_substrings``.
        """
        return cls.never(*cls.common_never()).once(*cls.common_once())

    @classmethod
    def common_never(cls) -> AbstractSet[str]:
        return {
            "libuv only supports millisecond timer resolution",
            "or '1type' as a synonym of type is deprecated",
            "Series.nonzero() is deprecated and will be removed in a future version",
            "Monkey-patching ssl after ssl has already been imported may lead to errors",
            "your performance may suffer as PyTables will pickle object types that it cannot map directly to c-types",
        }

    @classmethod
    def common_once(cls) -> AbstractSet[str]:
        return {
            "Trying to unpickle estimator",
        }


__all__ = ["WarningsConfig"]
