"""Tests for the AI Provider abstraction layer.

Coverage
--------
- LocalDevProvider: returns string, is_local_dev=True
- ProviderFactory: selects LOCAL_DEV by default
- ProviderFactory: OPENAI missing key → LOCAL_DEV
- ProviderFactory: ANTHROPIC missing key → LOCAL_DEV
- ProviderFactory: unknown provider name → LOCAL_DEV
- OpenAIProvider: mocked httpx response → expected text
- AnthropicProvider: mocked httpx response → expected text
- OllamaProvider: mocked httpx response → expected text
- Provider name and model_name properties
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai_providers.base_provider import AIMessage
from app.ai_providers.local_provider import LocalDevProvider
from app.ai_providers.openai_provider import OpenAIProvider
from app.ai_providers.anthropic_provider import AnthropicProvider
from app.ai_providers.ollama_provider import OllamaProvider
from app.ai_providers.provider_factory import get_provider


# ===========================================================================
# TestLocalDevProvider
# ===========================================================================


class TestLocalDevProvider:
    async def test_returns_string(self) -> None:
        provider = LocalDevProvider()
        messages = [
            AIMessage(role="system", content="You are AQAA."),
            AIMessage(role="user", content="What programmes does TUT offer?"),
        ]
        result = await provider.complete(messages)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_is_local_dev_true(self) -> None:
        assert LocalDevProvider().is_local_dev is True

    def test_provider_name(self) -> None:
        assert LocalDevProvider().provider_name == "local_dev"

    def test_model_name(self) -> None:
        assert LocalDevProvider().model_name == "template"

    async def test_contains_user_question(self) -> None:
        provider = LocalDevProvider()
        messages = [AIMessage(role="user", content="What is TUT?")]
        result = await provider.complete(messages)
        assert "What is TUT?" in result or "LOCAL_DEV" in result


# ===========================================================================
# TestProviderFactory
# ===========================================================================


class TestProviderFactory:
    def test_default_is_local_dev(self) -> None:
        with patch("app.ai_providers.provider_factory.settings") as mock_settings:
            mock_settings.AI_PROVIDER = "LOCAL_DEV"
            provider = get_provider()
        assert provider.is_local_dev

    def test_openai_missing_key_falls_back(self) -> None:
        with patch("app.ai_providers.provider_factory.settings") as mock_settings:
            mock_settings.AI_PROVIDER = "OPENAI"
            mock_settings.OPENAI_API_KEY = None
            provider = get_provider()
        assert provider.is_local_dev

    def test_openai_empty_key_falls_back(self) -> None:
        with patch("app.ai_providers.provider_factory.settings") as mock_settings:
            mock_settings.AI_PROVIDER = "OPENAI"
            mock_settings.OPENAI_API_KEY = ""
            provider = get_provider()
        assert provider.is_local_dev

    def test_anthropic_missing_key_falls_back(self) -> None:
        with patch("app.ai_providers.provider_factory.settings") as mock_settings:
            mock_settings.AI_PROVIDER = "ANTHROPIC"
            mock_settings.ANTHROPIC_API_KEY = None
            provider = get_provider()
        assert provider.is_local_dev

    def test_unknown_provider_falls_back(self) -> None:
        with patch("app.ai_providers.provider_factory.settings") as mock_settings:
            mock_settings.AI_PROVIDER = "UNICORN_LLM"
            provider = get_provider()
        assert provider.is_local_dev

    def test_openai_with_key_returns_openai_provider(self) -> None:
        with patch("app.ai_providers.provider_factory.settings") as mock_settings:
            mock_settings.AI_PROVIDER = "OPENAI"
            mock_settings.OPENAI_API_KEY = "sk-test-key"
            mock_settings.OPENAI_MODEL = "gpt-4o-mini"
            provider = get_provider()
        assert provider.provider_name == "openai"
        assert not provider.is_local_dev

    def test_anthropic_with_key_returns_anthropic_provider(self) -> None:
        with patch("app.ai_providers.provider_factory.settings") as mock_settings:
            mock_settings.AI_PROVIDER = "ANTHROPIC"
            mock_settings.ANTHROPIC_API_KEY = "sk-ant-test"
            mock_settings.ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
            provider = get_provider()
        assert provider.provider_name == "anthropic"
        assert not provider.is_local_dev

    def test_ollama_returns_ollama_provider(self) -> None:
        with patch("app.ai_providers.provider_factory.settings") as mock_settings:
            mock_settings.AI_PROVIDER = "OLLAMA"
            mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
            mock_settings.OLLAMA_MODEL = "llama3"
            provider = get_provider()
        assert provider.provider_name == "ollama"
        assert not provider.is_local_dev


# ===========================================================================
# TestOpenAIProvider
# ===========================================================================


class TestOpenAIProvider:
    def _provider(self) -> OpenAIProvider:
        return OpenAIProvider(api_key="sk-test-key", model="gpt-4o-mini")

    def test_provider_name(self) -> None:
        assert self._provider().provider_name == "openai"

    def test_model_name(self) -> None:
        assert self._provider().model_name == "gpt-4o-mini"

    def test_is_not_local_dev(self) -> None:
        assert not self._provider().is_local_dev

    async def test_complete_returns_content(self) -> None:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "TUT offers BTech programmes."}}]
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.ai_providers.openai_provider.httpx.AsyncClient", return_value=mock_client):
            result = await self._provider().complete(
                [AIMessage(role="user", content="What programmes?")]
            )

        assert result == "TUT offers BTech programmes."

    async def test_complete_sends_correct_model(self) -> None:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Answer."}}]
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.ai_providers.openai_provider.httpx.AsyncClient", return_value=mock_client):
            await self._provider().complete([AIMessage(role="user", content="test")])

        call_kwargs = mock_client.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["model"] == "gpt-4o-mini"


# ===========================================================================
# TestAnthropicProvider
# ===========================================================================


class TestAnthropicProvider:
    def _provider(self) -> AnthropicProvider:
        return AnthropicProvider(api_key="sk-ant-test", model="claude-haiku-4-5-20251001")

    def test_provider_name(self) -> None:
        assert self._provider().provider_name == "anthropic"

    def test_model_name(self) -> None:
        assert self._provider().model_name == "claude-haiku-4-5-20251001"

    def test_is_not_local_dev(self) -> None:
        assert not self._provider().is_local_dev

    async def test_complete_returns_content(self) -> None:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "content": [{"text": "CHE requires evidence submission."}]
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.ai_providers.anthropic_provider.httpx.AsyncClient", return_value=mock_client):
            result = await self._provider().complete(
                [
                    AIMessage(role="system", content="You are AQAA."),
                    AIMessage(role="user", content="What are CHE requirements?"),
                ]
            )

        assert result == "CHE requires evidence submission."

    async def test_system_prompt_extracted_correctly(self) -> None:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"content": [{"text": "Answer."}]}

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.ai_providers.anthropic_provider.httpx.AsyncClient", return_value=mock_client):
            await self._provider().complete([
                AIMessage(role="system", content="System context."),
                AIMessage(role="user", content="User question."),
            ])

        call_kwargs = mock_client.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["system"] == "System context."
        assert all(m["role"] != "system" for m in payload["messages"])


# ===========================================================================
# TestOllamaProvider
# ===========================================================================


class TestOllamaProvider:
    def _provider(self) -> OllamaProvider:
        return OllamaProvider(base_url="http://localhost:11434", model="llama3")

    def test_provider_name(self) -> None:
        assert self._provider().provider_name == "ollama"

    def test_model_name(self) -> None:
        assert self._provider().model_name == "llama3"

    def test_is_not_local_dev(self) -> None:
        assert not self._provider().is_local_dev

    async def test_complete_returns_content(self) -> None:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "Ollama response about modules."}
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.ai_providers.ollama_provider.httpx.AsyncClient", return_value=mock_client):
            result = await self._provider().complete(
                [AIMessage(role="user", content="What modules are offered?")]
            )

        assert result == "Ollama response about modules."

    async def test_sends_stream_false(self) -> None:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"message": {"content": "ok"}}

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.ai_providers.ollama_provider.httpx.AsyncClient", return_value=mock_client):
            await self._provider().complete([AIMessage(role="user", content="test")])

        call_kwargs = mock_client.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["stream"] is False
