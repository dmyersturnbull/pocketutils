import os
import warnings
from copy import copy

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
        raise NotConstructableError("Do not instantiate {}".format(self.__class__.__name__))

    @classmethod
    def init(cls):
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
    def filter(cls, **kwargs):
        """Same as warnings.filterwarnings."""
        warnings.filterwarnings(**kwargs)
        return cls

    @classmethod
    def substring_never(cls, substring: str):
        """Adds a filter containing this substring, never showing the warning."""
        warnings.filterwarnings(message=".*" + substring + ".*", action="ignore")
        return cls

    @classmethod
    def substring_once(cls, substring: str):
        """Adds a filter containing this substring, warning only once."""
        warnings.filterwarnings(message=".*" + substring + ".*", action="once")
        return cls

    @classmethod
    def filter_common_numeric(cls):
        """
        Adds filters for common unavoidable warnings from numpy, pandas, scikit-learn, etc.

        Returns:
            self
        """
        return (
            cls.substring_never("libuv only supports millisecond timer resolution")
            .substring_never("or '1type' as a synonym of type is deprecated")
            .substring_never(
                "Series.nonzero() is deprecated and will be removed in a future version"
            )
            .substring_never(
                "Monkey-patching ssl after ssl has already been imported may lead to errors"
            )
            .substring_never(
                "your performance may suffer as PyTables will pickle object types that it cannot map directly to c-types"
            )
            .substring_once("Trying to unpickle estimator")
            .substring_once("Passing require_full to OrganizingFrame.convert is deprecated")
        )

    @classmethod
    def view_filters(cls):
        return copy(warnings.filters)


__all__ = ["GlobalWarningUtils"]
