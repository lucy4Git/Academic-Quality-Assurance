"""JWT deny-list backed by Redis.

When a user logs out, the token's `jti` (JWT ID) claim is added to Redis
with a TTL equal to the token's remaining lifetime. Subsequent requests
with the same token are rejected before reaching any route handler.

E0-OD-002: Tokens are stored as opaque identifiers (jti) only — the full
JWT string is never stored in Redis.
"""

from __future__ import annotations

import time

from app.core.logging import get_logger
from app.core.redis_client import get_redis

logger = get_logger(__name__)

_DENY_LIST_PREFIX = "aqaa:jwt:deny:"


async def add_to_deny_list(jti: str, expires_at: int) -> None:
    """Blocklist a token by its JTI until its natural expiry.

    Args:
        jti: JWT ID claim from the token being revoked.
        expires_at: Unix timestamp when the token expires (from `exp` claim).
    """
    ttl = max(1, int(expires_at - time.time()))
    client = await get_redis()
    await client.setex(f"{_DENY_LIST_PREFIX}{jti}", ttl, "1")
    logger.info("token_revoked", jti=jti[:8] + "…", ttl_seconds=ttl)


async def is_token_denied(jti: str) -> bool:
    """Return True if the token has been explicitly revoked."""
    client = await get_redis()
    result = await client.exists(f"{_DENY_LIST_PREFIX}{jti}")
    return bool(result)
