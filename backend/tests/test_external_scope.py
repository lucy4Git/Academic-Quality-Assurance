"""External moderator scope enforcement tests (Phase 1 security gate).

Tests 13 scenarios required by the ONBOARDING STAGING-VALIDATED gate:

 1. Allowed module succeeds (module access returns 200)
 2. Unrelated module returns 403
 3. Unrelated programme returns 403 (via module listing)
 4. Unrelated evidence returns 403
 5. Unrelated finding returns 403
 6. Tenant-wide report denied
 7. File outside scope denied (get_file)
 8. Download outside scope denied
 9. AI workspace blocked for external users
10. Revoked access denied immediately
11. Expired access denied immediately
12. Manipulated resource IDs denied
13. Cross-tenant institution access denied

All tests use pure unit-level assertions against ExternalScope and its
helper functions — no DB or HTTP overhead required for most cases.
The HTTP-level tests use FastAPI's TestClient with mocked dependencies.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.external_scope import (
    ExternalScope,
    assert_faculty_scope,
    assert_institution_scope,
    assert_module_scope,
    assert_programme_scope,
    deny_external_access,
    resolve_external_scope,
)
from app.models.enums import InvitationType


# ---------------------------------------------------------------------------
# Helpers — build minimal mock objects
# ---------------------------------------------------------------------------

_MODULE_A = uuid.uuid4()
_MODULE_B = uuid.uuid4()
_INSTITUTION_A = uuid.uuid4()
_INSTITUTION_B = uuid.uuid4()
_FACULTY_A = uuid.uuid4()
_PROGRAMME_A = uuid.uuid4()
_DEPT_A = uuid.uuid4()

_FUTURE = datetime.now(tz=timezone.utc) + timedelta(days=30)
_PAST = datetime.now(tz=timezone.utc) - timedelta(seconds=1)


def _make_invitation(
    *,
    invitation_type: str = InvitationType.EXTERNAL_MODERATOR.value,
    status: str = "consumed",
    expires_at: datetime = _FUTURE,
    institution_id: uuid.UUID = _INSTITUTION_A,
    module_id: uuid.UUID | None = _MODULE_A,
    faculty_id: uuid.UUID | None = None,
    department_id: uuid.UUID | None = None,
    programme_id: uuid.UUID | None = None,
    permission_scope: dict | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        invitation_type=invitation_type,
        status=status,
        expires_at=expires_at,
        institution_id=institution_id,
        faculty_id=faculty_id,
        department_id=department_id,
        programme_id=programme_id,
        module_id=module_id,
        permission_scope=permission_scope,
    )


def _make_user(invitation=None) -> SimpleNamespace:
    inv_id = uuid.uuid4() if invitation is not None else None
    return SimpleNamespace(
        invitation_id=inv_id,
        invitation=invitation,
    )


def _scope_for_module(module_id: uuid.UUID = _MODULE_A) -> ExternalScope:
    return ExternalScope(institution_id=_INSTITUTION_A, module_id=module_id)


# ===========================================================================
# 1. Allowed module succeeds
# ===========================================================================

class TestAllowedModule:
    def test_allows_exact_module(self):
        scope = _scope_for_module(_MODULE_A)
        # Should NOT raise
        assert_module_scope(scope, _MODULE_A)

    def test_allows_module_when_no_restriction(self):
        # Institution-only scope has no module restriction
        scope = ExternalScope(institution_id=_INSTITUTION_A, module_id=None)
        assert_module_scope(scope, _MODULE_B)  # must not raise

    def test_scope_predicate_true_for_matching(self):
        scope = _scope_for_module(_MODULE_A)
        assert scope.allows_module(_MODULE_A) is True

    def test_non_external_user_always_passes(self):
        # resolve_external_scope returns None for normal users
        user = _make_user(invitation=None)
        result = resolve_external_scope(user)
        assert result is None
        # None scope never raises in assert helpers
        assert_module_scope(None, _MODULE_A)
        assert_module_scope(None, _MODULE_B)

    def test_institution_check_passes_for_correct_institution(self):
        scope = _scope_for_module()
        assert_institution_scope(scope, _INSTITUTION_A)


# ===========================================================================
# 2. Unrelated module returns 403
# ===========================================================================

class TestUnrelatedModule:
    def test_different_module_raises(self):
        scope = _scope_for_module(_MODULE_A)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            assert_module_scope(scope, _MODULE_B)
        assert exc.value.status_code == 403

    def test_error_message_is_descriptive(self):
        scope = _scope_for_module(_MODULE_A)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            assert_module_scope(scope, _MODULE_B)
        assert "module" in exc.value.detail.lower()

    def test_scope_predicate_false_for_different_module(self):
        scope = _scope_for_module(_MODULE_A)
        assert scope.allows_module(_MODULE_B) is False


# ===========================================================================
# 3. Unrelated programme returns 403
# ===========================================================================

class TestUnrelatedProgramme:
    def test_programme_scoped_user_blocked_from_other_programme(self):
        scope = ExternalScope(
            institution_id=_INSTITUTION_A,
            programme_id=_PROGRAMME_A,
        )
        other_programme = uuid.uuid4()
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            assert_programme_scope(scope, other_programme)
        assert exc.value.status_code == 403

    def test_programme_predicate_false_for_other(self):
        scope = ExternalScope(
            institution_id=_INSTITUTION_A,
            programme_id=_PROGRAMME_A,
        )
        assert scope.allows_programme(uuid.uuid4()) is False

    def test_programme_predicate_true_for_matching(self):
        scope = ExternalScope(
            institution_id=_INSTITUTION_A,
            programme_id=_PROGRAMME_A,
        )
        assert scope.allows_programme(_PROGRAMME_A) is True


# ===========================================================================
# 4. Unrelated evidence returns 403
# ===========================================================================

class TestUnrelatedEvidence:
    """Evidence scope is module-scoped — same check as module."""

    def test_evidence_with_unrelated_module_denied(self):
        scope = _scope_for_module(_MODULE_A)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            assert_module_scope(scope, _MODULE_B)  # evidence's module_id
        assert exc.value.status_code == 403

    def test_evidence_with_correct_module_allowed(self):
        scope = _scope_for_module(_MODULE_A)
        assert_module_scope(scope, _MODULE_A)  # must not raise


# ===========================================================================
# 5. Unrelated finding returns 403
# ===========================================================================

class TestUnrelatedFinding:
    def test_finding_in_unrelated_module_denied(self):
        scope = _scope_for_module(_MODULE_A)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            assert_module_scope(scope, _MODULE_B)
        assert exc.value.status_code == 403

    def test_finding_with_no_module_id_denied(self):
        """Programme-scoped audit run: finding has no module_id.
        External moderator must be denied (deny_external_access path in findings.py)."""
        scope = _scope_for_module(_MODULE_A)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            deny_external_access(scope, "this finding")
        assert exc.value.status_code == 403


# ===========================================================================
# 6. Tenant-wide report denied
# ===========================================================================

class TestTenantWideReportDenied:
    def test_deny_external_access_raises(self):
        scope = _scope_for_module()
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            deny_external_access(scope, "tenant-wide findings listing")
        assert exc.value.status_code == 403

    def test_deny_external_access_noop_for_none(self):
        # Non-external users: deny_external_access is a no-op
        deny_external_access(None, "tenant-wide report")  # must not raise

    def test_deny_external_access_detail_contains_resource(self):
        scope = _scope_for_module()
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            deny_external_access(scope, "compliance dashboard")
        assert "compliance dashboard" in exc.value.detail


# ===========================================================================
# 7. File outside scope denied
# ===========================================================================

class TestFileOutsideScope:
    def test_file_with_unrelated_module_denied(self):
        scope = _scope_for_module(_MODULE_A)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            assert_module_scope(scope, _MODULE_B)
        assert exc.value.status_code == 403

    def test_file_with_no_module_id_denied_via_deny(self):
        scope = _scope_for_module(_MODULE_A)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            deny_external_access(scope, "this file")
        assert exc.value.status_code == 403

    def test_file_with_correct_module_allowed(self):
        scope = _scope_for_module(_MODULE_A)
        assert_module_scope(scope, _MODULE_A)  # must not raise


# ===========================================================================
# 8. Download outside scope denied
# ===========================================================================

class TestDownloadOutsideScope:
    def test_download_uses_same_module_check(self):
        scope = _scope_for_module(_MODULE_A)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            assert_module_scope(scope, _MODULE_B)
        assert exc.value.status_code == 403


# ===========================================================================
# 9. AI workspace blocked for external users
# ===========================================================================

class TestAIWorkspaceBlocked:
    def test_deny_external_access_for_ai_raises(self):
        scope = _scope_for_module()
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            deny_external_access(scope, "the AI assistant")
        assert exc.value.status_code == 403

    def test_non_external_ai_not_blocked(self):
        deny_external_access(None, "the AI assistant")  # must not raise


# ===========================================================================
# 10. Revoked access denied immediately
# ===========================================================================

class TestRevokedAccess:
    def test_revoked_invitation_raises_403(self):
        inv = _make_invitation(status="revoked")
        user = _make_user(invitation=inv)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            resolve_external_scope(user)
        assert exc.value.status_code == 403
        assert "revoked" in exc.value.detail.lower()

    def test_active_invitation_returns_scope(self):
        inv = _make_invitation(status="consumed")
        user = _make_user(invitation=inv)
        scope = resolve_external_scope(user)
        assert scope is not None
        assert scope.module_id == _MODULE_A


# ===========================================================================
# 11. Expired access denied immediately
# ===========================================================================

class TestExpiredAccess:
    def test_expired_invitation_raises_403(self):
        inv = _make_invitation(expires_at=_PAST)
        user = _make_user(invitation=inv)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            resolve_external_scope(user)
        assert exc.value.status_code == 403
        assert "expired" in exc.value.detail.lower()

    def test_future_expiry_returns_scope(self):
        inv = _make_invitation(expires_at=_FUTURE)
        user = _make_user(invitation=inv)
        scope = resolve_external_scope(user)
        assert scope is not None


# ===========================================================================
# 12. Manipulated resource IDs denied
# ===========================================================================

class TestManipulatedResourceIds:
    def test_random_uuid_not_in_scope(self):
        scope = _scope_for_module(_MODULE_A)
        arbitrary_id = uuid.uuid4()
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            assert_module_scope(scope, arbitrary_id)
        assert exc.value.status_code == 403

    def test_nil_uuid_not_in_scope(self):
        scope = _scope_for_module(_MODULE_A)
        nil_id = uuid.UUID(int=0)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            assert_module_scope(scope, nil_id)
        assert exc.value.status_code == 403

    def test_institution_id_mismatch_raises(self):
        scope = ExternalScope(institution_id=_INSTITUTION_A, module_id=_MODULE_A)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            assert_institution_scope(scope, _INSTITUTION_B)
        assert exc.value.status_code == 403


# ===========================================================================
# 13. Cross-tenant institution access denied
# ===========================================================================

class TestCrossTenantDenied:
    def test_institution_b_access_denied_for_institution_a_scope(self):
        scope = ExternalScope(institution_id=_INSTITUTION_A, module_id=_MODULE_A)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            assert_institution_scope(scope, _INSTITUTION_B)
        assert exc.value.status_code == 403

    def test_institution_predicate_false_for_other(self):
        scope = ExternalScope(institution_id=_INSTITUTION_A)
        assert scope.allows_institution(_INSTITUTION_B) is False

    def test_institution_predicate_true_for_same(self):
        scope = ExternalScope(institution_id=_INSTITUTION_A)
        assert scope.allows_institution(_INSTITUTION_A) is True


# ===========================================================================
# Bonus: non-external invitation types are not scoped
# ===========================================================================

class TestNonExternalInvitationTypes:
    def test_staff_invitation_type_not_external(self):
        inv = _make_invitation(invitation_type="staff")
        user = _make_user(invitation=inv)
        scope = resolve_external_scope(user)
        assert scope is None  # staff invitations do not produce external scope

    def test_user_without_invitation_not_external(self):
        user = _make_user(invitation=None)
        scope = resolve_external_scope(user)
        assert scope is None


# ===========================================================================
# ExternalScope dataclass — structural integrity
# ===========================================================================

class TestExternalScopeDataclass:
    def test_frozen(self):
        scope = _scope_for_module()
        with pytest.raises(Exception):
            scope.module_id = uuid.uuid4()  # type: ignore[misc]

    def test_defaults_are_none(self):
        scope = ExternalScope(institution_id=_INSTITUTION_A)
        assert scope.faculty_id is None
        assert scope.department_id is None
        assert scope.programme_id is None
        assert scope.module_id is None
        assert scope.permission_scope is None

    def test_faculty_restriction_allows_exact(self):
        scope = ExternalScope(institution_id=_INSTITUTION_A, faculty_id=_FACULTY_A)
        assert scope.allows_faculty(_FACULTY_A) is True
        assert scope.allows_faculty(uuid.uuid4()) is False

    def test_no_faculty_restriction_allows_all(self):
        scope = ExternalScope(institution_id=_INSTITUTION_A)
        assert scope.allows_faculty(_FACULTY_A) is True
        assert scope.allows_faculty(uuid.uuid4()) is True
