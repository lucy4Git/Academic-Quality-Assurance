"""Tests — public registration, email verification, and admin approval.

Pure unit tests: all DB and email interactions are mocked.  No HTTP layer or
test database required, consistent with the existing AQAA test style.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

from app.models.enums import UserRole
from app.models.user import User
from app.services.auth_service import (
    AuthError,
    _generate_verification_code,
    authenticate_user,
    approve_user,
    reject_user,
    resend_verification_code,
    verify_email_code,
    public_register_user,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(
    *,
    email: str = "test@example.com",
    full_name: str = "Test User",
    is_active: bool = False,
    is_verified: bool = False,
    approval_status: str = "pending",
    verification_code: str | None = "123456",
    verification_code_expires_at: datetime | None = None,
    hashed_password: str = "HASH",
    role: UserRole = UserRole.LECTURER,
) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = email
    user.full_name = full_name
    user.is_active = is_active
    user.is_verified = is_verified
    user.approval_status = approval_status
    user.verification_code = verification_code
    user.verification_code_expires_at = (
        verification_code_expires_at
        or datetime.now(tz=timezone.utc) + timedelta(hours=24)
    )
    user.hashed_password = hashed_password
    user.role = role
    user.institution_id = None
    user.role_requested = "lecturer"
    user.reason_for_access = None
    user.institution_name_requested = "Test University"
    return user


def _mock_db_with_user(user: MagicMock | None) -> AsyncMock:
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    db = AsyncMock()
    db.execute.return_value = result
    return db


# ---------------------------------------------------------------------------
# _generate_verification_code
# ---------------------------------------------------------------------------


def test_generate_verification_code_length():
    code = _generate_verification_code()
    assert len(code) == 6
    assert code.isdigit()


def test_generate_verification_code_unique():
    codes = {_generate_verification_code() for _ in range(20)}
    assert len(codes) > 1  # extremely unlikely to be all the same


# ---------------------------------------------------------------------------
# public_register_user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_public_register_success():
    from app.schemas.auth import PublicRegisterRequest

    data = PublicRegisterRequest(
        email="new@example.com",
        full_name="New User",
        password="Secret123!",
        institution_name="Test University",
        role_requested=UserRole.LECTURER,
    )

    db = AsyncMock()
    db.refresh = AsyncMock()

    with patch("app.services.auth_service.get_user_by_email", return_value=None) as mock_lookup:
        with patch("app.services.auth_service.hash_password", return_value="HASHED"):
            await public_register_user(db, data)

    mock_lookup.assert_awaited_once_with(db, "new@example.com")
    db.add.assert_called_once()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_public_register_duplicate_email_raises():
    from app.schemas.auth import PublicRegisterRequest

    data = PublicRegisterRequest(
        email="existing@example.com",
        full_name="Existing User",
        password="Secret123!",
        institution_name="Test University",
        role_requested=UserRole.LECTURER,
    )

    existing = _make_user(email="existing@example.com")
    db = _mock_db_with_user(existing)

    with pytest.raises(AuthError, match="already exists"):
        await public_register_user(db, data)


# ---------------------------------------------------------------------------
# verify_email_code
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_email_correct_code():
    code = "654321"
    user = _make_user(
        is_verified=False,
        verification_code=code,
        verification_code_expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=24),
    )
    db = _mock_db_with_user(user)

    result = await verify_email_code(db, user.email, code)

    assert result.is_verified is True
    assert result.verification_code is None
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_verify_email_wrong_code_raises():
    user = _make_user(verification_code="111111", is_verified=False)
    db = _mock_db_with_user(user)

    with pytest.raises(AuthError, match="Invalid or expired"):
        await verify_email_code(db, user.email, "999999")


@pytest.mark.asyncio
async def test_verify_email_expired_raises():
    code = "123456"
    user = _make_user(
        is_verified=False,
        verification_code=code,
        verification_code_expires_at=datetime.now(tz=timezone.utc) - timedelta(hours=1),
    )
    db = _mock_db_with_user(user)

    with pytest.raises(AuthError, match="Invalid or expired"):
        await verify_email_code(db, user.email, code)


@pytest.mark.asyncio
async def test_verify_email_already_verified_is_idempotent():
    user = _make_user(is_verified=True, verification_code="123456")
    db = _mock_db_with_user(user)

    result = await verify_email_code(db, user.email, "123456")
    assert result.is_verified is True
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_verify_email_unknown_user_raises():
    db = _mock_db_with_user(None)

    with pytest.raises(AuthError, match="No account found"):
        await verify_email_code(db, "nobody@example.com", "123456")


# ---------------------------------------------------------------------------
# resend_verification_code
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resend_generates_new_code():
    user = _make_user(is_verified=False, verification_code="OLDCODE")
    db = _mock_db_with_user(user)

    result = await resend_verification_code(db, user.email)

    assert result.verification_code != "OLDCODE"
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_resend_raises_if_already_verified():
    user = _make_user(is_verified=True)
    db = _mock_db_with_user(user)

    with pytest.raises(AuthError, match="already verified"):
        await resend_verification_code(db, user.email)


@pytest.mark.asyncio
async def test_resend_raises_if_user_not_found():
    db = _mock_db_with_user(None)

    with pytest.raises(AuthError, match="No account found"):
        await resend_verification_code(db, "ghost@example.com")


# ---------------------------------------------------------------------------
# authenticate_user — new guards
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_authenticate_blocks_unverified_user():
    user = _make_user(is_verified=False, is_active=False, approval_status="pending")
    db = _mock_db_with_user(user)

    with patch("app.services.auth_service.verify_password", return_value=True):
        with pytest.raises(AuthError, match="not verified"):
            await authenticate_user(db, user.email, "Secret123!")


@pytest.mark.asyncio
async def test_authenticate_blocks_pending_approval():
    user = _make_user(is_verified=True, is_active=False, approval_status="pending")
    db = _mock_db_with_user(user)

    with patch("app.services.auth_service.verify_password", return_value=True):
        with pytest.raises(AuthError, match="awaiting administrator approval"):
            await authenticate_user(db, user.email, "Secret123!")


@pytest.mark.asyncio
async def test_authenticate_blocks_rejected_user():
    user = _make_user(is_verified=True, is_active=False, approval_status="rejected")
    db = _mock_db_with_user(user)

    with patch("app.services.auth_service.verify_password", return_value=True):
        with pytest.raises(AuthError, match="not approved"):
            await authenticate_user(db, user.email, "Secret123!")


@pytest.mark.asyncio
async def test_authenticate_allows_active_approved_user():
    user = _make_user(is_verified=True, is_active=True, approval_status="approved")
    db = _mock_db_with_user(user)

    with patch("app.services.auth_service.verify_password", return_value=True):
        result = await authenticate_user(db, user.email, "Secret123!")
    assert result == user


# ---------------------------------------------------------------------------
# approve_user / reject_user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approve_user_activates_account():
    user = _make_user(is_verified=True, is_active=False, approval_status="pending")
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = user
    db = AsyncMock()
    db.execute.return_value = result_mock

    approved = await approve_user(db, user.id, "lecturer", None)

    assert approved.is_active is True
    assert approved.approval_status == "approved"
    assert approved.role == UserRole.LECTURER
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_reject_user_deactivates_account():
    user = _make_user(is_verified=True, is_active=False, approval_status="pending")
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = user
    db = AsyncMock()
    db.execute.return_value = result_mock

    rejected = await reject_user(db, user.id, reason="Duplicate registration.")

    assert rejected.is_active is False
    assert rejected.approval_status == "rejected"
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_approve_user_not_found_raises():
    from app.core.exceptions import NotFoundError
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    db = AsyncMock()
    db.execute.return_value = result_mock

    with pytest.raises(NotFoundError):
        await approve_user(db, uuid.uuid4(), "lecturer", None)


@pytest.mark.asyncio
async def test_reject_user_not_found_raises():
    from app.core.exceptions import NotFoundError
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    db = AsyncMock()
    db.execute.return_value = result_mock

    with pytest.raises(NotFoundError):
        await reject_user(db, uuid.uuid4())


# ---------------------------------------------------------------------------
# Tenant isolation — registration does not set institution_id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_public_register_does_not_assign_institution():
    from app.schemas.auth import PublicRegisterRequest

    data = PublicRegisterRequest(
        email="isolated@example.com",
        full_name="Isolated User",
        password="Secret123!",
        institution_name="Any Uni",
        role_requested=UserRole.LECTURER,
    )

    db = AsyncMock()
    db.refresh = AsyncMock()

    captured_kwargs: dict = {}

    original_user_init = User.__init__

    def _capture_init(self_inner, **kwargs: object) -> None:
        captured_kwargs.update(kwargs)

    with patch("app.services.auth_service.get_user_by_email", return_value=None):
        with patch("app.services.auth_service.hash_password", return_value="HASHED"):
            await public_register_user(db, data)

    added_user = db.add.call_args[0][0]
    assert added_user.institution_id is None
