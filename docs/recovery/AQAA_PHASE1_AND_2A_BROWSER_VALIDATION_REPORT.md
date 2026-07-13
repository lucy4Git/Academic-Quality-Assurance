# AQAA Phase 1 & 2A Browser Validation Report (Combined)

**Document:** AQAA_PHASE1_AND_2A_BROWSER_VALIDATION_REPORT  
**Sprint:** Recovery Sprint  
**Date:** 2026-07-13  
**Status:** API VALIDATED — BROWSER SESSIONS PENDING

---

This document is the combined Phase 1 + Phase 2A validation report. See also `AQAA_BROWSER_VALIDATION_REPORT.md` for the detailed test matrix.

## API Validation Results

### Phase 1 — Embedding and AI Assistant

All tests conducted via `http://localhost:8000` using PowerShell HTTP calls.

| Test | Method | Endpoint | Credential | Result |
|------|--------|----------|------------|--------|
| Login | POST | `/api/v1/auth/login` | `qa.officer@tut.ac.za / ChangeMe123!` | ✓ JWT token issued |
| AI question — TUT | POST | `/api/v1/ai-assistant/ask` | QA officer token | ✓ `is_placeholder_mode: false` |
| AI question — sources | POST | `/api/v1/ai-assistant/ask` | QA officer token | ✓ `sources[]` contains real chunks |
| AI question — no stale notice | POST | `/api/v1/ai-assistant/ask` | QA officer token | ✓ No "hash-based placeholder" text |
| Docker embedding check | `docker exec` | Python import | N/A | ✓ `FastEmbedEmbeddingService, IS_PLACEHOLDER=False` |

### Phase 2A — Audit Centre

| Test | Method | Endpoint | Credential | Result |
|------|--------|----------|------------|--------|
| List audit runs | GET | `/api/v1/audits` | QA officer token | ✓ Returns 40+ `AuditRunBrief` records |

## Browser UI Validation (To Be Conducted)

### QA Officer Session
- [ ] Login → dashboard redirect
- [ ] Audit Centre shows `AuditRunBrief` list with agent type, run status badges, compliance scores
- [ ] Click audit run → detail view with findings, AI summary, timeline
- [ ] AI Workspace → ask question → answer with sources, no placeholder notice

### Lecturer Session
- [ ] Login → appropriate role dashboard
- [ ] AI Workspace available
- [ ] Cannot access admin-restricted pages (403 redirect)

### Coordinator Session
- [ ] Login → appropriate role dashboard
- [ ] Can trigger audit from module page
- [ ] New audit run appears in Audit Centre after completion

### Cross-Tenant Test
- [ ] TUT user cannot retrieve UP AI answers
- [ ] TUT user cannot see UP audit runs
