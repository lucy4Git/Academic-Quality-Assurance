"""Sprint E2 — STG-009: Prometheus instrumentation must not crash on _IncludedRouter.

Root cause (confirmed 2026-07-28 from live Render traceback):
    prometheus_fastapi_instrumentator 7.x iterates app.routes and accesses
    route.path unconditionally.  FastAPI 0.116+ (0.137+ officially) wraps
    routes registered via include_router() in _IncludedRouter objects that do
    not expose a .path attribute.  This raised:

        AttributeError: '_IncludedRouter' object has no attribute 'path'

    at prometheus_fastapi_instrumentator/routing.py line 55, converting every
    single /api/v1/* request into a plain-text HTTP 500.

Fix applied:
    requirements.txt bumped prometheus-fastapi-instrumentator from >=7.0,<8.0
    to >=8.0,<9.0.  Version 8.x explicitly handles _IncludedRouter via a
    _resolve_path() helper that checks hasattr(route, 'path') and falls back
    to include_context.prefix.  The fix is in the upstream package — no
    application-level workaround required.

Evidence:
    - Live traceback captured from Render logs 2026-07-28T12:47Z
    - Local 8.0.2 routing.py docstring: "FastAPI 0.116+ (officially 0.137)
      wraps routers via include_router in _IncludedRouter which does not
      expose a path attribute"
    - FastAPI installed: 0.139.2 (within the affected range)
"""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

PREFIX = settings.API_V1_PREFIX
client = TestClient(app, raise_server_exceptions=False)


class TestPrometheusDoesNotCrash:
    """Prometheus middleware must not convert API requests into HTTP 500."""

    def test_login_empty_body_returns_422_not_500(self):
        """Pydantic validation must run — Prometheus must not crash before it."""
        resp = client.post(f"{PREFIX}/auth/login", json={})
        assert resp.status_code == 422, (
            f"Expected 422 Unprocessable Entity, got {resp.status_code}. "
            "Prometheus middleware may be crashing before request handling. "
            "Check prometheus-fastapi-instrumentator version — must be >=8.0."
        )

    def test_me_without_token_returns_401_not_500(self):
        """/auth/me without a token must return 401, not 500."""
        resp = client.get(f"{PREFIX}/auth/me")
        assert resp.status_code == 401, (
            f"Expected 401 Unauthorized, got {resp.status_code}."
        )

    def test_institutions_without_token_returns_401_not_500(self):
        """/institutions without a token must return 401, not 500."""
        resp = client.get(f"{PREFIX}/institutions")
        assert resp.status_code == 401, (
            f"Expected 401 Unauthorized, got {resp.status_code}."
        )

    def test_register_empty_body_returns_422_not_500(self):
        """/auth/register with empty body must return 422, not 500."""
        resp = client.post(f"{PREFIX}/auth/register", json={})
        assert resp.status_code == 422, (
            f"Expected 422 Unprocessable Entity, got {resp.status_code}."
        )

    def test_health_returns_200(self):
        """/health must return 200 — sanity check that the app starts."""
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_nonexistent_route_returns_404(self):
        """Unknown routes must still return 404, not 500."""
        resp = client.get("/nonexistent-path-that-does-not-exist")
        assert resp.status_code == 404

    def test_metrics_endpoint_accessible(self):
        """/metrics must be reachable (200 or 401 in non-dev env — never 500)."""
        resp = client.get("/metrics")
        assert resp.status_code in (200, 401), (
            f"Expected 200 or 401 from /metrics, got {resp.status_code}."
        )


class TestPrometheusPackageVersion:
    """Verify the installed package version is in the fixed range."""

    def test_prometheus_instrumentator_version_is_8x(self):
        """prometheus-fastapi-instrumentator must be >=8.0 to contain the fix."""
        import importlib.metadata
        version = importlib.metadata.version("prometheus-fastapi-instrumentator")
        major = int(version.split(".")[0])
        assert major >= 8, (
            f"prometheus-fastapi-instrumentator {version} is in the buggy 7.x range. "
            "Upgrade to >=8.0 (STG-009 fix). Run: pip install "
            "'prometheus-fastapi-instrumentator>=8.0,<9.0'"
        )

    def test_routing_module_handles_routes_without_path(self):
        """_resolve_path in 8.x must handle objects without .path gracefully."""
        from prometheus_fastapi_instrumentator.routing import _resolve_path

        class _FakeIncludedRouter:
            """Minimal stand-in for FastAPI's _IncludedRouter — no .path attribute."""
            pass

        fake_route = _FakeIncludedRouter()
        result = _resolve_path(fake_route)
        assert result is None, (
            "_resolve_path must return None for objects without .path, "
            f"got {result!r}"
        )
