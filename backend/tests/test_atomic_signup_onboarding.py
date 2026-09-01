from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.models.enums import UserRole
from app.models.user_workspace_module import UserWorkspaceModule
from app.schemas.auth import PublicRegisterRequest
from app.services.auth_service import public_register_user

@pytest.mark.asyncio
@pytest.mark.parametrize(("signals", "persona"), [(["review_evidence", "identify_missing"], "quality_assurance_officer"), (["prepare_evidence", "module_owner"], "lecturer")])
async def test_atomic_onboarding_registration_infers_persona_and_provisions_private_workspace(signals, persona):
    db = AsyncMock()
    result = MagicMock(); result.scalar_one_or_none.return_value = None
    db.execute.return_value = result
    captured = []; db.add = lambda value: captured.append(value)
    data = PublicRegisterRequest(full_name="Atomic User", email=f"{persona}@example.com", password="Password123", work_focus_signals=signals, qa_interests=[signals[0]], evidence_types=["assessments"])
    settings = MagicMock(REGISTRATION_REQUIRES_ADMIN_APPROVAL=False)
    with patch("app.services.auth_service.settings", settings):
        user = await public_register_user(db, data)
    assert user.role == UserRole.GENERIC_USER
    assert user.persona == persona
    assert user.qa_interests == [signals[0]]
    workspace = next(value for value in captured if isinstance(value, UserWorkspaceModule))
    assert workspace.user_id == user.id
    db.flush.assert_awaited_once()
    db.commit.assert_awaited_once()