"""AI provider health and status endpoints — System Admin only.

GET /api/v1/providers/health  — concurrent health check of all configured providers
GET /api/v1/providers/status  — synchronous configuration snapshot (no HTTP probes)

Both endpoints are restricted to SYSTEM_ADMIN. All other roles receive HTTP 403.
The ProviderManager fallback logic continues to operate internally for all AI users
regardless of whether they can access these monitoring endpoints.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.ai_providers.manager import get_provider_manager
from app.dependencies import AdminRequired

router = APIRouter(prefix="/providers", tags=["AI Providers"])


@router.get(
    "/health",
    summary="AI provider health check (System Admin only)",
    description=(
        "Runs a lightweight probe against every configured AI provider concurrently "
        "and returns latency and status for each. Restricted to System Admin."
    ),
    response_model=dict[str, Any],
)
async def provider_health(
    _: Any = Depends(AdminRequired),
) -> dict[str, Any]:
    """Probe all configured providers and return health results."""
    manager = get_provider_manager()
    health = await manager.health_check_all()
    all_ok = all(v.get("status") == "ok" for v in health.values())
    return {
        "overall": "healthy" if all_ok else "degraded",
        "providers": health,
    }


@router.get(
    "/status",
    summary="AI provider configuration status (System Admin only)",
    description=(
        "Returns the active provider, model, fallback chain, and temperature/token settings "
        "without making any external HTTP calls. Restricted to System Admin."
    ),
    response_model=dict[str, Any],
)
async def provider_status(
    _: Any = Depends(AdminRequired),
) -> dict[str, Any]:
    """Return current provider configuration without probing external endpoints."""
    manager = get_provider_manager()
    return manager.get_status()
