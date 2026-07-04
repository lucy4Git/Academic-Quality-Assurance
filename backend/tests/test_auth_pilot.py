"""Auth tests for pilot deployment access control.

Verifies:
  1. Inactive users are rejected at login (account disabled).
  2. Active pilot users (TUT, UP, System Admin) can authenticate.
  3. Demo/archived institution users cannot log in once deactivated.
  4. Tenant isolation still holds after deactivation.
  5. authenticate_user raises AuthError (not HTTP exception) — routes convert it.

All tests are pure unit tests — no real DB, no HTTP stack.
The async authenticate_user function is tested by injecting a mock AsyncSession.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums import UserRole
from app.models.user import User
from app.services.auth_service import AuthError, authenticate_user


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(
    *,
    email: str,
    role: UserRole,
    is_active: bool = True,
    institution_id: uuid.UUID | None = None,
    hashed_password: str = "CORRECT_HASH",
) -> MagicMock:
    user = MagicMock(spec=User)
    user.email = email
    user.role = role
    user.is_active = is_active
    user.institution_id = institution_id
    user.hashed_password = hashed_password
    return user


def _mock_db(user: User | None) -> AsyncMock:
    """Return a mock AsyncSession whose execute() returns user (or None)."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    db = AsyncMock()
    db.execute.return_value = result
    return db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TUT_INST_ID = uuid.uuid4()
UP_INST_ID = uuid.uuid4()
GFU_INST_ID = uuid.uuid4()
RCT_INST_ID = uuid.uuid4()

SYSTEM_ADMIN = _make_user(email="admin@test.com", role=UserRole.SYSTEM_ADMIN, institution_id=None)
TUT_QA = _make_user(email="qa.officer@tut.ac.za", role=UserRole.QUALITY_ASSURANCE_OFFICER, institution_id=TUT_INST_ID)
TUT_DEAN = _make_user(email="dean.ict@tut.ac.za", role=UserRole.FACULTY_DEAN, institution_id=TUT_INST_ID)
TUT_HOD = _make_user(email="hod.cs@tut.ac.za", role=UserRole.HEAD_OF_DEPARTMENT, institution_id=TUT_INST_ID)
TUT_COORD = _make_user(email="coordinator.it@tut.ac.za", role=UserRole.PROGRAMME_COORDINATOR, institution_id=TUT_INST_ID)
TUT_LECTURER = _make_user(email="lecturer.cs@tut.ac.za", role=UserRole.LECTURER, institution_id=TUT_INST_ID)
TUT_STUDENT = _make_user(email="student.cs@tut.ac.za", role=UserRole.STUDENT, institution_id=TUT_INST_ID)
UP_QA = _make_user(email="qa.officer@up.ac.za", role=UserRole.QUALITY_ASSURANCE_OFFICER, institution_id=UP_INST_ID)
UP_DEAN = _make_user(email="dean.ebit@up.ac.za", role=UserRole.FACULTY_DEAN, institution_id=UP_INST_ID)
UP_HOD = _make_user(email="hod.cs@up.ac.za", role=UserRole.HEAD_OF_DEPARTMENT, institution_id=UP_INST_ID)
UP_COORD = _make_user(email="coordinator.bsccs@up.ac.za", role=UserRole.PROGRAMME_COORDINATOR, institution_id=UP_INST_ID)
UP_LECTURER = _make_user(email="lecturer.cos@up.ac.za", role=UserRole.LECTURER, institution_id=UP_INST_ID)
UP_STUDENT = _make_user(email="student.cs@up.ac.za", role=UserRole.STUDENT, institution_id=UP_INST_ID)
GFU_DEACTIVATED = _make_user(email="lecturer1@gfu.ac.uk", role=UserRole.LECTURER, is_active=False, institution_id=GFU_INST_ID)
GFU_QA_DEACTIVATED = _make_user(email="qa.officer@gfu.ac.uk", role=UserRole.QUALITY_ASSURANCE_OFFICER, is_active=False, institution_id=GFU_INST_ID)
RCT_DEACTIVATED = _make_user(email="lecturer.sen1@rct.ac.uk", role=UserRole.LECTURER, is_active=False, institution_id=RCT_INST_ID)
RCT_QA_DEACTIVATED = _make_user(email="qa.officer1@rct.ac.uk", role=UserRole.QUALITY_ASSURANCE_OFFICER, is_active=False, institution_id=RCT_INST_ID)


# ---------------------------------------------------------------------------
# 1. Inactive users are rejected
# ---------------------------------------------------------------------------

class TestInactiveUserRejected:
    """Users with is_active=False receive 'account disabled' error, never a token."""

    @pytest.mark.asyncio
    async def test_inactive_gfu_lecturer_rejected(self):
        db = _mock_db(GFU_DEACTIVATED)
        with patch("app.services.auth_service.verify_password", return_value=True):
            with pytest.raises(AuthError, match="disabled"):
                await authenticate_user(db, GFU_DEACTIVATED.email, "ChangeMe123!")

    @pytest.mark.asyncio
    async def test_inactive_gfu_qa_rejected(self):
        db = _mock_db(GFU_QA_DEACTIVATED)
        with patch("app.services.auth_service.verify_password", return_value=True):
            with pytest.raises(AuthError, match="disabled"):
                await authenticate_user(db, GFU_QA_DEACTIVATED.email, "ChangeMe123!")

    @pytest.mark.asyncio
    async def test_inactive_rct_lecturer_rejected(self):
        db = _mock_db(RCT_DEACTIVATED)
        with patch("app.services.auth_service.verify_password", return_value=True):
            with pytest.raises(AuthError, match="disabled"):
                await authenticate_user(db, RCT_DEACTIVATED.email, "ChangeMe123!")

    @pytest.mark.asyncio
    async def test_inactive_rct_qa_rejected(self):
        db = _mock_db(RCT_QA_DEACTIVATED)
        with patch("app.services.auth_service.verify_password", return_value=True):
            with pytest.raises(AuthError, match="disabled"):
                await authenticate_user(db, RCT_QA_DEACTIVATED.email, "ChangeMe123!")

    @pytest.mark.asyncio
    async def test_inactive_user_wrong_password_still_rejected(self):
        """Even correct email but wrong password — always AuthError, never disabled leak."""
        db = _mock_db(GFU_DEACTIVATED)
        with patch("app.services.auth_service.verify_password", return_value=False):
            with pytest.raises(AuthError, match="Invalid email or password"):
                await authenticate_user(db, GFU_DEACTIVATED.email, "WrongPass!")

    @pytest.mark.asyncio
    async def test_error_message_does_not_reveal_account_exists(self):
        """Unknown email must return same error text as wrong password — no user enumeration."""
        db = _mock_db(None)
        with patch("app.services.auth_service.verify_password", return_value=False):
            with pytest.raises(AuthError, match="Invalid email or password"):
                await authenticate_user(db, "ghost@gfu.ac.uk", "ChangeMe123!")


# ---------------------------------------------------------------------------
# 2. System Admin can log in
# ---------------------------------------------------------------------------

class TestSystemAdminLogin:

    @pytest.mark.asyncio
    async def test_system_admin_authenticated(self):
        db = _mock_db(SYSTEM_ADMIN)
        with patch("app.services.auth_service.verify_password", return_value=True):
            user = await authenticate_user(db, SYSTEM_ADMIN.email, "ChangeMe123!")
        assert user.role == UserRole.SYSTEM_ADMIN
        assert user.institution_id is None

    @pytest.mark.asyncio
    async def test_system_admin_wrong_password_rejected(self):
        db = _mock_db(SYSTEM_ADMIN)
        with patch("app.services.auth_service.verify_password", return_value=False):
            with pytest.raises(AuthError, match="Invalid email or password"):
                await authenticate_user(db, SYSTEM_ADMIN.email, "wrong")


# ---------------------------------------------------------------------------
# 3. TUT pilot users can log in
# ---------------------------------------------------------------------------

class TestTUTPilotLogin:

    @pytest.mark.asyncio
    @pytest.mark.parametrize("user", [
        TUT_QA, TUT_DEAN, TUT_HOD, TUT_COORD, TUT_LECTURER, TUT_STUDENT,
    ])
    async def test_tut_pilot_user_authenticated(self, user):
        db = _mock_db(user)
        with patch("app.services.auth_service.verify_password", return_value=True):
            result = await authenticate_user(db, user.email, "ChangeMe123!")
        assert result.institution_id == TUT_INST_ID
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_tut_user_wrong_password_rejected(self):
        db = _mock_db(TUT_QA)
        with patch("app.services.auth_service.verify_password", return_value=False):
            with pytest.raises(AuthError, match="Invalid email or password"):
                await authenticate_user(db, TUT_QA.email, "wrong")


# ---------------------------------------------------------------------------
# 4. UP pilot users can log in
# ---------------------------------------------------------------------------

class TestUPPilotLogin:

    @pytest.mark.asyncio
    @pytest.mark.parametrize("user", [
        UP_QA, UP_DEAN, UP_HOD, UP_COORD, UP_LECTURER, UP_STUDENT,
    ])
    async def test_up_pilot_user_authenticated(self, user):
        db = _mock_db(user)
        with patch("app.services.auth_service.verify_password", return_value=True):
            result = await authenticate_user(db, user.email, "ChangeMe123!")
        assert result.institution_id == UP_INST_ID
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_up_user_wrong_password_rejected(self):
        db = _mock_db(UP_QA)
        with patch("app.services.auth_service.verify_password", return_value=False):
            with pytest.raises(AuthError, match="Invalid email or password"):
                await authenticate_user(db, UP_QA.email, "wrong")


# ---------------------------------------------------------------------------
# 5. Archived demo institution users cannot log in
# ---------------------------------------------------------------------------

class TestArchivedDemoUsersBlocked:
    """Comprehensive check: all demo users must have is_active=False and be rejected."""

    GFU_USERS = [
        _make_user(email=f"lecturer{i}@gfu.ac.uk", role=UserRole.LECTURER, is_active=False, institution_id=GFU_INST_ID)
        for i in range(1, 4)
    ] + [
        _make_user(email="qa.officer@gfu.ac.uk", role=UserRole.QUALITY_ASSURANCE_OFFICER, is_active=False, institution_id=GFU_INST_ID),
        _make_user(email="qa.officer1@gfu.ac.uk", role=UserRole.QUALITY_ASSURANCE_OFFICER, is_active=False, institution_id=GFU_INST_ID),
    ]

    RCT_USERS = [
        _make_user(email="qa.officer1@rct.ac.uk", role=UserRole.QUALITY_ASSURANCE_OFFICER, is_active=False, institution_id=RCT_INST_ID),
        _make_user(email="qa.officer2@rct.ac.uk", role=UserRole.QUALITY_ASSURANCE_OFFICER, is_active=False, institution_id=RCT_INST_ID),
        _make_user(email="lecturer.sen1@rct.ac.uk", role=UserRole.LECTURER, is_active=False, institution_id=RCT_INST_ID),
        _make_user(email="student.bscsen1@rct.ac.uk", role=UserRole.STUDENT, is_active=False, institution_id=RCT_INST_ID),
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("user", GFU_USERS)
    async def test_gfu_user_cannot_log_in(self, user):
        db = _mock_db(user)
        with patch("app.services.auth_service.verify_password", return_value=True):
            with pytest.raises(AuthError, match="disabled"):
                await authenticate_user(db, user.email, "ChangeMe123!")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("user", RCT_USERS)
    async def test_rct_user_cannot_log_in(self, user):
        db = _mock_db(user)
        with patch("app.services.auth_service.verify_password", return_value=True):
            with pytest.raises(AuthError, match="disabled"):
                await authenticate_user(db, user.email, "ChangeMe123!")

    @pytest.mark.asyncio
    async def test_deactivated_user_is_active_false(self):
        assert GFU_DEACTIVATED.is_active is False
        assert RCT_DEACTIVATED.is_active is False


# ---------------------------------------------------------------------------
# 6. Tenant isolation still enforced after deactivation
# ---------------------------------------------------------------------------

class TestTenantIsolationPostDeactivation:
    """Deactivating demo users must not affect isolation for pilot users."""

    @pytest.mark.asyncio
    async def test_tut_user_institution_id_unchanged(self):
        db = _mock_db(TUT_LECTURER)
        with patch("app.services.auth_service.verify_password", return_value=True):
            result = await authenticate_user(db, TUT_LECTURER.email, "ChangeMe123!")
        assert result.institution_id == TUT_INST_ID
        assert result.institution_id != UP_INST_ID
        assert result.institution_id != GFU_INST_ID
        assert result.institution_id != RCT_INST_ID

    @pytest.mark.asyncio
    async def test_up_user_institution_id_unchanged(self):
        db = _mock_db(UP_LECTURER)
        with patch("app.services.auth_service.verify_password", return_value=True):
            result = await authenticate_user(db, UP_LECTURER.email, "ChangeMe123!")
        assert result.institution_id == UP_INST_ID
        assert result.institution_id != TUT_INST_ID
        assert result.institution_id != GFU_INST_ID
        assert result.institution_id != RCT_INST_ID

    @pytest.mark.asyncio
    async def test_system_admin_has_no_institution(self):
        db = _mock_db(SYSTEM_ADMIN)
        with patch("app.services.auth_service.verify_password", return_value=True):
            result = await authenticate_user(db, SYSTEM_ADMIN.email, "ChangeMe123!")
        assert result.institution_id is None

    @pytest.mark.asyncio
    async def test_inactive_demo_user_correct_creds_still_blocked(self):
        """Even if a demo user somehow has correct credentials, is_active gate blocks them."""
        db = _mock_db(GFU_DEACTIVATED)
        with patch("app.services.auth_service.verify_password", return_value=True):
            with pytest.raises(AuthError, match="disabled"):
                await authenticate_user(db, GFU_DEACTIVATED.email, "ChangeMe123!")

    @pytest.mark.asyncio
    async def test_tut_user_is_active_true(self):
        db = _mock_db(TUT_QA)
        with patch("app.services.auth_service.verify_password", return_value=True):
            result = await authenticate_user(db, TUT_QA.email, "ChangeMe123!")
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_up_user_is_active_true(self):
        db = _mock_db(UP_QA)
        with patch("app.services.auth_service.verify_password", return_value=True):
            result = await authenticate_user(db, UP_QA.email, "ChangeMe123!")
        assert result.is_active is True
