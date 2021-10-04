import contextlib
import logging
import os
import subprocess  # nosec
import textwrap
import warnings
from copy import copy
from enum import Enum
from pathlib import PurePath
from queue import Queue
from threading import Thread
from typing import Callable, Generator, Optional, Sequence

from pocketutils.core.input_output import DevNull
from pocketutils.tools.base_tools import BaseTools

logger = logging.getLogger("pocketutils")


@contextlib.contextmanager
def null_context(cls):
    yield


class CallTools(BaseTools):
    @classmethod
    @contextlib.contextmanager
    def silenced(
        cls, no_stdout: bool = True, no_stderr: bool = True
    ) -> Generator[None, None, None]:
        """
        Context manager that suppresses stdout and stderr.
        """
        # noinspection PyTypeChecker
        with contextlib.redirect_stdout(DevNull()) if no_stdout else cls.null_context():
            # noinspection PyTypeChecker
            with contextlib.redirect_stderr(DevNull()) if no_stderr else cls.null_context():
                yield

    @classmethod
    def call_cmd(cls, *cmd: str, **kwargs) -> subprocess.CompletedProcess:
        """
        Calls subprocess.run with capture_output=True.
        Logs a debug statement with the command beforehand.
            cmd: A sequence to call
            kwargs: Passed to subprocess.run
        """
        warnings.warn("call_cmd will be removed; use subprocess.check_output instead")
        logger.debug("Calling '{}'".format(" ".join(cmd)))
        return subprocess.run(*[str(c) for c in cmd], capture_output=True, check=True, **kwargs)

    @classmethod
    def call_cmd_utf(
        cls, *cmd: str, log: logging.Logger = logger, **kwargs
    ) -> subprocess.CompletedProcess:
        """
        Like ``call_cmd`` for utf-8 only.
        Set ``text=True`` and ``encoding=utf8``,
        and strips stdout and stderr of start/end whitespace before returning.
        Can also log formatted stdout and stderr on failure.
        Otherwise, logs the output, unformatted and unstripped, as DEBUG

        See Also:
            ``subprocess.check_output``, which only returns stdout
        """
        log.debug("Calling '{}'".format(" ".join(cmd)))
        kwargs = copy(kwargs)
        if "cwd" in kwargs and isinstance(kwargs["path"], PurePath):
            kwargs["cwd"] = str(kwargs["cwd"])
        try:
            x = subprocess.run(
                *[str(c) for c in cmd],
                capture_output=True,
                check=True,
                text=True,
                encoding="utf8",
                **kwargs,
            )
            log.debug(f"stdout: '{x.stdout}'")
            log.debug(f"stderr: '{x.stderr}'")
            x.stdout = x.stdout.strip()
            x.stderr = x.stderr.strip()
            return x
        except subprocess.CalledProcessError as e:
            cls.log_called_process_error(e, log_fn=log.error)
            raise

    @classmethod
    def log_called_process_error(
        cls,
        e: subprocess.CalledProcessError,
        *,
        log_fn: Callable[[str], None],
    ) -> None:
        """
        Outputs some formatted text describing the error with its full stdout and stderr.

        Args:
            e: The error
            log_fn: For example, ``logger.warning``
        """
        log_fn(f'Failed on command: {" ".join(e.cmd)}')
        out = None
        if e.stdout is not None:
            out = e.stdout.decode(encoding="utf8") if isinstance(e.stdout, bytes) else e.stdout
        log_fn("《no stdout》" if out is None else f"stdout: {out}")
        err = None
        if e.stderr is not None:
            err = e.stderr.decode(encoding="utf8") if isinstance(e.stderr, bytes) else e.stderr
        log_fn("《no stderr》" if err is None else f"stderr: {err}")

    @classmethod
    def stream_cmd_call(
        cls,
        cmd: Sequence[str],
        *,
        callback: Callable[[bool, bytes], None] = None,
        timeout_secs: Optional[float] = None,
        **kwargs,
    ) -> None:
        """
        Processes stdout and stderr on separate threads.
        Streamed -- can avoid filling a stdout or stderr buffer.
        Calls an external command, waits, and throws a
        ExternalCommandFailed for nonzero exit codes.

        Args:
            cmd: The command args
            callback: A function that processes (is_stderr, piped line).
                      If ``None``, uses :meth:`smart_log`.
            timeout_secs: Max seconds to wait for the next line
            kwargs: Passed to ``subprocess.Popen``; do not pass ``stdout`` or ``stderr``.

        Raises:
            CalledProcessError: If the exit code is nonzero
        """
        if callback is None:
            callback = cls.smart_log
        cmd = [str(p) for p in cmd]
        logger.debug("Streaming '{}'".format(" ".join(cmd)))
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
        try:
            q = Queue()
            Thread(target=cls._reader, args=[False, p.stdout, q]).start()
            Thread(target=cls._reader, args=[True, p.stderr, q]).start()
            for _ in range(2):
                for source, line in iter(q.get, None):
                    callback(source, line)
            exit_code = p.wait(timeout=timeout_secs)
        finally:
            p.kill()
        if exit_code != 0:
            raise subprocess.CalledProcessError(
                exit_code, " ".join(cmd), "<<unknown>>", "<<unknown>>"
            )

    @classmethod
    def smart_log(
        cls,
        is_stderr: bool,
        line: bytes,
        *,
        prefix: str = "",
        log: logging.Logger = logger,
    ) -> None:
        """
        Maps (is_stderr, piped line) pairs to logging statements.
        The data must be utf8-encoded.
        If the line starts with ``warning:`` (case-insensitive), uses ``log.warning``.
        The same is true for any other method attached to ``log``.
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
            logger.fatal(prefix + line)
        elif line.startswith("ERROR:"):
            logger.error(prefix + line)
        elif line.startswith("WARNING:"):
            logger.warning(prefix + line)
        elif line.startswith("INFO:"):
            logger.info(prefix + line)
        elif line.startswith("DEBUG:"):
            logger.debug(prefix + line)
        else:
            logger.debug(prefix + line)

    @classmethod
    def _disp(cls, out, ell, name):
        out = out.strip()
        if "\n" in out:
            ell(name + ":\n<<=====\n" + out + "\n=====>>")
        elif len(out) > 0:
            ell(name + ": <<===== " + out + " =====>>")
        else:
            ell(name + ": <no output>")

    @classmethod
    def _log(cls, out, err, ell):
        cls._disp(out, ell, "stdout")
        cls._disp(err, ell, "stderr")

    @classmethod
    def _reader(cls, pipe_type, pipe, queue):
        try:
            with pipe:
                for line in iter(pipe.readline, b""):
                    queue.put((pipe_type, line))
        finally:
            queue.put(None)

    @classmethod
    def _wrap(cls, s: str, ell: int) -> str:
        wrapped = textwrap.wrap(s.strip(), ell - 4)
        return textwrap.indent(os.linesep.join(wrapped), "    ")


__all__ = ["CallTools"]
