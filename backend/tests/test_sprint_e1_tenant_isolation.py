"""Sprint E1 comprehensive tenant isolation tests.

E0-OD-006: 'Every tenant-owned table must retain an institution identifier.
Every applicable service-layer query must enforce institution filtering. Any
discovered isolation gap is an E1 blocker.'

Tests cover:
1. Positive: user can access their own institution's resources
2. Negative: user CANNOT access another institution's resources via cross-tenant IDs
3. Admin bypass: SYSTEM_ADMIN can access any institution
4. Service-layer enforcement: corrective action service enforces tenant isolation
5. Dependencies: assert_institution_access enforces tenant scope
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums import UserRole


def _make_user(role: UserRole, institution_id: uuid.UUID | None = None) -> MagicMock:
    user = MagicMock()
    user.id = uuid.uuid4()
    user.role = role
    user.institution_id = institution_id or uuid.uuid4()
    user.is_active = True
    return user


# ===========================================================================
# assert_institution_access (dependencies.py)
# ===========================================================================


class TestAssertInstitutionAccess:
    def test_same_institution_permitted(self) -> None:
        from app.dependencies import assert_institution_access
        from fastapi import HTTPException

        inst_id = uuid.uuid4()
        user = _make_user(UserRole.QUALITY_ASSURANCE_OFFICER, inst_id)
        # Should not raise
        assert_institution_access(user, inst_id)

    def test_different_institution_raises_403(self) -> None:
        from app.dependencies import assert_institution_access
        from fastapi import HTTPException

        user = _make_user(UserRole.QUALITY_ASSURANCE_OFFICER)
        other_inst = uuid.uuid4()

        with pytest.raises(HTTPException) as exc_info:
            assert_institution_access(user, other_inst)
        assert exc_info.value.status_code == 403

    def test_system_admin_bypasses_check(self) -> None:
        from app.dependencies import assert_institution_access

        admin = _make_user(UserRole.SYSTEM_ADMIN)
        other_inst = uuid.uuid4()
        # Must not raise for any institution
        assert_institution_access(admin, other_inst)

    def test_lecturer_blocked_from_other_institution(self) -> None:
        from app.dependencies import assert_institution_access
        from fastapi import HTTPException

        user = _make_user(UserRole.LECTURER)
        other_inst = uuid.uuid4()
        with pytest.raises(HTTPException) as exc_info:
            assert_institution_access(user, other_inst)
        assert exc_info.value.status_code == 403

    def test_student_blocked_from_other_institution(self) -> None:
        from app.dependencies import assert_institution_access
        from fastapi import HTTPException

        user = _make_user(UserRole.STUDENT)
        other_inst = uuid.uuid4()
        with pytest.raises(HTTPException) as exc_info:
            assert_institution_access(user, other_inst)
        assert exc_info.value.status_code == 403


# ===========================================================================
# Corrective action service — tenant isolation (service layer)
# ===========================================================================


class TestCorrectiveActionTenantIsolation:
    @pytest.mark.asyncio
    async def test_create_for_own_institution_allowed(self) -> None:
        from app.services.corrective_action_service import create_corrective_action
        from app.schemas.corrective_action import CorrectiveActionCreate

        inst_id = uuid.uuid4()
        user = _make_user(UserRole.PROGRAMME_COORDINATOR, inst_id)

        mock_action = MagicMock()
        mock_action.id = uuid.uuid4()

        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        data = CorrectiveActionCreate(
            institution_id=inst_id,
            title="Fix assessment documentation",
        )

        # Should not raise DomainPermissionError
        with patch("app.services.corrective_action_service.CorrectiveAction") as MockCA, \
             patch("app.services.corrective_action_service.CorrectiveActionHistory"):
            mock_instance = MagicMock()
            mock_instance.id = uuid.uuid4()
            MockCA.return_value = mock_instance
            await create_corrective_action(db, data, user)
            db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_for_other_institution_raises(self) -> None:
        from app.services.corrective_action_service import create_corrective_action
        from app.schemas.corrective_action import CorrectiveActionCreate
        from app.core.exceptions import DomainPermissionError

        user = _make_user(UserRole.PROGRAMME_COORDINATOR)
        other_inst = uuid.uuid4()  # Different from user.institution_id

        db = AsyncMock()
        data = CorrectiveActionCreate(
            institution_id=other_inst,
            title="Attempting cross-tenant write",
        )

        with pytest.raises(DomainPermissionError):
            await create_corrective_action(db, data, user)

    @pytest.mark.asyncio
    async def test_admin_can_create_for_any_institution(self) -> None:
        from app.services.corrective_action_service import create_corrective_action
        from app.schemas.corrective_action import CorrectiveActionCreate

        admin = _make_user(UserRole.SYSTEM_ADMIN)
        other_inst = uuid.uuid4()

        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        data = CorrectiveActionCreate(
            institution_id=other_inst,
            title="Admin cross-institution action",
        )

        with patch("app.services.corrective_action_service.CorrectiveAction") as MockCA, \
             patch("app.services.corrective_action_service.CorrectiveActionHistory"):
            mock_instance = MagicMock()
            mock_instance.id = uuid.uuid4()
            MockCA.return_value = mock_instance
            await create_corrective_action(db, data, admin)
            db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_enforces_institution_scope(self) -> None:
        from app.services.corrective_action_service import list_corrective_actions
        from app.core.exceptions import DomainPermissionError

        user = _make_user(UserRole.PROGRAMME_COORDINATOR)
        other_inst = uuid.uuid4()
        db = AsyncMock()

        with pytest.raises(DomainPermissionError):
            await list_corrective_actions(db, other_inst, user)

    @pytest.mark.asyncio
    async def test_get_enforces_institution_scope(self) -> None:
        from app.services.corrective_action_service import get_corrective_action
        from app.core.exceptions import DomainPermissionError, NotFoundError

        user = _make_user(UserRole.PROGRAMME_COORDINATOR)
        other_inst = uuid.uuid4()

        mock_action = MagicMock()
        mock_action.institution_id = other_inst  # Different institution

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_action)
        db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(DomainPermissionError):
            await get_corrective_action(db, uuid.uuid4(), user)


# ===========================================================================
# Positive isolation — same institution can read its own data
# ===========================================================================


class TestPositiveTenantIsolation:
    @pytest.mark.asyncio
    async def test_same_institution_can_list_actions(self) -> None:
        from app.services.corrective_action_service import list_corrective_actions

        inst_id = uuid.uuid4()
        user = _make_user(UserRole.PROGRAMME_COORDINATOR, inst_id)

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=mock_result)

        result = await list_corrective_actions(db, inst_id, user)
        assert result == []
        db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_same_institution_get_succeeds(self) -> None:
        from app.services.corrective_action_service import get_corrective_action

        inst_id = uuid.uuid4()
        user = _make_user(UserRole.PROGRAMME_COORDINATOR, inst_id)
        action_id = uuid.uuid4()

        mock_action = MagicMock()
        mock_action.institution_id = inst_id  # Same institution

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_action)
        db.execute = AsyncMock(return_value=mock_result)

        result = await get_corrective_action(db, action_id, user)
        assert result is mock_action
