# AQAA Unverified Completion Claims

**Audit Date:** 2026-07-13  
**Purpose:** Identify features claimed as complete in documentation, CHANGELOG, or PHASE_TRACKER that were not verified through live testing in this audit.  
**Classification:** UNVERIFIED means "not confirmed false — just not confirmed true."

---

## Methodology

A claim is "unverified" if:
1. It appears in CHANGELOG.md, PHASE_TRACKER.md, or commit message as complete, and
2. It was not exercised through a live API call or browser test in this audit session.

A claim is "contradicted" if evidence actively disproves it.

---

## Phase 3 Sprint 3 — "Advanced RAG + Citation Verification"

**Claim** (commit `bc9d4ae`): Production Advanced RAG with citation verification

**Evidence:**
- AI ask endpoint returns real LLM responses ✅
- `is_placeholder_mode: true` in every AI response ❌
- "hash-based placeholder embeddings, not semantic embeddings" ❌

**Classification: CONTRADICTED**

The commit message claims "Production RAG" but the live system returns explicit confirmation that retrieval uses placeholder embeddings. Citations generated may not be semantically grounded. This is the most significant contradiction between documentation and runtime reality.

---

## Phase 4 Wave 2 — "Live streaming verified (92% grounding score)"

**Claim** (PHASE_TRACKER.md): "Live streaming verified (92% grounding score) ✅"

**Evidence:**
- SSE streaming route exists (`/api/v1/ai-assistant/ask-stream`)
- The 92% grounding score comes from `StreamMetadataEvent.confidence_score`
- This score is LLM-self-reported (the LLM reports its confidence), not computed from retrieval quality
- Given `is_placeholder_mode: true`, the score reflects the LLM's confidence in its answer, not the accuracy of retrieved context

**Classification: MISLEADING** — streaming likely works, but the grounding score does not measure what the documentation implies.

---

## Phase 4 Wave 3 — "Live-tested all 7 user roles"

**Claim** (PHASE_TRACKER.md): "Live-tested all 7 user roles through browser Preview ✅"

**MULTI_ROLE_LIVE_UX_VALIDATION_REPORT.md** lists:
- admin@test.com ✅ PASSED
- qa.officer@tut.ac.za ✅ PASSED
- qa.officer@up.ac.za ✅ PASSED
- lecturer.cs@tut.ac.za ✅ PASSED
- lecturer.cos@up.ac.za ✅ PASSED
- student.cs@tut.ac.za ✅ PASSED
- student.cs@up.ac.za ✅ PASSED

**Evidence in this audit:** Admin, QA Officer (TUT), Lecturer (TUT), Student (TUT) confirmed live. QA Officer (UP), Lecturer (UP), Student (UP) — tested in previous session but not independently re-verified in this audit's new context window.

**Classification: PLAUSIBLY TRUE** — 4 roles confirmed in this audit; 3 additional roles confirmed in the prior session; documentation is consistent with observed behaviour.

---

## PHASE_TRACKER — Phase 2 "8 AI audit agents" Complete

**Claim:** All 8 AI audit agents complete and functional

**Evidence:**
- 16 agent files exist (8 domain orchestrators + 8 agent classes) ✅
- Module Folder Audit: trigger → 202 → complete with findings ✅
- Assessment, Moderation, Attendance, Evidence, Outcome, Accreditation, Programme Review agents: code complete but not individually triggered in this audit

**Classification: PLAUSIBLY TRUE** — 7 of 8 agents unverified but structurally identical to the verified one.

---

## CHANGELOG 4.1.0 — "Conversation search, pinning, session history"

**Claim:** Search input filters conversation history; pin/unpin with localStorage persistence

**Evidence:**
- Code present in `AiWorkspaceView.tsx` (~950 lines)
- Not directly tested via browser in this audit
- localStorage key documented: `aqaa:pinned-sessions`

**Classification: UNVERIFIED** — code exists; behaviour not confirmed live.

---

## CHANGELOG 4.1.0 — "Export response as .md download"

**Claim:** Per-message Markdown export with citations block

**Evidence:** Code present in AiWorkspaceView; not tested.

**Classification: UNVERIFIED**

---

## CHANGELOG 4.1.0 — "Stop generation (AbortController)"

**Claim:** Abort controller cancels in-flight SSE stream

**Evidence:** Code pattern expected to be present; not tested live.

**Classification: UNVERIFIED**

---

## PHASE_TRACKER — "Phase 3 Split 2 Wave 2: Public Knowledge Acquisition"

**Claim:** robots.txt compliance, rate limiting + retry

**Evidence:**
- `acquisition.py` route present ✅
- SourceRegistrar, CrawlScheduler classes exist ✅
- robots.txt / rate limiting: present in code documentation; not verified at runtime

**Classification: PLAUSIBLY TRUE** — code architecture supports the claim; runtime behaviour not confirmed.

---

## PHASE_TRACKER — "Phase 1: File upload pipeline"

**Claim:** Complete file upload with state machine (pending → scanning → ready)

**Evidence:**
- Upload endpoint exists (`POST /api/v1/files/upload`) ✅
- State machine code present ✅
- `scan_service.py` exists ✅
- No files uploaded in audit; scan behaviour not tested

**Classification: PLAUSIBLY TRUE** — upload likely works; AV scanning unconfirmed.

---

## CHANGELOG 4.0.0 — "Mobile responsive layout verified"

**Claim:** Mobile responsive — sidebar overlay, hamburger, nav closes on tap

**Evidence:**
- Code structure supports this (AppShell, Sidebar with overlay CSS)
- Not tested at mobile viewport in this audit

**Classification: PLAUSIBLY TRUE** — code is present; mobile viewport not exercised.

---

## Summary Table

| Claim | Classification |
|-------|---------------|
| Advanced RAG (Phase 3 S3) | **CONTRADICTED** |
| 92% grounding score (genuine) | **MISLEADING** |
| All 7 roles live-tested | PLAUSIBLY TRUE |
| All 8 AI agents functional | PLAUSIBLY TRUE |
| Conversation search/pin/session | UNVERIFIED |
| .md export | UNVERIFIED |
| Stop generation | UNVERIFIED |
| robots.txt compliance | PLAUSIBLY TRUE |
| File AV scanning | PLAUSIBLY TRUE |
| Mobile responsiveness | PLAUSIBLY TRUE |
