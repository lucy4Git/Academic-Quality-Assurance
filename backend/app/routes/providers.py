"""AI provider health and status endpoints.

GET /api/v1/providers/health  — concurrent health check of all configured providers
GET /api/v1/providers/status  — synchronous configuration snapshot (no HTTP probes)

Both endpoints require authentication. Health is QA-officer+ only;
status is available to all authenticated users.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.ai_providers.manager import get_provider_manager
from app.dependencies import AnyAuthenticatedUser, QAOfficerRequired

router = APIRouter(prefix="/providers", tags=["AI Providers"])


@router.get(
    "/health",
    summary="AI provider health check",
    description=(
        "Runs a lightweight probe against every configured AI provider concurrently "
        "and returns latency and status for each. Requires QA Officer role or above."
    ),
    response_model=dict[str, Any],
)
async def provider_health(
    _: Any = Depends(QAOfficerRequired),
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
    summary="AI provider configuration status",
    description=(
        "Returns the active provider, model, fallback chain, and temperature/token settings "
        "without making any external HTTP calls. Available to all authenticated users."
    ),
    response_model=dict[str, Any],
)
async def provider_status(
    _: Any = Depends(AnyAuthenticatedUser),
) -> dict[str, Any]:
    """Return current provider configuration without probing external endpoints."""
    manager = get_provider_manager()
    return manager.get_status()
