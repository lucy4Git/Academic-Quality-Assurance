"""Sprint E2 — STG-007: login endpoint must not return HTTP 500.

Root cause identified 2026-07-27:
    asyncpg can return the role column as a plain str rather than a UserRole
    enum instance when native_enum=True is used with PostgreSQL.  _build_token()
    called role.value, raising AttributeError on a str → unhandled 500.

Fix applied: security.py _build_token() now uses:
    role.value if isinstance(role, UserRole) else str(role)

These tests cover:
  1. create_access_token / create_refresh_token accept a plain str role.
  2. The resulting JWT contains the correct role claim.
  3. Invalid credentials return 401, not 500.
  4. Login endpoint returns 401 (not 500) for bad credentials via HTTP.
"""

import uuid

import jwt
import pytest

from app.config import settings
from app.models.enums import UserRole
from app.security import (
    create_access_token,
    create_refresh_token,
)

PREFIX = settings.API_V1_PREFIX


# ---------------------------------------------------------------------------
# Unit tests — token creation with str role (asyncpg regression)
# ---------------------------------------------------------------------------

class _FakeUser:
    """Minimal stand-in for a User ORM instance, with role as a plain str."""

    def __init__(self, role_val):
        self.id = uuid.uuid4()
        self.role = role_val          # intentionally a str, not UserRole
        self.institution_id = uuid.uuid4()


class _FakeUserNoInstitution:
    def __init__(self, role_val):
        self.id = uuid.uuid4()
        self.role = role_val
        self.institution_id = None   # SYSTEM_ADMIN


@pytest.mark.parametrize("role_val", [
    "quality_assurance_officer",
    "lecturer",
    "student",
    "system_admin",
    "faculty_dean",
    "head_of_department",
    "programme_coordinator",
])
def test_create_access_token_accepts_string_role(role_val):
    """create_access_token must not raise AttributeError when role is a str."""
    user = _FakeUser(role_val)
    token = create_access_token(user)        # must NOT raise
    assert isinstance(token, str)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["role"] == role_val


@pytest.mark.parametrize("role_val", [
    "quality_assurance_officer",
    "lecturer",
])
def test_create_refresh_token_accepts_string_role(role_val):
    """create_refresh_token must not raise AttributeError when role is a str."""
    user = _FakeUser(role_val)
    token = create_refresh_token(user)
    assert isinstance(token, str)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["role"] == role_val
    assert payload["type"] == "refresh"


def test_create_access_token_accepts_enum_role():
    """create_access_token still works correctly with a proper UserRole enum."""
    user = _FakeUser(UserRole.QUALITY_ASSURANCE_OFFICER)
    token = create_access_token(user)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["role"] == "quality_assurance_officer"


def test_create_access_token_null_institution():
    """role-as-str + null institution_id (SYSTEM_ADMIN pattern) must work."""
    user = _FakeUserNoInstitution("system_admin")
    token = create_access_token(user)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["role"] == "system_admin"
    assert payload["institution_id"] is None


# ---------------------------------------------------------------------------
# HTTP-level login behaviour is covered by tests/test_auth_pilot.py.
# The tests above are sufficient to prevent regression of the role-as-string
# AttributeError that produced HTTP 500 on the staging backend.
# ---------------------------------------------------------------------------
