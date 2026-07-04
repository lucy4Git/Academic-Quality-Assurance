# AI Model Configuration Guide

## Environment variables

All AI configuration lives in `backend/.env`. The backend must be restarted after changes.

```env
# ── AI Provider ──────────────────────────────────────────────────────────────
# Options: LOCAL_DEV | OPENAI | ANTHROPIC | OLLAMA
AI_PROVIDER=LOCAL_DEV

# ── OpenAI ───────────────────────────────────────────────────────────────────
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

# ── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-haiku-4-5-20251001

# ── Ollama (local) ───────────────────────────────────────────────────────────
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# ── Local (no key required) ──────────────────────────────────────────────────
LOCAL_MODEL_PATH=

# ── Shared generation parameters ─────────────────────────────────────────────
AI_TEMPERATURE=0.3
AI_MAX_TOKENS=1024
```

## Choosing a provider

### LOCAL_DEV (default)
No API key required. Uses deterministic template assembly from retrieved knowledge chunks. Suitable for development and demonstration environments. Responses are clearly marked with an amber banner in the UI.

### OpenAI
Requires `OPENAI_API_KEY`. Recommended model: `gpt-4o-mini` (cost-effective) or `gpt-4o` (highest quality).

```env
AI_PROVIDER=OPENAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

### Anthropic
Requires `ANTHROPIC_API_KEY`. Recommended model: `claude-haiku-4-5-20251001` (fast, low cost) or `claude-sonnet-5` (higher quality).

```env
AI_PROVIDER=ANTHROPIC
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-haiku-4-5-20251001
```

### Ollama (self-hosted)
No API key required. Requires a running Ollama instance with the target model pulled.

```bash
# Install Ollama and pull a model
ollama pull llama3
```

```env
AI_PROVIDER=OLLAMA
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

For Docker deployments, set `OLLAMA_BASE_URL=http://host.docker.internal:11434` to reach Ollama on the host machine.

## Fallback behaviour

If the configured provider is unavailable (missing key, unreachable endpoint, HTTP error), the backend automatically falls back to LOCAL_DEV and logs a warning. The API never returns a 500 error due to AI provider failure.

Fallback scenarios:
- `AI_PROVIDER=OPENAI` but `OPENAI_API_KEY` is empty → LOCAL_DEV
- `AI_PROVIDER=ANTHROPIC` but `ANTHROPIC_API_KEY` is empty → LOCAL_DEV
- Unknown value (e.g. `AI_PROVIDER=GEMINI`) → LOCAL_DEV (warning logged)
- Provider `complete()` raises any exception → LOCAL_DEV template for that request

## Generation parameters

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_TEMPERATURE` | `0.3` | Lower = more deterministic. Recommended range: 0.1–0.5 for QA use cases |
| `AI_MAX_TOKENS` | `1024` | Maximum tokens in the AI response. Increase to 2048 for longer analytical answers |

## Verifying provider configuration

Check the `provider` and `model` fields in any `/ai-assistant/ask` response:

```json
{
  "answer": "...",
  "provider": "anthropic",
  "model": "claude-haiku-4-5-20251001",
  "is_placeholder_mode": false
}
```

`is_placeholder_mode: true` indicates LOCAL_DEV is active (either configured or fallback).

## Docker restart after config change

```bash
docker compose restart backend
```

Changes to `backend/.env` take effect on next container start. The database, Qdrant, and Redis do not need to restart.

## Security notes

- Never commit `backend/.env` to version control.
- API keys should be rotated via the provider dashboard if exposed.
- For production deployments, inject secrets via environment variables or a secrets manager rather than `.env` files.
- `AI_TEMPERATURE` and `AI_MAX_TOKENS` are non-sensitive and safe to commit in environment templates.
