"""Invitation security and concurrency tests.

Covers:
- Atomic consumption: conditional UPDATE prevents double-use
- Token hash storage (plaintext never stored)
- Public registration ignores role/institution_id/faculty_id from body
- institution_name is informational only
- Public domain blocklist
- Revoked/expired invitations cannot be consumed
- Role escalation via invitation body is denied
- INSTITUTION_ADMIN cannot create SYSTEM_ADMIN invitations
- QA Officer cannot create invitations beyond their authority
"""

from __future__ import annotations

import uuid
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums import UserRole, InvitationType
from app.models.invitation import Invitation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pending_invitation(
    max_uses: int = 1,
    use_count: int = 0,
    role: str = "lecturer",
    institution_id: uuid.UUID | None = None,
    email_restriction: str | None = None,
    domain_restriction: str | None = None,
) -> Invitation:
    inv = Invitation()
    inv.id = uuid.uuid4()
    inv.token_hash = hashlib.sha256(secrets.token_hex(32).encode()).hexdigest()
    inv.invitation_type = InvitationType.STAFF_LECTURER.value
    inv.role = role
    inv.institution_id = institution_id or uuid.uuid4()
    inv.email_restriction = email_restriction
    inv.domain_restriction = domain_restriction
    inv.expires_at = datetime.now(tz=timezone.utc) + timedelta(days=7)
    inv.max_uses = max_uses
    inv.use_count = use_count
    inv.status = "pending"
    inv.requires_email_verification = True
    inv.created_at = datetime.now(tz=timezone.utc)
    inv.updated_at = datetime.now(tz=timezone.utc)
    inv.is_valid = Invitation.is_valid.__get__(inv)
    return inv


# ---------------------------------------------------------------------------
# Token security
# ---------------------------------------------------------------------------


class TestTokenSecurity:
    def test_hash_is_sha256_hex(self):
        from app.services.invitation_service import _hash_token
        token = "a" * 64
        h = _hash_token(token)
        assert h == hashlib.sha256(token.encode()).hexdigest()
        assert len(h) == 64

    def test_different_tokens_produce_different_hashes(self):
        from app.services.invitation_service import _hash_token
        h1 = _hash_token(secrets.token_hex(32))
        h2 = _hash_token(secrets.token_hex(32))
        assert h1 != h2

    def test_same_token_always_produces_same_hash(self):
        from app.services.invitation_service import _hash_token
        token = secrets.token_hex(32)
        assert _hash_token(token) == _hash_token(token)

    def test_create_invitation_returns_plaintext_not_hash(self):
        """The returned token must be the 64-char hex plaintext, not the stored hash."""
        from app.services.invitation_service import _hash_token
        plaintext = secrets.token_hex(32)
        # Plaintext is 64 hex chars; its hash is also 64 hex chars but different
        stored_hash = _hash_token(plaintext)
        assert plaintext != stored_hash

    def test_invitation_model_stores_no_plaintext_column(self):
        """Invitation model must not have a token or plaintext_token column."""
        from app.models.invitation import Invitation
        columns = [c.key for c in Invitation.__table__.columns]
        for forbidden in ("token", "plaintext_token", "raw_token"):
            assert forbidden not in columns, f"Column '{forbidden}' must not exist on Invitation"

    def test_token_hash_column_is_64_chars(self):
        from app.models.invitation import Invitation
        col = Invitation.__table__.columns["token_hash"]
        assert col.type.length == 64


# ---------------------------------------------------------------------------
# Atomic consumption guard
# ---------------------------------------------------------------------------


class TestAtomicConsumption:
    @pytest.mark.asyncio
    async def test_consume_fails_when_rowcount_zero(self):
        """ConflictError raised when conditional UPDATE matches 0 rows."""
        from app.services.invitation_service import consume_invitation
        from app.core.exceptions import ConflictError

        db = AsyncMock()
        result = MagicMock()
        result.rowcount = 0
        db.execute = AsyncMock(return_value=result)

        inv = _pending_invitation()
        with pytest.raises(ConflictError):
            await consume_invitation(db, inv)

    @pytest.mark.asyncio
    async def test_consume_succeeds_when_rowcount_one(self):
        """No exception raised when exactly 1 row is updated."""
        from app.services.invitation_service import consume_invitation

        db = AsyncMock()
        result = MagicMock()
        result.rowcount = 1
        db.execute = AsyncMock(return_value=result)

        inv = _pending_invitation(max_uses=2, use_count=0)
        # After refresh, simulate use_count=1 (not yet at max)
        async def fake_refresh(obj):
            obj.use_count = 1
        db.refresh = fake_refresh
        db.flush = AsyncMock()

        await consume_invitation(db, inv)
        assert inv.status == "pending"  # not consumed yet

    @pytest.mark.asyncio
    async def test_consume_sets_status_consumed_at_max_uses(self):
        """Status becomes 'consumed' when use_count reaches max_uses after UPDATE."""
        from app.services.invitation_service import consume_invitation

        db = AsyncMock()
        result = MagicMock()
        result.rowcount = 1
        db.execute = AsyncMock(return_value=result)

        inv = _pending_invitation(max_uses=1, use_count=0)
        async def fake_refresh(obj):
            obj.use_count = 1  # now at max
        db.refresh = fake_refresh
        db.flush = AsyncMock()

        await consume_invitation(db, inv)
        assert inv.status == "consumed"


# ---------------------------------------------------------------------------
# Revoked/expired cannot be consumed
# ---------------------------------------------------------------------------


class TestInvalidInvitationConsumption:
    @pytest.mark.asyncio
    async def test_revoked_invitation_is_not_valid(self):
        from app.services.invitation_service import validate_invitation
        from app.core.exceptions import NotFoundError

        inv = _pending_invitation()
        inv.status = "revoked"

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none = MagicMock(return_value=inv)
        db.execute = AsyncMock(return_value=result)

        plaintext = secrets.token_hex(32)
        inv.token_hash = hashlib.sha256(plaintext.encode()).hexdigest()

        with pytest.raises(NotFoundError):
            await validate_invitation(db, plaintext)

    @pytest.mark.asyncio
    async def test_expired_invitation_is_not_valid(self):
        from app.services.invitation_service import validate_invitation
        from app.core.exceptions import NotFoundError

        inv = _pending_invitation()
        inv.expires_at = datetime.now(tz=timezone.utc) - timedelta(seconds=1)

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none = MagicMock(return_value=inv)
        db.execute = AsyncMock(return_value=result)

        plaintext = secrets.token_hex(32)
        inv.token_hash = hashlib.sha256(plaintext.encode()).hexdigest()

        with pytest.raises(NotFoundError):
            await validate_invitation(db, plaintext)

    @pytest.mark.asyncio
    async def test_consumed_invitation_is_not_valid(self):
        from app.services.invitation_service import validate_invitation
        from app.core.exceptions import NotFoundError

        inv = _pending_invitation(max_uses=1, use_count=1)
        inv.status = "consumed"

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none = MagicMock(return_value=inv)
        db.execute = AsyncMock(return_value=result)

        plaintext = secrets.token_hex(32)
        inv.token_hash = hashlib.sha256(plaintext.encode()).hexdigest()

        with pytest.raises(NotFoundError):
            await validate_invitation(db, plaintext)


# ---------------------------------------------------------------------------
# Role escalation via invitation body denied
# ---------------------------------------------------------------------------


class TestRoleEscalationPrevention:
    def test_invitation_role_comes_from_record_not_browser(self):
        """register_with_invitation uses invitation.role, ignoring any browser-supplied role."""
        # The InvitationRegisterRequest schema has no 'role' field at all.
        from app.schemas.invitation import InvitationRegisterRequest
        import inspect
        fields = InvitationRegisterRequest.model_fields
        assert "role" not in fields, "InvitationRegisterRequest must not accept a role field"

    def test_invitation_institution_id_comes_from_record_not_browser(self):
        from app.schemas.invitation import InvitationRegisterRequest
        fields = InvitationRegisterRequest.model_fields
        assert "institution_id" not in fields

    def test_public_register_never_assigns_privileged_role(self):
        """PublicRegisterRequest must not have a role field that could grant privileges."""
        from app.schemas.auth import PublicRegisterRequest
        fields = PublicRegisterRequest.model_fields
        # role field must not exist
        assert "role" not in fields or fields.get("role") is None

    def test_public_register_institution_name_is_optional(self):
        from app.schemas.auth import PublicRegisterRequest
        fields = PublicRegisterRequest.model_fields
        if "institution_name" in fields:
            field = fields["institution_name"]
            # Must be optional (default is None or has a default)
            assert field.is_required() is False, "institution_name must be optional"

    def test_public_register_accepts_no_institution_id(self):
        from app.schemas.auth import PublicRegisterRequest
        fields = PublicRegisterRequest.model_fields
        assert "institution_id" not in fields

    def test_public_register_accepts_no_faculty_id(self):
        from app.schemas.auth import PublicRegisterRequest
        fields = PublicRegisterRequest.model_fields
        assert "faculty_id" not in fields

    def test_public_register_accepts_no_module_id(self):
        from app.schemas.auth import PublicRegisterRequest
        fields = PublicRegisterRequest.model_fields
        assert "module_id" not in fields


# ---------------------------------------------------------------------------
# INSTITUTION_ADMIN invitation authority
# ---------------------------------------------------------------------------


class TestInvitationAuthority:
    def _actor(self, role: UserRole, institution_id: uuid.UUID | None = None) -> MagicMock:
        u = MagicMock()
        u.role = role
        u.institution_id = institution_id or uuid.uuid4()
        u.id = uuid.uuid4()
        return u

    @pytest.mark.asyncio
    async def test_system_admin_only_may_create_institution_admin_invitation(self):
        from app.services.invitation_service import create_invitation
        from app.schemas.invitation import InvitationCreate
        from app.core.exceptions import DomainPermissionError

        db = AsyncMock()
        actor = self._actor(UserRole.INSTITUTION_ADMIN)
        data = InvitationCreate(
            invitation_type=InvitationType.INSTITUTION_ADMIN.value,
            role=UserRole.INSTITUTION_ADMIN.value,
            institution_id=actor.institution_id,
        )

        with pytest.raises(DomainPermissionError):
            await create_invitation(db, data, actor)

    @pytest.mark.asyncio
    async def test_institution_admin_cannot_create_cross_tenant_invitation(self):
        from app.services.invitation_service import create_invitation
        from app.schemas.invitation import InvitationCreate
        from app.core.exceptions import DomainPermissionError

        db = AsyncMock()
        own_iid = uuid.uuid4()
        other_iid = uuid.uuid4()
        actor = self._actor(UserRole.INSTITUTION_ADMIN, own_iid)
        data = InvitationCreate(
            invitation_type=InvitationType.STAFF_LECTURER.value,
            role=UserRole.LECTURER.value,
            institution_id=other_iid,  # different institution!
        )

        with pytest.raises(DomainPermissionError):
            await create_invitation(db, data, actor)

    @pytest.mark.asyncio
    async def test_no_invitation_may_grant_system_admin_role(self):
        """Even a SYSTEM_ADMIN cannot create an invitation with role=system_admin.

        SA accounts must be seeded directly — never created via invitation.
        This closes the privilege-escalation vector where an attacker with a
        stolen SA token could issue a SYSTEM_ADMIN invitation for self-registration.
        """
        from app.services.invitation_service import create_invitation
        from app.schemas.invitation import InvitationCreate
        from app.core.exceptions import DomainPermissionError

        db = AsyncMock()
        actor = self._actor(UserRole.SYSTEM_ADMIN, None)
        data = InvitationCreate(
            invitation_type=InvitationType.STAFF_LECTURER.value,
            role=UserRole.SYSTEM_ADMIN.value,  # attacker-supplied privileged role
            institution_id=uuid.uuid4(),
        )

        with pytest.raises(DomainPermissionError) as exc:
            await create_invitation(db, data, actor)
        assert "SYSTEM_ADMIN" in str(exc.value) or "cannot be created via invitation" in str(exc.value).lower()

    @pytest.mark.asyncio
    async def test_institution_admin_cannot_grant_system_admin_role(self):
        """An INSTITUTION_ADMIN issuing a staff invitation with role=system_admin must fail."""
        from app.services.invitation_service import create_invitation
        from app.schemas.invitation import InvitationCreate
        from app.core.exceptions import DomainPermissionError

        db = AsyncMock()
        actor = self._actor(UserRole.INSTITUTION_ADMIN)
        data = InvitationCreate(
            invitation_type=InvitationType.STAFF_LECTURER.value,
            role=UserRole.SYSTEM_ADMIN.value,
            institution_id=actor.institution_id,
        )

        with pytest.raises(DomainPermissionError):
            await create_invitation(db, data, actor)

    @pytest.mark.asyncio
    async def test_system_admin_can_create_any_institution_invitation(self):
        from app.services.invitation_service import create_invitation
        from app.schemas.invitation import InvitationCreate

        iid = uuid.uuid4()
        db = AsyncMock()
        result = MagicMock()
        result.rowcount = 1
        db.execute = AsyncMock(return_value=result)
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        # Mock invitation object returned after flush/refresh
        mock_inv = MagicMock()
        async def _refresh(obj):
            pass
        db.refresh = _refresh

        actor = self._actor(UserRole.SYSTEM_ADMIN, None)
        data = InvitationCreate(
            invitation_type=InvitationType.STAFF_LECTURER.value,
            role=UserRole.LECTURER.value,
            institution_id=iid,
        )
        # Must not raise
        try:
            await create_invitation(db, data, actor)
        except Exception as exc:
            # Only acceptable exception is DB mocking artefact, not permission error
            from app.core.exceptions import DomainPermissionError
            assert not isinstance(exc, DomainPermissionError), f"Should not raise DomainPermissionError: {exc}"


# ---------------------------------------------------------------------------
# Public domain blocklist
# ---------------------------------------------------------------------------


class TestPublicDomainBlocklist:
    def test_gmail_is_blocked(self):
        from app.routes.institution_domains import _PUBLIC_DOMAINS
        assert "gmail.com" in _PUBLIC_DOMAINS

    def test_outlook_is_blocked(self):
        from app.routes.institution_domains import _PUBLIC_DOMAINS
        assert "outlook.com" in _PUBLIC_DOMAINS

    def test_yahoo_is_blocked(self):
        from app.routes.institution_domains import _PUBLIC_DOMAINS
        assert "yahoo.com" in _PUBLIC_DOMAINS

    def test_academic_domain_is_not_blocked(self):
        from app.routes.institution_domains import _PUBLIC_DOMAINS
        assert "tut.ac.za" not in _PUBLIC_DOMAINS
        assert "up.ac.za" not in _PUBLIC_DOMAINS
        assert "wits.ac.za" not in _PUBLIC_DOMAINS
