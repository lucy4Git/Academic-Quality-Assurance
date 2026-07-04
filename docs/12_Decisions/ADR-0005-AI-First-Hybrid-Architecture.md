# ADR-0005 — AI-First Hybrid Architecture

**Status:** Accepted  
**Date:** 2026-06-11  
**Deciders:** Architecture design session  
**Supersedes:** None  
**Superseded by:** —

---

## Context

Academic quality assurance in South African higher education is a human-led, evidence-based process governed by CHE, DHET, and SAQA. QA Officers, Faculty Deans, and Programme Coordinators are responsible for compliance decisions. These are professional judgements that carry institutional and regulatory consequences.

At the same time, the manual process of auditing module folders — checking that 10+ required document types are present, correctly classified, dated, and signed — is time-consuming and error-prone at scale. An institution with 300+ modules cannot manually audit all of them in a reasonable time.

The question is: how much of the QA process can be automated, and where must human judgement be preserved?

---

## Decision

AQAA uses an **AI-First Hybrid Architecture**:
- AI agents automate the pattern detection, evidence classification, and gap identification tasks
- Human academic professionals retain authority over all compliance decisions, findings approvals, and regulatory submissions

**Architecture rules:**
1. AI agents return **findings** and **recommendations** — never final compliance verdicts
2. All AI audit runs are asynchronous (HTTP 202 + poll pattern)
3. Human workflow states (Draft → Pending QA Review → Approved/Rejected) sit above AI outputs
4. AI confidence scores are surfaced in all findings — users can see how confident the AI is
5. IKP rules (institution-specific compliance logic) are loaded into agents at runtime — agents are configurable, not hardcoded

**Current AI agent portfolio (8 agents):**
- Module Folder Audit, Assessment Compliance, Moderation Compliance, Attendance Compliance, Evidence Verification, Outcome Alignment, Accreditation Readiness, Programme Review

---

## Consequences

### Positive
- Institutions trust the platform because humans retain authority
- Regulatory bodies (CHE) accept AI-assisted processes when humans make final decisions
- AI handles the repetitive, pattern-based work (is this document present? is it dated?)
- Human QA Officers focus on interpretation, judgement, and institutional knowledge
- The platform scales to 300+ modules without requiring proportional QA staff growth
- Confidence scores make AI limitations visible to users

### Negative
- Not a fully automated QA platform — human time is still required for review
- AI agents require good evidence data — garbage in, garbage out
- AI findings require human review workflow, adding steps before final report generation
- Maintaining 8 agent codebases requires ongoing engineering effort

### Neutral
- Future phases will add IKP-aware agent behaviour (agents load institution-specific rules)
- Natural language QA queries are planned (Phase 7) but not implemented
- Agent quality improves as more institutions are onboarded and IKP rules are refined

---

## Alternatives Considered

### Alternative 1 — Full AI Automation
AI makes compliance decisions without human review.

**Rejected because:** Regulatory submissions in South African higher education require human accountability. A QA Officer must be able to testify to the accuracy of compliance reports. Full AI automation would remove the human accountability chain required by CHE and SAQA.

### Alternative 2 — Manual QA Only (No AI)
AQAA provides digital tools for manual QA processes without AI automation.

**Rejected because:** Manual-only auditing does not scale. An institution with 300 modules cannot manually complete 10-item checklists for every module in time for accreditation cycles. Some automation of evidence gap detection is necessary for the platform to be commercially viable.

### Alternative 3 — Rules-Engine Only (No ML)
Replace AI agents with deterministic rule engines.

**Partially implemented:** The manual QA engine (Phase 4A) is a rules-based system. The AI agents layer ML-based content classification and semantic matching on top of deterministic rules. The hybrid approach uses rules where precision is critical and ML where ambiguity exists (document classification, outcome alignment).

---

## Implementation Notes

Agent execution pattern:
```
POST /{prefix}/modules/{id}/trigger → HTTP 202 + {"run_id": "..."}
Background task: agent.run(run_id)
GET /api/v1/audits/{run_id} → poll until run_status ∈ {completed, failed}
GET /api/v1/audits/{id}/report → full findings when completed
```

Agent files: `backend/app/agents/` — **do not modify without explicit authorisation**.

---

## References

- `docs/00_Project/AQAA_MASTER_ARCHITECTURE.md` — Section 6: AI-First Hybrid Strategy
- `backend/app/agents/` — all 8 AI agent implementations
- `docs/09_AI/AGENT_ARCHITECTURE.md` (to be written)
