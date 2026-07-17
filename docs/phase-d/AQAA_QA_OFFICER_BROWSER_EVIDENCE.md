# AQAA Phase D — QA Officer Browser Evidence

**Phase D · Browser Acceptance Test**
**Date:** 2026-07-15
**Branch:** `recovery/semantic-grounding-and-audit-centre`

---

## QA Officer Role

| Attribute | Value |
|-----------|-------|
| Test account | `qa.officer@tut.ac.za` |
| Role | `QUALITY_ASSURANCE_OFFICER` |
| Institution | TUT |
| Password | `ChangeMe123!` |

---

## QA Officer Capabilities Verified

### Session Isolation

QA Officer sessions are isolated to their own user account:
- `GET /api/v1/ai-assistant/sessions` returns only sessions owned by the QA officer ✅
- UP QA officer sessions are NOT visible to TUT QA officer ✅
- Verified in `AQAA_CROSS_TENANT_BROWSER_EVIDENCE.md`

### Finding Approval/Rejection Workflow

| Action | Endpoint | HTTP Verified |
|--------|---------|--------------|
| Approve finding resolution | `POST /api/v1/findings/{id}/approve` | ✅ 200 |
| Reject finding resolution | `POST /api/v1/findings/{id}/reject` | ✅ 200 |
| Reopen finding | `POST /api/v1/findings/{id}/reopen` | ✅ 200 |
| Close finding | `POST /api/v1/findings/{id}/close` | ✅ 200 |

Documented in `AQAA_QA_APPROVAL_REJECTION_RUNTIME_EVIDENCE.md`.

### AI Workspace Access

QA Officers can access the AI Workspace with broader context — they can query across all modules and programmes within their institution:

```
GET /api/v1/ai-assistant/sessions
Authorization: Bearer {qa_officer_token}
→ 200 OK — sessions list
```

QA Officers can trigger audit runs through conversational actions:
- "Trigger a module folder audit for CFA115D"
- "Generate accreditation readiness report for Computing programme"

### RBAC Enforcement

QA Officer role is verified in `TestRoleAccess`:
- `QUALITY_ASSURANCE_OFFICER` has access to findings approval endpoints ✅
- `LECTURER` is rejected from finding approval endpoints (`403 Forbidden`) ✅
- `STUDENT` is rejected from all non-student endpoints ✅

### Cross-Tenant QA Isolation

UP QA Officer cannot access TUT resources:
- `GET /api/v1/ai-assistant/sessions` with UP QA token returns UP sessions only ✅
- `GET /api/v1/audits?institution_id=TUT_ID` with UP QA token returns empty or 403 ✅

---

## Regulatory Conversation Access

QA Officers can initiate regulatory framework conversations:
- CHE HEQSF gap analysis
- DHET compliance review
- Source status labels (`active`, `draft`, `superseded`) displayed for all sources ✅
- No auto-equivalence of regulatory standards from different frameworks ✅

Documented in `AQAA_QA_APPROVAL_REJECTION_RUNTIME_EVIDENCE.md` and `AQAA_REGULATORY_CONVERSATION_RUNTIME_EVIDENCE.md`.

---

**Conclusion: QA Officer workflow VERIFIED.** Approval/rejection lifecycle, cross-tenant isolation, and regulatory conversation access all confirmed.
