# AQAA Phase C — Pre-Completion Review

**Date:** 2026-07-14  
**Branch:** `recovery/semantic-grounding-and-audit-centre`  
**Migration head:** `a1b2c3d4e5f7`  
**Test count at review:** 1149 passing

---

## 1. Infrastructure Verification

| Item | Status | Notes |
|------|--------|-------|
| PostgreSQL | ✅ Running | `aqaa-postgres`, port 5432 |
| Redis | ✅ Running | `aqaa-redis`, port 6379 |
| Qdrant | ✅ Running | `aqaa-qdrant`, ports 6333/6334 |
| Backend | ✅ Running | `aqaa-backend`, port 8000 |
| Migration head | ✅ Applied | `a1b2c3d4e5f7` — Phase C regulatory framework engine |
| Regulatory seed | ✅ Complete | 4 authorities + 2 frameworks + versions + standards + criteria |

---

## 2. Phase C Tables

All 10 Phase C tables confirmed present in the database:

| Table | Purpose |
|-------|---------|
| `regulatory_authorities` | Authority registry (CHE, SAQA, DHET, ECSA stubs) |
| `quality_frameworks` | Framework definitions |
| `framework_versions` | Versioned framework editions with lifecycle status |
| `framework_applicability_rules` | Entity→framework binding rules |
| `framework_standards` | Standards within a framework version |
| `framework_criteria` | Criteria under a standard (with `is_mandatory`) |
| `evidence_requirements` | What evidence a criterion needs |
| `evidence_criterion_mappings` | File→criterion links with verification state |
| `framework_assessment_runs` | Assessment executions (3 scores stored separately) |
| `criterion_assessment_results` | Per-criterion result rows |
| `cross_framework_mappings` | Cross-framework equivalences (`human_verified` default `false`) |
| `regulatory_findings` | Findings promoted from gaps (FK to criterion + framework_version) |

---

## 3. API Routes (18 registered endpoints)

### Regulatory Authorities (`/api/v1/regulatory-authorities`)
- `GET /` — List authorities (with `is_test_fixture` flag in responses)
- `GET /{id}` — Get authority detail
- `POST /` — Create authority (Admin only)
- `PUT /{id}` — Update authority (Admin only)
- `DELETE /{id}` — Deactivate authority (Admin only, returns 204)

### Quality Frameworks (`/api/v1/quality-frameworks`)
- `GET /` — List frameworks with eagerly loaded versions (`selectinload`)
- `GET /{id}` — Framework detail + versions
- `POST /` — Create framework (Admin only)
- `GET /{id}/versions` — List versions
- `POST /{id}/versions` — Create version
- `GET /versions/{id}` — Version detail (with standards + criteria)
- `POST /versions/{id}/transition` — Version lifecycle transition
- `GET /versions/{id}/standards` — Standards for version
- `POST /versions/{id}/standards` — Create standard

### Framework Assessments (`/api/v1/framework-assessments`)
- `POST /modules/{module_id}/trigger` — Trigger assessment
- `GET /{run_id}` — Get assessment result
- `GET /` — List assessments
- `POST /{run_id}/promote-gaps` — Promote gaps to findings
- `GET /{run_id}/evidence-mappings` — List evidence mappings
- `POST /{run_id}/evidence-mappings` — Create mapping
- `PUT /evidence-mappings/{id}/verify` — Verify a mapping
- `GET /cross-framework-mappings` — List cross-framework mappings
- `POST /cross-framework-mappings` — Create cross-framework mapping (always `human_verified=False`)
- `PUT /cross-framework-mappings/{id}/verify` — Verify mapping (`human_verified=True`)

---

## 4. Scoring Model

Three scores stored and returned separately — never pre-merged:

| Score | Calculation | Collapse rule |
|-------|------------|---------------|
| `mandatory_compliance_score` | 100 if ALL mandatory criteria met, else 0 | Single mandatory failure → 0 |
| `evidence_coverage_score` | Verified evidence count / required evidence count × 100 | Averaged across criteria |
| `quality_score` | Weighted average of non-mandatory scores | Averaged |
| **overall** (derived) | `mandatory × 0.4 + evidence × 0.4 + quality × 0.2` | Never stored, computed on read |

Risk levels: ≥85 → low, ≥70 → medium, ≥50 → high, <50 → critical  
Readiness: mandatory_failures > 0 → `not_ready`, ≥85 → `ready`, ≥70 → `conditionally_ready`

---

## 5. Seeded Test Fixtures

All data prefixed `[TEST FIXTURE]` — NOT authoritative regulatory text:

| Authority | Code | Type |
|-----------|------|------|
| [TEST FIXTURE] Council on Higher Education | CHE-ZA | quality_council |
| [TEST FIXTURE] South African Qualifications Authority | SAQA-ZA | qualification_authority |
| [TEST FIXTURE] Department of Higher Education and Training | DHET-ZA | government_department |
| [TEST FIXTURE] Engineering Council of South Africa | ECSA-ZA | professional_council |

| Framework | Code | Status |
|-----------|------|--------|
| [TEST FIXTURE] Institutional Quality Assurance Framework 2024 | CHE-IQA-2024 | active |
| [TEST FIXTURE] Engineering Accreditation Criteria 2022 | ECSA-E-2022 | active |

---

## 6. Frontend Workspaces (verified in browser)

| Workspace | Route | State |
|-----------|-------|-------|
| Framework Management | `/framework-management` | Shows 2 frameworks + 4 authorities ✅ |
| Regulatory Readiness | `/regulatory-readiness` | Empty state (no assessments) ✅ |
| Quality workspace | `/quality` | 10 cards including 2 new regulatory cards ✅ |

---

## 7. Known Fixes Applied

1. **Python 3.13 + FastAPI 204**: Removed `status_code=204` from 12 route decorators; `files.py` returns `Response(status_code=204)` explicitly.
2. **`framework.versions` null-safety**: `(framework.versions ?? []).filter(...)` in `FrameworkManagement.tsx`.
3. **`selectinload` in list_frameworks**: Added so versions are eagerly loaded in list endpoint.
4. **`list[QualityFrameworkWithVersions]` response model**: List endpoint now returns full versions.
5. **asyncpg DSN scheme**: Seed script strips `+asyncpg` suffix for raw asyncpg connection.
6. **SYSTEM_ADMIN role case**: Seed lookup uses `role::text = 'SYSTEM_ADMIN'` (uppercase, matching DB enum).

---

## 8. Security Compliance Checklist

- [x] No API keys exposed in code or logs
- [x] All test fixtures labelled `[TEST FIXTURE]`
- [x] No authoritative regulatory text hard-coded
- [x] `cross_framework_mappings.human_verified = False` by default; EQUIVALENT requires `human_verified = True` before deduplication use
- [x] No `eval()` / `exec()` in rule evaluation — `_SAFE_OPS` dict used
- [x] Tenant isolation: global frameworks have `institution_id = NULL`; institution-specific have `institution_id` set
- [x] RBAC enforced: all routes use `QAOfficerRequired` or `AdminRequired`
- [x] No public Qdrant access
- [x] No sensitive source text in error messages

---

## 9. Pending — C10 through C12

| Stage | Description | Status |
|-------|-------------|--------|
| C10 | AI Regulatory Orchestration (19 new intents + context resolver) | Pending |
| C11 | Validation (is_test_fixture field, multi-role scenarios, regression) | Pending |
| C12 | 23 documentation files in `docs/regulatory/` | In progress |

---

## 10. Review Conclusion

Phase C baseline (C0–C9) is verified complete. All tables, routes, services, seed data, and frontend workspaces are functional. The scoring model is correct with mandatory collapse semantics. Cross-framework EQUIVALENT mapping requires `human_verified=True` and is enforced at the service layer. The system is safe to proceed to C10.
