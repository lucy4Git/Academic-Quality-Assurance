# AI Provider Implementation Guide

## Adding a new provider

1. Create `backend/app/ai_providers/{name}_provider.py`:

```python
from app.ai_providers.base_provider import AIMessage, BaseAIProvider
import httpx

class MyProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def complete(
        self,
        messages: list[AIMessage],
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.example.com/v1/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    @property
    def provider_name(self) -> str:
        return "my_provider"

    @property
    def model_name(self) -> str:
        return self._model
```

2. Register in `provider_factory.py`:

```python
if provider_name == "MY_PROVIDER":
    api_key = getattr(settings, "MY_PROVIDER_API_KEY", None)
    if not api_key:
        logger.warning("MY_PROVIDER_API_KEY missing. Falling back to LOCAL_DEV.")
        return LocalDevProvider()
    from app.ai_providers.my_provider import MyProvider
    return MyProvider(api_key=api_key, model=getattr(settings, "MY_PROVIDER_MODEL", "default"))
```

3. Add to `_KNOWN_PROVIDERS` set:

```python
_KNOWN_PROVIDERS = {"OPENAI", "ANTHROPIC", "OLLAMA", "LOCAL_DEV", "MY_PROVIDER"}
```

4. Add config fields in `backend/app/config.py`:

```python
MY_PROVIDER_API_KEY: str | None = None
MY_PROVIDER_MODEL: str = "default-model"
```

5. Write tests in `backend/tests/test_ai_providers.py` (see existing pattern for OpenAI/Anthropic).

## Testing providers

All provider tests use `httpx.AsyncClient` mocking — no real API calls. Pattern:

```python
async def test_my_provider_complete(self):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"choices": [{"message": {"content": "Answer."}}]}
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("app.ai_providers.my_provider.httpx.AsyncClient", return_value=mock_client):
        provider = MyProvider(api_key="test-key", model="my-model")
        result = await provider.complete([AIMessage(role="user", content="Question?")])
    assert result == "Answer."
```

## Switching providers at runtime

Set `AI_PROVIDER` in `backend/.env` and restart the backend. The factory is called once per request — no caching.

```env
# Use Anthropic
AI_PROVIDER=ANTHROPIC
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-haiku-4-5-20251001

# Use OpenAI
AI_PROVIDER=OPENAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Use Ollama (local)
AI_PROVIDER=OLLAMA
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Local dev (default — no key required)
AI_PROVIDER=LOCAL_DEV
```

## Patching settings in tests

The factory imports `settings` at module level for patchability:

```python
# In provider_factory.py (module level — required for patching to work)
from app.config import settings

# In test:
with patch("app.ai_providers.provider_factory.settings") as mock_settings:
    mock_settings.AI_PROVIDER = "OPENAI"
    mock_settings.OPENAI_API_KEY = "test-key"
    mock_settings.OPENAI_MODEL = "gpt-4o-mini"
    provider = get_provider()
    assert isinstance(provider, OpenAIProvider)
```

Never import settings inside `get_provider()` — that creates a local reference that `patch` cannot intercept.

## Anthropic message format

The Anthropic API requires the system message to be a separate top-level field, not a member of the `messages` array. `AnthropicProvider` handles this automatically:

```python
system_content = next((m.content for m in messages if m.role == "system"), "")
user_messages = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
payload = {"model": ..., "system": system_content, "messages": user_messages, ...}
```

## Error handling contract

Provider `complete()` methods should raise on HTTP errors via `response.raise_for_status()`. `AssistantService.ask()` catches all exceptions and falls back to LOCAL_DEV template mode. Providers must never swallow exceptions internally.
