# ADIP — Document Validation Engine (Layer 5)

**Document ID:** ADIP-L5-001  
**Version:** 1.0.0  
**Status:** Architecture Design  
**Last Updated:** 2026-06-29

---

## 1. Purpose

The Validation Engine is ADIP's quality gate. Before any extracted content influences the IKP or AI knowledge base, it must pass structural validation, source credibility checks, duplicate detection, confidence scoring, and — where confidence is insufficient — human review.

**Principle:** ADIP never loads unverified data as official truth. The Validation Engine enforces this.

---

## 2. Validation Pipeline

Every `ExtractionResult` passes through six sequential validation stages:

```
ExtractionResult
    │
    ▼ Stage 1: Structural Validation
    │   (schema check, required fields, data types)
    │
    ▼ Stage 2: Source Credibility
    │   (official domain? verified cert? known institution source?)
    │
    ▼ Stage 3: Duplicate Detection
    │   (content hash, semantic similarity, field-level dedup)
    │
    ▼ Stage 4: Confidence Scoring
    │   (per-field confidence from document + extraction quality)
    │
    ▼ Stage 5: Gate Decision
    │   HIGH (≥ 0.90)  → auto-proceed to Knowledge Mapping
    │   MEDIUM (0.70–0.89) → Human Review Queue
    │   LOW (< 0.70)   → Quarantine
    │
    ▼ Stage 6: Validation Record
        (persist full validation audit trail)
```

---

## 3. Stage 1 — Structural Validation

Validates that extracted chunks and tables conform to expected ADIP schema:

**Chunk validation rules:**
- `text` must not be empty
- `page_number` must be integer ≥ 1 if document has pages
- `chunk_type` must be a valid enum value
- `sequence_index` must be unique within document

**Table validation rules:**
- Header row must have ≥ 2 columns
- Data rows must have same column count as header
- No entirely empty rows (strip, then check)

**Field extraction validation (for structured fields):**
| Expected Field | Validation Rule |
|---------------|----------------|
| `nqf_level` | Must be integer 1–10 |
| `credits` | Must be integer 10–600 |
| `aps_minimum` | Must be integer 18–50 |
| `programme_code` | Must match regex `[A-Z]{2,4}-?[A-Z0-9]{2,6}` |
| `module_code` | Must match regex `[A-Z]{2,4}[0-9]{3}` |
| `academic_year` | Must match `YYYY/YYYY` or `YYYY` |
| `email` | Must match email regex |
| `phone` | Must match SA phone regex |

**On failure:** Chunk is flagged `INVALID_STRUCTURE` and excluded from Knowledge Mapping. Logged to validation record.

---

## 4. Stage 2 — Source Credibility Assessment

**For URL-sourced documents:**

| Check | Pass Condition | Confidence Adjustment |
|-------|---------------|----------------------|
| HTTPS with valid certificate | Certificate valid, not expired | +0.05 |
| Domain matches institution's official domain | `tut.ac.za` for TUT records | +0.10 |
| Domain is registered official source in IKP | IKP contains `official_domains: ["tut.ac.za"]` | +0.05 |
| HTTP 200 response (not redirect-then-200) | Direct response | No adjustment |
| Last-modified header > 1 year old | Content may be stale | -0.05 |
| Domain is secondary/aggregator site | `briefly.co.za`, `studychoices.org.za` | -0.50 |

**For uploaded documents:**

| Check | Pass Condition | Confidence Adjustment |
|-------|---------------|----------------------|
| Uploaded by institution admin user | `user.role ≥ QUALITY_ASSURANCE_OFFICER` | +0.10 |
| Uploaded by lecturer (within institution) | `user.role == LECTURER` | No adjustment |
| File metadata author matches institution | PDF author field contains institution name | +0.05 |
| Institution logo/watermark detected | Visual classification of header | +0.03 |

---

## 5. Stage 3 — Duplicate Detection

### 5.1 Exact Duplicate (Hash Match)
If a new document has the same `content_hash_sha256` as an existing document for the same `institution_id`:
- **Same academic year** → Reject as duplicate, return existing `document_id`
- **Different academic year** → Register as new version

### 5.2 Field-Level Duplicate Detection
When a field is extracted (e.g., "NQF Level = 6 for Diploma in Computer Science"), check:
- Does the IKP already contain this field for this entity?
- If yes and values match → reinforce confidence (multiple sources agree)
- If yes and values conflict → flag as `CONFLICTING_DATA`, route to human review

### 5.3 Semantic Duplicate Detection (Future)
Planned for Phase 7: use vector similarity to detect semantically identical content in different documents (e.g., the same policy text appearing in two different PDFs).

---

## 6. Stage 4 — Confidence Scoring

Confidence is calculated per extracted field, not per document:

```
field_confidence = base_document_confidence
                 × extraction_quality_factor
                 × source_credibility_factor
                 × position_clarity_factor
                 × cross_reference_bonus

base_document_confidence:
  official_html                    → 1.00
  official_pdf (native text)       → 0.92
  official_pdf (OCR)               → 0.78
  uploaded by institution admin    → 0.88
  uploaded by lecturer             → 0.82
  secondary website                → 0.45

extraction_quality_factor:
  exact string match (verbatim)    → 1.00
  regex from clean text            → 0.95
  table cell (identified header)   → 0.90
  table cell (inferred header)     → 0.78
  OCR high quality (>90% conf)     → 0.82
  OCR medium quality (70–90%)      → 0.70
  OCR low quality (<70%)           → 0.55
  AI inference                     → 0.55

position_clarity_factor:
  explicit label ("NQF Level: 6")  → 1.00
  column header ("NQF Level")      → 0.92
  contextual ("offered at NQF 6")  → 0.80
  implicit                         → 0.65

cross_reference_bonus:
  Confirmed by ≥ 2 official sources → +0.05 (capped at 1.00)
  Confirmed by HEQSF national std  → +0.03
  Conflicts with other source       → -0.15
```

**Example calculation for TUT ICT NQF level from official HTML:**
```
base = 1.00 (official_html)
× extraction_quality = 0.98 (verbatim: "NQF level 6")
× position_clarity = 1.00 (explicit label)
× cross_reference = +0.00 (no second source yet)
= 0.98 field confidence → AUTO-LOAD
```

**Example calculation for APS from secondary website (studychoices.org.za):**
```
base = 0.45 (secondary website)
× extraction_quality = 0.95 (clean table extraction)
× position_clarity = 0.92 (column header "APS (Math)")
= 0.39 → QUARANTINE (below 0.70)
```

---

## 7. Stage 5 — Gate Decision and Routing

| Confidence Band | Classification | Action |
|----------------|---------------|--------|
| ≥ 0.90 | `HIGH_CONFIDENCE` | Auto-proceed to Knowledge Mapping |
| 0.80–0.89 | `MEDIUM_HIGH` | Proceed with `verified = false`; review within 30 days |
| 0.70–0.79 | `MEDIUM` | Add to Human Review Queue; hold from IKP until approved |
| 0.50–0.69 | `LOW` | Quarantine; do not load; add to investigation log |
| < 0.50 | `VERY_LOW` | Reject and discard (do not log in IKP candidates) |

---

## 8. Stage 6 — Validation Record

A `ValidationRecord` is persisted for every document processed:

```json
{
  "id": "UUID",
  "document_id": "UUID",
  "institution_id": "UUID",
  "validated_at": "2026-06-29T10:05:00Z",
  "structural_valid": true,
  "source_credibility_score": 0.97,
  "duplicate_detected": false,
  "fields_extracted": 47,
  "fields_high_confidence": 41,
  "fields_medium_confidence": 5,
  "fields_quarantined": 1,
  "human_review_items": 5,
  "validation_warnings": [
    "Page 35: table header ambiguous — 'APS' may be Math or Math Lit not distinguished"
  ],
  "overall_document_confidence": 0.94
}
```

---

## 9. Human Review Queue

Items in the Human Review Queue are presented to an ADIP Admin user (planned Phase 6 UI):

| Field | Extracted Value | Confidence | Source | Proposed Action |
|-------|----------------|-----------|--------|----------------|
| `programme.nqf_level` | 7 | 0.75 | Table (stream mode, low accuracy) | Verify against official PDF page 15 |
| `admission_req.aps_minimum_math` | 26 | 0.79 | OCR from scanned table | Confirm against Part6_ICT Prospectus |

Review options:
- **Confirm** → confidence upgraded to 0.92 (human verified); field loads to IKP
- **Correct + Confirm** → reviewer provides correct value; loads with confidence 0.92
- **Reject** → field quarantined; logged as unresolvable from this source
