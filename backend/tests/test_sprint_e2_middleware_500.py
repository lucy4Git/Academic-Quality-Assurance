"""Sprint E2 — STG-008: SlowAPIMiddleware crashes on all /api/v1/* routes.

Root cause (confirmed 2026-07-28):
    SlowAPIMiddleware._find_route_handler uses Match.FULL to locate route
    handlers.  FastAPI's include_router() creates _IncludedRouter objects
    that return Match.PARTIAL only, so handler is always None for /api/v1/*
    paths.  When handler is None, _check_request_limit exits early without
    calling __evaluate_limits, leaving request.state.view_rate_limit unset.
    The subsequent _inject_headers(response, request.state.view_rate_limit)
    raises AttributeError, which BaseHTTPMiddleware converts to a plain-text
    HTTP 500 for every single API endpoint — even before Pydantic validation,
    even for wrong credentials, even for endpoints without rate-limit decorators.

Fix applied:
    _PatchedSlowAPIMiddleware.dispatch pre-initialises
    request.state.view_rate_limit = None before delegating to the parent.
    __evaluate_limits overwrites this with the real value when limits apply.
    _inject_headers safely skips header injection when current_limit is None.

Evidence of fix:
    - POST /api/v1/auth/login with {} body → was 500, now 422.
    - POST /api/v1/auth/login with wrong credentials → was 500, now 401.
    - POST /api/v1/auth/login with valid credentials → was 500, now 200.
"""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

PREFIX = settings.API_V1_PREFIX
client = TestClient(app, raise_server_exceptions=False)


class TestMiddlewareDoesNotCrash:
    """API endpoints must not return 500 due to SlowAPIMiddleware AttributeError."""

    def test_login_empty_body_returns_422_not_500(self):
        """Empty body must produce a validation error, not a server error."""
        resp = client.post(f"{PREFIX}/auth/login", json={})
        assert resp.status_code == 422, (
            f"Expected 422 Unprocessable Entity, got {resp.status_code}. "
            "SlowAPIMiddleware may be crashing before Pydantic validation."
        )

    def test_refresh_invalid_token_returns_401_not_500(self):
        """/auth/refresh with a bad token must return 401, not 500."""
        resp = client.post(
            f"{PREFIX}/auth/refresh",
            json={"refresh_token": "not_a_valid_token"},
        )
        assert resp.status_code == 401, (
            f"Expected 401 Unauthorized, got {resp.status_code}."
        )

    def test_register_empty_body_returns_422_not_500(self):
        """/auth/register with empty body must return 422, not 500."""
        resp = client.post(f"{PREFIX}/auth/register", json={})
        assert resp.status_code == 422, (
            f"Expected 422 Unprocessable Entity, got {resp.status_code}."
        )

    def test_me_without_token_returns_401_not_500(self):
        """/auth/me without Authorization header must return 401, not 500."""
        resp = client.get(f"{PREFIX}/auth/me")
        assert resp.status_code == 401, (
            f"Expected 401 Unauthorized, got {resp.status_code}."
        )

    def test_institutions_without_token_returns_401_not_500(self):
        """/institutions without Authorization header must return 401, not 500."""
        resp = client.get(f"{PREFIX}/institutions")
        assert resp.status_code == 401, (
            f"Expected 401 Unauthorized, got {resp.status_code}."
        )

    def test_health_still_returns_200(self):
        """/health must still return 200 after the middleware patch."""
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_nonexistent_route_still_returns_404(self):
        """Unknown routes must still return 404."""
        resp = client.get("/nonexistent")
        assert resp.status_code == 404
