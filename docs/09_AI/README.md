# AI Documentation

This section documents AQAA's AI agent architecture, IKP integration, and reasoning systems.

## AI Agent Portfolio

| Agent | File | Scope | Status |
|-------|------|-------|--------|
| Module Folder Audit | `backend/app/agents/module_folder_audit.py` | Module | ✅ Implemented |
| Assessment Compliance | `backend/app/agents/assessment_compliance.py` | Module | ✅ Implemented |
| Moderation Compliance | `backend/app/agents/moderation_compliance.py` | Module | ✅ Implemented |
| Attendance Compliance | `backend/app/agents/attendance_compliance.py` | Module | ✅ Implemented |
| Evidence Verification | `backend/app/agents/evidence_verification.py` | Module | ✅ Implemented |
| Outcome Alignment | `backend/app/agents/outcome_alignment.py` | Module | ✅ Implemented |
| Accreditation Readiness | `backend/app/agents/accreditation_readiness.py` | Module | ✅ Implemented |
| Programme Review | `backend/app/agents/programme_review_agent.py` | Programme | ✅ Implemented |

## AI Architecture Principles

1. **AI assists, humans decide** — findings are recommendations, not verdicts
2. **Asynchronous execution** — all agents run in background tasks (HTTP 202 pattern)
3. **IKP-aware (planned)** — agents will load institution-specific rules from IKP in Phase 7
4. **Confidence scoring** — every finding carries a confidence score
5. **Provenance citation** — findings cite the IKP rule that triggered them (planned Phase 7)

## Critical Rule

**Do not modify any file in `backend/app/agents/` without explicit authorisation.**  
Agent logic is the core IP of the AQAA platform.

## Contents

| Document | Status |
|----------|--------|
| `AGENT_ARCHITECTURE.md` | ⏳ Planned |
| `AI_RULES_FORMAT.md` | ⏳ Planned |
| `CONFIDENCE_SCORING.md` | ⏳ Planned |
| `IKP_AI_INTEGRATION.md` | ⏳ Planned (Phase 7) |
| `PROMPT_TEMPLATES.md` | ⏳ Planned (Phase 7) |
