"""Sprint E2 — API documentation exposure policy.

Policy (confirmed 2026-07-27):
  Swagger UI, ReDoc, and OpenAPI JSON are served under the versioned API prefix
  (/api/v1/docs, /api/v1/redoc, /api/v1/openapi.json) and are available in
  every environment.  Root-level paths (/docs, /redoc, /openapi.json) return
  404 because FastAPI never mounts them there — this is correct, not a bug.

  There is no APP_ENV-based disabling.  The design trade-off is:
    - Pros: developer ergonomics, client code generation, integration partner
      onboarding without a separate documentation step.
    - Cons: API shape is public.  Mitigated by the fact that all data endpoints
      require authentication (JWT); documentation exposure alone grants no access.

  If a future policy decision requires hiding docs in production, set
  docs_url=None / redoc_url=None / openapi_url=None in create_app() for
  APP_ENV in {"pilot", "production"}.  Do not implement that change without an
  explicit owner decision — these tests will catch an unintended regression in
  either direction.
"""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)

PREFIX = settings.API_V1_PREFIX  # "/api/v1"


class TestDocumentationUrlPolicy:
    """Root-level doc paths must 404; versioned paths must succeed."""

    def test_root_docs_returns_404(self):
        resp = client.get("/docs")
        assert resp.status_code == 404, (
            "/docs must 404 — docs are only served under the API prefix"
        )

    def test_root_openapi_returns_404(self):
        resp = client.get("/openapi.json")
        assert resp.status_code == 404, (
            "/openapi.json must 404 — OpenAPI schema is only served under the API prefix"
        )

    def test_root_redoc_returns_404(self):
        resp = client.get("/redoc")
        assert resp.status_code == 404, (
            "/redoc must 404 — ReDoc is only served under the API prefix"
        )

    def test_versioned_docs_reachable(self):
        resp = client.get(f"{PREFIX}/docs")
        assert resp.status_code == 200, (
            f"{PREFIX}/docs must be reachable — Swagger UI is served under the API prefix"
        )

    def test_versioned_openapi_reachable(self):
        resp = client.get(f"{PREFIX}/openapi.json")
        assert resp.status_code == 200, (
            f"{PREFIX}/openapi.json must be reachable — OpenAPI schema is served under the API prefix"
        )

    def test_versioned_redoc_reachable(self):
        resp = client.get(f"{PREFIX}/redoc")
        assert resp.status_code == 200, (
            f"{PREFIX}/redoc must be reachable — ReDoc is served under the API prefix"
        )

    def test_openapi_schema_is_valid_json(self):
        resp = client.get(f"{PREFIX}/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert "openapi" in schema
        assert "paths" in schema
        assert "info" in schema

    def test_openapi_schema_contains_auth_endpoint(self):
        resp = client.get(f"{PREFIX}/openapi.json")
        schema = resp.json()
        paths = schema.get("paths", {})
        assert any("/auth/" in p for p in paths), (
            "OpenAPI schema must include auth routes"
        )
