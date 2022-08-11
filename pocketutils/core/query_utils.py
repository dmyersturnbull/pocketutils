import logging
import random
import time
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, ByteString, Callable, Mapping, Optional
from urllib import request

logger = logging.getLogger("pocketutils")


def download_urllib(req: request.Request) -> bytes:
    with request.urlopen(req) as q:
        return q.read()


@dataclass(frozen=True, repr=True, order=True)
class TimeTaken:
    query: timedelta
    wait: timedelta


class QueryExecutor:
    """
    A synchronous GET/POST query executor that limits the rate of requests.
    """

    def __init__(
        self,
        sec_delay_min: float = 0.25,
        sec_delay_max: float = 0.25,
        encoding: Optional[str] = "utf-8",
        querier: Optional[Callable[[request.Request], ByteString]] = None,
    ):
        self._min = sec_delay_min
        self._max = sec_delay_max
        self._rand = random.Random()  # nosec
        self._encoding = encoding
        self._next_at = 0
        self._querier = download_urllib if querier is None else querier
        self._time_taken = None

    @property
    def last_time_taken(self) -> TimeTaken:
        return self._time_taken

    def __call__(
        self,
        url: str,
        method: str = "get",
        encoding: Optional[str] = "-1",
        headers: Optional[Mapping[str, str]] = None,
        errors: str = "ignore",
    ) -> str:
        headers = {} if headers is None else headers
        encoding = self._encoding if encoding == "-1" else encoding
        now = time.monotonic()
        wait_secs = self._next_at - now
        if now < self._next_at:
            time.sleep(wait_secs)
        now = time.monotonic()
        req = request.Request(url=url, method=method, headers=headers)
        content = self._querier(req)
        if encoding is None:
            data = content.decode(errors=errors)
        else:
            data = content.decode(encoding=encoding, errors=errors)
        now_ = time.monotonic()
        self._time_taken = TimeTaken(timedelta(seconds=wait_secs), timedelta(seconds=now_ - now))
        self._next_at = now_ + self._rand.uniform(self._min, self._max)
        return data


class QueryMixin:
    @property
    def executor(self) -> QueryExecutor:
        raise NotImplementedError()

    def _query(self, url: str, *, sink: Callable[[str], Any] = logger.debug) -> str:
        data = self.executor(url)
        tt = self.executor.last_time_taken
        wt, qt = tt.wait.total_seconds(), tt.query.total_seconds()
        bts = int(len(data) * 8 / 1024)
        sink(f"Queried {bts} kb from {url} in {qt:.1} s with {wt:.1} s of wait")
        return data


__all__ = ["QueryExecutor", "TimeTaken", "QueryMixin"]
