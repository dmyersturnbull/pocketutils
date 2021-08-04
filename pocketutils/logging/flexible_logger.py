from __future__ import annotations

import datetime
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from pocketutils.core import PathLike


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

    def add_file(self, path: PathLike, level: int = logging.DEBUG):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        return self._add(logging.FileHandler(str(path)), level)

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


__all__ = ["BasicFlexLogger"]
