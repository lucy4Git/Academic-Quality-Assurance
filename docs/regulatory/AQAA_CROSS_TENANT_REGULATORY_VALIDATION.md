# AQAA Cross-Tenant Regulatory Validation

**Phase C Closure Gate | 2026-07-14**

---

## Overview

Validates that no regulatory data from Tshwane University of Technology (TUT)
is accessible to University of Pretoria (UP) users, and vice versa.

---

## Tenant Isolation Mechanism

Tenant isolation in the regulatory engine is enforced at **three layers**:

### Layer 1 — Service layer SQL filter

`regulatory_orchestration_service.py` → `_resolve_effective_frameworks()`:

```sql
SELECT qf.* FROM quality_frameworks qf
WHERE qf.is_active = TRUE
  AND (qf.institution_id IS NULL OR qf.institution_id = :user_institution_id)
```

Global frameworks (`institution_id IS NULL`) are visible to all institutions.
Institution-specific frameworks are only visible to their own institution.

### Layer 2 — Citation filter

`regulatory_orchestration_service.py` → `_build_citations()`:

```python
if context.institution_id is not None:
    stmt = stmt.where(
        or_(
            QualityFramework.institution_id.is_(None),
            QualityFramework.institution_id == context.institution_id,
        )
    )
```

Even if a framework ID somehow leaked into the effective_framework_codes list,
this second filter prevents it from being cited.

### Layer 3 — Institution code resolution

`ai_assistant.py` → `_resolve_institution_code()`:

Non-admin users are locked to their own institution. The request body
`institution_code` is ignored for non-admin users — the DB lookup uses
`current_user.institution_id` directly.

---

## 18 Data Categories — Zero Leakage Validation

| # | Data category | TUT→UP leakage | UP→TUT leakage |
|---|---------------|---------------|---------------|
| 1 | Regulatory authorities (institution-specific) | ✅ None | ✅ None |
| 2 | Quality frameworks (institution-specific) | ✅ None | ✅ None |
| 3 | Framework versions | ✅ None | ✅ None |
| 4 | Framework standards | ✅ None | ✅ None |
| 5 | Framework criteria | ✅ None | ✅ None |
| 6 | Evidence requirements | ✅ None | ✅ None |
| 7 | Applicability rules | ✅ None | ✅ None |
| 8 | Cross-framework mappings | ✅ None | ✅ None |
| 9 | Framework assessment runs | ✅ None | ✅ None |
| 10 | Assessment criterion results | ✅ None | ✅ None |
| 11 | Audit findings | ✅ None | ✅ None |
| 12 | Regulatory citations in AI responses | ✅ None | ✅ None |
| 13 | AI chat session content | ✅ None (user_id scoped) | ✅ None |
| 14 | Audit run history | ✅ None | ✅ None |
| 15 | Uploaded evidence files | ✅ None (module → dept → institution scoped) | ✅ None |
| 16 | User accounts | ✅ None | ✅ None |
| 17 | Institution name in AI responses | ✅ TUT name only | ✅ UP name only |
| 18 | Effective framework list in regulatory SSE event | ✅ TUT frameworks only | ✅ UP frameworks only |

Global frameworks (`institution_id = NULL`, all prefixed `[TEST FIXTURE]`) are
visible to **both** TUT and UP — this is expected and correct behaviour for shared
national standards (CHE-HEQ-2023, DHET-SPF-2022, SAQA-NQF-2012, ECSA-E-2022,
HPCSA-MED-2023, SACE-PGCE-2022, QCTO-OQF-2021).

---

## System Admin Cross-Tenant Access

SYSTEM_ADMIN users CAN access both TUT and UP data, but only one tenant at a time.
They must explicitly supply `institution_code` in each request. The response is
scoped to that institution only.

**This is intentional** — System Admins are platform operators, not institution staff.
They cannot see both institutions' data in a single API response.

---

## Test: UP Admin querying TUT frameworks

```
POST /api/v1/ai-assistant/ask-stream
Authorization: Bearer <UP_SYSTEM_ADMIN_JWT>
{
  "question": "Which frameworks apply?",
  "institution_code": "UP"
}
```

**Expected:** effective_frameworks contains only global frameworks (visible to UP)
**Actual:** Same — no TUT-specific frameworks appear ✅

```
POST /api/v1/ai-assistant/ask-stream
Authorization: Bearer <UP_SYSTEM_ADMIN_JWT>
{
  "question": "Which frameworks apply?",
  "institution_code": "TUT"
}
```

**Expected:** effective_frameworks contains TUT-visible frameworks
**Actual:** Same — UP-specific frameworks do NOT appear in TUT's response ✅

---

## Audit Trail

The `logger.info()` call in `orchestrate_regulatory_query()` records:
```
RegulatoryOrchestration: intent=... mode=... user=<uuid> institution=<uuid> frameworks=[...]
```

This provides a server-side audit trail for every regulatory query. The institution
UUID is always recorded, making cross-tenant queries detectable in server logs.
