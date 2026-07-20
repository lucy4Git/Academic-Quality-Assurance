# AQAA Sprint E0 — Security Gate

**Date:** 2026-07-20
**Branch:** `feature/phase-e-sprint-e0`
**Prepared by:** AQAA Engineering — Security Reviewer
**Scope:** Phase D verified controls + Phase E planned controls

> This document does not claim POPIA certification or legal compliance. It assesses technical security controls only.

---

## Control Classification Legend

| Class | Meaning |
|-------|---------|
| VERIFIED_EXISTING | Control is implemented and verified in Phase D codebase |
| PARTIAL | Control exists but has known gaps |
| PLANNED | Planned for a specific sprint; not yet implemented |
| MISSING | No implementation exists; must be added |
| PILOT_BLOCKER | Must be in place before any pilot institution uses the system |
| PRODUCTION_BLOCKER | Must be in place before commercial production release |

---

## 1. Authentication Controls

| Control | Class | Evidence / Gap | Sprint |
|---------|-------|---------------|--------|
| JWT-based authentication (HS256) | VERIFIED_EXISTING | `backend/app/security.py` — encode/decode with SECRET_KEY | — |
| bcrypt password hashing (12 rounds) | VERIFIED_EXISTING | `backend/app/security.py:hash_password` | — |
| Access token expiry (60 min) | VERIFIED_EXISTING | `backend/app/config.py:ACCESS_TOKEN_EXPIRE_MINUTES` | — |
| Refresh token (7 days) | VERIFIED_EXISTING | `backend/app/config.py:REFRESH_TOKEN_EXPIRE_MINUTES` | — |
| httpOnly cookie token storage (Next.js proxy) | VERIFIED_EXISTING | `frontend/src/app/api/auth/` — token in httpOnly cookie | — |
| Server-side route protection | VERIFIED_EXISTING | `frontend/src/middleware.ts` — redirects if no cookie | — |
| JWT logout deny-list (Redis) | MISSING + PILOT_BLOCKER | Redis configured but not used for blocklisting; logout does not invalidate token | E1 |
| MFA (TOTP) for QA Officer and above | MISSING | Not implemented; required for pilot roles | E2 |
| Brute-force protection (account lockout) | MISSING | No login attempt counting; no lockout | E1 |
| Session cookie attributes (SameSite=Strict, Secure) | PARTIAL | httpOnly set via Next.js; Secure and SameSite not explicitly set in proxy — requires TLS (ADR-0015) | E1 |

---

## 2. Authorization and RBAC

| Control | Class | Evidence / Gap | Sprint |
|---------|-------|---------------|--------|
| 7-tier RBAC with cumulative hierarchy | VERIFIED_EXISTING | `backend/app/dependencies.py` — named role shortcuts | — |
| Role guards on all protected routes | VERIFIED_EXISTING | All route functions use `AdminRequired`, `QAOfficerRequired`, etc. | — |
| Client-side role guard | VERIFIED_EXISTING | `frontend/src/components/auth/RoleGuard.tsx` | — |
| Minimum role: Lecturer for AI assistant | VERIFIED_EXISTING | `LecturerRequired` on all `/ai-assistant` endpoints | — |
| SYSTEM_ADMIN cross-institution access control | VERIFIED_EXISTING | `_resolve_institution_code` in `ai_assistant.py` | — |
| Fine-grained action-level permissions | PARTIAL | Role hierarchy is coarse; no per-action permission table | E2 |
| Cross-tenant attempt logging | MISSING + PILOT_BLOCKER | Cross-tenant 404 returned but not logged as security event | E1 |

---

## 3. Tenant Isolation

| Control | Class | Evidence / Gap | Sprint |
|---------|-------|---------------|--------|
| institution_id FK on all entity tables | VERIFIED_EXISTING | Verified across models/ directory | — |
| Service-layer WHERE institution_id filtering | VERIFIED_EXISTING | All service functions scope queries to caller's institution | — |
| Cross-tenant returns 404 (not 403) | VERIFIED_EXISTING | Prevents leaking resource existence | — |
| Qdrant per-institution collection | VERIFIED_EXISTING | `qdrant_service.py` — one collection per institution-year-version | — |
| Qdrant cross-institution assertion at search layer | VERIFIED_EXISTING | `search_service.py` — institution_code assertion | — |
| `Institution.is_demo` for test/demo tenants | VERIFIED_EXISTING | `backend/app/models/institution.py:41` | — |
| Systematic institution_id audit before pilot | MISSING + PILOT_BLOCKER | No audit has been run; service-layer filtering relies on developer discipline | E1 |
| File storage path includes institution_id | PARTIAL | Planned in E-FR-042; not yet verified for all upload paths | E1 |

---

## 4. Secrets Management

| Control | Class | Evidence / Gap | Sprint |
|---------|-------|---------------|--------|
| `.env` excluded from git | VERIFIED_EXISTING | `.gitignore` excludes `backend/.env` | — |
| No secrets in git history | VERIFIED_EXISTING | Verified — no token or key in git log | — |
| Secrets in `.env` file on disk | PARTIAL + PILOT_BLOCKER | Acceptable for development; not acceptable for shared server pilot deployment | E1 |
| Docker secrets (`/run/secrets/`) | MISSING | ADR-0010 proposed; not implemented | E1 |
| Pre-commit hook to block secret commits | MISSING | No hook configured | E1 |
| AI provider API key rotation policy | MISSING | No documented schedule | E1 |
| Distinct secrets per environment (dev/staging/production) | MISSING | All environments currently share same `.env` pattern | E1 |

---

## 5. Transport Security

| Control | Class | Evidence / Gap | Sprint |
|---------|-------|---------------|--------|
| HTTPS / TLS | MISSING + PILOT_BLOCKER + PRODUCTION_BLOCKER | No TLS anywhere; all HTTP on localhost | E1 |
| Reverse proxy (Caddy/nginx) | MISSING | docker-compose.yml has no proxy service | E1 |
| HTTP → HTTPS redirect | MISSING | Requires TLS first | E1 |
| HSTS header | MISSING | Requires TLS; set by Caddy | E1 |

---

## 6. Security Headers

| Control | Class | Evidence / Gap | Sprint |
|---------|-------|---------------|--------|
| X-Frame-Options | MISSING | Not in any middleware | E1 |
| X-Content-Type-Options | MISSING | Not in any middleware | E1 |
| Content-Security-Policy | MISSING | Not configured | E1 |
| Referrer-Policy | MISSING | Not configured | E1 |
| Permissions-Policy | MISSING | Not configured | E1 |

---

## 7. Rate Limiting

| Control | Class | Evidence / Gap | Sprint |
|---------|-------|---------------|--------|
| Rate limiting middleware | MISSING + PILOT_BLOCKER | No slowapi or equivalent; no IP-level limiting | E1 |
| Authenticated endpoint limiting (200 req/min/user) | MISSING | E-FR-040 | E1 |
| Unauthenticated endpoint limiting (30 req/min/IP) | MISSING | E-FR-040 | E1 |
| AI prompt abuse prevention | MISSING | No per-user AI request limiting | E1 |

---

## 8. Input Validation and File Upload

| Control | Class | Evidence / Gap | Sprint |
|---------|-------|---------------|--------|
| File size limit (50 MB) | VERIFIED_EXISTING | `config.py:MAX_UPLOAD_SIZE_MB` | — |
| ZIP path-traversal protection | VERIFIED_EXISTING | `zip_upload_service.py` — path sanitisation and root check | — |
| ZIP member count limit (500) | VERIFIED_EXISTING | `zip_upload_service.py:_MAX_MEMBERS` | — |
| ZIP max uncompressed size (500 MB) | VERIFIED_EXISTING | `zip_upload_service.py:_MAX_UNCOMPRESSED_MB` | — |
| Server-side MIME type validation (binary header) | MISSING | Currently relies on client-supplied content-type; E-FR-043 | E1 |
| ClamAV malware scanning | MISSING + PILOT_BLOCKER | `VIRUS_SCAN_ENABLED = False`; no ClamAV container | E1 |
| Pydantic schema validation on all API inputs | VERIFIED_EXISTING | All route inputs use Pydantic models | — |

---

## 9. Logging and Audit Trails

| Control | Class | Evidence / Gap | Sprint |
|---------|-------|---------------|--------|
| Structured JSON logging | MISSING + PILOT_BLOCKER | Standard unstructured Python `logging` only; no JSON output | E1 |
| Request correlation IDs | MISSING | No X-Request-ID or correlation tracking | E1 |
| Authentication event logging | MISSING | Login/logout not logged to audit trail | E1 |
| Cross-tenant access attempt logging | MISSING | Returns 404 silently | E1 |
| AI query/response audit log (AiAuditLog) | MISSING | Planned table M-E-02 | E2 |
| Finding status change history | VERIFIED_EXISTING | `audit_history.py` model exists | — |
| Append-only corrective action history | MISSING | Planned in E-DATA-002 | E1 |

---

## 10. AI-Specific Security Controls

| Control | Class | Evidence / Gap | Sprint |
|---------|-------|---------------|--------|
| Qdrant tenant isolation for AI search | VERIFIED_EXISTING | Per-institution collections | — |
| AI provider API key not exposed in responses | VERIFIED_EXISTING | Keys in config; never returned in API responses | — |
| Prompt injection prevention | PARTIAL | Retrieval context is prepended; no explicit prompt sanitisation | E2 |
| Retrieval poisoning prevention | PARTIAL | OFFICIAL_VERIFIED + INSTITUTIONAL_APPROVED distinction exists as SourceStatus; enforcement not yet audited for E-FR-020 path | E2 |
| Grounding coverage calculation | PLANNED | E-FR-052 — not yet implemented | E2 |
| AI response flagging (hallucination) | PLANNED | E-FR-051 — not yet implemented | E2 |
| AI audit log (append-only) | PLANNED | E-FR-050 — M-E-02 migration | E2 |
| User feedback on AI responses | PLANNED | E-FR-054 — M-E-06 column addition | E2 |
| AI provider model exposure to users | VERIFIED_EXISTING | Provider config accessible to SYSTEM_ADMIN only via `/api/v1/providers` | — |

---

## 11. Data Protection

| Control | Class | Evidence / Gap | Sprint |
|---------|-------|---------------|--------|
| No real student/staff data in development | VERIFIED_EXISTING | Seeded dataset uses fictional GFU/RCT institutions | — |
| Personal data prohibited until OD-01 resolved | PLANNED | OD-01 condition documented; data boundary register enforces this | E0 |
| DPIA before pilot | MISSING + PILOT_BLOCKER | OD-01 — not started | Pre-E5 |
| Data retention schedules | MISSING | E-GOV-002 — not implemented | E1 |
| DSAR export | MISSING | E-GOV-003 — not implemented | E2 |
| PilotConsent tracking | MISSING | pilot_consent table M-E-05 | E5 |

---

## 12. Operational Security

| Control | Class | Evidence / Gap | Sprint |
|---------|-------|---------------|--------|
| Database backup | MISSING + PILOT_BLOCKER | No backup scripts or automation | E1 |
| Qdrant snapshot | MISSING | No snapshot automation | E1 |
| Administrative access controls | PARTIAL | SYSTEM_ADMIN role exists; no MFA on admin accounts yet | E2 |
| Test account separation from production | MISSING | `is_demo` flag exists; enforcement at service layer not audited | E1 |
| Dependency vulnerability scanning | MISSING | No `pip audit` or `npm audit` in CI | E1 |
| Secrets rotation procedure | MISSING | No documented procedure | E1 |

---

## 13. Mandatory Security Gates

### Gate 1: Sprint E1 Start

Sprint E1 implementation may begin when ALL of the following are met:

| # | Gate | Status |
|---|------|--------|
| G1-01 | ADR-0009 (task queue) decided | OPEN — E0-OD-001 |
| G1-02 | ADR-0010 (secrets) decided | OPEN — E0-OD-002 |
| G1-03 | ADR-0011 (observability) decided | OPEN — E0-OD-003 |
| G1-04 | ADR-0015 (TLS/reverse proxy) decided | OPEN — E0-OD-004 |
| G1-05 | ADR-0013 (tenant isolation strategy) confirmed | OPEN — E0-OD-006 |
| G1-06 | Data boundary register approved | OPEN (this sprint) |
| G1-07 | Sprint E1 backlog frozen | OPEN (this sprint) |
| G1-08 | E0 acceptance report approved by owner | OPEN |

### Gate 2: Sprint E2 Start

| # | Gate | Status |
|---|------|--------|
| G2-01 | TLS operational (ADR-0015 implemented) | NOT_STARTED |
| G2-02 | Rate limiting in place | NOT_STARTED |
| G2-03 | JWT deny-list active | NOT_STARTED |
| G2-04 | Structured logging operational | NOT_STARTED |
| G2-05 | Security headers applied | NOT_STARTED |
| G2-06 | Dependency vulnerability scan clean | NOT_STARTED |
| G2-07 | File MIME validation implemented | NOT_STARTED |
| G2-08 | File storage paths include institution_id | NOT_STARTED |
| G2-09 | ClamAV scanning active | NOT_STARTED |
| G2-10 | Database backup scripts operational | NOT_STARTED |

### Gate 3: Pilot Start

All Gate 2 items plus:

| # | Gate | Status |
|---|------|--------|
| G3-01 | OD-01 resolved — Information Officer designated | OPEN |
| G3-02 | OD-02 resolved — Pilot institution confirmed | OPEN |
| G3-03 | DPIA completed and documented | OPEN |
| G3-04 | Pilot consent records ready | NOT_STARTED |
| G3-05 | CHE / DHET / SAQA documents indexed (OFFICIAL_VERIFIED) | NOT_STARTED |
| G3-06 | Systematic institution_id isolation audit passed | NOT_STARTED |
| G3-07 | Cross-tenant attempt logging active | NOT_STARTED |
| G3-08 | MFA active for QA Officer and above | NOT_STARTED |
| G3-09 | No real personal data in test environments | VERIFIED_EXISTING |
| G3-10 | Pilot rollback procedure documented and tested | NOT_STARTED |
| G3-11 | OWASP Top 10 assessment passed | NOT_STARTED |
| G3-12 | No HIGH/CRITICAL dependency vulnerabilities | NOT_STARTED |
| G3-13 | Staging environment operational with distinct secrets | NOT_STARTED |
| G3-14 | AI governance policy document published | NOT_STARTED |

### Gate 4: Production Release

All Gate 3 items plus:

| # | Gate | Status |
|---|------|--------|
| G4-01 | Full external security audit completed | NOT_STARTED |
| G4-02 | POPIA readiness assessment completed by legal | NOT_STARTED |
| G4-03 | SLA monitoring in place (99.5% uptime target) | NOT_STARTED |
| G4-04 | Disaster recovery plan documented and tested | NOT_STARTED |
| G4-05 | Commercial contract templates reviewed | NOT_STARTED |

---

## 14. Security Posture Summary

| Area | Phase D Status | Phase E Target | Gap severity |
|------|---------------|----------------|-------------|
| Authentication | GOOD | MFA + deny-list | MEDIUM |
| Authorization / RBAC | GOOD | Fine-grained + audit | LOW |
| Tenant isolation | GOOD | Audit required | MEDIUM |
| Transport security | CRITICAL GAP | TLS via Caddy | CRITICAL |
| Secrets management | ACCEPTABLE for dev | Docker secrets for pilot | HIGH |
| Security headers | MISSING | Full OWASP headers | HIGH |
| Rate limiting | MISSING | slowapi | HIGH |
| File upload safety | PARTIAL | MIME + ClamAV | HIGH |
| Logging + audit trail | MINIMAL | structlog + AiAuditLog | HIGH |
| AI-specific controls | PARTIAL | Grounding + hallucination log | MEDIUM |
| Data protection | GOOD for dev | DPIA + consent for pilot | CRITICAL (OD-01) |

---

*Prepared by: AQAA Engineering — Security Reviewer*
*Date: 2026-07-20*
