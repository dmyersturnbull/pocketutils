from __future__ import annotations
import datetime
from typing import Optional
import os, logging
from datetime import datetime
from pocketutils.core.exceptions import DirDoesNotExistError


class BasicFlexLogger:
    """
    Usage:
    BasicFlexLogger().add_stdout().add_file('abc.log')
    """

    def __init__(
        self,
        name: Optional[str] = None,
        formatter=logging.Formatter("%(asctime)s %(levelname)-8s: %(message)s"),
    ):
        """Initializes a logger that can write to a log file and/or stdout."""
        self._underlying = logging.getLogger(name)
        self._underlying.setLevel(logging.NOTSET)
        self._formatter = formatter
        self.datetime_started = datetime.datetime.now()

    def add_file(self, path: str, level: int = logging.DEBUG):
        self._make_dirs(os.path.dirname(path))
        return self._add(logging.FileHandler(path), level)

    def add_stdout(self, level: int = logging.INFO):
        return self._add(logging.StreamHandler(), level)

    def add_handler(self, handler: logging.Handler):
        self._underlying.addHandler(handler)
        return self

    def _add(self, handler, level):
        handler.setLevel(level)
        handler.setFormatter(self._formatter)
        self._underlying.addHandler(handler)
        return self

    def _make_dirs(self, output_dir: str) -> None:
        # note that we can't import from pocketutils.files (common shouldn't depend on files)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        elif not os.path.isdir(output_dir):
            raise DirDoesNotExistError(
                "{} already exists and is not a directory".format(output_dir), path=output_dir,
            )


__all__ = ["BasicFlexLogger"]
