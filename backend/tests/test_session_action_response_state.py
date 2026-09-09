import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.routes.ai_assistant import archive_session, pin_session


class _CountResult:
    def scalar_one(self):
        return 0


def _session(user_id):
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user_id,
        mode="qa_assistant",
        title="Acceptance",
        provider=None,
        model_name=None,
        is_active=True,
        is_deleted=False,
        is_pinned=False,
        is_archived=False,
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_pin_response_reports_persisted_state():
    user = SimpleNamespace(id=uuid.uuid4())
    session = _session(user.id)
    db = SimpleNamespace(
        get=AsyncMock(return_value=session),
        commit=AsyncMock(),
        execute=AsyncMock(return_value=_CountResult()),
    )

    response = await pin_session(session.id, db, user)

    assert session.is_pinned is True
    assert response.is_pinned is True
    assert response.is_archived is False


@pytest.mark.asyncio
async def test_archive_response_preserves_pin_and_reports_archive_state():
    user = SimpleNamespace(id=uuid.uuid4())
    session = _session(user.id)
    session.is_pinned = True
    db = SimpleNamespace(
        get=AsyncMock(return_value=session),
        commit=AsyncMock(),
        execute=AsyncMock(return_value=_CountResult()),
    )

    response = await archive_session(session.id, db, user)

    assert response.is_pinned is True
    assert response.is_archived is True
