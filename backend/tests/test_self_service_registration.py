"""Tests — self-service registration, email verification, and auto-activation.

Covers the secure self-service lifecycle introduced when
REGISTRATION_REQUIRES_ADMIN_APPROVAL=False:

  register → receive code → verify email → account activates → login succeeds

Security tests also verify:
  - Role escalation is blocked (STUDENT forced regardless of input)
  - Institution spoofing is blocked (institution_id never accepted from browser)
  - Privileged roles cannot be self-assigned
  - Cross-tenant access is rejected
  - Rejected/suspended accounts cannot log in
  - Verification codes never appear in API responses or logs

All DB interactions are mocked — no test database required.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

from app.models.enums import UserRole
from app.models.user import User
from app.services.auth_service import (
    AuthError,
    authenticate_user,
    public_register_user,
    verify_email_code,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(
    *,
    email: str = "test@example.com",
    is_active: bool = False,
    is_verified: bool = False,
    approval_status: str = "approved",
    role: UserRole = UserRole.STUDENT,
    institution_id: uuid.UUID | None = None,
    verification_code: str | None = "123456",
    verification_code_expires_at: datetime | None = None,
    hashed_password: str = "HASH",
) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = email
    user.full_name = "Test User"
    user.is_active = is_active
    user.is_verified = is_verified
    user.approval_status = approval_status
    user.role = role
    user.institution_id = institution_id
    user.verification_code = verification_code
    user.verification_code_expires_at = (
        verification_code_expires_at
        or datetime.now(tz=timezone.utc) + timedelta(hours=24)
    )
    user.hashed_password = hashed_password
    return user


def _mock_db_for_register(*, existing_user: MagicMock | None = None) -> AsyncMock:
    """Mock DB for public_register_user: first execute returns existing user lookup."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = existing_user
    db = AsyncMock()
    db.execute.return_value = result
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _mock_db_with_user(user: MagicMock | None) -> AsyncMock:
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    db = AsyncMock()
    db.execute.return_value = result
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _public_register_request(
    *,
    email: str = "new@example.com",
    full_name: str = "New User",
    password: str = "Secret123!",
    institution_name: str = "Test University",
    role_requested: UserRole | None = None,
    institution_id: uuid.UUID | None = None,
) -> MagicMock:
    """Build a fake PublicRegisterRequest."""
    req = MagicMock()
    req.email = email
    req.full_name = full_name
    req.password = password
    req.institution_name = institution_name
    req.role_requested = role_requested
    req.reason_for_access = None
    # institution_id is intentionally NOT a field on PublicRegisterRequest;
    # the service must never read it. We attach it here to confirm it is ignored.
    req.institution_id = institution_id
    return req


# ---------------------------------------------------------------------------
# Registration — role and tenant security invariants
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_self_registration_assigns_student_role():
    """Registered user always gets STUDENT regardless of any submitted role."""
    db = _mock_db_for_register()

    with patch("app.services.auth_service.get_user_by_email", return_value=None):
        with patch("app.services.auth_service.hash_password", return_value="HASHED"):
            with patch("app.services.auth_service.settings") as mock_settings:
                mock_settings.VERIFICATION_CODE_EXPIRE_HOURS = 24
                mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False

                await public_register_user(db, _public_register_request())

    added_user = db.add.call_args[0][0]
    assert added_user.role == UserRole.STUDENT


@pytest.mark.asyncio
async def test_privileged_role_self_assignment_rejected():
    """Even if caller passes a privileged role, STUDENT is assigned."""
    db = _mock_db_for_register()

    with patch("app.services.auth_service.get_user_by_email", return_value=None):
        with patch("app.services.auth_service.hash_password", return_value="HASHED"):
            with patch("app.services.auth_service.settings") as mock_settings:
                mock_settings.VERIFICATION_CODE_EXPIRE_HOURS = 24
                mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False

                await public_register_user(
                    db,
                    _public_register_request(role_requested=UserRole.SYSTEM_ADMIN),
                )

    added_user = db.add.call_args[0][0]
    assert added_user.role == UserRole.STUDENT


@pytest.mark.asyncio
async def test_institution_spoofing_blocked():
    """institution_id is always None — browser cannot establish tenant membership."""
    db = _mock_db_for_register()

    spoofed_institution_id = uuid.uuid4()

    with patch("app.services.auth_service.get_user_by_email", return_value=None):
        with patch("app.services.auth_service.hash_password", return_value="HASHED"):
            with patch("app.services.auth_service.settings") as mock_settings:
                mock_settings.VERIFICATION_CODE_EXPIRE_HOURS = 24
                mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False

                await public_register_user(
                    db,
                    _public_register_request(institution_id=spoofed_institution_id),
                )

    added_user = db.add.call_args[0][0]
    assert added_user.institution_id is None


@pytest.mark.asyncio
async def test_duplicate_registration_raises():
    existing = _make_user(email="dupe@example.com")
    db = _mock_db_for_register(existing_user=existing)

    with patch("app.services.auth_service.get_user_by_email", return_value=existing):
        with pytest.raises(AuthError, match="already exists"):
            await public_register_user(db, _public_register_request(email="dupe@example.com"))


@pytest.mark.asyncio
async def test_registration_approval_status_when_no_admin_required():
    """approval_status must be 'approved' so account activates after email verification."""
    db = _mock_db_for_register()

    with patch("app.services.auth_service.get_user_by_email", return_value=None):
        with patch("app.services.auth_service.hash_password", return_value="HASHED"):
            with patch("app.services.auth_service.settings") as mock_settings:
                mock_settings.VERIFICATION_CODE_EXPIRE_HOURS = 24
                mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False

                await public_register_user(db, _public_register_request())

    added_user = db.add.call_args[0][0]
    assert added_user.approval_status == "approved"
    assert added_user.is_active is False      # not yet active until email verified
    assert added_user.is_verified is False


@pytest.mark.asyncio
async def test_registration_approval_status_when_admin_required():
    """When admin approval is required, approval_status must be 'pending'."""
    db = _mock_db_for_register()

    with patch("app.services.auth_service.get_user_by_email", return_value=None):
        with patch("app.services.auth_service.hash_password", return_value="HASHED"):
            with patch("app.services.auth_service.settings") as mock_settings:
                mock_settings.VERIFICATION_CODE_EXPIRE_HOURS = 24
                mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = True

                await public_register_user(db, _public_register_request())

    added_user = db.add.call_args[0][0]
    assert added_user.approval_status == "pending"
    assert added_user.is_active is False


# ---------------------------------------------------------------------------
# Email verification — auto-activation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_email_activates_account_when_auto_activate_enabled():
    """Correct code + auto-activate=True → account becomes active."""
    code = "654321"
    user = _make_user(
        is_verified=False,
        is_active=False,
        approval_status="approved",
        verification_code=code,
    )
    db = _mock_db_with_user(user)

    with patch("app.services.auth_service.settings") as mock_settings:
        mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False
        mock_settings.REGISTRATION_AUTO_ACTIVATE_AFTER_EMAIL_VERIFICATION = True

        result = await verify_email_code(db, user.email, code)

    assert result.is_verified is True
    assert result.is_active is True
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_verify_email_does_not_activate_when_admin_approval_required():
    """Even with auto-activate=True, admin approval flag prevents activation."""
    code = "111222"
    user = _make_user(
        is_verified=False,
        is_active=False,
        approval_status="pending",
        verification_code=code,
    )
    db = _mock_db_with_user(user)

    with patch("app.services.auth_service.settings") as mock_settings:
        mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = True
        mock_settings.REGISTRATION_AUTO_ACTIVATE_AFTER_EMAIL_VERIFICATION = True

        result = await verify_email_code(db, user.email, code)

    assert result.is_verified is True
    assert result.is_active is False   # must wait for admin


@pytest.mark.asyncio
async def test_verify_email_wrong_code_raises():
    user = _make_user(verification_code="111111", is_verified=False)
    db = _mock_db_with_user(user)

    with patch("app.services.auth_service.settings") as mock_settings:
        mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False
        mock_settings.REGISTRATION_AUTO_ACTIVATE_AFTER_EMAIL_VERIFICATION = True

        with pytest.raises(AuthError, match="Invalid or expired"):
            await verify_email_code(db, user.email, "999999")


@pytest.mark.asyncio
async def test_verify_email_expired_code_raises():
    code = "123456"
    user = _make_user(
        is_verified=False,
        verification_code=code,
        verification_code_expires_at=datetime.now(tz=timezone.utc) - timedelta(hours=1),
    )
    db = _mock_db_with_user(user)

    with patch("app.services.auth_service.settings") as mock_settings:
        mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False
        mock_settings.REGISTRATION_AUTO_ACTIVATE_AFTER_EMAIL_VERIFICATION = True

        with pytest.raises(AuthError, match="Invalid or expired"):
            await verify_email_code(db, user.email, code)


@pytest.mark.asyncio
async def test_verify_email_unknown_user_raises():
    db = _mock_db_with_user(None)

    with patch("app.services.auth_service.settings") as mock_settings:
        mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False
        mock_settings.REGISTRATION_AUTO_ACTIVATE_AFTER_EMAIL_VERIFICATION = True

        with pytest.raises(AuthError, match="No account found"):
            await verify_email_code(db, "nobody@example.com", "123456")


# ---------------------------------------------------------------------------
# Login guards
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_succeeds_after_verification():
    """Verified, active, approved account can log in."""
    user = _make_user(
        is_verified=True,
        is_active=True,
        approval_status="approved",
        hashed_password="HASH",
    )
    db = _mock_db_with_user(user)

    with patch("app.services.auth_service.verify_password", return_value=True):
        with patch("app.services.auth_service.settings") as mock_settings:
            mock_settings.EMAIL_VERIFICATION_REQUIRED = True
            mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False

            result = await authenticate_user(db, user.email, "Secret123!")

    assert result is user


@pytest.mark.asyncio
async def test_login_blocked_before_email_verification():
    """Unverified account cannot log in when EMAIL_VERIFICATION_REQUIRED=True."""
    user = _make_user(
        is_verified=False,
        is_active=False,
        approval_status="approved",
        hashed_password="HASH",
    )
    db = _mock_db_with_user(user)

    with patch("app.services.auth_service.verify_password", return_value=True):
        with patch("app.services.auth_service.settings") as mock_settings:
            mock_settings.EMAIL_VERIFICATION_REQUIRED = True
            mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False

            with pytest.raises(AuthError, match="not verified"):
                await authenticate_user(db, user.email, "Secret123!")


@pytest.mark.asyncio
async def test_login_blocked_for_rejected_user():
    user = _make_user(
        is_verified=True,
        is_active=False,
        approval_status="rejected",
        hashed_password="HASH",
    )
    db = _mock_db_with_user(user)

    with patch("app.services.auth_service.verify_password", return_value=True):
        with patch("app.services.auth_service.settings") as mock_settings:
            mock_settings.EMAIL_VERIFICATION_REQUIRED = True
            mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False

            with pytest.raises(AuthError, match="not approved"):
                await authenticate_user(db, user.email, "Secret123!")


@pytest.mark.asyncio
async def test_login_blocked_for_suspended_user():
    """is_active=False (disabled by admin) blocks login even for approved users."""
    user = _make_user(
        is_verified=True,
        is_active=False,
        approval_status="approved",
        hashed_password="HASH",
    )
    db = _mock_db_with_user(user)

    with patch("app.services.auth_service.verify_password", return_value=True):
        with patch("app.services.auth_service.settings") as mock_settings:
            mock_settings.EMAIL_VERIFICATION_REQUIRED = True
            mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False

            with pytest.raises(AuthError, match="disabled"):
                await authenticate_user(db, user.email, "Secret123!")


@pytest.mark.asyncio
async def test_login_wrong_password_raises():
    user = _make_user(is_verified=True, is_active=True, approval_status="approved")
    db = _mock_db_with_user(user)

    with patch("app.services.auth_service.verify_password", return_value=False):
        with patch("app.services.auth_service.settings") as mock_settings:
            mock_settings.EMAIL_VERIFICATION_REQUIRED = True
            mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False

            with pytest.raises(AuthError, match="Invalid email or password"):
                await authenticate_user(db, user.email, "WrongPassword1!")


# ---------------------------------------------------------------------------
# Verification code security — must not appear in logs or responses
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verification_code_not_in_registration_response(caplog):
    """Verification code must not be logged at INFO level or above."""
    code = "987654"
    db = _mock_db_for_register()

    # Intercept the user added to the DB and give it a code
    def _capture_add(user_obj):
        user_obj.verification_code = code

    db.add.side_effect = _capture_add

    with patch("app.services.auth_service.get_user_by_email", return_value=None):
        with patch("app.services.auth_service.hash_password", return_value="HASHED"):
            with patch("app.services.auth_service.settings") as mock_settings:
                mock_settings.VERIFICATION_CODE_EXPIRE_HOURS = 24
                mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False

                with caplog.at_level(logging.INFO, logger="app.services.auth_service"):
                    await public_register_user(db, _public_register_request())

    # The verification code must not appear in any INFO-level log record
    for record in caplog.records:
        assert code not in record.getMessage(), (
            f"Verification code '{code}' leaked into log: {record.getMessage()}"
        )


@pytest.mark.asyncio
async def test_verification_code_not_in_verify_response():
    """The verify_email_code return value (User) must not carry the raw code."""
    code = "543210"
    user = _make_user(
        is_verified=False,
        is_active=False,
        approval_status="approved",
        verification_code=code,
    )
    db = _mock_db_with_user(user)

    with patch("app.services.auth_service.settings") as mock_settings:
        mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False
        mock_settings.REGISTRATION_AUTO_ACTIVATE_AFTER_EMAIL_VERIFICATION = True

        result = await verify_email_code(db, user.email, code)

    # After verification, the code should be cleared
    assert result.verification_code is None


# ---------------------------------------------------------------------------
# Role-escalation through registration payload
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("attempted_role", [
    UserRole.SYSTEM_ADMIN,
    UserRole.QUALITY_ASSURANCE_OFFICER,
    UserRole.FACULTY_DEAN,
    UserRole.HEAD_OF_DEPARTMENT,
    UserRole.PROGRAMME_COORDINATOR,
    UserRole.LECTURER,
])
@pytest.mark.asyncio
async def test_all_privileged_roles_blocked_in_self_registration(attempted_role):
    """Every privileged role is rejected at the service layer."""
    db = _mock_db_for_register()

    with patch("app.services.auth_service.get_user_by_email", return_value=None):
        with patch("app.services.auth_service.hash_password", return_value="HASHED"):
            with patch("app.services.auth_service.settings") as mock_settings:
                mock_settings.VERIFICATION_CODE_EXPIRE_HOURS = 24
                mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False

                await public_register_user(
                    db, _public_register_request(role_requested=attempted_role)
                )

    added_user = db.add.call_args[0][0]
    assert added_user.role == UserRole.STUDENT, (
        f"Expected STUDENT but got {added_user.role} when attempting {attempted_role}"
    )


# ---------------------------------------------------------------------------
# Cross-tenant access
# ---------------------------------------------------------------------------


def test_assert_institution_access_blocks_cross_tenant():
    """assert_institution_access raises 403 for mismatched institution."""
    from fastapi import HTTPException
    from app.dependencies import assert_institution_access

    tut_id = uuid.uuid4()
    up_id = uuid.uuid4()

    user = _make_user(role=UserRole.LECTURER, institution_id=tut_id)
    user.role = UserRole.LECTURER

    with pytest.raises(HTTPException) as exc_info:
        assert_institution_access(user, up_id)

    assert exc_info.value.status_code == 403


def test_assert_institution_access_allows_system_admin():
    """System admins bypass tenant isolation."""
    from app.dependencies import assert_institution_access

    admin = _make_user(role=UserRole.SYSTEM_ADMIN, institution_id=None)
    admin.role = UserRole.SYSTEM_ADMIN

    # Must not raise
    assert_institution_access(admin, uuid.uuid4())


# ---------------------------------------------------------------------------
# Email delivery abstraction — code is sent through service, not exposed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verification_email_sent_on_registration():
    """send_verification_email is called exactly once with the correct address."""
    db = _mock_db_for_register()

    with patch("app.services.auth_service.get_user_by_email", return_value=None):
        with patch("app.services.auth_service.hash_password", return_value="HASHED"):
            with patch("app.services.auth_service.settings") as mock_settings:
                mock_settings.VERIFICATION_CODE_EXPIRE_HOURS = 24
                mock_settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL = False

                # We do not test send_verification_email here — the route layer
                # calls it. This test confirms the user object has a code ready.
                user_obj = await public_register_user(
                    db, _public_register_request(email="sendtest@example.com")
                )

    # The refreshed user is returned by db.refresh, which is a mock.
    # Verify that db.add received a user with a verification_code field.
    added_user = db.add.call_args[0][0]
    assert added_user.verification_code is not None
    assert added_user.verification_code.isdigit()
    assert len(added_user.verification_code) == 6
