import asyncio
import tempfile
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

from httpx import AsyncClient, Response
from orjson import orjson


@dataclass(frozen=True, slots=True, kw_only=True)
class PollingRestDownloader:
    """
    For example:

    ``python
        return client.post(
            url,
            params=params,
            data=data,
            files=files,
            timeout=self.timeout_sec,
            follow_redirects=True,
        )
    ``
    """

    post: Callable[[AsyncClient], Awaitable[Response]]
    get: Callable[[AsyncClient, dict[str, str | list[str] | dict[str]]], Awaitable[Response]]
    initial_wait_sec: float = 20
    subsequent_wait_sec: float = 5
    max_wait_sec: float = 120

    def _get(self: Self, client: AsyncClient, data: dict[str, Any]) -> Awaitable[Response]:
        raise NotImplementedError()

    async def __call__(self: Self) -> dict:
        async with AsyncClient(http2=True) as client:
            response = await self.post(client)
            response.raise_for_status()
            data = orjson.loads(response.text)
            response = None
            t0 = time.monotonic()
            while response is None or response.status_code != 200:
                if time.monotonic() - t0 > self.max_wait_sec:
                    raise TimeoutError()
                await asyncio.sleep(self.subsequent_wait_sec if response else self.initial_wait_sec)
                response = await self.get(client, data)
                if response.status_code not in {200, 404}:
                    response.raise_for_status()
        return orjson.loads(response)


@dataclass(frozen=True, slots=True)
class FileStreamer:
    async def __call__(self: Self, url: str, path: Path) -> None:
        with tempfile.NamedTemporaryFile(dir=path.parent) as download_file:
            async with AsyncClient(http2=True) as client, client.stream(url) as response:
                for chunk in response.iter_bytes():
                    download_file.write(chunk)
                    await asyncio.sleep(0)
            Path(download_file.name).rename(path)


@dataclass(frozen=True, slots=True)
class RichFileStreamer:
    async def __call__(self: Self, url: str, path: Path) -> None:
        import rich.progress

        with tempfile.NamedTemporaryFile(dir=path.parent) as download_file:
            async with AsyncClient(http2=True) as client, client.stream(url) as response:
                total = int(response.headers["Content-Length"])
                with rich.progress.Progress(
                    "[progress.percentage]{task.percentage:>3.0f}%",
                    rich.progress.BarColumn(bar_width=None),
                    rich.progress.DownloadColumn(),
                    rich.progress.TransferSpeedColumn(),
                ) as progress:
                    download_task = progress.add_task("Download", total=total)
                    for chunk in response.iter_bytes():
                        download_file.write(chunk)
                        progress.update(download_task, completed=response.num_bytes_downloaded)
                        await asyncio.sleep(0)
            Path(download_file.name).rename(path)


__all__ = ["PollingRestDownloader", "FileStreamer", "RichFileStreamer"]
