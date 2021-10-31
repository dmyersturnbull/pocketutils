"""
Low-level tools (e.g. memory management).
"""
import atexit
import signal
import sys
import traceback
from collections import Callable
from dataclasses import dataclass
from typing import Any, Union

from pocketutils.core.input_output import Writeable

from pocketutils.tools.base_tools import BaseTools


@dataclass(frozen=True, repr=True)
class SignalHandler:
    name: str
    code: int
    desc: str
    sink: Union[Writeable, Callable[[str], Any]]

    def __call__(self):
        sys.stderr.write(f"~~{self.name}[{self.code}] ({self.desc})~~")
        traceback.print_stack(file=sys.stderr)
        for line in traceback.format_stack():
            sys.stderr.write(line)


@dataclass(frozen=True, repr=True)
class ExitHandler:
    sink: Writeable

    def __call__(self):
        self.sink.write(f"~~EXIT~~")
        traceback.print_stack(file=sys.stderr)
        for line in traceback.format_stack():
            self.sink.write(line)


class SystemTools(BaseTools):
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
