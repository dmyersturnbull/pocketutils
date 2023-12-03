# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0

import contextlib
import logging
import subprocess  # nosec
from collections.abc import Callable, Generator, Mapping, Sequence
from copy import copy
from dataclasses import dataclass
from pathlib import PurePath
from queue import Queue
from subprocess import CalledProcessError, CompletedProcess
from threading import Thread
from typing import IO, Any, AnyStr, Self, Unpack

from pocketutils.core.input_output import DevNull

__all__ = ["CallUtils", "CallTools"]

logger = logging.getLogger("pocketutils")


@contextlib.contextmanager
def null_context():
    yield


@dataclass(slots=True, frozen=True)
class CallUtils:
    @contextlib.contextmanager
    def silenced(self: Self, no_stdout: bool = True, no_stderr: bool = True) -> Generator[None, None, None]:
        """
        Context manager that suppresses stdout and stderr.
        """
        # noinspection PyTypeChecker
        with contextlib.redirect_stdout(DevNull()) if no_stdout else null_context():
            # noinspection PyTypeChecker
            with contextlib.redirect_stderr(DevNull()) if no_stderr else null_context():
                yield

    def call_cmd_utf(
        self: Self,
        *cmd: str,
        log_fn: Callable[[str], Any] | None = logger.debug,
        **kwargs: Unpack[Mapping[str, Any]],
    ) -> CompletedProcess:
        """
        Like `call_cmd` for utf-8 only.
        Set `text=True` and `encoding=utf-8`,
        and strips stdout and stderr of start/end whitespace before returning.
        Can also log formatted stdout and stderr on failure.
        Otherwise, logs the output, unformatted and unstripped, as DEBUG

        See Also:
            `subprocess.check_output`, which only returns stdout
        """
        log_fn("Calling '{}'".format(" ".join(cmd)))
        kwargs = copy(kwargs)
        if "cwd" in kwargs and isinstance(kwargs["path"], PurePath):
            kwargs["cwd"] = str(kwargs["cwd"])
        calling = dict(
            *[str(c) for c in cmd],
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
            **kwargs,
        )
        x = subprocess.run(**calling)  # nosec
        log_fn(f"stdout: '{x.stdout}'")
        log_fn(f"stderr: '{x.stderr}'")
        x.stdout = x.stdout.strip()
        x.stderr = x.stderr.strip()
        return x

    def log_called_process_error(self: Self, e: CalledProcessError, *, log_fn: Callable[[str], None]) -> None:
        """
        Outputs some formatted text describing the error with its full stdout and stderr.

        Args:
            e: The error
            log_fn: For example, `logger.warning`
        """
        log_fn(f'Failed on command: {" ".join(e.cmd)}')
        out = None
        if e.stdout is not None:
            out = e.stdout.decode(encoding="utf-8") if isinstance(e.stdout, bytes) else e.stdout
        log_fn("<no stdout>" if out is None else f"stdout: {out}")
        err = None
        if e.stderr is not None:
            err = e.stderr.decode(encoding="utf-8") if isinstance(e.stderr, bytes) else e.stderr
        log_fn("<no stderr>" if err is None else f"stderr: {err}")

    def stream_cmd_call(
        self: Self,
        cmd: Sequence[str],
        *,
        callback: Callable[[bool, bytes], None] | None = None,
        timeout_secs: float | None = None,
        **kwargs: Unpack[Mapping[str, Any]],
    ) -> None:
        """
        Processes stdout and stderr on separate threads.
        Streamed -- can avoid filling a stdout or stderr buffer.
        Calls an external command, waits, and throws a
        ExternalCommandFailed for nonzero exit codes.

        Args:
            cmd: The command args
            callback: A function that processes (is_stderr, piped line).
                      If `None`, uses :meth:`smart_log`.
            timeout_secs: Max seconds to wait for the next line
            kwargs: Passed to `subprocess.Popen`; do not pass `stdout` or `stderr`.

        Raises:
            CalledProcessError: If the exit code is nonzero
        """
        if callback is None:
            callback = self.smart_log
        cmd = [str(p) for p in cmd]
        logger.debug("Streaming '{}'".format(" ".join(cmd)))
        calling = dict(stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
        p = subprocess.Popen(cmd, **calling)  # nosec
        try:
            q = Queue()
            Thread(target=self._reader, args=[False, p.stdout, q]).start()
            Thread(target=self._reader, args=[True, p.stderr, q]).start()
            for _ in range(2):
                for source, line in iter(q.get, None):
                    callback(source, line)
            exit_code = p.wait(timeout=timeout_secs)
        finally:
            p.kill()
        if exit_code != 0:
            raise CalledProcessError(exit_code, " ".join(cmd), "<unknown>", "<unknown>")

    def smart_log(
        self: Self,
        is_stderr: bool,
        line: bytes,
        *,
        prefix: str = "",
        log: logging.Logger = logger,
    ) -> None:
        """
        Maps (is_stderr, piped line) pairs to logging statements.
        The data must be utf-8-encoded.
        If the line starts with `warning:` (case-insensitive), uses `log.warning`.
        The same is true for any other method attached to `log`.
        Falls back to DEBUG if no valid prefix is found.
        This is useful if you wrote an external application (e.g. in C)
        and want those logging statements mapped into your calling Python code.
        """
        line = line.decode("utf-8")
        try:
            fn = getattr(log, line.split(":")[0].lower())
        except AttributeError:
            fn = log.debug
        source = "stderr" if is_stderr else "stdout"
        fn(f"{fn.__name__.upper()} [{source}]: {line}")
        if line.lower().startswith("FATAL:"):
            logger.fatal(prefix + line[6:])
        elif line.startswith("ERROR:"):
            logger.error(prefix + line[6:])
        elif line.startswith("WARNING:"):
            logger.warning(prefix + line[8:])
        elif line.startswith("INFO:"):
            logger.info(prefix + line[5:])
        elif line.startswith("DEBUG:"):
            logger.debug(prefix + line[6:])
        else:
            logger.debug(prefix + line)

    def _reader(self: Self, is_stderr: bool, pipe: IO[AnyStr], queue: Queue):
        try:
            with pipe:
                for line in iter(pipe.readline, b""):
                    queue.put((is_stderr, line))
        finally:
            queue.put(None)


CallTools = CallUtils()
