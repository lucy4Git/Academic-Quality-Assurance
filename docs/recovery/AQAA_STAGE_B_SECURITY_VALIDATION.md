# AQAA Stage B — Security Validation

**Date**: 2026-07-13  
**Sprint**: Stage B Recovery  

---

## Security Constraints (Verbatim, from Sprint Spec)

> "Do not expose API keys."  
> "Do not use fake success."  
> "Do not: Remove tenant filters, Disable RBAC, Use admin bypasses, Expose provider keys, Log document contents unnecessarily, Log access tokens, Return confidential evidence to System Administrators automatically, Add public Qdrant access, Store secrets in frontend code, Include sensitive source text in error messages"

---

## Validation Results

### 1. Tenant Isolation

| Check | Method | Result |
|-------|--------|--------|
| UP QA Officer sees TUT findings | Browser `/findings` | 0 findings ✅ |
| UP QA Officer calls TUT finding UUID | `GET /api/v1/findings/{tut_uuid}` | 403 Forbidden ✅ |
| `_assert_tenant()` on accreditation routes | Code review | Present on all `/{run_id}` endpoints ✅ |
| Gap promotion tenant check | `gap_promotion_service.py:79` | `run.institution_id == actor.institution_id` ✅ |

### 2. RBAC Enforcement

| Check | Result |
|-------|--------|
| Student cannot access `/findings` | Access Denied page ✅ |
| Lecturer cannot acknowledge/escalate/close | No action buttons rendered ✅ |
| `promote-gaps` requires QA Officer+ | `QAOfficerRequired` dependency ✅ |
| `reject` endpoint requires a note | `DomainError` raised if note empty ✅ |
| `request-review` restricted to QA Officer | `QAOfficerRequired` (was Lecturer) ✅ |
| State machine `_TRANSITION_ROLES` enforced server-side | `finding_service.py` ✅ |

### 3. Token / Credential Safety

| Check | Result |
|-------|--------|
| JWTs in httpOnly cookies only | `frontend/src/app/api/auth/` proxy routes ✅ |
| No tokens in localStorage/sessionStorage | JS never touches tokens ✅ |
| API calls via Next.js proxy (`/api/proxy/`) | Browser never calls FastAPI directly ✅ |
| No API keys in frontend code | Confirmed — no `NEXT_PUBLIC_*` secrets ✅ |
| `SECRET_KEY` in `backend/.env` (gitignored) | Not committed ✅ |

### 4. AI Provider Key Safety

| Check | Result |
|-------|--------|
| LLM provider keys in `backend/.env` | Not committed ✅ |
| Keys not logged | No `logger.info(api_key)` patterns ✅ |
| Keys not returned in error responses | Exception handler returns generic messages ✅ |

### 5. Qdrant Access

| Check | Result |
|-------|--------|
| Qdrant port 6333 not publicly exposed | `docker-compose.yml` — local bind only ✅ |
| Tenant filter on all vector searches | `institution_code` filter in Qdrant queries ✅ |

### 6. Fake Success / Placeholder Detection

Stage B changes contain no:
- `return {"status": "ok"}` without real processing
- Hard-coded mock data
- `TODO: implement` stubs in new endpoints

The `gap_promotion_service.py` and `promote-gaps` endpoint are fully functional. The accreditation polling uses real run IDs from the backend.

---

## No Regressions to Security Controls

All changes in Stage B (canonical lifecycle, accreditation polling, gap promotion) were additive or corrective. No existing security controls were modified, removed, or bypassed.
