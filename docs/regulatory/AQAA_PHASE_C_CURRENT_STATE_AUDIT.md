# AQAA Phase C — Current State Audit

**Date**: 2026-07-14  
**Branch**: `recovery/semantic-grounding-and-audit-centre`  
**Starting commit**: `72aae37`  
**Migration head**: `7a8b9c0d1e2f`  
**Docker**: All 4 containers healthy (postgres, redis, qdrant, backend)

---

## Repository Root

`C:\Users\Staff 101\OneDrive\Desktop\AQAA`

---

## Baseline Confirmed

| Capability | Status |
|-----------|--------|
| Auth (JWT, httpOnly cookies, RBAC) | ✅ OPERATIONAL |
| Multi-tenancy + tenant isolation | ✅ OPERATIONAL |
| Semantic embeddings (Qdrant) | ✅ OPERATIONAL (Stage A) |
| 8 AI audit agents | ✅ OPERATIONAL |
| Findings Centre (12-status lifecycle) | ✅ OPERATIONAL (Stage B) |
| Findings state machine + audit trail | ✅ OPERATIONAL (Stage B) |
| Accreditation workspace + polling | ✅ OPERATIONAL (Stage B) |
| Gap promotion (accreditation → findings) | ✅ OPERATIONAL (Stage B) |
| Backend test suite: 1149 pass | ✅ |
| Frontend TypeScript: 0 errors | ✅ |

---

## Existing Accreditation Components — Phase C Classification

| Component | Location | Classification | Rationale |
|-----------|----------|---------------|-----------|
| `AccreditationReadiness` agent | `backend/app/agents/accreditation_readiness.py` | PRESERVE | Core audit logic; not replaced |
| `accreditation_readiness_service.py` | `backend/app/services/` | PRESERVE | Run management; not replaced |
| `accreditation_readiness_report_service.py` | `backend/app/services/` | EXTEND | Add framework-specific scoring |
| `accreditation_readiness_audits.py` (routes) | `backend/app/routes/` | EXTEND | Add framework endpoints |
| `AccreditationWorkspace.tsx` | `frontend/src/app/(main)/accreditation/` | EXTEND → MIGRATE | Evolve to Regulatory Readiness; keep until new is complete |
| `gap_promotion_service.py` | `backend/app/services/` | EXTEND | Add framework citation fields |
| `schemas/accreditation_readiness.py` | `backend/app/schemas/` | PRESERVE | Existing schema kept |
| `models/accreditation.py` | `backend/app/models/` | UNKNOWN | Needs inspection |

---

## What Does NOT Exist (Phase C Must Build)

| Component | Status |
|-----------|--------|
| Regulatory Authority model | ❌ Missing |
| Quality Framework model | ❌ Missing |
| Framework Version model | ❌ Missing |
| Standard model | ❌ Missing |
| Criterion model | ❌ Missing |
| Evidence Requirement model | ❌ Missing |
| Applicability Rule model | ❌ Missing |
| Evidence Mapping model | ❌ Missing |
| Framework Assessment model | ❌ Missing |
| Cross-Framework Mapping model | ❌ Missing |
| Framework Management workspace (frontend) | ❌ Missing |
| Regulatory Readiness workspace (frontend) | ❌ Missing |
| Regulatory context in AI orchestration | ❌ Missing |
| Regulatory citations on AuditFinding | ❌ Missing |

---

## Migration Chain at Phase C Start

```
99c7b97c9a76 → bcb42a8b6462 → 6bcc7db53782 → a1afe7223e2a → 146ff3d10cd9
→ 2a7b17360d01 → 7c5db84357e3 → b0df78d4b8ec → a1b2c3d4e5f6 → c4d5e6f7a8b9
→ d5e6f7a8b9c0 → e6f7a8b9c0d1 → f7a8b9c0d1e2 → b2c3d4e5f6a7 → c3d4e5f6a7b8
→ d4e5f6a7b8c9 → 39b2fec2e97f → 7a8b9c0d1e2f (HEAD)
```

Phase C will add new migrations from `7a8b9c0d1e2f`.

---

## Key Files for Phase C Integration

- `backend/app/models/base.py` — `Base`, `UUIDPrimaryKeyMixin`, `TimestampMixin` (must inherit)
- `backend/app/models/enums.py` — all shared enums (Phase C adds new enums here)
- `backend/app/dependencies.py` — RBAC shortcuts (`QAOfficerRequired`, etc.)
- `backend/app/core/exceptions.py` — domain exceptions
- `backend/app/models/audit_finding.py` — `AuditFinding` (Phase C extends with regulatory FKs)
- `backend/app/models/institution.py` — tenant anchor
- `backend/app/main.py` — router registration (Phase C adds new routers)
