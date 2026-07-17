# AQAA Regulatory Engine — Security Constraints

**Phase C | Version 1.0 | 2026-07-14**

These constraints are hard requirements. They may not be relaxed without a formal security review.

---

## 1. No API Key Exposure

Do not log, return, or store AI provider API keys in:
- API responses
- Error messages
- Log files (any level)
- Frontend code or environment variables accessible to the browser

---

## 2. No Fake Success

Do not return success responses when the underlying operation failed. Do not use:
- Hardcoded success status
- Silent error swallowing that returns HTTP 200 on failure
- `try: ... except: pass` without logging or re-raising

---

## 3. Standalone Project

AQAA is a completely standalone project. It must not be connected to, merged with, copied from, renamed after, or influenced by:

- The MSc Academic Intelligence System
- ResearchOS
- RIAE Agent
- Lecturer Support Agent
- PersonalOS
- Any other project on this machine

No shared database, no shared authentication system, no shared codebase.

---

## 4. Tenant Filter Requirements

Do not:
- Remove tenant filters (`institution_id` scoping)
- Disable RBAC
- Use admin bypasses that expose cross-tenant data
- Add public Qdrant access
- Return confidential evidence content to System Administrators automatically

---

## 5. No Hard-Coded Regulatory Standards

Do not hard-code incomplete or invented regulatory standards as if they were authoritative. All regulatory content must be:
- Clearly labelled `[TEST FIXTURE]` for development stubs
- Sourced from the regulatory authority's official documentation for production data
- Version-controlled with `effective_from`/`effective_to` dates

---

## 6. No Automatic Text Authority

Do not automatically treat imported text as authoritative. External documents imported into the knowledge base require:
- Human review before being surfaced as authoritative
- Explicit authority assignment linking the content to a regulatory authority
- Source URL and version information

---

## 7. No Auto-Equivalence

Do not allow the AI to mark two standards as legally equivalent without human verification. Cross-framework EQUIVALENT mappings require `human_verified = true` before use in:
- Evidence deduplication
- Compliance scoring
- Accreditation recommendations

---

## 8. No Unsafe Code Evaluation

Do not use `eval()`, `exec()`, or `importlib` to evaluate criterion rules. The safe declarative evaluator uses a `_SAFE_OPS` dict with lambda functions only.

---

## 9. Sensitive Data Handling

Do not:
- Log document contents unnecessarily
- Log access tokens at any level
- Include sensitive source text in error messages
- Store secrets in frontend code
- Store API keys in version-controlled files

---

## 10. Conflict Escalation

Do not automatically resolve conflicting regulatory requirements. When CONFLICTING cross-framework mappings are present, the system must:
- Set generation mode to `MANUAL_REVIEW_REQUIRED`
- Return a caveat directing the user to their QA Officer
- Never choose a side in the conflict in AI-generated responses
