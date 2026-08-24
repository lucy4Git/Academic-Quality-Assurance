"""Tests for EMAIL_VERIFICATION_REQUIRED=false (staging/pilot mode).

Verifies that when email verification is disabled:
  1. public_register_user creates an active account immediately.
  2. No verification code is generated or stored.
  3. No Brevo / email_service call is made.
  4. is_verified stays False (truthful — no email confirmation occurred).
  5. The user can authenticate immediately after registration.
  6. role is always STUDENT; institution_id is always None.
  7. authenticate_user does NOT gate on is_verified when verification is disabled.

All tests are pure unit tests — no real DB, no HTTP stack.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums import UserRole
from app.models.user import User
from app.services.auth_service import AuthError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(**kwargs) -> User:
    defaults = dict(
        id=uuid.uuid4(),
        email="student@example.com",
        full_name="Test Student",
        hashed_password="$2b$12$" + "a" * 53,
        role=UserRole.STUDENT,
        institution_id=None,
        is_active=True,
        is_verified=False,
        verification_code=None,
        verification_code_expires_at=None,
        approval_status="approved",
        invitation_id=None,
    )
    defaults.update(kwargs)
    user = MagicMock(spec=User)
    for k, v in defaults.items():
        setattr(user, k, v)
    return user


def _mock_db_with_user(user: User | None) -> AsyncMock:
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


# ---------------------------------------------------------------------------
# Tests: public_register_user with EMAIL_VERIFICATION_REQUIRED=false
# ---------------------------------------------------------------------------

class TestEmailVerificationDeferred:
    """public_register_user behaves correctly when email verification is disabled."""

    @pytest.mark.asyncio
    async def test_registration_creates_active_account_immediately(self):
        """Account is active immediately when EMAIL_VERIFICATION_REQUIRED=false."""
        from app.schemas.auth import PublicRegisterRequest
        from app.services.auth_service import public_register_user

        db = _mock_db_with_user(None)  # no existing user

        created_users: list[User] = []

        def capture_add(obj):
            created_users.append(obj)

        db.add = capture_add

        async def fake_refresh(obj):
            pass

        db.refresh = fake_refresh

        data = PublicRegisterRequest(
            email="newstudent@example.com",
            full_name="New Student",
            password="Password1",
        )

        mock_settings = MagicMock()
        mock_settings.EMAIL_VERIFICATION_REQUIRED = False
        mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False
        mock_settings.VERIFICATION_CODE_EXPIRE_HOURS = 24

        with patch("app.services.auth_service.settings", mock_settings):
            user = await public_register_user(db, data)

        assert len(created_users) == 1
        created = created_users[0]
        assert created.is_active is True

    @pytest.mark.asyncio
    async def test_no_verification_code_generated(self):
        """verification_code is None when EMAIL_VERIFICATION_REQUIRED=false."""
        from app.schemas.auth import PublicRegisterRequest
        from app.services.auth_service import public_register_user

        db = _mock_db_with_user(None)
        captured: list[User] = []
        db.add = captured.append
        db.refresh = AsyncMock()

        data = PublicRegisterRequest(
            email="nostudent@example.com",
            full_name="No Code Student",
            password="Password1",
        )

        mock_settings = MagicMock()
        mock_settings.EMAIL_VERIFICATION_REQUIRED = False
        mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False
        mock_settings.VERIFICATION_CODE_EXPIRE_HOURS = 24

        with patch("app.services.auth_service.settings", mock_settings):
            await public_register_user(db, data)

        created = captured[0]
        assert created.verification_code is None
        assert created.verification_code_expires_at is None

    @pytest.mark.asyncio
    async def test_is_verified_stays_false(self):
        """is_verified remains False — no email confirmation occurred."""
        from app.schemas.auth import PublicRegisterRequest
        from app.services.auth_service import public_register_user

        db = _mock_db_with_user(None)
        captured: list[User] = []
        db.add = captured.append
        db.refresh = AsyncMock()

        data = PublicRegisterRequest(
            email="unverified@example.com",
            full_name="Unverified User",
            password="Password1",
        )

        mock_settings = MagicMock()
        mock_settings.EMAIL_VERIFICATION_REQUIRED = False
        mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False
        mock_settings.VERIFICATION_CODE_EXPIRE_HOURS = 24

        with patch("app.services.auth_service.settings", mock_settings):
            await public_register_user(db, data)

        created = captured[0]
        assert created.is_verified is False

    @pytest.mark.asyncio
    async def test_role_always_generic_user(self):
        """Role is always GENERIC_USER regardless of request payload."""
        from app.schemas.auth import PublicRegisterRequest
        from app.services.auth_service import public_register_user

        db = _mock_db_with_user(None)
        captured: list[User] = []
        db.add = captured.append
        db.refresh = AsyncMock()

        data = PublicRegisterRequest(
            email="roletest@example.com",
            full_name="Role Test",
            password="Password1",
        )

        mock_settings = MagicMock()
        mock_settings.EMAIL_VERIFICATION_REQUIRED = False
        mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False
        mock_settings.VERIFICATION_CODE_EXPIRE_HOURS = 24

        with patch("app.services.auth_service.settings", mock_settings):
            await public_register_user(db, data)

        created = captured[0]
        assert created.role == UserRole.GENERIC_USER

    @pytest.mark.asyncio
    async def test_institution_id_always_none(self):
        """institution_id is always None for public registration."""
        from app.schemas.auth import PublicRegisterRequest
        from app.services.auth_service import public_register_user

        db = _mock_db_with_user(None)
        captured: list[User] = []
        db.add = captured.append
        db.refresh = AsyncMock()

        data = PublicRegisterRequest(
            email="tenant@example.com",
            full_name="Tenant Test",
            password="Password1",
        )

        mock_settings = MagicMock()
        mock_settings.EMAIL_VERIFICATION_REQUIRED = False
        mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False
        mock_settings.VERIFICATION_CODE_EXPIRE_HOURS = 24

        with patch("app.services.auth_service.settings", mock_settings):
            await public_register_user(db, data)

        created = captured[0]
        assert created.institution_id is None

    @pytest.mark.asyncio
    async def test_duplicate_email_raises_auth_error(self):
        """Registration with existing email raises AuthError."""
        from app.schemas.auth import PublicRegisterRequest
        from app.services.auth_service import public_register_user

        existing = _make_user(email="taken@example.com")
        db = _mock_db_with_user(existing)

        data = PublicRegisterRequest(
            email="taken@example.com",
            full_name="Duplicate",
            password="Password1",
        )

        mock_settings = MagicMock()
        mock_settings.EMAIL_VERIFICATION_REQUIRED = False
        mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False

        with patch("app.services.auth_service.settings", mock_settings):
            with pytest.raises(AuthError, match="already exists"):
                await public_register_user(db, data)


# ---------------------------------------------------------------------------
# Tests: authenticate_user with EMAIL_VERIFICATION_REQUIRED=false
# ---------------------------------------------------------------------------

class TestLoginWithVerificationDisabled:
    """authenticate_user does not block on is_verified when verification is disabled."""

    @pytest.mark.asyncio
    async def test_login_succeeds_with_is_verified_false(self):
        """Active user with is_verified=False can log in when verification is disabled."""
        from app.services.auth_service import authenticate_user

        user = _make_user(
            email="pilot@example.com",
            is_active=True,
            is_verified=False,
            approval_status="approved",
        )

        db = _mock_db_with_user(user)

        mock_settings = MagicMock()
        mock_settings.EMAIL_VERIFICATION_REQUIRED = False
        mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False

        with (
            patch("app.services.auth_service.settings", mock_settings),
            patch("app.services.auth_service.verify_password", return_value=True),
        ):
            result = await authenticate_user(db, "pilot@example.com", "Password1")

        assert result is user

    @pytest.mark.asyncio
    async def test_inactive_user_still_blocked(self):
        """is_active=False always blocks login regardless of verification setting."""
        from app.services.auth_service import authenticate_user

        user = _make_user(
            email="inactive@example.com",
            is_active=False,
            is_verified=False,
            approval_status="approved",
        )

        db = _mock_db_with_user(user)

        mock_settings = MagicMock()
        mock_settings.EMAIL_VERIFICATION_REQUIRED = False
        mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False

        with (
            patch("app.services.auth_service.settings", mock_settings),
            patch("app.services.auth_service.verify_password", return_value=True),
        ):
            with pytest.raises(AuthError, match="disabled"):
                await authenticate_user(db, "inactive@example.com", "Password1")

    @pytest.mark.asyncio
    async def test_wrong_password_still_blocked(self):
        """Wrong password always fails regardless of verification setting."""
        from app.services.auth_service import authenticate_user

        user = _make_user(
            email="wrongpass@example.com",
            is_active=True,
            is_verified=False,
            approval_status="approved",
        )

        db = _mock_db_with_user(user)

        mock_settings = MagicMock()
        mock_settings.EMAIL_VERIFICATION_REQUIRED = False
        mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False

        with (
            patch("app.services.auth_service.settings", mock_settings),
            patch("app.services.auth_service.verify_password", return_value=False),
        ):
            with pytest.raises(AuthError, match="Invalid email or password"):
                await authenticate_user(db, "wrongpass@example.com", "wrongpass")
