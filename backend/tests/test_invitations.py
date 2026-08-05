"""Tests for the invitation model, service, and registration flow.

Security invariants verified:
- Token is hashed on storage; plaintext never appears in DB lookups
- Role/institution_id from invitation cannot be overridden by browser
- Expired invitations are rejected
- Consumed invitations are rejected (replay protection)
- Revoked invitations are rejected
- Email-restriction and domain-restriction are enforced
- Tenant isolation: institution admin cannot revoke another institution's invitation
- INSTITUTION_ADMIN invitation type requires SYSTEM_ADMIN authority
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.enums import InvitationType, InvitationStatus, UserRole
from app.models.invitation import Invitation
from app.models.institution_domain import InstitutionDomain
from app.core.exceptions import ConflictError, DomainPermissionError, NotFoundError
from app.schemas.invitation import InvitationCreate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user(role=UserRole.SYSTEM_ADMIN, institution_id=None):
    u = MagicMock()
    u.id = uuid.uuid4()
    u.role = role
    u.institution_id = institution_id
    return u


def _invitation(
    status="pending",
    use_count=0,
    max_uses=1,
    expires_delta=timedelta(days=7),
    role=UserRole.LECTURER.value,
    institution_id=None,
    email_restriction=None,
    domain_restriction=None,
    requires_email_verification=True,
):
    inv = MagicMock(spec=Invitation)
    inv.id = uuid.uuid4()
    inv.token_hash = hashlib.sha256(b"testtoken").hexdigest()
    inv.status = status
    inv.use_count = use_count
    inv.max_uses = max_uses
    inv.expires_at = datetime.now(tz=timezone.utc) + expires_delta
    inv.role = role
    inv.institution_id = institution_id or uuid.uuid4()
    inv.email_restriction = email_restriction
    inv.domain_restriction = domain_restriction
    inv.requires_email_verification = requires_email_verification
    inv.is_valid = Invitation.is_valid.__get__(inv)
    return inv


# ---------------------------------------------------------------------------
# Invitation.is_valid() unit tests
# ---------------------------------------------------------------------------

class TestInvitationIsValid:
    def test_valid_pending_not_expired_not_exhausted(self):
        inv = _invitation()
        assert inv.is_valid() is True

    def test_revoked_is_invalid(self):
        inv = _invitation(status="revoked")
        assert inv.is_valid() is False

    def test_consumed_is_invalid(self):
        inv = _invitation(status="consumed")
        assert inv.is_valid() is False

    def test_expired_is_invalid(self):
        inv = _invitation(expires_delta=timedelta(seconds=-1))
        assert inv.is_valid() is False

    def test_max_uses_exhausted_is_invalid(self):
        inv = _invitation(use_count=1, max_uses=1)
        assert inv.is_valid() is False

    def test_batch_invitation_still_valid_under_max_uses(self):
        inv = _invitation(use_count=4, max_uses=10)
        assert inv.is_valid() is True


# ---------------------------------------------------------------------------
# invitation_service unit tests (DB mocked)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


class TestCreateInvitation:
    @pytest.mark.asyncio
    async def test_creates_and_returns_plaintext_token(self, mock_db):
        from app.services.invitation_service import create_invitation

        creator = _user(role=UserRole.SYSTEM_ADMIN)
        data = InvitationCreate(
            invitation_type=InvitationType.STAFF_LECTURER.value,
            role=UserRole.LECTURER.value,
            expires_in_days=7,
        )

        mock_db.refresh = AsyncMock(side_effect=lambda inv: None)

        inv, token = await create_invitation(mock_db, data, creator)

        assert len(token) == 64  # 32 bytes → 64 hex chars
        assert inv.token_hash == hashlib.sha256(token.encode()).hexdigest()
        assert inv.invitation_type == InvitationType.STAFF_LECTURER.value

    @pytest.mark.asyncio
    async def test_plaintext_not_stored(self, mock_db):
        from app.services.invitation_service import create_invitation

        creator = _user(role=UserRole.SYSTEM_ADMIN)
        data = InvitationCreate(
            invitation_type=InvitationType.STAFF_LECTURER.value,
            role=UserRole.LECTURER.value,
        )

        mock_db.refresh = AsyncMock(side_effect=lambda inv: None)
        inv, token = await create_invitation(mock_db, data, creator)

        # Confirm no plaintext attribute on the model object
        assert not hasattr(inv, "token") or getattr(inv, "token", None) != token

    @pytest.mark.asyncio
    async def test_institution_admin_invitation_requires_system_admin(self, mock_db):
        from app.services.invitation_service import create_invitation

        creator = _user(role=UserRole.QUALITY_ASSURANCE_OFFICER)
        data = InvitationCreate(
            invitation_type=InvitationType.INSTITUTION_ADMIN.value,
            role=UserRole.QUALITY_ASSURANCE_OFFICER.value,
        )

        with pytest.raises(DomainPermissionError):
            await create_invitation(mock_db, data, creator)

    @pytest.mark.asyncio
    async def test_system_admin_can_create_institution_admin_invitation(self, mock_db):
        from app.services.invitation_service import create_invitation

        creator = _user(role=UserRole.SYSTEM_ADMIN)
        data = InvitationCreate(
            invitation_type=InvitationType.INSTITUTION_ADMIN.value,
            role=UserRole.QUALITY_ASSURANCE_OFFICER.value,
        )

        mock_db.refresh = AsyncMock(side_effect=lambda inv: None)
        inv, token = await create_invitation(mock_db, data, creator)
        assert inv.invitation_type == InvitationType.INSTITUTION_ADMIN.value


class TestValidateInvitation:
    @pytest.mark.asyncio
    async def test_valid_token_returns_invitation(self, mock_db):
        from app.services.invitation_service import validate_invitation

        token = "a" * 64
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        inv = _invitation()
        inv.token_hash = token_hash

        result = MagicMock()
        result.scalar_one_or_none.return_value = inv
        mock_db.execute = AsyncMock(return_value=result)

        returned = await validate_invitation(mock_db, token)
        assert returned is inv

    @pytest.mark.asyncio
    async def test_not_found_raises(self, mock_db):
        from app.services.invitation_service import validate_invitation

        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        with pytest.raises(NotFoundError):
            await validate_invitation(mock_db, "badtoken")

    @pytest.mark.asyncio
    async def test_expired_invitation_raises(self, mock_db):
        from app.services.invitation_service import validate_invitation

        inv = _invitation(expires_delta=timedelta(seconds=-1))
        result = MagicMock()
        result.scalar_one_or_none.return_value = inv
        mock_db.execute = AsyncMock(return_value=result)

        with pytest.raises(NotFoundError):
            await validate_invitation(mock_db, "anytoken")

    @pytest.mark.asyncio
    async def test_consumed_invitation_raises(self, mock_db):
        from app.services.invitation_service import validate_invitation

        inv = _invitation(status="consumed")
        result = MagicMock()
        result.scalar_one_or_none.return_value = inv
        mock_db.execute = AsyncMock(return_value=result)

        with pytest.raises(NotFoundError):
            await validate_invitation(mock_db, "anytoken")

    @pytest.mark.asyncio
    async def test_email_restriction_enforced(self, mock_db):
        from app.services.invitation_service import validate_invitation

        inv = _invitation(email_restriction="allowed@example.com")
        result = MagicMock()
        result.scalar_one_or_none.return_value = inv
        mock_db.execute = AsyncMock(return_value=result)

        with pytest.raises(DomainPermissionError):
            await validate_invitation(mock_db, "anytoken", email="other@example.com")

    @pytest.mark.asyncio
    async def test_domain_restriction_enforced(self, mock_db):
        from app.services.invitation_service import validate_invitation

        inv = _invitation(domain_restriction="tut.ac.za")
        result = MagicMock()
        result.scalar_one_or_none.return_value = inv
        mock_db.execute = AsyncMock(return_value=result)

        with pytest.raises(DomainPermissionError):
            await validate_invitation(mock_db, "anytoken", email="user@wits.ac.za")

    @pytest.mark.asyncio
    async def test_domain_restriction_passes_matching_domain(self, mock_db):
        from app.services.invitation_service import validate_invitation

        inv = _invitation(domain_restriction="tut.ac.za")
        result = MagicMock()
        result.scalar_one_or_none.return_value = inv
        mock_db.execute = AsyncMock(return_value=result)

        returned = await validate_invitation(mock_db, "anytoken", email="staff@tut.ac.za")
        assert returned is inv


class TestConsumeInvitation:
    @pytest.mark.asyncio
    async def test_increments_use_count(self, mock_db):
        from app.services.invitation_service import consume_invitation

        inv = _invitation(use_count=0, max_uses=2, status="pending")
        await consume_invitation(mock_db, inv)

        assert inv.use_count == 1
        assert inv.status == "pending"

    @pytest.mark.asyncio
    async def test_marks_consumed_when_max_reached(self, mock_db):
        from app.services.invitation_service import consume_invitation

        inv = _invitation(use_count=0, max_uses=1, status="pending")
        await consume_invitation(mock_db, inv)

        assert inv.use_count == 1
        assert inv.status == "consumed"


class TestRevokeInvitation:
    @pytest.mark.asyncio
    async def test_system_admin_can_revoke_any(self, mock_db):
        from app.services.invitation_service import revoke_invitation

        inv = _invitation()
        inv.institution_id = uuid.uuid4()
        result = MagicMock()
        result.scalar_one_or_none.return_value = inv
        mock_db.execute = AsyncMock(return_value=result)

        actor = _user(role=UserRole.SYSTEM_ADMIN)
        revoked = await revoke_invitation(mock_db, inv.id, actor)
        assert revoked.status == "revoked"

    @pytest.mark.asyncio
    async def test_qa_officer_cannot_revoke_other_institution(self, mock_db):
        from app.services.invitation_service import revoke_invitation

        inst_a = uuid.uuid4()
        inst_b = uuid.uuid4()
        inv = _invitation()
        inv.institution_id = inst_b
        result = MagicMock()
        result.scalar_one_or_none.return_value = inv
        mock_db.execute = AsyncMock(return_value=result)

        actor = _user(role=UserRole.QUALITY_ASSURANCE_OFFICER, institution_id=inst_a)
        with pytest.raises(DomainPermissionError):
            await revoke_invitation(mock_db, inv.id, actor)

    @pytest.mark.asyncio
    async def test_revoking_already_consumed_raises_conflict(self, mock_db):
        from app.services.invitation_service import revoke_invitation

        inv = _invitation(status="consumed")
        result = MagicMock()
        result.scalar_one_or_none.return_value = inv
        mock_db.execute = AsyncMock(return_value=result)

        actor = _user(role=UserRole.SYSTEM_ADMIN)
        with pytest.raises(ConflictError):
            await revoke_invitation(mock_db, inv.id, actor)


# ---------------------------------------------------------------------------
# Domain-based institution assignment tests
# ---------------------------------------------------------------------------

class TestGetInstitutionByEmailDomain:
    @pytest.mark.asyncio
    async def test_returns_domain_record_for_matching_domain(self, mock_db):
        from app.services.invitation_service import get_institution_by_email_domain

        domain_record = MagicMock(spec=InstitutionDomain)
        domain_record.institution_id = uuid.uuid4()

        result = MagicMock()
        result.scalar_one_or_none.return_value = domain_record
        mock_db.execute = AsyncMock(return_value=result)

        returned = await get_institution_by_email_domain(mock_db, "student@tut.ac.za")
        assert returned is domain_record

    @pytest.mark.asyncio
    async def test_returns_none_for_unrecognised_domain(self, mock_db):
        from app.services.invitation_service import get_institution_by_email_domain

        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        returned = await get_institution_by_email_domain(mock_db, "user@gmail.com")
        assert returned is None

    @pytest.mark.asyncio
    async def test_returns_none_for_email_without_at(self, mock_db):
        from app.services.invitation_service import get_institution_by_email_domain

        returned = await get_institution_by_email_domain(mock_db, "notanemail")
        assert returned is None


# ---------------------------------------------------------------------------
# Registration-with-invitation security tests
# ---------------------------------------------------------------------------

class TestRegisterWithInvitation:
    @pytest.mark.asyncio
    async def test_role_from_invitation_not_browser(self, mock_db):
        """Browser cannot override role; invitation's role wins."""
        from app.services.auth_service import register_with_invitation
        from app.schemas.invitation import InvitationRegisterRequest

        institution_id = uuid.uuid4()
        inv = _invitation(
            role=UserRole.LECTURER.value,
            institution_id=institution_id,
            requires_email_verification=False,
        )

        # validate_invitation returns inv; get_user_by_email returns None
        validate_result = MagicMock()
        validate_result.scalar_one_or_none.return_value = inv

        email_result = MagicMock()
        email_result.scalar_one_or_none.return_value = None

        call_count = [0]

        async def fake_execute(stmt):
            c = call_count[0]
            call_count[0] += 1
            if c == 0:
                return validate_result
            return email_result

        mock_db.execute = fake_execute
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        data = InvitationRegisterRequest(
            token="a" * 64,
            full_name="Test Lecturer",
            email="lecturer@tut.ac.za",
            password="SecurePass1!",
        )

        user, req_verify = await register_with_invitation(mock_db, data)

        # Role must come from invitation, not from data
        assert user.role == UserRole.LECTURER or str(user.role) in (UserRole.LECTURER.value, "lecturer")
        assert user.institution_id == institution_id
        assert req_verify is False

    @pytest.mark.asyncio
    async def test_duplicate_email_raises_auth_error(self, mock_db):
        from app.services.auth_service import register_with_invitation, AuthError
        from app.schemas.invitation import InvitationRegisterRequest

        inv = _invitation(requires_email_verification=False)
        existing_user = MagicMock()

        validate_result = MagicMock()
        validate_result.scalar_one_or_none.return_value = inv

        email_result = MagicMock()
        email_result.scalar_one_or_none.return_value = existing_user

        call_count = [0]

        async def fake_execute(stmt):
            c = call_count[0]
            call_count[0] += 1
            if c == 0:
                return validate_result
            return email_result

        mock_db.execute = fake_execute

        data = InvitationRegisterRequest(
            token="a" * 64,
            full_name="Duplicate",
            email="dup@example.com",
            password="SecurePass1!",
        )

        with pytest.raises(AuthError, match="already exists"):
            await register_with_invitation(mock_db, data)


# ---------------------------------------------------------------------------
# InvitationType and InvitationStatus enum sanity tests
# ---------------------------------------------------------------------------

class TestEnums:
    def test_all_invitation_types_defined(self):
        expected = {
            "STUDENT_ONBOARDING", "STAFF_LECTURER", "STAFF_COORDINATOR",
            "STAFF_HOD", "STAFF_DEAN", "QA_OFFICER",
            "EXTERNAL_MODERATOR", "INSTITUTION_ADMIN",
        }
        actual = {e.name for e in InvitationType}
        assert expected == actual

    def test_all_invitation_statuses_defined(self):
        expected = {"PENDING", "CONSUMED", "EXPIRED", "REVOKED"}
        actual = {e.name for e in InvitationStatus}
        assert expected == actual
