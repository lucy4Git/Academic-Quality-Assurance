# AQAA Phase E — Regulatory Knowledge Plan

**Date:** 2026-07-17
**Prepared by:** AQAA Engineering — Principal Systems Architect
**Status:** APPROVED_WITH_CONDITIONS

---

## 1. Current State

At Phase D, Qdrant contains:
- `tut_2026_v1_1_0`: 196 points — TUT institutional knowledge (processed IKP documents)
- `up_2026_v1_0_0`: 28 points — UP institutional knowledge (processed IKP documents)
- `source_status` field exists on all regulatory records in PostgreSQL
- `SourceStatus` enum: `OFFICIAL_VERIFIED`, `OFFICIAL_UNVERIFIED`, `INSTITUTIONAL_APPROVED`, `TEST_FIXTURE`, `DRAFT_IMPORT`, `SUPERSEDED`, `ARCHIVED`
- All current Qdrant content is classified as `TEST_FIXTURE` — no `OFFICIAL_VERIFIED` documents are indexed

**Impact:** The anti-hallucination guard exists and the citation architecture is complete. However, all citations currently draw from test content. Pilot deployment requires at least CHE, DHET, and SAQA frameworks to be indexed as `OFFICIAL_VERIFIED`.

---

## 2. Target State

By end of Sprint E3 (pre-pilot), the following must be achieved:

| Framework | Issuing Body | Status Target | Point Count Estimate |
|-----------|-------------|--------------|---------------------|
| HEQSF (NQF Level 5–10) | CHE | OFFICIAL_VERIFIED | ~100 |
| Policy on Minimum Requirements for Teacher Education Qualifications | DHET | OFFICIAL_VERIFIED | ~80 |
| NQF Level Descriptors | SAQA | OFFICIAL_VERIFIED | ~40 |
| CHE Good Practice Guide for Self-Evaluation | CHE | OFFICIAL_VERIFIED | ~120 |
| Institutional Policy Documents (per pilot institution) | Institution | INSTITUTIONAL_APPROVED | Variable |

---

## 3. Document Sourcing Plan

### 3.1 CHE — Council on Higher Education

**Documents to source:**
1. HEQSF (Higher Education Qualifications Sub-Framework) — latest edition
2. CHE Good Practice Guide for South African Higher Education Institutions
3. CHE Accreditation Criteria for Programmes Leading to Professional Qualifications
4. CHE Annual National Report on the State of Higher Education (most recent)

**Source:** [www.che.ac.za](https://www.che.ac.za) — all publications are freely downloadable as PDF

**Process:**
- Download from official CHE website
- Record: document title, version, download URL, download date
- Verify document hash after download
- Obtain written permission if terms of use require (check CHE copyright notice)
- Index with `source_status = OFFICIAL_VERIFIED`, `issuing_body = "CHE"`

### 3.2 DHET — Department of Higher Education and Training

**Documents to source:**
1. Policy on the Minimum Requirements for Teacher Education Qualifications (2015 or later revision)
2. National Plan for Post-School Education and Training
3. Policy Framework for the Provision of Distance Education in South African Universities

**Source:** Government Gazette (www.gov.za), DHET website

**Process:** Same as CHE. Government Gazette publications are public domain.

### 3.3 SAQA — South African Qualifications Authority

**Documents to source:**
1. NQF Level Descriptors for the South African NQF
2. SAQA Regulations for the Registration of Qualifications and Part Qualifications on the NQF
3. SAQA Policy and Criteria for the Evaluation of Foreign Qualifications (for reference)

**Source:** [www.saqa.org.za](https://www.saqa.org.za)

### 3.4 QCTO — Quality Council for Trades and Occupations (Priority: P1, deferred if no pilot institution requires)

**Documents to source if applicable:**
1. QCTO Qualification Design Requirements
2. QCTO Assessment Quality Partners (AQP) accreditation criteria

**Defer until:** A pilot institution with occupational programmes is confirmed.

### 3.5 ECSA, HPCSA, SACE (Priority: P2, Phase F)

These professional council frameworks are specialist and require per-programme applicability rules. Deferred to Phase F unless a pilot institution specifically requires one.

---

## 4. Ingestion Pipeline

### 4.1 Document Processing Workflow

```
1. Operator downloads PDF from official source
2. Operator records metadata in RegulatoryDocumentRegistry (via admin panel)
   {title, issuing_body, version, effective_date, source_url}
   status = DRAFT_IMPORT
3. Operator uploads PDF via POST /api/v1/regulatory-docs/{id}/ingest
4. Background job: IKP processing pipeline
   a. Extract text (PyMuPDF / pdfminer)
   b. Clean and chunk (512-token chunks, 64-token overlap)
   c. Embed (all-MiniLM-L6-v2, 384 dimensions)
   d. Upsert to Qdrant with payload:
      {
        institution_id: null,        # null = national document
        source_status: "OFFICIAL_VERIFIED",
        issuing_body: "CHE",
        document_version: "2023",
        effective_date: "2023-01-01",
        regulatory_doc_id: "<uuid>",
        chunk_index: N,
        section_title: "...",
        text: "..."
      }
5. Update RegulatoryDocumentRegistry:
   status = OFFICIAL_VERIFIED
   qdrant_collection = "national_frameworks_2026"
   point_count = N
   ingested_at = now()
6. Operator verifies: run test query, confirm citation appears in AI workspace
```

### 4.2 National Collection Strategy

All national regulatory documents (CHE, DHET, SAQA) are indexed into a single shared Qdrant collection `national_frameworks_2026`. This collection is:
- Available to all institutions (no `institution_id` filter — filtered out)
- Read-only via the application API
- Updated only by AQAA Engineering operators
- Versioned: when a new edition of a document is released, a new collection `national_frameworks_{year}` is created and the old one is archived

### 4.3 Institutional Collection Strategy

Each institution has its own Qdrant collection `{institution_id}_docs` for:
- Institutional policies uploaded by the institution's System Admin
- Faculty-specific guidelines
- Internal QA procedures

These documents are indexed with `source_status = INSTITUTIONAL_APPROVED` and are only returned for queries from that institution.

---

## 5. Document Versioning and Supersession

### 5.1 Version Lifecycle

```
DRAFT_IMPORT → OFFICIAL_VERIFIED → SUPERSEDED → ARCHIVED
                                         ↑
                     When a new version of the same document is ingested,
                     the old version's source_status is updated to SUPERSEDED
                     and superseded_by = new_document_id
```

### 5.2 Citation Handling for Superseded Documents

When a QA Officer cites a regulatory clause:
- If source status is `SUPERSEDED`, the AI response includes: "Note: This document has been superseded by [new version]. Verify the current requirements."
- The system does not block citation of superseded documents — historical audit records must remain legible.
- Superseded documents are excluded from new query results by default but can be included via an explicit operator flag.

### 5.3 Annual Review Schedule

| Framework | Review Month | Action |
|-----------|-------------|--------|
| CHE HEQSF | January | Check for updated edition; re-ingest if changed |
| DHET Policy on Teacher Education | March | Check for new Government Gazette notice |
| SAQA NQF Descriptors | June | Verify current edition; re-index if revised |
| All OFFICIAL_VERIFIED docs | Annually (July) | Full source URL check; mark SUPERSEDED if URL 404s |

---

## 6. Per-Institution Policy Indexing

### 6.1 Workflow

Institutions can upload their own policy documents through the admin panel. The workflow:

1. Institution System Admin navigates to `/admin/regulatory-docs`
2. Uploads PDF or DOCX policy document
3. Fills in: title, effective date, policy category (QUALITY_ASSURANCE, ASSESSMENT, ATTENDANCE, etc.)
4. Submits — triggers indexing background job
5. Document indexed with `source_status = INSTITUTIONAL_APPROVED`, `institution_id = <this institution>`
6. Document appears in AI Workspace citations for this institution's users only

### 6.2 Content Controls

Institutional documents are scanned (ClamAV) before indexing. Content is not reviewed by AQAA Engineering for accuracy — the institution is responsible for the correctness of their uploaded policies.

---

## 7. Regulatory Collection Registry — Initial Data

Before pilot go-live, the following entries must exist in `regulatory_document_registry`:

| Entry | Issuing Body | Status | Qdrant Collection |
|-------|-------------|--------|------------------|
| HEQSF (NQF Levels 5–10) | CHE | OFFICIAL_VERIFIED | national_frameworks_2026 |
| CHE Good Practice Guide | CHE | OFFICIAL_VERIFIED | national_frameworks_2026 |
| Policy on Min Requirements for Teacher Ed | DHET | OFFICIAL_VERIFIED | national_frameworks_2026 |
| NQF Level Descriptors | SAQA | OFFICIAL_VERIFIED | national_frameworks_2026 |
| TUT IKP 2026 v1.1.0 | TUT (internal) | INSTITUTIONAL_APPROVED | tut_2026_v1_1_0 |
| UP IKP 2026 v1.0.0 | UP (internal) | INSTITUTIONAL_APPROVED | up_2026_v1_0_0 |

---

## 8. Grounding Coverage Monitoring

Once pilot begins, weekly reporting on:

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| % responses with ≥1 OFFICIAL_VERIFIED citation | ≥ 85% | < 75% |
| % responses with zero sources cited | ≤ 5% | > 10% |
| % responses citing SUPERSEDED documents | ≤ 2% | > 5% |
| Confirmed hallucination rate | < 1 per 1,000 | > 3 per 1,000 |

---

## Referenced Documents

- [AQAA_PHASE_E_DATA_REQUIREMENTS.md](AQAA_PHASE_E_DATA_REQUIREMENTS.md) — RegulatoryDocumentRegistry schema
- [AQAA_PHASE_E_SECURITY_AND_GOVERNANCE_PLAN.md](AQAA_PHASE_E_SECURITY_AND_GOVERNANCE_PLAN.md) — AI governance and third-party data sharing
- [AQAA_PHASE_E_EVALUATION_PLAN.md](AQAA_PHASE_E_EVALUATION_PLAN.md) — Grounding coverage metrics
