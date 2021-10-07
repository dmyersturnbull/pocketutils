import itertools
import logging
import multiprocessing
import time
import warnings
from datetime import datetime
from typing import (
    Any,
    Callable,
    Collection,
    Generator,
    Iterable,
    Iterator,
    Optional,
    TypeVar,
    Union,
)

from pocketutils.tools.base_tools import BaseTools
from pocketutils.tools.unit_tools import UnitTools

logger = logging.getLogger("pocketutils")
T = TypeVar("T")
K = TypeVar("K", covariant=True)
V = TypeVar("V", contravariant=True)


class LoopTools(BaseTools):
    @classmethod
    def loop(
        cls,
        things: Iterable[T],
        *,
        log: Union[None, str, Callable[[str], Any]] = None,
        every_i: int = 10,
        n_total: Optional[int] = None,
    ) -> Generator[T, None, None]:
        """
        Loops over elements while logging time taken, % processed, etc.

        Args:
            things: Items to process; if sized or ``n_total`` is passed,
                    will log estimates and % complete
            log: Write by calling this function.
                 The returned value is ignored.
                 if ``str``, gets a function from python logging
                 (via :attr:`pocketutils.tools.loop_tools.logger`);
                 see :meth:`get_log_function`.
                 If ``None``, does not log.
            every_i: Log after every ``every_i`` items processed
            n_total: Provide if ``things`` is not sized yet the total number
                     of items is known
        """
        log = cls.get_log_function(log)
        if hasattr(things, "__len__") or n_total is not None:
            # noinspection PyTypeChecker
            yield from cls._loop_timing(things, log, every_i, n_total)
        else:
            yield from cls._loop_logging(things, log, every_i)

    @classmethod
    def parallel(
        cls,
        items: Collection[K],
        function: Callable[[K], V],
        *,
        to=print,
        n_cores: int = 2,
        poll_sec: float = 0.4,
    ) -> None:
        """
        Process items with multiprocessing and a rotating cursor with % complete.

        Args:
            items: Items to process; must have ``__len__`` defined
            function: Called per item
            to: Write (log) to this function; ``end="\r"`` is passed for the cursor
            n_cores: The number pool cores
            poll_sec: Check for new every ``poll_sec`` seconds
        """
        t0 = time.monotonic()
        if to is not None:
            to(f"Using {n_cores} cores...")
        with multiprocessing.Pool(n_cores) as pool:
            queue = multiprocessing.Manager().Queue()
            result = pool.starmap_async(function, items)
            cycler = itertools.cycle(r"\|/―")
            while not result.ready():
                percent = queue.qsize() / len(items)
                if to is not None:
                    to(f"% complete: {percent:.0%} {next(cycler)}", end="\r")
                time.sleep(poll_sec)
            got = result.get()
        delta = UnitTools.delta_time_to_str(time.monotonic() - t0)
        if to is not None:
            to(f"\nProcessed {len(got)} items in {delta}")

    @classmethod
    def _loop_logging(
        cls,
        things: Iterable[T],
        log: Union[None, str, Callable[[str], None]] = None,
        every_i: int = 10,
    ) -> Iterator[T]:
        log = cls.get_log_function(log)
        initial_start_time = time.monotonic()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log(f"Started processing at {now}.")
        i = 0
        for i, thing in enumerate(things):
            t0 = time.monotonic()
            yield thing
            t1 = time.monotonic()
            if i % every_i == 0 and i > 0:
                elapsed_s = UnitTools.delta_time_to_str(t1 - t0)
                log(f"Processed next {every_i} in {elapsed_s}")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        delta = UnitTools.delta_time_to_str(time.monotonic() - initial_start_time)
        log(f"Processed {i}/{i} in {delta}. Done at {now}.")

    @classmethod
    def _loop_timing(
        cls,
        things: Collection[Any],
        log: Union[None, str, Callable[[str], None]] = None,
        every_i: int = 10,
        n_total: Optional[int] = None,
    ):
        log = cls.get_log_function(log)
        n_total = len(things) if n_total is None else n_total
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log(f"Started processing {n_total} items at {now}.")
        t0 = time.monotonic()
        initial_start_time = time.monotonic()
        for i, thing in enumerate(things):
            yield thing
            t1 = time.monotonic()
            if i % every_i == 0 and i < n_total - 1:
                estimate = (t1 - initial_start_time) / (i + 1) * (n_total - i - 1)
                elapsed_s = UnitTools.delta_time_to_str(t1 - t0)
                estimate_s = UnitTools.delta_time_to_str(estimate)
                log(f"Processed {i+1}/{n_total} in {elapsed_s}. Estimated {estimate_s} left.")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        delta = UnitTools.delta_time_to_str(time.monotonic() - initial_start_time)
        log(f"Processed {n_total}/{n_total} in {delta}. Done at {now}.")


__all__ = ["LoopTools"]
