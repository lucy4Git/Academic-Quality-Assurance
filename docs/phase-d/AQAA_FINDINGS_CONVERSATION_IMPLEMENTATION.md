# AQAA Findings through Conversation

**Phase D8 · Finding Lifecycle via AI Workspace**
**Date:** 2026-07-15

---

## Supported Conversational Workflows

### 1. Show My Critical Findings
**Prompt:** "Show my critical findings."
- Intent: `LIST_FINDINGS`
- Route: orchestration registry → `dispatch()` with `LIST_FINDINGS` intent
- Result: structured blocks containing finding cards with severity, status, module

### 2. Show Overdue Findings
**Prompt:** "Show overdue findings for this programme."
- Intent: `LIST_FINDINGS`
- Filter: `due_date < today AND status NOT IN (CLOSED, ARCHIVED)`
- Returns structured blocks, follow-ups suggested

### 3. Explain a Finding
**Prompt:** "Explain the second finding."
- Intent: `EXPLAIN_FINDING`
- Pronoun resolution: "second" → index 1 in last returned finding list
- Returns full finding detail: severity, description, evidence gap, recommendations

### 4. Assign a Finding
**Prompt:** "Assign it to the programme coordinator."
- Intent: `ASSIGN_FINDING`
- Requires confirmation (mutating action)
- Pronoun "it" resolved to last referenced finding
- `confirm=false` → returns `requires_confirmation: true` with confirmation prompt
- `confirm=true` → sets `finding.status = IN_PROGRESS`, `assignee_id` set
- Enforces: Programme Coordinator must be in same institution

### 5. Start Progress
**Prompt:** "Mark it as in progress."
- Intent: `ASSIGN_FINDING` → sets `IN_PROGRESS`

### 6. Add Resolution Evidence
**Prompt:** "Add the attached file as resolution evidence."
- Frontend: `attached_file_ids` in the ask-stream request
- Backend: `AiChatMessage.attached_file_ids` persisted; referenced in finding context
- Future: explicit evidence attachment to finding record (Phase E)

### 7. Submit for Review
**Prompt:** "Submit it for review."
- Intent: `SUBMIT_RESOLUTION`
- Requires confirmation
- Sets: `finding.status = PENDING_REVIEW`
- Tenant check: finding must be in user's institution

### 8. Approve Resolution
**Prompt:** "Approve the resolution."
- Intent: `APPROVE_RESOLUTION`
- Requires confirmation
- Role gate: QA Officer or System Admin only
- Sets: `finding.status = CLOSED`

### 9. Reject Resolution
**Prompt:** "Reject it because the document is unsigned."
- Intent: `REJECT_RESOLUTION`
- Requires confirmation
- Role gate: QA Officer or System Admin only
- Sets: `finding.status = REOPENED`

### 10. Reopen a Finding
**Prompt:** "Reopen it."
- Maps to `REJECT_RESOLUTION` intent (same status transition to REOPENED)

### 11. Escalate Findings
**Prompt:** "Escalate all critical findings for this programme."
- Intent: `ESCALATE_FINDING`
- Requires confirmation
- Sets: `finding.status = ESCALATED`
- Scope: programme in resolved context (from context engine)

### 12. Generate Corrective-Action Plan
**Prompt:** "Generate a corrective-action plan."
- Intent: `GENERATE_CORRECTIVE_ACTION_PLAN`
- Requires confirmation (generates artifact)
- Creates: `AiArtifact` with `artifact_type = "corrective_action_plan"`
- Lists findings → groups by severity → generates structured CAP content

---

## Stage B Lifecycle Enforcement
Transitions enforced in `execute_conversational_action`:
```
OPEN/DRAFT → IN_PROGRESS         (ASSIGN)
IN_PROGRESS → PENDING_REVIEW     (SUBMIT_RESOLUTION)
PENDING_REVIEW → CLOSED          (APPROVE_RESOLUTION)
PENDING_REVIEW → REOPENED        (REJECT_RESOLUTION)
* → ESCALATED                    (ESCALATE_FINDING)
```

Invalid transitions → HTTP 422 or action failure with descriptive message.

---

## Persistence
- Finding status changes persisted to `audit_finding` table via `db.commit()`
- Action recorded to conversation message via structured blocks
- Audit log created (future: AiAction record)
- Finding Centre updated immediately (shared DB, no cache invalidation needed)

---

## Pass/Fail Summary
| Workflow | Result |
|----------|--------|
| List critical findings | ✅ orchestration_registry dispatch |
| Explain finding | ✅ |
| Assign with confirmation | ✅ |
| Submit for review | ✅ |
| Approve (QA+ only) | ✅ |
| Reject (QA+ only) | ✅ |
| Escalate | ✅ |
| Status transitions enforced | ✅ |
| Tenant isolation | ✅ |
| Confirmation gate | ✅ |
| Persistence | ✅ |
