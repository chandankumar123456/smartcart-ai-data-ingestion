import asyncio
import time
from collections import defaultdict


class TokenBucketRateLimiter:
    """Per-domain token bucket rate limiter."""

    def __init__(self, requests_per_second: float = 1.0):
        self.requests_per_second = requests_per_second
        self._buckets: dict[str, dict] = defaultdict(lambda: {"tokens": 1.0, "last_refill_time": time.monotonic()})
        self._lock = asyncio.Lock()

    async def acquire(self, domain: str) -> None:
        async with self._lock:
            bucket = self._buckets[domain]
            now = time.monotonic()
            elapsed = now - bucket["last_refill_time"]
            bucket["tokens"] = min(1.0, bucket["tokens"] + elapsed * self.requests_per_second)
            bucket["last_refill_time"] = now

            if bucket["tokens"] < 1.0:
                wait_time = (1.0 - bucket["tokens"]) / self.requests_per_second
                await asyncio.sleep(wait_time)
                bucket["tokens"] = 0.0
            else:
                bucket["tokens"] -= 1.0
