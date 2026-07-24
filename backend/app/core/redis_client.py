"""Async Redis client singleton.

Used by: JWT deny-list, rate limiting state, ARQ background task queue.
Connection is created lazily on first use and shared across requests.
"""

from __future__ import annotations

import redis.asyncio as aioredis

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Return the shared async Redis client, creating it on first call."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        logger.info("redis_client_created", url=settings.REDIS_URL.split("@")[-1])
    return _redis_client


async def close_redis() -> None:
    """Close the shared Redis connection (called on application shutdown)."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("redis_client_closed")


async def check_redis_health() -> bool:
    """Ping Redis and return True if reachable."""
    try:
        client = await get_redis()
        return await client.ping()
    except Exception:
        return False
