# AQAA Accreditation Current State

**Document:** AQAA_ACCREDITATION_CURRENT_STATE  
**Sprint:** Recovery Sprint — Stage B (Updated)  
**Date:** 2026-07-13  
**Status:** Backend WORKING; Frontend PLACEHOLDER → being replaced

---

## Pre-Sprint Classification

| Component | Classification | Notes |
|-----------|---------------|-------|
| `backend/app/models/accreditation.py` (AccreditationBody, Accreditation) | WORKING | Full ORM models with FK to institution, programme, accreditation body |
| `backend/app/agents/accreditation_readiness.py` | WORKING | Meta-agent aggregating 6 compliance sub-agents; produces score + risk level + gaps + recommendations |
| `backend/app/agents/accreditation_agent.py` | PLACEHOLDER | Empty file (1 blank line), unused — dead stub |
| `backend/app/schemas/accreditation_readiness.py` | WORKING | Full Pydantic schemas: ReadinessFindingRead, SubAgentReadinessRead, FindingsSummaryRead, AccreditationReadinessReport, AccreditationReadinessRunBrief/Read, AccreditationReadinessTriggerResponse |
| `backend/app/routes/accreditation_readiness_audits.py` | WORKING | 6 endpoints: trigger, latest, history, get run, get report, resolve finding |
| `backend/app/services/accreditation_readiness_service.py` | WORKING | Full service layer |
| `backend/app/services/accreditation_readiness_report_service.py` | WORKING | Report builder |
| `frontend/src/app/(main)/accreditation/page.tsx` | PLACEHOLDER | `<PlaceholderPage title="Accreditation Readiness" />` |
| `frontend/src/lib/api/` (accreditation readiness) | MISSING | No API client for readiness audit endpoints |
| `frontend/src/types/` (readiness schemas) | MISSING | No TypeScript types for readiness report, sub-agent breakdown, etc. |
| `frontend/src/lib/constants.ts` | WORKING | AGENT_ROUTE_PREFIX maps accreditation_readiness correctly |
| `frontend/src/lib/rbac.ts` | WORKING | `/accreditation` route gated to DEAN_AND_ABOVE |
| Seed data (accreditation_bodies.json, accreditations.json) | WORKING | Present in database/seed_data/ |

---

## Accreditation Agent Design

The `AccreditationReadinessAgent` is a **meta-agent** — it does not run document analysis directly. Instead it:

1. Reads the latest completed run from each of 6 sub-agents for a given module
2. Scores each sub-agent against a 70.0 threshold
3. Computes `presence_score` (weighted checklist: 6 sub-agents × weights summing to 100)
4. Computes `quality_score` (evidence-pack completeness + unresolved-findings penalty)
5. Combined `overall_score = presence × 0.60 + quality × 0.40`
6. Derives `risk_level`: LOW / MEDIUM / HIGH / CRITICAL
7. Collates gaps and deduplicated recommendations from failing sub-agents

Sub-agent weights:

| Sub-Agent | Weight | Threshold |
|-----------|--------|-----------|
| MODULE_FOLDER_AUDIT | 15 | 70.0 |
| ASSESSMENT_COMPLIANCE | 20 | 70.0 |
| MODERATION_COMPLIANCE | 20 | 70.0 |
| ATTENDANCE_COMPLIANCE | 15 | 70.0 |
| EVIDENCE_VERIFICATION | 15 | 70.0 |
| OUTCOME_ALIGNMENT | 15 | 70.0 |

Evidence pack threshold: 90.0 (quality score penalty if below this).

---

## Gap: Frontend Accreditation Workspace

The entire backend pipeline exists and is API-ready. What was missing:
- TypeScript types for AccreditationReadinessReport, SubAgentReadinessRead, etc.
- API client module for the 6 readiness audit endpoints
- TanStack Query hooks
- A real accreditation workspace page (module selector → trigger run → view report)

These are implemented in Stage B7 (see commit following this document).
