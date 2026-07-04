# ADIP — Knowledge Mapping Engine (Layer 6)

**Document ID:** ADIP-L6-001  
**Version:** 1.0.0  
**Status:** Architecture Design  
**Last Updated:** 2026-06-29

---

## 1. Purpose

The Knowledge Mapping Engine translates extracted, validated document chunks into **structured IKP entity candidates**. It answers: "This text says 'Diploma in Computer Science (NQF level 6)' — which IKP entity does that belong to, and what fields does it populate?"

This is the bridge between unstructured extracted text and the typed, relational IKP knowledge graph.

---

## 2. IKP Entity Target Map

Every IKP layer is a potential mapping target:

| ADIP Extraction → | IKP Entity | IKP Layer | Key Fields |
|-------------------|-----------|-----------|-----------|
| Institution name, code, contact | `Institution` | Layer 1 | name, code, phone, email, website |
| Campus name, address | `Campus` | Layer 1 | name, address, province, gps |
| Faculty name, dean name, prospectus URL | `Faculty` | Layer 2 | name, code, campus, dean_name |
| Department name, HOD name, contact | `Department` | Layer 2 | name, code, hod_name, hod_email |
| Programme name, NQF, credits | `Programme` | Layer 2 + 5 | name, code, nqf_level, total_credits |
| APS, subject requirements | `AdmissionRequirement` | Layer 5 | aps_min_math, aps_min_math_lit, english_level |
| Module name, code, credits, semester | `Module` | Layer 2 | name, code, credits, semester |
| Learning outcomes | `LearningOutcome` | Layer 3 | description, assessment_method |
| Assessment types, weightings | `Assessment` | Layer 3 | type, weighting, due_date |
| Pass mark, grading scale | `QAPolicy.assessment` | Layer 4 | pass_mark, grading_descriptor |
| Examination periods, semester dates | `AcademicCalendar` | Layer 6 | semester_start, exam_period |
| Examination rules | `QAPolicy.examination` | Layer 4 + 6 | rule_text, effective_date |
| WIL requirements | `QAPolicy.wil` | Layer 6 | hours_required, employer_requirement |
| AI compliance rules | `AIRule` | Layer 7 | condition_json, action_json |

---

## 3. Mapping Strategies

### 3.1 Pattern-Based Field Extraction (Regex)

For well-structured documents with predictable layouts (TUT prospectuses):

```python
# Conceptual — not production code
FIELD_PATTERNS = {
    "nqf_level": [
        r"NQF\s+[Ll]evel\s+(\d)",           # "NQF level 6"
        r"NQF:\s*(\d)",                       # "NQF: 6"
        r"National Qualifications Framework.*?level\s+(\d)",
    ],
    "total_credits": [
        r"(\d{2,3})\s+credits",              # "360 credits"
        r"credits?:\s*(\d{2,3})",
    ],
    "aps_minimum_math": [
        r"APS.*?(?:Math(?:ematics)?)[^\d]*(\d{2})",  # "APS (Math): 26"
        r"minimum\s+APS.*?(\d{2}).*?[Mm]ath",
    ],
    "programme_code": [
        r"\b([A-Z]{2,4}-[A-Z]{2,4})\b",     # "BSC-CS"
        r"Code:\s*([A-Z0-9-]{3,10})",
    ],
    "module_code": [
        r"\b([A-Z]{2,4}\d{3})\b",            # "CS101"
    ],
}
```

### 3.2 Table-Based Mapping

For admission requirements and programme tables:

```python
# Conceptual mapping of a detected table
COLUMN_HEADER_MAP = {
    "Programme":         "programme.name",
    "NQF Level":         "programme.nqf_level",
    "Credits":           "programme.total_credits",
    "APS (Math)":        "admission_req.aps_minimum_math",
    "APS (Math Lit)":    "admission_req.aps_minimum_math_literacy",
    "English Level":     "admission_req.english_minimum_level",
    "Duration":          "programme.duration_years",
    "Campus":            "programme.campus",
}
# Each data row → one KnowledgeMappingCandidate per field
```

### 3.3 Heading Hierarchy Mapping

For documents organised by headings (module guides, programme guides):

```
Heading 1: "Faculty of ICT"                    → Faculty entity
  Heading 2: "Department of Computer Science"  → Department entity
    Heading 3: "Diploma in Computer Science"   → Programme entity
      Content: "NQF Level: 6"                  → programme.nqf_level = 6
      Content: "Total Credits: 360"            → programme.total_credits = 360
```

ADIP builds a heading hierarchy stack during extraction and uses it as context for all fields found within a section.

### 3.4 Semantic Mapping (Planned — Phase 7)

For unstructured text where patterns fail:
- Embed text chunks with sentence transformers
- Compare embeddings to known IKP field descriptions
- If similarity > 0.82 → propose mapping
- These mappings always go to Human Review (confidence floor: 0.72)

---

## 4. KnowledgeMappingCandidate Model

Every proposed field-to-entity mapping is a `KnowledgeMappingCandidate`:

```json
{
  "id": "UUID",
  "document_id": "UUID",
  "institution_id": "UUID",
  "ikp_entity_type": "programme",
  "ikp_entity_key": "Diploma in Computer Science",
  "ikp_field_name": "nqf_level",
  "extracted_value": "6",
  "coerced_value": 6,
  "value_type": "integer",
  "extraction_method": "regex_pattern_match",
  "source_chunk_id": "UUID",
  "source_page": 12,
  "source_verbatim": "Diploma in Computer Science (NQF level 6)",
  "confidence": 0.96,
  "status": "auto_approved",
  "reviewer_id": null,
  "reviewed_at": null,
  "conflicts_with": null,
  "proposed_at": "2026-06-29T10:06:00Z"
}
```

---

## 5. Conflict Resolution

When a new mapping candidate conflicts with an existing IKP value:

| Scenario | Action |
|---------|--------|
| New value from higher-confidence source | Propose override; add to human review |
| New value from same-confidence source | Flag as conflict; both values in review queue |
| New value from lower-confidence source | Keep existing; log conflict but do not override |
| Values are semantically equivalent | Treat as confirmation; reinforce confidence |

Conflict resolution always produces a human-reviewable record — ADIP never silently overwrites an existing IKP field with a conflicting value.

---

## 6. Institution-Neutral Mapping Configuration

Entity mapping configurations are stored **per institution** in the IKP, not hardcoded:

```json
{
  "institution_code": "TUT",
  "programme_code_patterns": ["[A-Z]{2,4}-[A-Z]{2,5}"],
  "module_code_patterns": ["[A-Z]{2,4}[0-9]{3}"],
  "campus_aliases": {
    "Soshanguve": "Soshanguve South",
    "Sosh South": "Soshanguve South"
  },
  "known_faculty_names": {
    "ICT": "Faculty of Information and Communication Technology",
    "FEBE": "Faculty of Engineering and the Built Environment"
  }
}
```

This allows ADIP to handle institutional naming variations without code changes per institution.
