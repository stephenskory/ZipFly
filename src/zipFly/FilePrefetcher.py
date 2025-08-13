import asyncio
from typing import List, Optional, AsyncGenerator

class FilePrefetcher:
    def __init__(self, files: List, prefetch_files: int = 20, queue_maxsize: int = 2):
        self.files = files
        self.prefetch_files = prefetch_files
        self.queue_maxsize = queue_maxsize

        self.n = len(files)
        self.prefetchers: List[Optional[_SingleFilePrefetch]] = [None] * self.n

        self.inflight = 0
        self.next_to_start = 0

    async def _start_prefetch(self, idx: int):
        pf = _SingleFilePrefetch(self.files[idx], self.queue_maxsize)
        self.prefetchers[idx] = pf
        await pf.start()
        self.inflight += 1
        self.next_to_start = max(self.next_to_start, idx + 1)

    async def ensure_prefetch(self, idx: int):
        """Ensure the prefetcher for file `idx` is started, refill window as needed."""
        if self.prefetchers[idx] is None:
            await self._start_prefetch(idx)

        # Refill window
        while self.next_to_start < self.n and self.inflight < self.prefetch_files:
            await self._start_prefetch(self.next_to_start)

    async def stream_file_data(self, idx: int) -> AsyncGenerator[bytes, None]:
        """Yields chunks of a single file in order, managing prefetch completion."""
        pf = self.prefetchers[idx]
        while True:
            chunk = await pf.queue.get()
            if chunk is None:
                if pf.task:
                    await pf.task
                    pf.task = None
                self.inflight -= 1

                # keep window full
                while self.next_to_start < self.n and self.inflight < self.prefetch_files:
                    await self._start_prefetch(self.next_to_start)
                break
            yield chunk


class _SingleFilePrefetch:
    """Handles a single file's async queue and task."""

    def __init__(self, file, queue_maxsize: int = 2):
        self.file = file
        self.queue = asyncio.Queue(maxsize=queue_maxsize)
        self.task: Optional[asyncio.Task] = None

    async def start(self):
        self.task = asyncio.create_task(self._prefetch())

    async def _prefetch(self):
        agen = self.file.async_generate_processed_file_data()
        try:
            async for chunk in agen:
                await self.queue.put(chunk)
        except (GeneratorExit, asyncio.CancelledError):
            await agen.aclose()
            raise
        except Exception:
            await self.queue.put(None)
            raise
        else:
            await self.queue.put(None)
