# AQAA Remaining Issues Register

**Document:** AQAA_REMAINING_ISSUES_REGISTER  
**Sprint:** Recovery Sprint  
**Date:** 2026-07-13  
**Status:** LIVE — Update as issues are resolved

---

## Open Issues

### ISSUE-001 — AI Provider Falls Back to LOCAL_DEV

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | AI provider |
| **Status** | Open |
| **Root cause** | `AI_PROVIDER=OPENAI` is set but OpenAI key has `insufficient_quota`. Provider chain falls back to `LocalDevProvider` (template assembly). |
| **Impact** | AI answers are template boilerplate, not real LLM output. The retrieval and embedding layers are real; only generation is templated. |
| **Evidence** | `POST /api/v1/ai-assistant/ask` → `provider: local_dev`, `model: template` |

**Resolution options (in order of preference):**

1. **Fund the OpenAI key** — add billing at platform.openai.com; no code change needed
2. **Use Ollama** — install Ollama, pull `qwen3:8b`, set `AI_PROVIDER=OLLAMA`, `OLLAMA_BASE_URL=http://host.docker.internal:11434`
3. **Use Anthropic** — set `ANTHROPIC_API_KEY` (currently blank) and `AI_PROVIDER=ANTHROPIC`
4. **Obtain valid Gemini key** — current key (`AQ.Ab8R...`) appears invalid; standard format is `AIza...`

---

### ISSUE-002 — IKP Knowledge Base Coverage Gap

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Knowledge base |
| **Status** | Open |
| **Root cause** | `knowledge_chunks.json` files primarily contain structured module/programme metadata (codes, credits, names), not free-text policy documents. |
| **Impact** | Compliance-related queries ("What are the assessment compliance requirements?") retrieve module metadata entries rather than policy text. Retrieval works correctly but knowledge base lacks policy content. |

**Resolution:** Enrich the IKP knowledge chunks with assessment policy text, compliance checklists, moderation procedure documents, and accreditation criteria. This is a knowledge engineering task requiring IKP content authors to add policy documents to the chunking pipeline.

---

### ISSUE-003 — fastembed Model Cached in Container (Not in Image)

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Category** | Infrastructure |
| **Status** | Open |
| **Root cause** | `fastembed` was installed via `docker exec` on the running container. If the container is recreated (e.g., `docker compose down && docker compose up`), fastembed must be reinstalled. |
| **Impact** | Fresh container start without fastembed will fall back to placeholder embeddings. |

**Resolution:** Add `fastembed` to the Docker build (either via `requirements.txt` in a rebuilt image, or via `docker compose up --build`). The `requirements.txt` entry `fastembed>=0.3,<1.0` is already added — a fresh `docker compose up --build` will install it permanently.

```bash
docker compose down
docker compose up -d --build
```

---

### ISSUE-004 — Browser Validation Not Yet Conducted

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Category** | QA |
| **Status** | Open |
| **Root cause** | Recovery sprint focused on backend and API-level fixes. Full interactive browser sessions not yet completed. |
| **Impact** | UI correctness for Audit Centre, AI Workspace, and role-based views not yet validated visually. |

**Resolution:** Conduct browser validation sessions as specified in `AQAA_BROWSER_VALIDATION_REPORT.md`.

---

### ISSUE-005 — Gemini API Key Format Invalid

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Category** | AI provider |
| **Status** | Open |
| **Root cause** | `GEMINI_API_KEY` in `backend/.env` has format `AQ.Ab8R...`. Standard Google AI Studio keys begin with `AIza`. All API calls to Gemini endpoints returned 404. |
| **Impact** | Gemini cannot be used as an AI provider. |

**Resolution:** Obtain a valid Gemini API key from Google AI Studio (https://aistudio.google.com/app/apikey). Replace the value in `backend/.env`.

---

## Resolved Issues (Reference)

| ID | Issue | Resolved in |
|----|-------|-------------|
| RESOLVED-001 | SHA-256 placeholder embeddings — `is_placeholder_mode: true` | Recovery Sprint Phase 1 |
| RESOLVED-002 | `GET /api/v1/audits` returning empty list (route collision) | Recovery Sprint Phase 2A |
| RESOLVED-003 | Stale "placeholder embeddings" notice in AI answers | Recovery Sprint Phase 1 |
| RESOLVED-004 | Docker container had no working embedding provider | Recovery Sprint Phase 1 (fastembed) |
| RESOLVED-005 | Frontend Audit Centre showing manual audit data instead of AI runs | Recovery Sprint Phase 2A |
