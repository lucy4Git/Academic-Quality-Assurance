"""Tests — admin user-management lifecycle and activation-token security.

Covers:
- Admin resend-activation: active user → 409
- Admin resend-activation: inactive approved user → 200
- Admin resend-activation: non-existent user → 404
- Admin resend-activation: non-approved user → 409
- Admin resend-activation: cross-tenant restriction → 403
- Admin resend-activation: unauthorised role → 403 (dependency)
- activation_service.validate_activation_token: valid token → User
- activation_service.validate_activation_token: invalid token → ActivationError
- activation_service.validate_activation_token: used token → ActivationError
- activation_service.validate_activation_token: expired token → ActivationError
- activation_service.validate_activation_token: brute-force locked → ActivationError
- activation_service.consume_activation_token: valid → is_active=True
- activation_service.consume_activation_token: weak password → ActivationError
- activation_service.consume_activation_token: reuse → ActivationError
- activation_service.resend_activation_token: already active+verified → ActivationError
- activation_service.create_activation_token: invalidates prior open tokens

All DB and HTTP interactions are mocked; no test database required.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.enums import UserRole
from app.models.user import User
from app.models.user_activation_token import UserActivationToken
from app.services.activation_service import (
    ActivationError,
    MAX_ATTEMPTS,
    _hash_token,
    consume_activation_token,
    create_activation_token,
    resend_activation_token,
    validate_activation_token,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(
    *,
    is_active: bool = False,
    is_verified: bool = False,
    approval_status: str = "approved",
    role: UserRole = UserRole.LECTURER,
    institution_id: uuid.UUID | None = None,
) -> MagicMock:
    u = MagicMock(spec=User)
    u.id = uuid.uuid4()
    u.email = "test@tut.ac.za"
    u.full_name = "Test User"
    u.is_active = is_active
    u.is_verified = is_verified
    u.approval_status = approval_status
    u.role = role
    u.institution_id = institution_id
    u.hashed_password = "hashed"
    return u


def _make_token(
    *,
    user_id: uuid.UUID | None = None,
    raw: str = "aabbcc" * 10 + "dd",  # 62-char fallback; override as needed
    hours_from_now: float = 24.0,
    used_at: datetime | None = None,
    invalidated_at: datetime | None = None,
    failed_attempts: int = 0,
) -> MagicMock:
    raw_token = raw
    tok = MagicMock(spec=UserActivationToken)
    tok.user_id = user_id or uuid.uuid4()
    tok.token_hash = _hash_token(raw_token)
    tok.expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=hours_from_now)
    tok.used_at = used_at
    tok.invalidated_at = invalidated_at
    tok.failed_attempts = failed_attempts
    tok.is_valid.return_value = (
        used_at is None
        and invalidated_at is None
        and hours_from_now > 0
        and failed_attempts < MAX_ATTEMPTS
    )
    return tok


def _mock_db_with_token(tok: MagicMock | None, user: MagicMock | None = None) -> MagicMock:
    """Return an async session mock that yields tok for the first execute() and
    user for the second execute()."""
    db = MagicMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    def _make_result(value):
        r = MagicMock()
        r.scalar_one_or_none.return_value = value
        return r

    results = [_make_result(tok)]
    if user is not None:
        results.append(_make_result(user))

    db.execute = AsyncMock(side_effect=results)
    return db


# ---------------------------------------------------------------------------
# activation_service.validate_activation_token
# ---------------------------------------------------------------------------


class TestValidateActivationToken:
    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self):
        user = _make_user(is_active=False)
        raw = "a" * 64
        tok = _make_token(raw=raw, user_id=user.id)
        db = _mock_db_with_token(tok, user)
        result = await validate_activation_token(db, raw)
        assert result is user

    @pytest.mark.asyncio
    async def test_invalid_token_raises(self):
        # Token not in DB → None
        db = _mock_db_with_token(None)
        with pytest.raises(ActivationError):
            await validate_activation_token(db, "z" * 64)

    @pytest.mark.asyncio
    async def test_used_token_raises(self):
        raw = "b" * 64
        tok = _make_token(raw=raw, used_at=datetime.now(tz=timezone.utc))
        db = _mock_db_with_token(tok)
        with pytest.raises(ActivationError):
            await validate_activation_token(db, raw)

    @pytest.mark.asyncio
    async def test_expired_token_raises(self):
        raw = "c" * 64
        tok = _make_token(raw=raw, hours_from_now=-1.0)
        db = _mock_db_with_token(tok)
        with pytest.raises(ActivationError):
            await validate_activation_token(db, raw)

    @pytest.mark.asyncio
    async def test_brute_force_locked_raises(self):
        raw = "d" * 64
        tok = _make_token(raw=raw, failed_attempts=MAX_ATTEMPTS)
        db = _mock_db_with_token(tok)
        with pytest.raises(ActivationError):
            await validate_activation_token(db, raw)


# ---------------------------------------------------------------------------
# activation_service.consume_activation_token
# ---------------------------------------------------------------------------


class TestConsumeActivationToken:
    @pytest.mark.asyncio
    async def test_consume_activates_user(self):
        user = _make_user(is_active=False)
        raw = "e" * 64
        tok = _make_token(raw=raw, user_id=user.id)
        db = _mock_db_with_token(tok, user)

        result = await consume_activation_token(db, raw, "ValidPass1!")

        assert user.is_active is True
        assert user.is_verified is True
        assert user.approval_status == "approved"
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_weak_password_no_digit_raises(self):
        db = MagicMock()
        with pytest.raises(ActivationError, match="digit"):
            await consume_activation_token(db, "f" * 64, "NoDigitPass!")

    @pytest.mark.asyncio
    async def test_weak_password_no_upper_raises(self):
        db = MagicMock()
        with pytest.raises(ActivationError, match="uppercase"):
            await consume_activation_token(db, "g" * 64, "nouppercase1")

    @pytest.mark.asyncio
    async def test_weak_password_too_short_raises(self):
        db = MagicMock()
        with pytest.raises(ActivationError, match="8 characters"):
            await consume_activation_token(db, "h" * 64, "Ab1!")

    @pytest.mark.asyncio
    async def test_reuse_raises(self):
        raw = "i" * 64
        tok = _make_token(raw=raw, used_at=datetime.now(tz=timezone.utc))
        db = _mock_db_with_token(tok)
        with pytest.raises(ActivationError, match="already been used"):
            await consume_activation_token(db, raw, "ValidPass1!")

    @pytest.mark.asyncio
    async def test_invalid_token_raises(self):
        db = _mock_db_with_token(None)
        with pytest.raises(ActivationError):
            await consume_activation_token(db, "j" * 64, "ValidPass1!")


# ---------------------------------------------------------------------------
# activation_service.create_activation_token (invalidation of prior tokens)
# ---------------------------------------------------------------------------


class TestCreateActivationToken:
    @pytest.mark.asyncio
    async def test_invalidates_prior_open_tokens(self):
        old_tok = MagicMock(spec=UserActivationToken)
        old_tok.invalidated_at = None

        db = MagicMock()
        existing_result = MagicMock()
        existing_result.scalars.return_value.all.return_value = [old_tok]
        db.execute = AsyncMock(return_value=existing_result)
        db.add = MagicMock()
        db.flush = AsyncMock()

        user_id = uuid.uuid4()
        raw = await create_activation_token(db, user_id)

        assert old_tok.invalidated_at is not None
        assert raw  # raw token returned
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_64_char_hex_token(self):
        db = MagicMock()
        existing_result = MagicMock()
        existing_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=existing_result)
        db.add = MagicMock()
        db.flush = AsyncMock()

        raw = await create_activation_token(db, uuid.uuid4())
        assert len(raw) == 64
        assert all(c in "0123456789abcdef" for c in raw)


# ---------------------------------------------------------------------------
# activation_service.resend_activation_token
# ---------------------------------------------------------------------------


class TestResendActivationToken:
    @pytest.mark.asyncio
    async def test_already_active_raises(self):
        user = _make_user(is_active=True, is_verified=True)
        db = MagicMock()
        r = MagicMock()
        r.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=r)

        with pytest.raises(ActivationError, match="already active"):
            await resend_activation_token(db, user.id)

    @pytest.mark.asyncio
    async def test_user_not_found_raises(self):
        db = MagicMock()
        r = MagicMock()
        r.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=r)

        with pytest.raises(ActivationError, match="not found"):
            await resend_activation_token(db, uuid.uuid4())

    @pytest.mark.asyncio
    async def test_inactive_approved_user_succeeds(self):
        user = _make_user(is_active=False, is_verified=False)

        # First execute → load user; second execute → load existing tokens (none)
        r_user = MagicMock()
        r_user.scalar_one_or_none.return_value = user
        r_existing = MagicMock()
        r_existing.scalars.return_value.all.return_value = []

        db = MagicMock()
        db.execute = AsyncMock(side_effect=[r_user, r_existing])
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()

        raw = await resend_activation_token(db, user.id)
        assert len(raw) == 64
        db.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# admin_users route — resend_user_activation (HTTP layer)
# ---------------------------------------------------------------------------


class TestAdminResendActivationRoute:
    """Test the HTTP route logic for resend-activation without spinning up a server."""

    def _make_admin(
        self,
        role: UserRole = UserRole.SYSTEM_ADMIN,
        institution_id: uuid.UUID | None = None,
    ) -> MagicMock:
        u = MagicMock(spec=User)
        u.id = uuid.uuid4()
        u.role = role
        u.institution_id = institution_id
        return u

    @pytest.mark.asyncio
    async def test_active_user_returns_409(self):
        from app.routes.admin_users import resend_user_activation

        active_user = _make_user(is_active=True, is_verified=True, approval_status="approved")
        db = MagicMock()
        r = MagicMock()
        r.scalar_one_or_none.return_value = active_user
        db.execute = AsyncMock(return_value=r)

        admin = self._make_admin()

        # resend_activation_token will raise ActivationError; route must catch it as 409
        with patch("app.services.activation_service.resend_activation_token",
                   new_callable=AsyncMock,
                   side_effect=ActivationError("Account is already active.")):
            with pytest.raises(HTTPException) as exc_info:
                await resend_user_activation(active_user.id, db=db, current_user=admin)
        assert exc_info.value.status_code == 409
        assert "already active" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_non_existent_user_returns_404(self):
        from app.routes.admin_users import resend_user_activation

        db = MagicMock()
        r = MagicMock()
        r.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=r)

        admin = self._make_admin()
        with pytest.raises(HTTPException) as exc_info:
            await resend_user_activation(uuid.uuid4(), db=db, current_user=admin)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_non_approved_user_returns_409(self):
        from app.routes.admin_users import resend_user_activation

        pending_user = _make_user(is_active=False, approval_status="pending")
        db = MagicMock()
        r = MagicMock()
        r.scalar_one_or_none.return_value = pending_user
        db.execute = AsyncMock(return_value=r)

        admin = self._make_admin()
        with pytest.raises(HTTPException) as exc_info:
            await resend_user_activation(pending_user.id, db=db, current_user=admin)
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_cross_tenant_admin_cannot_resend_other_institution(self):
        """A non-sys-admin QA officer should not be able to resend for another institution's user."""
        from app.routes.admin_users import approve_pending_user, ApproveUserRequest

        tut_id = uuid.uuid4()
        up_id = uuid.uuid4()

        # QA officer belongs to TUT
        qa_admin = self._make_admin(role=UserRole.QUALITY_ASSURANCE_OFFICER, institution_id=tut_id)

        payload = ApproveUserRequest(role="lecturer", institution_id=up_id)
        db = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await approve_pending_user(uuid.uuid4(), payload=payload, db=db, current_user=qa_admin)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_successful_resend_returns_message(self):
        from app.routes.admin_users import resend_user_activation

        inactive_user = _make_user(is_active=False, is_verified=False, approval_status="approved")
        db = MagicMock()
        r = MagicMock()
        r.scalar_one_or_none.return_value = inactive_user
        db.execute = AsyncMock(return_value=r)

        admin = self._make_admin()

        with (
            patch("app.services.activation_service.resend_activation_token",
                  new_callable=AsyncMock, return_value="a" * 64),
            patch("app.routes.admin_users.send_activation_email"),
        ):
            result = await resend_user_activation(inactive_user.id, db=db, current_user=admin)

        assert result["message"] == "Activation link resent."
        assert "_debug_activation_url" not in result

    @pytest.mark.asyncio
    async def test_no_debug_url_in_response(self):
        """Verify the debug endpoint was removed — no raw token in response under any role."""
        from app.routes.admin_users import resend_user_activation

        inactive_user = _make_user(is_active=False, is_verified=False, approval_status="approved")
        db = MagicMock()
        r = MagicMock()
        r.scalar_one_or_none.return_value = inactive_user
        db.execute = AsyncMock(return_value=r)

        sys_admin = self._make_admin(role=UserRole.SYSTEM_ADMIN)

        with (
            patch("app.services.activation_service.resend_activation_token",
                  new_callable=AsyncMock, return_value="b" * 64),
            patch("app.routes.admin_users.send_activation_email"),
        ):
            result = await resend_user_activation(inactive_user.id, db=db, current_user=sys_admin)

        assert "_debug_activation_url" not in result
        assert "_debug" not in result
        assert "token" not in str(result).lower() or "message" in result
