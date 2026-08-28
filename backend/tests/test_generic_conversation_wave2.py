"""Regression coverage for the Generic Wave 2 conversation architecture."""

from types import SimpleNamespace

import pytest

from app.ai_providers.base_provider import AIMessage
from app.models.enums import UserRole
from app.routes import ai_assistant


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
        "system", "user", "assistant", "user"
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
