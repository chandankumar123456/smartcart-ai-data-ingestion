import asyncio
import random
from urllib.parse import urlparse

import httpx

from utils.logger import logger
from utils.rate_limiter import TokenBucketRateLimiter

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

_rate_limiter = TokenBucketRateLimiter(requests_per_second=1.0)


def _get_domain(url: str) -> str:
    return urlparse(url).netloc


async def fetch(
    url: str,
    headers: dict | None = None,
    retries: int = 3,
    backoff: float = 1.0,
    timeout: float = 30.0,
) -> dict | list | None:
    """Fetch a URL with rotating user agents, exponential backoff, and rate limiting."""
    domain = _get_domain(url)

    merged_headers = {"User-Agent": random.choice(USER_AGENTS)}
    if headers:
        merged_headers.update(headers)

    last_error: Exception | None = None
    for attempt in range(retries):
        await _rate_limiter.acquire(domain)
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=merged_headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            last_error = exc
            logger.warning(f"HTTP {exc.response.status_code} on {url} (attempt {attempt + 1}/{retries})")
            if exc.response.status_code in (429, 503):
                await asyncio.sleep(backoff * (2**attempt))
            else:
                break
        except Exception as exc:
            last_error = exc
            logger.warning(f"Request error on {url} (attempt {attempt + 1}/{retries}): {exc}")
            await asyncio.sleep(backoff * (2**attempt))

    logger.error(f"All {retries} attempts failed for {url}: {last_error}")
    return None
