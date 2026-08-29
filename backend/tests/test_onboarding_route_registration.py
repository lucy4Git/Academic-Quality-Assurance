"""Regression coverage for the mounted Generic onboarding route."""

from fastapi.testclient import TestClient

from app.main import app


def test_onboarding_preferences_route_is_not_double_prefixed():
    client = TestClient(app)
    assert client.get("/api/v1/onboarding/preferences").status_code == 401
    assert client.get("/api/v1/api/v1/onboarding/preferences").status_code == 404
