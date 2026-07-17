# AQAA Full Session Restoration Evidence

**Phase D · Runtime Validation 4**
**Date:** 2026-07-15
**Branch:** `recovery/semantic-grounding-and-audit-centre`

---

## Test Scenario

Created a session containing:
- Attached file (`aqaa_grounding_fixture.txt`)
- Grounded answer citing the attached file
- Unique validation string in the answer
- Two conversation turns (initial + follow-up)

Then restored the session via `GET /api/v1/ai-assistant/sessions/{session_id}` and verified every field.

---

## Session Creation Evidence

### Turn 1 — Initial grounded question

```
User: "State the unique requirement from the attached file verbatim."
attached_file_ids: ["9d6aed52-168b-4c06-a436-8c90ca434530"]
institution_code: TUT
```

**SSE events received:**
- `attachment`: `grounding_status=success`, `used_count=1`, `failed_count=0`
- `sources`: `entity_type=attached_file`, `entity_id=9d6aed52-...`, `title=aqaa_grounding_fixture.txt`
- `token` (streamed answer containing unique string)
- `session`: `session_id=5b7bb592-1812-400f-af95-d5b67d880ba6`

### Turn 2 — Follow-up in same session

```
User: "Summarise the scope section from the attached file."
session_id: 5b7bb592-1812-400f-af95-d5b67d880ba6
attached_file_ids: ["9d6aed52-168b-4c06-a436-8c90ca434530"]
```

**Session ID preserved:** `5b7bb592-1812-400f-af95-d5b67d880ba6` ✓

---

## Restoration Evidence

```
GET /api/v1/ai-assistant/sessions/5b7bb592-1812-400f-af95-d5b67d880ba6
→ 200 OK
```

### Session Header Fields

| Field | Value |
|-------|-------|
| `id` | `5b7bb592-1812-400f-af95-d5b67d880ba6` |
| `title` | State the unique requirement from the attached file verbatim. |
| `is_pinned` | `false` |
| `is_archived` | `false` |
| `messages` count | 4 (2 user + 2 assistant) |

### Message 1 — User (Turn 1)

| Field | Value |
|-------|-------|
| `role` | `user` |
| `content` | State the unique requirement from the attached file verbatim. |
| `attached_file_ids` | `["9d6aed52-168b-4c06-a436-8c90ca434530"]` |

**✅ Attachment IDs persisted to user message and restored.**

### Message 2 — Assistant (Turn 1)

| Field | Value |
|-------|-------|
| `role` | `assistant` |
| `content` length | 542 characters |
| `sources` | present (non-null) |
| `structured_blocks` | null (no structured blocks in this response) |
| Unique string in content | **YES** — `AQAA-UNIQUE-ATTACHMENT-VALIDATION-7319` |

### Message 3 — User (Turn 2)

| Field | Value |
|-------|-------|
| `role` | `user` |
| `content` | Summarise the scope section from the attached file. |
| `attached_file_ids` | `["9d6aed52-168b-4c06-a436-8c90ca434530"]` |

### Message 4 — Assistant (Turn 2)

| Field | Value |
|-------|-------|
| `role` | `assistant` |
| `content` length | 542 characters |
| `sources` | present |

---

## Restoration Checklist

| Requirement | Result |
|-------------|--------|
| Session ID preserved across turns | ✅ |
| User message content restored | ✅ |
| `attached_file_ids` restored on user message | ✅ |
| File ID matches original upload | ✅ `9d6aed52-168b-4c06-a436-8c90ca434530` |
| Assistant message content restored | ✅ |
| Unique validation string in restored answer | ✅ |
| `sources` restored (entity_type=attached_file) | ✅ |
| `is_pinned` present and defaulting to false | ✅ |
| `is_archived` present and defaulting to false | ✅ |
| Session title restored from first question | ✅ |
| Multi-turn history complete (4 messages) | ✅ |

---

## Session Persistence Architecture

```
POST /ask-stream
  → _persist_and_stream() accumulates:
      answer_parts       → joined as AiChatMessage.content (assistant)
      sources_data       → AiChatMessage.sources (JSONB)
      structured_blocks  → AiChatMessage.structured_blocks (JSONB)
      citations_data     → AiChatMessage.citations (JSONB)
  → _persist_message_pair() writes:
      user message with attached_file_ids
      assistant message with all accumulated data
  → SSE session event emits session_id

GET /sessions/{id}
  → db.get(AiChatSession, session_id)
  → user_id ownership check (403 if mismatch)
  → query AiChatMessage ORDER BY created_at ASC
  → serialize to ChatSessionDetail with ChatMessageBrief[]
```

**Conclusion: Validation 4 PASSED.**
