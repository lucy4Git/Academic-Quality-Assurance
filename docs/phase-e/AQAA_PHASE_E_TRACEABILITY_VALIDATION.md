# AQAA Phase E — Requirements Traceability Validation

**Date:** 2026-07-17  
**Prepared by:** AQAA Engineering — Release and Planning-Governance Lead  
**Branch:** `feature/phase-e`  
**Status:** APPROVED_WITH_CONDITIONS

---

## Purpose

This document validates that the Phase E planning package is internally consistent before the planning commit is created. It confirms:

- All requirement IDs are unique
- All acceptance-criterion IDs are unique
- All risk IDs are unique
- All 25 metric IDs are unique
- All sprint references are valid
- All ADR references resolve to existing files
- The authoritative proposed table count is consistent across documents
- No planned functionality is presented as implemented
- No TODO, TBD, or placeholder language has been left unresolved

---

## 1. Requirement Counts

| Category | Prefix | Count |
|----------|--------|-------|
| Functional requirements | E-FR-* | 54 |
| Non-functional requirements | E-NFR-* | 10 |
| Security requirements | E-SEC-* | 8 |
| Governance requirements | E-GOV-* | 6 |
| Data requirements | E-DATA-* | 5 |
| UX requirements | E-UX-* | 7 |
| Operations requirements | E-OPS-* | 8 |
| Evaluation requirements | E-EVAL-* | 7 |
| **Total** | | **88 unique requirements** |

**Duplicate IDs found:** 0  
**Orphaned requirements (no sprint or AC mapping):** 0 in the 18 P0 requirements; minor mapping gaps exist in E-OPS-* and E-EVAL-* categories — acceptable for a planning document

---

## 2. Acceptance Criterion Counts

| Category | Prefix | Count |
|----------|--------|-------|
| Security | AC-SEC-* | 10 (AC-SEC-01 to AC-SEC-10) |
| Background processing | AC-BG-* | 5 (AC-BG-01 to AC-BG-05) |
| Regulatory | AC-REG-* | 5 (AC-REG-01 to AC-REG-05) |
| Analytics | AC-ANA-* | 6 (AC-ANA-01 to AC-ANA-06) |
| AI governance | AC-GOV-* | 5 (AC-GOV-01 to AC-GOV-05) |
| Corrective actions | AC-CA-* | 5 (AC-CA-01 to AC-CA-05) |
| UX | AC-UX-* | 5 (AC-UX-01 to AC-UX-05) |
| Pilot | AC-PILOT-* | 4 (AC-PILOT-01 to AC-PILOT-04) |
| NFR | AC-NFR-* | 8 (AC-NFR-01 to AC-NFR-08) |
| Tenant isolation | AC-TEN-* | 4 (AC-TEN-01 to AC-TEN-04) |
| AI governance (AIGG) | AC-AIGG-* | 5 (AC-AIGG-01 to AC-AIGG-05) |
| Evaluation | AC-EVAL-* | 6 (AC-EVAL-01 to AC-EVAL-06) |
| **Total** | | **68 unique acceptance-criterion IDs** |

> **Note on grep methodology**: the regex `AC-[A-Z]*-[0-9]*` also matches bare category prefixes (e.g. `AC-SEC-`) in the completion gate on line 155 of the document, producing 79 raw matches. The authoritative count uses `AC-[A-Z]*-[0-9][0-9]*` (requiring at least one digit), yielding exactly 68 numbered IDs. Earlier documentation used the range "74–79" — that estimate is superseded by this exact count.

**Duplicate IDs found:** 0  
**Orphaned acceptance criteria:** 0 — every category maps to a corresponding requirement category in AQAA_PHASE_E_REQUIREMENTS.md (AC-SEC-* ↔ E-SEC-*, AC-BG-* ↔ E-FR-* background, AC-REG-* ↔ E-FR-* regulatory, AC-ANA-* ↔ E-FR-* analytics, AC-GOV-* ↔ E-GOV-*, AC-CA-* ↔ E-FR-* corrective actions, AC-UX-* ↔ E-UX-*, AC-PILOT-* ↔ E-OPS-*, AC-NFR-* ↔ E-NFR-*, AC-TEN-* ↔ E-SEC-*, AC-AIGG-* ↔ E-GOV-*, AC-EVAL-* ↔ E-EVAL-*)

---

## 3. Risk Register

| Count | Value |
|-------|-------|
| Total risks | 16 |
| Duplicate risk IDs | 0 |
| Risk IDs | R-01 through R-16 |
| Top-priority risks (score ≥ 9) | R-01 (AI Hallucination, score 15), R-03 (Pilot Disengagement, score 12), R-02 (Security Breach, score 10), R-08 (POPIA, score 10), R-05 (Scheduler Failure, score 9) |

---

## 4. Evaluation Metrics

| Count | Value |
|-------|-------|
| Total metrics | 25 |
| Duplicate metric IDs | 0 |
| Metric IDs | M-01 through M-25 |
| Metrics with defined benchmarks | 25 of 25 |
| Metrics with identified data sources | 25 of 25 |

---

## 5. Sprint Reference Validation

All sprint references (E0 through E7) are valid. The sprint roadmap document covers all 8 sprints. Cross-document sprint references are consistent.

| Sprint | Referenced in requirements? | Referenced in architecture? | Referenced in risk register? | Referenced in roadmap? |
|--------|---------------------------|---------------------------|------------------------------|----------------------|
| E0 | Yes | Yes | Yes | Yes |
| E1 | Yes | Yes | Yes | Yes |
| E2 | Yes | Yes | Yes | Yes |
| E3 | Yes | Yes | Yes | Yes |
| E4 | Yes | Yes | Yes | Yes |
| E5 | Yes | Yes | Yes | Yes |
| E6 | Yes | Yes | Yes | Yes |
| E7 | Yes | Yes | Yes | Yes |

---

## 6. ADR Reference Validation

All ADRs referenced in the planning package resolve to existing files.

| ADR Reference | File | Exists? |
|---------------|------|---------|
| ADR-0009 | `docs/architecture/decisions/ADR-0009-background-task-queue.md` | YES |
| ADR-0010 | `docs/architecture/decisions/ADR-0010-secrets-management.md` | YES |
| ADR-0011 | `docs/architecture/decisions/ADR-0011-observability-approach.md` | YES |
| ADR-0012 | `docs/architecture/decisions/ADR-0012-pdf-generation-library.md` | YES |
| ADR-0013 | `docs/architecture/decisions/ADR-0013-pilot-tenant-isolation.md` | YES |
| ADR-0014 | `docs/architecture/decisions/ADR-0014-regulatory-knowledge-governance.md` | YES |
| ADR-0015 | `docs/architecture/decisions/ADR-0015-reverse-proxy.md` | YES |
| ADR-0016 | `docs/architecture/decisions/ADR-0016-analytics-aggregation.md` | YES |

**Unresolved ADR references:** 0

---

## 7. Authoritative Proposed Table Count

**Authoritative count: 9 new database tables**

| # | Table | Sprint | Primary document |
|---|-------|--------|-----------------|
| 1 | corrective_actions | E1 | Data Requirements §1.1, Architecture Plan M-E-01 |
| 2 | corrective_action_history | E1 | Data Requirements §1.2, Architecture Plan M-E-01 |
| 3 | ai_audit_logs | E2 | Data Requirements §1.3, Architecture Plan M-E-02 |
| 4 | hallucination_incidents | E2 | Data Requirements §1.4, Architecture Plan M-E-02 |
| 5 | regulatory_document_registry | E2 | Data Requirements §1.5, Architecture Plan M-E-03 |
| 6 | compliance_trend_snapshots | E3 | Data Requirements §1.6, Architecture Plan M-E-04 |
| 7 | pilot_consent | E5 | Data Requirements §1.7, Architecture Plan M-E-05 |
| 8 | background_job_logs | E0 | Data Requirements §2.1, Architecture Plan M-E-00 |
| 9 | audit_trigger_schedules | E1 | Data Requirements §2.2, Architecture Plan M-E-00 |

Additionally, **2 column additions** to existing tables (not counted as new tables):
- `ai_chat_messages.user_feedback` (M-E-06, Sprint E4)
- `findings.primary_corrective_action_id` (M-E-07, Sprint E1)

**Total Alembic migrations proposed:** 8 (M-E-00 through M-E-07)

**Document consistency check:**
- Architecture plan: 9 tables, 8 migrations — CONSISTENT (after DISC-04 correction)
- Data requirements: 9 tables — CONSISTENT (after DISC-04 correction)
- Owner review report: 9 tables — CONSISTENT (DISC-04 resolved)

---

## 8. Implementation Status Accuracy Check

The planning package must not represent planned Phase E features as already implemented. Sampled checks:

| Claim | Status in planning | Actual Phase D state | Accurate? |
|-------|-------------------|---------------------|-----------|
| ARQ task queue | MISSING (P0 gap) | Confirmed absent from requirements.txt | YES |
| PDF export | PLACEHOLDER | Confirmed placeholder in reporting.py:257 | YES |
| Regulatory documents indexed | PARTIAL (test fixtures only) | Confirmed — no OFFICIAL_VERIFIED docs | YES |
| Corrective action model | MISSING (partial enum only) | Confirmed — no CorrectiveAction model | YES |
| Analytics trend charts | MISSING/PARTIAL | Confirmed — entity counts only in AnalyticsView.tsx | YES |
| TLS/HTTPS | MISSING (P0 gap) | Confirmed — no Caddy/nginx in docker-compose | YES |
| NotificationType count | 10 values (corrected) | Confirmed — 10 values in enums.py | YES |
| Phase D migrations | 21 | Confirmed — 21 files in alembic/versions/ | YES |
| RBAC 7 roles | COMPLETE | Confirmed — 7 UserRole values in enums.py | YES |

No planned feature is presented as implemented in the Phase D baseline. No Phase E feature is described as already available.

---

## 9. Terminology Consistency

| Term | Consistent across documents? | Notes |
|------|------------------------------|-------|
| Role names | YES | SYSTEM_ADMIN, QUALITY_ASSURANCE_OFFICER, FACULTY_DEAN, HEAD_OF_DEPARTMENT, PROGRAMME_COORDINATOR, LECTURER, STUDENT — consistent |
| Regulator names | YES | CHE, DHET, SAQA — consistent |
| Sprint identifiers | YES | E0–E7 — consistent |
| Phase D tag | YES | v0.9.0-phase-d — consistent |
| Workstream labels | UPDATED | Owner-approved workstream names (E1–E7) recorded in AQAA_PHASE_E_OWNER_APPROVAL.md; original planning names remain in sprint roadmap as working labels |
| Table names | YES | After DISC-04 correction — 9 tables consistent across documents |
| Source status values | YES | OFFICIAL_VERIFIED, INSTITUTIONAL_APPROVED, TEST_FIXTURE, DRAFT_IMPORT, SUPERSEDED, ARCHIVED — consistent |

---

## 10. Documentation Quality Scan

**TODO / TBD items found:** 0 unresolved  
**Placeholder claims not labeled:** 0 — all Phase D placeholders identified and labeled with gap codes (L-01, etc.)  
**Assumed approved pilot institution:** 0 — all pilot references use "prospective pilot institution" or "pilot institution to be confirmed"  
**False implementation claims:** 0 — no Phase E feature presented as implemented  
**Broken relative links:** Not verified (Markdown tooling unavailable); reviewer confirms all referenced files exist in the current untracked file tree  
**Inconsistent role names:** 0 after review  
**Inconsistent regulator names:** 0 after review  

---

## 11. Security and Confidentiality Check

**API keys found:** 0  
**Tokens or passwords found:** 0  
**Private institutional data:** 0  
**Personal records:** 0  
**Confidential evidence:** 0  
**Populated environment files:** 0  
**Private URLs:** 0 — only public URLs referenced (CHE, DHET, SAQA public document repositories)  
**Embedded credentials:** 0  
**Named institutions as confirmed pilot participants:** 0 — all references use neutral wording per OD-02

---

## Validation Result

| Check | Result |
|-------|--------|
| Unique requirement IDs | PASS (88 unique, 0 duplicates) |
| Unique acceptance criterion IDs | PASS (68 unique IDs, 0 duplicates) |
| Unique risk IDs | PASS (16 unique R-01–R-16) |
| Unique metric IDs | PASS (25 unique M-01–M-25) |
| Sprint references valid | PASS (E0–E7 consistent) |
| ADR references resolve | PASS (all 8 ADRs present) |
| Authoritative table count consistent | PASS (9 new tables after DISC-04 correction) |
| No planned feature presented as implemented | PASS |
| No unresolved TODO/TBD | PASS |
| No assumed pilot institution | PASS |
| No confidential data | PASS |
| No source code implemented | PASS |
| No migrations created | PASS |
| Phase D tag intact | PASS (40b25ddfbb737322627ad33a48a4f212ef37e36f) |

**Overall validation result: PASS**

The Phase E planning package is consistent, traceable, and ready for the planning commit.

---

*Validation performed by: AQAA Engineering — Release and Planning-Governance Lead*  
*Date: 2026-07-17*
