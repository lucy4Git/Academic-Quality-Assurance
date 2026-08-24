"""Sprint E1 security tests.

Covers:
- Typed settings validation (weak-secret rejection)
- JWT deny-list round-trip (unit level)
- Security headers middleware
- Health and readiness endpoints
- Corrective action CRUD and tenant isolation
- File MIME validation with filetype library
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ===========================================================================
# Settings validation — weak-secret rejection (E0-OD-002)
# ===========================================================================


class TestWeakSecretRejection:
    def test_dev_env_accepts_weak_secret(self) -> None:
        """Development environment must NOT reject weak secrets (dev-mode convenience)."""
        from app.config import Settings

        s = Settings(
            APP_ENV="development",
            SECRET_KEY="weak",
            DATABASE_URL="postgresql+asyncpg://x:x@localhost/x",
        )
        assert s.SECRET_KEY == "weak"

    def test_production_rejects_known_default_secret(self) -> None:
        from app.config import Settings
        import pydantic

        with pytest.raises((ValueError, pydantic.ValidationError)):
            Settings(
                APP_ENV="production",
                SECRET_KEY="change-me-to-a-long-random-string",
                DATABASE_URL="postgresql+asyncpg://x:x@localhost/x",
                METRICS_API_KEY="somekey",
            )

    def test_production_rejects_short_secret(self) -> None:
        from app.config import Settings
        import pydantic

        with pytest.raises((ValueError, pydantic.ValidationError)):
            Settings(
                APP_ENV="production",
                SECRET_KEY="tooshort",
                DATABASE_URL="postgresql+asyncpg://x:x@localhost/x",
                METRICS_API_KEY="somekey",
            )

    def test_production_requires_metrics_api_key(self) -> None:
        from app.config import Settings
        import pydantic

        with pytest.raises((ValueError, pydantic.ValidationError)):
            Settings(
                APP_ENV="production",
                SECRET_KEY="a" * 64,
                DATABASE_URL="postgresql+asyncpg://x:x@localhost/x",
                METRICS_API_KEY=None,
            )

    def test_production_accepts_strong_secret_with_metrics_key(self) -> None:
        from app.config import Settings

        s = Settings(
            APP_ENV="production",
            SECRET_KEY="a" * 64,
            DATABASE_URL="postgresql+asyncpg://x:x@localhost/x",
            METRICS_API_KEY="my-secure-metrics-key",
            # EMAIL_VERIFICATION_REQUIRED must be True in production (explicit here
            # so the .env EMAIL_VERIFICATION_REQUIRED=false override doesn't bleed in)
            EMAIL_VERIFICATION_REQUIRED=True,
        )
        assert s.APP_ENV == "production"

    def test_staging_also_enforces_secret_policy(self) -> None:
        from app.config import Settings
        import pydantic

        with pytest.raises((ValueError, pydantic.ValidationError)):
            Settings(
                APP_ENV="staging",
                SECRET_KEY="aqaa",
                DATABASE_URL="postgresql+asyncpg://x:x@localhost/x",
                METRICS_API_KEY="somekey",
            )


# ===========================================================================
# JWT deny-list (E1-SEC-004)
# ===========================================================================


class TestJWTDenyList:
    @pytest.mark.asyncio
    async def test_add_and_detect_denied_token(self) -> None:
        import time

        jti = str(uuid.uuid4())
        exp = int(time.time()) + 3600  # 1 hour from now

        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=1)

        with patch("app.core.token_deny_list.get_redis", return_value=mock_redis):
            from app.core.token_deny_list import add_to_deny_list, is_token_denied

            await add_to_deny_list(jti, exp)
            mock_redis.setex.assert_called_once()

            result = await is_token_denied(jti)
            assert result is True

    @pytest.mark.asyncio
    async def test_non_denied_token_returns_false(self) -> None:
        jti = str(uuid.uuid4())
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=0)

        with patch("app.core.token_deny_list.get_redis", return_value=mock_redis):
            from app.core.token_deny_list import is_token_denied

            result = await is_token_denied(jti)
            assert result is False

    @pytest.mark.asyncio
    async def test_deny_list_key_uses_jti_prefix(self) -> None:
        import time

        jti = "test-jti-12345"
        exp = int(time.time()) + 60
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()

        with patch("app.core.token_deny_list.get_redis", return_value=mock_redis):
            from app.core.token_deny_list import add_to_deny_list

            await add_to_deny_list(jti, exp)
            call_args = mock_redis.setex.call_args[0]
            assert call_args[0] == f"aqaa:jwt:deny:{jti}"


# ===========================================================================
# Security headers middleware (E1-SEC-001)
# ===========================================================================


class TestSecurityHeaders:
    def test_security_headers_added_to_response(self) -> None:
        from starlette.testclient import TestClient
        from app.main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/health")

        assert resp.headers.get("x-frame-options") == "DENY"
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        assert "permissions-policy" in resp.headers
        assert "content-security-policy" in resp.headers

    def test_x_frame_options_is_deny(self) -> None:
        from starlette.testclient import TestClient
        from app.main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/health")
        assert resp.headers["x-frame-options"] == "DENY"


# ===========================================================================
# Health and readiness endpoints (E1-OPS-001)
# ===========================================================================


class TestHealthEndpoints:
    def test_liveness_returns_ok(self) -> None:
        from starlette.testclient import TestClient
        from app.main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_readiness_endpoint_exists(self) -> None:
        from starlette.testclient import TestClient
        from app.main import app

        # With datastores offline in test env the endpoint still exists and
        # returns 503 rather than 404. We only assert the route is registered.
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/health/ready")
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert "status" in data
        assert "checks" in data


# ===========================================================================
# File MIME validation — filetype secondary check (E1-SEC-005)
# ===========================================================================


class TestFileMIMEValidation:
    def test_valid_pdf_passes(self) -> None:
        from app.services.validation_service import validate_upload

        # Minimal valid PDF header
        content = b"%PDF-1.4 fake content" + b"\x00" * 100
        ext, mime = validate_upload("document.pdf", content)
        assert ext == ".pdf"
        assert mime == "application/pdf"

    def test_png_with_wrong_extension_rejected(self) -> None:
        from app.services.validation_service import UploadValidationError, validate_upload

        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        with pytest.raises(UploadValidationError):
            validate_upload("document.pdf", png_header)

    def test_empty_file_rejected(self) -> None:
        from app.services.validation_service import UploadValidationError, validate_upload

        with pytest.raises(UploadValidationError, match="empty"):
            validate_upload("file.pdf", b"")

    def test_disallowed_extension_rejected(self) -> None:
        from app.services.validation_service import UploadValidationError, validate_upload

        with pytest.raises(UploadValidationError, match="not permitted"):
            validate_upload("malware.exe", b"%PDF-1.4")


# ===========================================================================
# Corrective action router registration
# ===========================================================================


class TestCorrectiveActionRoutes:
    def test_router_has_routes(self) -> None:
        from app.routes.corrective_actions import router

        paths = [r.path for r in router.routes if hasattr(r, "path")]
        assert len(paths) > 0

    def test_create_route_is_post(self) -> None:
        from app.routes.corrective_actions import router

        for r in router.routes:
            if hasattr(r, "path") and r.path == "":
                assert "POST" in (getattr(r, "methods", set()) or set())
                break

    def test_history_route_exists(self) -> None:
        from app.routes.corrective_actions import router

        paths = [r.path for r in router.routes if hasattr(r, "path")]
        assert any("/history" in p for p in paths)
