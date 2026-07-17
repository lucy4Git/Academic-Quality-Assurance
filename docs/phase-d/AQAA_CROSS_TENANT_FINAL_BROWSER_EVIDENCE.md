# AQAA Phase D — Cross-Tenant Final Browser Evidence

**Phase D · Browser Acceptance Test**
**Date:** 2026-07-15
**Branch:** `recovery/semantic-grounding-and-audit-centre`

---

## Institutions Under Test

| Code | Institution | UUID |
|------|-------------|------|
| TUT | Tshwane University of Technology | `46bb6ff4-2ad8-4abe-9ace-6422d9b7636c` |
| UP | University of Pretoria | `a3294995-a14e-4574-950a-8d77031d8310` |

---

## Browser-Level Isolation

### TUT Workspace

Logged in as `lecturer.cs@tut.ac.za` (TUT Lecturer):
- Header breadcrumb: **"Tshwane University of Technology"** ✅
- Knowledge base returns TUT modules only (CFA115D, FRD118G, BFS115D, CFB115D, CGA115D) ✅
- No UP modules appear in any response ✅
- Institution indicator: **"AQAA · TUT"** ✅

---

## Six Isolation Points Verified (HTTP API)

| Isolation Point | Test | Result |
|-----------------|------|--------|
| TUT session → UP user blocked | `GET /sessions/{tut_session_id}` with UP token | ✅ 403 |
| UP session → TUT user blocked | `GET /sessions/{up_session_id}` with TUT token | ✅ 403 |
| TUT sessions absent from UP list | `GET /sessions` with UP token | ✅ No TUT sessions |
| UP sessions absent from TUT list | `GET /sessions` with TUT token | ✅ No UP sessions |
| UP QA sessions absent from TUT QA list | `GET /sessions` with TUT QA token | ✅ No UP QA sessions |
| Attachment `institution_id` correct | Source record for TUT attachment | ✅ TUT UUID |

---

## Session Ownership vs Entity Existence

**Important distinction:**

- `GET /sessions/{id}` returns **403 Forbidden** when the session exists but belongs to a different user — this is correct. Sessions return 403 because "the session exists, you just don't own it."
- `GET /modules/{id}` returns **404 Not Found** when accessed by a user from a different institution — this avoids leaking module existence across tenants.

This distinction is intentional and documented in `TestCrossTenantSessionAccess` (2 tests in `test_phase_d_gaps.py`). ✅

---

## Knowledge Base Isolation

The TUT Institutional Knowledge Package (`institution_id = TUT_UUID`) is:
- Indexed in Qdrant with institution-scoped metadata ✅
- Filtered at query time: `institution_id` filter applied to all vector searches ✅
- Never returned in response to UP user queries ✅

When `lecturer.cs@tut.ac.za` asks "What modules does TUT offer?", the response includes only TUT modules. No UP modules are present. ✅

---

## Attachment Cross-Tenant

Files uploaded by TUT users are stamped with `institution_id = TUT_UUID`:
```python
file.institution_id = current_user.institution_id
```

When a UP user queries a TUT session (if they somehow obtained the session ID), they receive 403 before the attachment content is ever accessed. ✅

TUT attachment `institution_id` appears correctly in grounding source records:
```json
{
  "entity_type": "attached_file",
  "institution_id": "46bb6ff4-2ad8-4abe-9ace-6422d9b7636c"
}
```

---

## Unit Test Coverage

| Test class | Tests | Result |
|-----------|-------|--------|
| `TestCrossTenantSessionAccess` | 2 | ✅ |
| `TestArtifactTenantIsolation` | 6 | ✅ |
| `TestModuleTenantIsolation` | 8 | ✅ |

**Conclusion: Cross-tenant isolation VERIFIED.** All 6 isolation points confirmed. Session ownership returns 403; module/programme endpoints return 404 for cross-tenant access.
