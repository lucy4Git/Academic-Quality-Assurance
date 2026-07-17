# AQAA Attachment Context Integration

**Phase D4 · Linking Attachments to Conversation, Message, and Academic Context**
**Date:** 2026-07-15

---

## Architecture

### Context Resolution Flow
```
User sends message with attached files
      ↓
context_engine.resolve_context()
      → resolves module_id, programme_id, institution
      → emits "context" SSE event (includes module_id, programme_id)
      ↓
ask-stream receives AskRequest.attached_file_ids
      ↓
_persist_message_pair() saves user AiChatMessage
      → AiChatMessage.attached_file_ids = [file_id, ...]
      ↓
AiChatSession.context_snapshot updated with resolved context
```

### Module Context Requirement
Files must be uploaded within module context. The `module_id` is:
1. Resolved automatically when a question mentions a module code (e.g. "CSC401")
2. Propagated from `WorkspaceContextHint` when set by the frontend
3. Exposed in the context SSE event's `module_id` field
4. Stored in `activeModuleId` state in the frontend workspace

### File-to-Conversation Linking
- `AiChatMessage.attached_file_ids` (JSONB) stores the list of `File.id` values
- Saved by `_persist_message_pair()` when `attached_file_ids` is non-empty
- `AiChatSession.context_snapshot` (JSONB) stores the full resolved context

### File-to-Message Linking
Each user message that includes file attachments persists `attached_file_ids` directly on the `AiChatMessage` record. This allows conversation restoration to re-display which files were attached to each turn.

### Evidence Scope Restriction
When `AskRequest.attached_file_ids` is non-empty and the question references "these files", "attached documents", "this folder", or "uploaded evidence":
- The execution plan (request_planner) detects EVIDENCE intent
- The orchestration registry routes to the evidence audit agent
- Retrieval scope is limited to the attached file IDs

**Files are NOT automatically promoted to canonical institutional evidence.** They remain in `upload_state: READY` until a QA Officer explicitly accepts them.

---

## Upload State Machine
```
UPLOADED → PROCESSING → READY (clean)
                      → QUARANTINED (security scan failed)
                      → FAILED (storage error)
```

States after attachment:
- `ready`: file is accessible and safe — included in retrieval
- `quarantined`: file is blocked — frontend throws error, not included
- `pending_review`: (future) requires human classification before use
- `needs_classification`: (future) AI suggests category, human confirms

---

## Tenant Isolation
`file_service.upload_file → _resolve_module_institution(db, module_id)`:
- Queries `Faculty.institution_id` via hierarchy JOIN
- If `module_id` not in user's institution → `NotFoundError` → HTTP 404
- System Admin can access any module

---

## Pass/Fail Summary
| Check | Result |
|-------|--------|
| Files linked to conversation message | ✅ AiChatMessage.attached_file_ids |
| Session context snapshot updated | ✅ AiChatSession.context_snapshot |
| Module context required for upload | ✅ module_id required form field |
| module_id in context SSE event | ✅ to_public_dict() now includes module_id, programme_id |
| Files not auto-promoted to canonical evidence | ✅ upload_state stays READY |
| Tenant isolation on upload | ✅ _resolve_module_institution |
| attached_file_ids in AskRequest | ✅ |
