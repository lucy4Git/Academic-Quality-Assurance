# AQAA Regulatory Framework Engine — API Reference

**Phase C | Version 1.0 | 2026-07-14**

---

## Base URL

`http://localhost:8000/api/v1`

All endpoints require a valid `Bearer` JWT token. Obtain via `POST /auth/token` or `POST /auth/login`.

---

## Regulatory Authorities

### `GET /regulatory-authorities`

List regulatory authorities visible to the caller.

**Query params:** `institution_id` (UUID, optional), `include_global` (bool, default true), `active_only` (bool, default true), `limit`, `offset`

**Response:** `200 OK` — `list[RegulatoryAuthorityRead]`

```json
[
  {
    "id": "uuid",
    "code": "CHE-ZA",
    "name": "[TEST FIXTURE] Council on Higher Education",
    "short_name": "CHE",
    "authority_type": "quality_council",
    "jurisdiction": "National",
    "country": "ZA",
    "is_external": true,
    "is_internal": false,
    "is_active": true,
    "is_test_fixture": true,
    "status": "active",
    "institution_id": null,
    "created_at": "...",
    "updated_at": "..."
  }
]
```

**RBAC:** QA Officer and above.

---

### `GET /regulatory-authorities/{id}`

Get a single authority by ID.

**Response:** `200 OK` — `RegulatoryAuthorityRead`  
**Error:** `404 Not Found`

---

### `POST /regulatory-authorities`

Create a new regulatory authority.

**Body:** `RegulatoryAuthorityCreate`  
**Response:** `201 Created` — `RegulatoryAuthorityRead`  
**RBAC:** System Admin only.

---

### `PUT /regulatory-authorities/{id}`

Update an authority's metadata.

**Body:** `RegulatoryAuthorityUpdate` (all fields optional)  
**Response:** `200 OK` — `RegulatoryAuthorityRead`  
**RBAC:** System Admin only.

---

### `DELETE /regulatory-authorities/{id}`

Deactivate an authority (soft delete — sets `is_active = false`).

**Response:** `204 No Content`  
**RBAC:** System Admin only.

---

## Quality Frameworks

### `GET /quality-frameworks`

List frameworks with eagerly loaded versions.

**Query params:** `institution_id`, `include_global` (default true), `active_only` (default true), `limit`, `offset`

**Response:** `200 OK` — `list[QualityFrameworkWithVersions]`  
Each item includes a `versions[]` array of `FrameworkVersionBrief` and `is_test_fixture: bool`.

---

### `GET /quality-frameworks/{framework_id}`

Framework detail with versions.

**Response:** `200 OK` — `QualityFrameworkWithVersions`

---

### `POST /quality-frameworks`

Create a framework.

**Body:** `QualityFrameworkCreate`  
**Response:** `201 Created` — `QualityFrameworkRead`  
**RBAC:** System Admin only.

---

### `GET /quality-frameworks/{framework_id}/versions`

List all versions of a framework.

**Response:** `200 OK` — `list[FrameworkVersionRead]`

---

### `POST /quality-frameworks/{framework_id}/versions`

Create a new version (starts in `DRAFT` status).

**Body:** `FrameworkVersionCreate`  
**Response:** `201 Created` — `FrameworkVersionRead`  
**RBAC:** System Admin only.

---

### `GET /quality-frameworks/versions/{version_id}`

Version detail including standards and criteria.

**Response:** `200 OK` — `FrameworkVersionRead` (with `standards[].criteria[]`)

---

### `POST /quality-frameworks/versions/{version_id}/transition`

Advance a version through its lifecycle.

**Body:** `{ "new_status": "under_review" }`

**Allowed transitions:**
- `draft → under_review`
- `under_review → approved | draft`
- `approved → active | draft`
- `active → superseded | retired`
- `superseded → archived`
- `retired → archived`

Activating a version auto-SUPERSEDEs the current ACTIVE version of the same framework.

**Response:** `200 OK` — `FrameworkVersionRead`  
**RBAC:** System Admin only.

---

### `GET /quality-frameworks/versions/{version_id}/standards`

Standards for a version (active only, ordered by sequence).

**Response:** `200 OK` — `list[FrameworkStandardRead]` (each with `criteria[]`)

---

### `POST /quality-frameworks/versions/{version_id}/standards`

Create a standard within a version.

**Body:** `FrameworkStandardCreate`  
**Response:** `201 Created` — `FrameworkStandardRead`  
**RBAC:** System Admin only.

---

## Framework Assessments

### `POST /framework-assessments/modules/{module_id}/trigger`

Trigger a framework assessment for a module. Returns immediately with run ID.

**Body:**
```json
{
  "framework_version_id": "uuid",
  "assessment_scope": "full",
  "assessment_period": "2024"
}
```

**Response:** `202 Accepted` — `{ "run_id": "uuid", "status": "pending" }`

Poll `GET /framework-assessments/{run_id}` until `status` ∈ `{completed, failed}`.

---

### `GET /framework-assessments/{run_id}`

Assessment result detail.

**Response:** `200 OK` — `FrameworkAssessmentRunRead`

```json
{
  "id": "uuid",
  "status": "completed",
  "mandatory_compliance_score": 0.0,
  "evidence_coverage_score": 66.7,
  "quality_score": 80.0,
  "overall_score": 40.0,
  "risk_level": "critical",
  "readiness_status": "not_ready",
  "mandatory_failures": 1,
  "criterion_results": [...]
}
```

**Note:** `mandatory_compliance_score` is 0 if ANY mandatory criterion is unmet.

---

### `GET /framework-assessments`

List assessments for an institution.

**Query params:** `institution_id` (required), `framework_version_id`, `target_entity_id`, `limit`, `offset`

---

### `POST /framework-assessments/{run_id}/promote-gaps`

Promote unmet criteria from an assessment to the findings tracker.

Deduplicates on `(audit_run_id, framework_version_id, criterion_id)`.

**Response:** `200 OK` — `{ "promoted": N, "already_existed": M }`

---

### `GET /framework-assessments/{run_id}/evidence-mappings`

Evidence mappings for an assessment run.

---

### `POST /framework-assessments/{run_id}/evidence-mappings`

Create an evidence→criterion mapping.

**Body:** `EvidenceMappingCreate`  
**Response:** `201 Created` — `EvidenceMappingRead`

---

### `PUT /framework-assessments/evidence-mappings/{id}/verify`

Verify or reject an evidence mapping.

**Body:** `{ "approved": true, "validation_note": "..." }`  
Only VERIFIED mappings count toward `evidence_coverage_score`.

---

### `GET /framework-assessments/cross-framework-mappings`

List cross-framework mappings.

**Query params:** `source_version_id`, `target_version_id`, `mapping_type`, `human_verified_only`

---

### `POST /framework-assessments/cross-framework-mappings`

Create a cross-framework mapping. Always created with `human_verified = false`.

**Body:** `CrossFrameworkMappingCreate`

---

### `PUT /framework-assessments/cross-framework-mappings/{id}/verify`

Verify a cross-framework mapping (`human_verified = true`).

**Security:** EQUIVALENT mappings may only be used in deduplication after `human_verified = true`.  
**RBAC:** QA Officer and above.

---

## Error Responses

| Status | Meaning |
|--------|---------|
| 400 | Validation error (Pydantic) |
| 401 | Missing or invalid JWT |
| 403 | Insufficient role |
| 404 | Resource not found |
| 409 | Conflict (duplicate) |
| 422 | Unprocessable entity |

All errors follow `{ "detail": "message" }`.
