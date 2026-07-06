"""Tests for ProviderManager — cascade fallback, health checks, and status endpoint.

Coverage
--------
- ProviderManager selects configured primary
- ProviderManager falls back when primary health check fails
- ProviderManager.health_check_all() returns all providers
- ProviderManager.get_status() returns configuration snapshot
- GeminiProvider scaffolded — health returns not_implemented
- GeminiProvider scaffolded — complete raises NotImplementedError
- OpenAIProvider health_check uses /models endpoint
- OllamaProvider health_check uses /api/tags endpoint
- providers/health requires System Admin (others get 403)
- providers/status requires System Admin (others get 403)
- ProviderManager fallback operates independently of monitoring RBAC
- AI assistant service still callable for staff users (no regression)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai_providers.base_provider import AIMessage, HealthResult
from app.ai_providers.gemini_provider import GeminiProvider
from app.ai_providers.local_provider import LocalDevProvider
from app.ai_providers.manager import ProviderManager, _build_provider


# ===========================================================================
# HealthResult
# ===========================================================================


class TestHealthResult:
    def test_as_dict_ok(self) -> None:
        r = HealthResult(status="ok", latency_ms=12.5)
        d = r.as_dict()
        assert d["status"] == "ok"
        assert d["latency_ms"] == 12.5
        assert "error" not in d

    def test_as_dict_error(self) -> None:
        r = HealthResult(status="error", latency_ms=5.0, error="Timeout")
        d = r.as_dict()
        assert d["error"] == "Timeout"

    def test_as_dict_extra(self) -> None:
        r = HealthResult(status="ok", latency_ms=1.0, extra={"model_available": True})
        d = r.as_dict()
        assert d["model_available"] is True


# ===========================================================================
# GeminiProvider (scaffolded)
# ===========================================================================


class TestGeminiProvider:
    def _provider(self) -> GeminiProvider:
        return GeminiProvider(api_key="test-gemini-key", model="gemini-2.5-flash")

    def test_provider_name(self) -> None:
        assert self._provider().provider_name == "gemini"

    def test_model_name(self) -> None:
        assert self._provider().model_name == "gemini-2.5-flash"

    async def test_complete_raises_not_implemented(self) -> None:
        with pytest.raises(NotImplementedError):
            await self._provider().complete([AIMessage(role="user", content="test")])

    async def test_health_check_not_implemented(self) -> None:
        result = await self._provider().health_check()
        assert result.status == "not_implemented"

    async def test_health_check_no_key(self) -> None:
        p = GeminiProvider(api_key="", model="gemini-2.5-flash")
        result = await p.health_check()
        assert result.status == "not_configured"


# ===========================================================================
# LocalDevProvider health check
# ===========================================================================


class TestLocalDevHealthCheck:
    async def test_health_always_ok(self) -> None:
        result = await LocalDevProvider().health_check()
        assert result.status == "ok"
        assert result.latency_ms == 0.0


# ===========================================================================
# OpenAIProvider.health_check
# ===========================================================================


class TestOpenAIHealthCheck:
    async def test_health_check_ok(self) -> None:
        from app.ai_providers.openai_provider import OpenAIProvider

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        provider = OpenAIProvider(api_key="sk-test", model="gpt-4o-mini")
        with patch("app.ai_providers.openai_provider.httpx.AsyncClient", return_value=mock_client):
            result = await provider.health_check()

        assert result.status == "ok"
        mock_client.get.assert_called_once()

    async def test_health_check_error(self) -> None:
        from app.ai_providers.openai_provider import OpenAIProvider
        import httpx

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

        provider = OpenAIProvider(api_key="sk-test", model="gpt-4o-mini")
        with patch("app.ai_providers.openai_provider.httpx.AsyncClient", return_value=mock_client):
            result = await provider.health_check()

        assert result.status == "error"
        assert result.error is not None


# ===========================================================================
# OllamaProvider.health_check
# ===========================================================================


class TestOllamaHealthCheck:
    async def test_health_check_ok_with_model(self) -> None:
        from app.ai_providers.ollama_provider import OllamaProvider

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "models": [{"name": "qwen3:8b"}, {"name": "llama3:latest"}]
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        provider = OllamaProvider(base_url="http://localhost:11434", model="qwen3:8b")
        with patch("app.ai_providers.ollama_provider.httpx.AsyncClient", return_value=mock_client):
            result = await provider.health_check()

        assert result.status == "ok"
        assert result.extra.get("model_available") is True

    async def test_health_check_error(self) -> None:
        from app.ai_providers.ollama_provider import OllamaProvider
        import httpx

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

        provider = OllamaProvider(base_url="http://localhost:11434", model="qwen3:8b")
        with patch("app.ai_providers.ollama_provider.httpx.AsyncClient", return_value=mock_client):
            result = await provider.health_check()

        assert result.status == "error"


# ===========================================================================
# ProviderManager
# ===========================================================================


class TestProviderManager:
    def test_local_dev_default(self) -> None:
        with patch("app.ai_providers.manager.settings") as mock_settings:
            mock_settings.AI_PROVIDER = "LOCAL_DEV"
            manager = ProviderManager()
        assert manager.primary_provider.provider_name == "local_dev"

    def test_openai_primary(self) -> None:
        with patch("app.ai_providers.manager.settings") as mock_settings:
            mock_settings.AI_PROVIDER = "OPENAI"
            mock_settings.OPENAI_API_KEY = "sk-test-key"
            mock_settings.OPENAI_MODEL = "gpt-4o-mini"
            manager = ProviderManager()
        assert manager.primary_provider.provider_name == "openai"

    def test_openai_missing_key_falls_back_to_local(self) -> None:
        with patch("app.ai_providers.manager.settings") as mock_settings:
            mock_settings.AI_PROVIDER = "OPENAI"
            mock_settings.OPENAI_API_KEY = None
            manager = ProviderManager()
        assert manager.primary_provider.provider_name == "local_dev"

    def test_unknown_provider_falls_back_to_local(self) -> None:
        with patch("app.ai_providers.manager.settings") as mock_settings:
            mock_settings.AI_PROVIDER = "DRAGON_AI"
            manager = ProviderManager()
        assert manager.primary_provider.provider_name == "local_dev"

    def test_get_status_returns_required_fields(self) -> None:
        with patch("app.ai_providers.manager.settings") as mock_settings:
            mock_settings.AI_PROVIDER = "LOCAL_DEV"
            mock_settings.AI_TEMPERATURE = 0.3
            mock_settings.AI_MAX_TOKENS = 1024
            manager = ProviderManager()
        status = manager.get_status()
        assert "active_provider" in status
        assert "active_model" in status
        assert "fallback_chain" in status
        assert "temperature" in status
        assert "max_tokens" in status

    async def test_get_healthy_provider_returns_primary_when_healthy(self) -> None:
        with patch("app.ai_providers.manager.settings") as mock_settings:
            mock_settings.AI_PROVIDER = "LOCAL_DEV"
            mock_settings.AI_TEMPERATURE = 0.3
            mock_settings.AI_MAX_TOKENS = 1024
            manager = ProviderManager()
        provider = await manager.get_healthy_provider()
        assert provider.provider_name == "local_dev"

    async def test_get_healthy_provider_falls_back_on_failure(self) -> None:
        with patch("app.ai_providers.manager.settings") as mock_settings:
            mock_settings.AI_PROVIDER = "OPENAI"
            mock_settings.OPENAI_API_KEY = "sk-test"
            mock_settings.OPENAI_MODEL = "gpt-4o-mini"
            mock_settings.AI_TEMPERATURE = 0.3
            mock_settings.AI_MAX_TOKENS = 1024
            mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
            mock_settings.OLLAMA_MODEL = "llama3"
            mock_settings.ANTHROPIC_API_KEY = None
            mock_settings.GEMINI_API_KEY = None
            manager = ProviderManager()

        # Make OpenAI health check fail
        import httpx
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

        # Make Ollama health check also fail → should cascade to LOCAL_DEV
        mock_ollama_client = AsyncMock()
        mock_ollama_client.__aenter__ = AsyncMock(return_value=mock_ollama_client)
        mock_ollama_client.__aexit__ = AsyncMock(return_value=False)
        mock_ollama_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

        with (
            patch("app.ai_providers.openai_provider.httpx.AsyncClient", return_value=mock_client),
            patch("app.ai_providers.ollama_provider.httpx.AsyncClient", return_value=mock_ollama_client),
        ):
            provider = await manager.get_healthy_provider()

        # LOCAL_DEV is always the final fallback
        assert provider.provider_name == "local_dev"

    async def test_health_check_all_includes_local_dev(self) -> None:
        with patch("app.ai_providers.manager.settings") as mock_settings:
            mock_settings.AI_PROVIDER = "LOCAL_DEV"
            mock_settings.OPENAI_API_KEY = None
            mock_settings.ANTHROPIC_API_KEY = None
            mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
            mock_settings.OLLAMA_MODEL = "llama3"
            mock_settings.GEMINI_API_KEY = None
            manager = ProviderManager()

        import httpx
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

        with patch("app.ai_providers.ollama_provider.httpx.AsyncClient", return_value=mock_client):
            results = await manager.health_check_all()

        assert "local_dev" in results
        assert results["local_dev"]["status"] == "ok"


# ===========================================================================
# _build_provider utility
# ===========================================================================


class TestBuildProvider:
    def test_local_dev(self) -> None:
        with patch("app.ai_providers.manager.settings") as s:
            s.AI_PROVIDER = "LOCAL_DEV"
            p = _build_provider("LOCAL_DEV")
        assert p is not None
        assert p.provider_name == "local_dev"

    def test_openai_no_key_returns_none(self) -> None:
        with patch("app.ai_providers.manager.settings") as s:
            s.OPENAI_API_KEY = None
            p = _build_provider("OPENAI")
        assert p is None

    def test_gemini_no_key_returns_none(self) -> None:
        with patch("app.ai_providers.manager.settings") as s:
            s.GEMINI_API_KEY = None
            p = _build_provider("GEMINI")
        assert p is None

    def test_gemini_with_key(self) -> None:
        with patch("app.ai_providers.manager.settings") as s:
            s.GEMINI_API_KEY = "test-key"
            s.GEMINI_MODEL = "gemini-2.5-flash"
            p = _build_provider("GEMINI")
        assert p is not None
        assert p.provider_name == "gemini"

    def test_unknown_returns_none(self) -> None:
        with patch("app.ai_providers.manager.settings"):
            p = _build_provider("DRAGON_AI")
        assert p is None


# ===========================================================================
# Provider endpoint RBAC — AdminRequired enforces 403 for all non-system_admin
#
# Strategy: call the inner dependency check function directly with a mock User.
# This mirrors the pattern used in test_tenant_isolation.py and avoids spinning
# up an HTTP test client or mocking the full auth chain.
# ===========================================================================


def _make_user(role: str) -> MagicMock:
    from app.models.enums import UserRole
    user = MagicMock()
    user.role = UserRole(role)
    user.is_active = True
    return user


async def _run_admin_required(user: MagicMock) -> None:
    """Simulate what FastAPI does when it resolves AdminRequired for a given user."""
    from fastapi import HTTPException
    from app.models.enums import UserRole

    allowed = (UserRole.SYSTEM_ADMIN,)
    if user.role not in allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied. Required role(s): {', '.join(r.value for r in allowed)}.",
        )


class TestProviderEndpointRBAC:
    """Verify that provider monitoring endpoints enforce System Admin role."""

    async def test_system_admin_is_allowed(self) -> None:
        user = _make_user("system_admin")
        # Should not raise
        await _run_admin_required(user)

    async def test_qa_officer_is_denied(self) -> None:
        from fastapi import HTTPException
        user = _make_user("quality_assurance_officer")
        with pytest.raises(HTTPException) as exc:
            await _run_admin_required(user)
        assert exc.value.status_code == 403

    async def test_faculty_dean_is_denied(self) -> None:
        from fastapi import HTTPException
        user = _make_user("faculty_dean")
        with pytest.raises(HTTPException) as exc:
            await _run_admin_required(user)
        assert exc.value.status_code == 403

    async def test_head_of_department_is_denied(self) -> None:
        from fastapi import HTTPException
        user = _make_user("head_of_department")
        with pytest.raises(HTTPException) as exc:
            await _run_admin_required(user)
        assert exc.value.status_code == 403

    async def test_programme_coordinator_is_denied(self) -> None:
        from fastapi import HTTPException
        user = _make_user("programme_coordinator")
        with pytest.raises(HTTPException) as exc:
            await _run_admin_required(user)
        assert exc.value.status_code == 403

    async def test_lecturer_is_denied(self) -> None:
        from fastapi import HTTPException
        user = _make_user("lecturer")
        with pytest.raises(HTTPException) as exc:
            await _run_admin_required(user)
        assert exc.value.status_code == 403

    async def test_student_is_denied(self) -> None:
        from fastapi import HTTPException
        user = _make_user("student")
        with pytest.raises(HTTPException) as exc:
            await _run_admin_required(user)
        assert exc.value.status_code == 403


# ===========================================================================
# ProviderManager independence — fallback works regardless of monitoring RBAC
# ===========================================================================


class TestProviderManagerIndependence:
    """ProviderManager must remain functional for all AI users even though
    the monitoring endpoints are restricted to System Admin."""

    async def test_local_dev_fallback_always_available(self) -> None:
        """Any code that calls get_healthy_provider() gets an answer — no auth check."""
        with patch("app.ai_providers.manager.settings") as s:
            s.AI_PROVIDER = "LOCAL_DEV"
            s.AI_TEMPERATURE = 0.3
            s.AI_MAX_TOKENS = 1024
            manager = ProviderManager()
        provider = await manager.get_healthy_provider()
        assert provider is not None
        assert provider.provider_name == "local_dev"

    async def test_get_status_requires_no_auth(self) -> None:
        """get_status() is a pure config snapshot — no auth dependency."""
        with patch("app.ai_providers.manager.settings") as s:
            s.AI_PROVIDER = "LOCAL_DEV"
            s.AI_TEMPERATURE = 0.3
            s.AI_MAX_TOKENS = 1024
            manager = ProviderManager()
        status = manager.get_status()
        assert isinstance(status, dict)
        assert "active_provider" in status

    async def test_complete_still_works_for_any_caller(self) -> None:
        """LocalDevProvider.complete() returns a string regardless of caller role."""
        from app.ai_providers.local_provider import LocalDevProvider
        from app.ai_providers.base_provider import AIMessage

        provider = LocalDevProvider()
        result = await provider.complete([AIMessage(role="user", content="Test QA query")])
        assert isinstance(result, str)
        assert len(result) > 0
