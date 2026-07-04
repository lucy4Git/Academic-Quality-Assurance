# ADIP — Provenance Engine (Layer 7)

**Document ID:** ADIP-L7-001  
**Version:** 1.0.0  
**Status:** Architecture Design  
**Last Updated:** 2026-06-29

---

## 1. Purpose

The Provenance Engine generates fine-grained, field-level provenance records that trace every piece of knowledge in AQAA back to its exact source location. This implements the ADR-0006 mandate: every knowledge object must be traceable.

ADIP's provenance goes further than the basic IKP provenance envelope — it records the **exact location within the document** (page number, paragraph number, table row, cell range, slide number, timestamp) so that a human or AI can navigate directly to the source.

---

## 2. ProvenanceAnchor Model

A `ProvenanceAnchor` is created for every `KnowledgeMappingCandidate`:

```json
{
  "id": "UUID",
  "ikp_entity_type": "programme",
  "ikp_entity_key": "Diploma in Computer Science",
  "ikp_field_name": "nqf_level",
  "document_id": "UUID",
  "institution_id": "UUID",

  "source": {
    "type": "official_pdf",
    "url": "https://www.tut.ac.za/media/.../Part6_ICT_Prospectus.pdf",
    "document_title": "2026 Prospectus Part 6 Faculty of ICT",
    "publisher": "Tshwane University of Technology",
    "publisher_verified": true,
    "published_date": "2025-08-15",
    "retrieved_date": "2026-06-29"
  },

  "location": {
    "page_number": 12,
    "paragraph_index": 3,
    "slide_number": null,
    "sheet_name": null,
    "cell_range": null,
    "table_index": null,
    "table_row": null,
    "timestamp_seconds": null,
    "section_path": ["Programmes Offered", "Computer Science"]
  },

  "extraction": {
    "method": "pdf_native_text + regex_pattern",
    "verbatim_quote": "Diploma in Computer Science (NQF level 6)",
    "quote_char_offset_start": 4520,
    "quote_char_offset_end": 4562,
    "ocr_confidence": null,
    "extractor_version": "pdfminer.six 20221105"
  },

  "confidence": {
    "score": 0.96,
    "breakdown": {
      "document_source": 0.92,
      "extraction_quality": 1.00,
      "position_clarity": 1.00,
      "cross_reference_bonus": 0.04
    }
  },

  "verification": {
    "verified": false,
    "verified_by": null,
    "verified_at": null,
    "verification_method": null
  },

  "validity": {
    "effective_date": "2026-01-01",
    "expiry_date": null,
    "academic_year": "2026",
    "supersedes": null,
    "status": "active"
  },

  "created_at": "2026-06-29T10:07:00Z"
}
```

---

## 3. Location Coordinates by Document Type

ADIP records the most precise location possible for each format:

| Format | Location Fields Used |
|--------|---------------------|
| PDF (text) | `page_number`, `paragraph_index`, `char_offset_start/end`, `section_path` |
| PDF (table) | `page_number`, `table_index`, `table_row`, `column_name` |
| PDF (OCR) | `page_number`, `bounding_box` (x, y, w, h in points) |
| DOCX | `paragraph_index`, `style_name`, `section_path` |
| PPTX | `slide_number`, `shape_name`, `section_path` |
| XLSX | `sheet_name`, `cell_range` (e.g., "B12") |
| HTML | `section_path`, `xpath`, `css_selector` |
| Video/Audio | `timestamp_seconds`, `transcript_segment_index` |

---

## 4. Cross-Source Provenance Reinforcement

When the same fact is confirmed by multiple independent sources:

```json
{
  "ikp_field_name": "nqf_level",
  "ikp_entity_key": "Diploma in Computer Science",
  "confirmed_value": 6,
  "provenance_anchors": [
    {
      "anchor_id": "UUID-1",
      "source_url": "https://www.tut.ac.za/ict/computer-science/",
      "confidence": 0.98,
      "verbatim": "Diploma in Computer Science (NQF level 6)"
    },
    {
      "anchor_id": "UUID-2",
      "source_url": "Part6_ICT_Prospectus.pdf",
      "confidence": 0.96,
      "verbatim": "NQF Level 6"
    }
  ],
  "combined_confidence": 0.99,
  "note": "Two independent official sources confirm NQF Level 6"
}
```

Multi-source confirmation raises the combined confidence using:
```
combined = 1 - ((1 - conf_1) × (1 - conf_2))
```

---

## 5. Contradiction Detection

When two ProvenanceAnchors propose different values for the same field:

```json
{
  "contradiction_id": "UUID",
  "ikp_field": "admission_req.aps_minimum_math",
  "entity": "Diploma in Computer Science",
  "anchor_1": { "value": 26, "source": "Part6_ICT_Prospectus.pdf p.15", "confidence": 0.92 },
  "anchor_2": { "value": 24, "source": "studychoices.org.za", "confidence": 0.45 },
  "resolution": "anchor_1 selected (higher confidence + official source)",
  "resolution_method": "automatic_confidence_priority",
  "requires_human_review": false,
  "created_at": "2026-06-29T10:07:30Z"
}
```

When confidence scores are within 0.10 of each other, the contradiction always routes to human review.

---

## 6. Provenance Expiry and Refresh

Every provenance anchor has an `effective_date` and optional `expiry_date`.

**Automatic expiry triggers:**
- `academic_year` in the anchor is older than the current year + 1 → flag as `stale`
- Institution releases a new prospectus → prior year anchors become `superseded`
- Source URL returns 404 → anchor flagged as `source_unavailable`

**Refresh behaviour:**
- When a new document is ingested for a field that has a stale anchor, ADIP creates a new anchor
- Old anchor is set to `status: superseded`
- Both anchors are preserved for historical queries

---

## 7. Provenance API (Planned)

Future API endpoints for provenance transparency:

```
GET /api/v1/adip/provenance?entity_type=programme&entity_key=Diploma+in+Computer+Science&field=nqf_level
→ Returns all ProvenanceAnchors for this field, ordered by confidence

GET /api/v1/adip/provenance/{anchor_id}
→ Returns single ProvenanceAnchor with full detail

GET /api/v1/adip/provenance/document/{document_id}
→ Returns all anchors derived from a specific document

GET /api/v1/adip/provenance/contradictions?institution_id={id}
→ Returns all unresolved contradictions for an institution
```
