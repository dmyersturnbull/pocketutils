import time
import random
from typing import Optional, Callable, Mapping
from urllib import request


def download_urllib(req: request.Request) -> bytes:
    with request.urlopen(req) as q:
        return q.read()


class QueryExecutor:
    """
    A synchronous GET/POST query executor that limits the rate of requests.
    """

    def __init__(
        self,
        sec_delay_min: float = 0.25,
        sec_delay_max: float = 0.25,
        encoding: Optional[str] = "utf-8",
        querier: Optional[Callable[[request.Request], bytes]] = None,
    ):
        self._min = sec_delay_min
        self._max = sec_delay_max
        self._rand = random.Random()  # nosec
        self._encoding = encoding
        self._next_at = 0
        self._querier = download_urllib if querier is None else querier

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
        if now < self._next_at:
            time.sleep(self._next_at - now)
        req = request.Request(url=url, method=method, headers=headers)
        content = self._querier(req)
        if encoding is None:
            data = content.decode(errors=errors)
        else:
            data = content.decode(encoding=encoding, errors=errors)
        self._next_at = time.monotonic() + self._rand.uniform(self._min, self._max)
        return data


__all__ = ["QueryExecutor"]
