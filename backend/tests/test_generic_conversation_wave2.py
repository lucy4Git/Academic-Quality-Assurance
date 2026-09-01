"""Regression coverage for the Generic Wave 2 conversation architecture."""

from types import SimpleNamespace
import uuid

import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, MagicMock

from app.ai_providers.base_provider import AIMessage
from app.core.exceptions import NotFoundError
from app.models.enums import UserRole
from app.routes import ai_assistant
from app.schemas.ai_assistant import AskRequest


class _RecordingProvider:
    provider_name = "test"
    model_name = "test-model"
    is_local_dev = False

    def __init__(self) -> None:
        self.messages: list[AIMessage] = []

    async def complete(self, messages, temperature=0.3, max_tokens=1024):
        self.messages = messages
        return "A grounded generic response."


@pytest.mark.asyncio
async def test_generic_resolution_has_no_institution_code():
    user = SimpleNamespace(role=UserRole.GENERIC_USER, institution_id=None)
    assert await ai_assistant._resolve_institution_code(None, user, None) is None


@pytest.mark.asyncio
async def test_generic_stream_passes_bounded_history_to_provider(monkeypatch):
    provider = _RecordingProvider()
    manager = SimpleNamespace(get_healthy_provider=lambda: None)

    async def get_provider():
        return provider

    manager.get_healthy_provider = get_provider
    monkeypatch.setattr(ai_assistant, "get_provider_manager", lambda: manager)
    user = SimpleNamespace(role=UserRole.GENERIC_USER)
    history = [
        AIMessage(role="user", content="I do not have a memorandum."),
        AIMessage(role="assistant", content="That is a stated missing item."),
    ]

    events = [
        event
        async for event in ai_assistant._stream_ask(
            "Which gap should I address first?",
            None,
            5,
            "qa_assistant",
            current_user=user,
            conversation_history=history,
        )
    ]

    assert [message.role for message in provider.messages] == [
        "system", "system", "user", "assistant", "user"
    ]
    assert provider.messages[-1].content == "Which gap should I address first?"
    assert any('"type": "token"' in event for event in events)


def test_only_canonical_streaming_route_is_registered():
    paths = {route.path for route in ai_assistant.router.routes}
    assert "/ai-assistant/ask-stream" in paths
    assert "/ai-assistant/sessions/{session_id}/ask-stream" not in paths


def test_conversation_search_route_does_not_collide_with_uuid_detail_route():
    paths = {route.path for route in ai_assistant.router.routes}
    assert "/ai-assistant/session-search" in paths
    assert "/ai-assistant/sessions/search" not in paths


@pytest.mark.asyncio
async def test_denied_generic_attachment_does_not_create_or_mutate_session(monkeypatch):
    db = AsyncMock()
    user = SimpleNamespace(
        id=uuid.uuid4(), role=UserRole.GENERIC_USER, institution_id=None
    )
    request = AskRequest(
        question="Review this file",
        attached_file_ids=[uuid.uuid4()],
    )

    async def deny_file(*_args, **_kwargs):
        raise NotFoundError("File", request.attached_file_ids[0])

    monkeypatch.setattr("app.services.file_service.get_file_for_user", deny_file)

    with pytest.raises(NotFoundError):
        await ai_assistant.ask_assistant_stream(
            body=request, db=db, current_user=user, ext_scope=None
        )

    db.commit.assert_not_awaited()
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_generic_attached_evidence_is_passed_to_provider_with_source(monkeypatch):
    provider = _RecordingProvider()
    manager = SimpleNamespace(get_healthy_provider=AsyncMock(return_value=provider))
    monkeypatch.setattr(ai_assistant, "get_provider_manager", lambda: manager)
    user = SimpleNamespace(role=UserRole.GENERIC_USER)
    chunks = [{
        "entity_id": str(uuid.uuid4()),
        "title": "module-guide.pdf",
        "source_document": "module-guide.pdf",
        "text": "The module has four learning outcomes.",
    }]

    events = [event async for event in ai_assistant._stream_ask(
        "What evidence is present?", None, 5, "qa_assistant",
        current_user=user, file_chunks=chunks,
    )]

    assert any("module-guide.pdf" in message.content for message in provider.messages)
    assert any('"type": "metadata"' in event for event in events)
    assert any('"grounding_status": "grounded"' in event for event in events)


@pytest.mark.asyncio
async def test_no_evidence_determination_is_guarded_without_calling_provider(monkeypatch):
    def provider_manager_must_not_run():
        raise AssertionError("no-evidence guard must bypass all AI providers")

    monkeypatch.setattr(ai_assistant, "get_provider_manager", provider_manager_must_not_run)
    user = SimpleNamespace(role=UserRole.GENERIC_USER)

    events = [event async for event in ai_assistant._stream_ask(
        "Review my module folder and tell me which required documents are missing.",
        None,
        5,
        "qa_assistant",
        current_user=user,
        file_chunks=[],
    )]

    assert any("UNABLE TO DETERMINE" in event for event in events)
    assert any('"provider": "grounding_guard"' in event for event in events)
    assert any('"grounding_status": "no_source_found"' in event for event in events)
    assert not any('"PRESENT"' in event or '"MISSING"' in event for event in events)


@pytest.mark.asyncio
async def test_user_stated_facts_are_labelled_not_retrieved(monkeypatch):
    provider = _RecordingProvider()
    manager = SimpleNamespace(get_healthy_provider=AsyncMock(return_value=provider))
    monkeypatch.setattr(ai_assistant, "get_provider_manager", lambda: manager)
    user = SimpleNamespace(role=UserRole.GENERIC_USER)

    events = [event async for event in ai_assistant._stream_ask(
        "My assessment memorandum is missing. Which issue should I address first?",
        None,
        5,
        "qa_assistant",
        current_user=user,
        file_chunks=[],
    )]

    assert "USER-STATED FACTS" in "".join(events)
    assert any(
        message.role == "system" and "not retrieved or independently verified" in message.content
        for message in provider.messages
    )
    assert not any('"type": "metadata"' in event and '"grounded"' in event for event in events)


@pytest.mark.asyncio
async def test_retrieved_evidence_is_explicitly_labelled_and_cited(monkeypatch):
    provider = _RecordingProvider()
    manager = SimpleNamespace(get_healthy_provider=AsyncMock(return_value=provider))
    monkeypatch.setattr(ai_assistant, "get_provider_manager", lambda: manager)
    user = SimpleNamespace(role=UserRole.GENERIC_USER)
    chunks = [{
        "entity_id": str(uuid.uuid4()),
        "title": "owned-evidence.txt",
        "source_document": "owned-evidence.txt",
        "text": "The assessment memorandum is absent.",
    }]

    events = [event async for event in ai_assistant._stream_ask(
        "Which documents are missing?", None, 5, "qa_assistant",
        current_user=user, file_chunks=chunks,
    )]

    assert "RETRIEVED EVIDENCE" in "".join(events)
    assert any("owned-evidence.txt" in event for event in events)
    assert any('"grounding_status": "grounded"' in event for event in events)


@pytest.mark.asyncio
async def test_system_admin_cannot_read_another_users_personal_conversation():
    session = MagicMock(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        institution_id=None,
        is_active=True,
    )
    db = AsyncMock()
    db.get = AsyncMock(return_value=session)
    admin = SimpleNamespace(id=uuid.uuid4(), role=UserRole.SYSTEM_ADMIN)

    with pytest.raises(HTTPException) as exc_info:
        await ai_assistant.get_session(
            session_id=session.id, db=db, current_user=admin
        )

    assert exc_info.value.status_code == 403
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_system_admin_cannot_delete_another_users_personal_conversation():
    session = MagicMock(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        institution_id=None,
        is_active=True,
        is_deleted=False,
    )
    db = AsyncMock()
    db.get = AsyncMock(return_value=session)
    admin = SimpleNamespace(id=uuid.uuid4(), role=UserRole.SYSTEM_ADMIN)

    with pytest.raises(HTTPException) as exc_info:
        await ai_assistant.delete_session(
            session_id=session.id, db=db, current_user=admin
        )

    assert exc_info.value.status_code == 403
    db.commit.assert_not_awaited()
