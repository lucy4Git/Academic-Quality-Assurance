# Institutional Knowledge Foundation — Architecture

**Subsystem:** Split 2 Wave 1
**Status:** Complete (2026-07-07)

## Purpose

Provide a provenance-aware institutional knowledge graph for all 26 South
African public universities, so that downstream QA agents and the RAG pipeline
have a realistic structure to operate on while clearly distinguishing verified
public data from synthetic demo data.

## Data model

Extends the existing five-level hierarchy
(`Institution → Faculty → Department → Programme → Module`) with:

| Model | Parent | Table |
|-------|--------|-------|
| `Campus` | Institution | `campuses` |
| `School` | Faculty (Department optionally links via `school_id`) | `schools` |
| `Qualification` | Programme | `qualifications` |
| `LearningOutcome` | Module | `learning_outcomes` |
| `GraduateAttribute` | Institution | `graduate_attributes` |
| `Policy` / `PolicyVersion` | Institution / Policy | `policies` / `policy_versions` |
| `InstitutionDocument` | Institution | `institution_documents` |
| `AccreditationBody` | — (global) | `accreditation_bodies` |
| `Accreditation` | Institution (+ Body, optional Programme) | `accreditations` |
| `Contact` | Institution | `contacts` |

`departments.school_id` is a nullable FK — schools are used by only some
universities (Wits, UKZN, NMU).

## Provenance model

Every provenance-bearing row has:

- `data_status` ∈ {`public_verified`, `needs_review`, `synthetic_demo`, `customer_data`}
- `is_synthetic` (bool) — always `true` for `synthetic_demo`
- `source_url` / `source_name`
- `data_confidence` (0–1, nullable)

Trust ranking (used by the seeder to avoid downgrades):
`synthetic_demo(0) < needs_review(1) < public_verified(2) < customer_data(3)`.

## API layer

`backend/app/routes/institution_knowledge.py` — read-only. Tenant isolation via
`assert_institution_access`; `/overview` is `AdminRequired`; students receive
only public profile data.

## Security boundaries

- No write endpoints in this wave.
- Students: public profile only (public contacts, no internal documents).
- `/overview` and cross-institution access: System Admin only.
- No authentication/RBAC/ProviderManager/RAG changes.
