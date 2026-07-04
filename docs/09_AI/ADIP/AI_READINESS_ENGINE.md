# ADIP — AI Readiness Engine (Layer 9)

**Document ID:** ADIP-L9-001  
**Version:** 1.0.0  
**Status:** Architecture Design  
**Last Updated:** 2026-06-29

---

## 1. Purpose

The AI Readiness Engine prepares all ADIP-indexed content for retrieval-augmented generation (RAG), confidence-aware reasoning, document comparison, and structured compliance analysis by AQAA's AI audit agents.

This layer sits above the Knowledge Index (Layer 8) and transforms indexed content into forms that AI can reason over — not just retrieve.

---

## 2. RAG Preparation

### 2.1 RAG Chunk Design

A RAG chunk is a self-contained, citable unit of knowledge:

```json
{
  "chunk_id": "UUID",
  "document_id": "UUID",
  "institution_id": "UUID",
  "academic_year": "2026",
  "text": "The Diploma in Computer Science (NQF Level 6, 360 credits) is offered at Soshanguve South Campus. Admission requires a minimum APS of 26 with Mathematics at Level 5 and English at Level 4.",
  "context_window": {
    "preceding": "The Department of Computer Science offers the following qualifications:",
    "following": "The Advanced Diploma in Computer Science (NQF Level 7) follows this Diploma."
  },
  "citation": {
    "document_title": "2026 Prospectus Part 6 Faculty of ICT",
    "source_url": "https://www.tut.ac.za/media/.../Part6_ICT_Prospectus.pdf",
    "page_number": 12,
    "retrieved_date": "2026-06-29"
  },
  "structured_facts": {
    "programme_name": "Diploma in Computer Science",
    "nqf_level": 6,
    "total_credits": 360,
    "campus": "Soshanguve South",
    "aps_minimum_math": 26,
    "math_level_required": 5,
    "english_level_required": 4
  },
  "confidence": 0.96,
  "tags": ["programme", "ict", "diploma", "computer_science", "nqf_6", "admission"]
}
```

### 2.2 RAG Retrieval Context for AI Agents

When an AI audit agent runs for a module (e.g., CS101 — Introduction to Programming at TUT/ICT):

```
Agent Query: "What documents are required for this module's QA folder?"

ADIP retrieves:
1. QA Policy chunks (assessment policy, examination rules)
2. Programme description chunks (Diploma in CS requirements)
3. Module guide chunks (CS101 specific if available)
4. Prior audit findings for CS101 (from audit_history)

Composes context window for AI reasoning:
- Institution: TUT
- Programme: Diploma in Computer Science (NQF 6)
- Module: CS101 Introduction to Programming
- QA requirements from: Students' Rules Part 1, pp. 22–24
- Assessment policy: Chapter 4 Examination Rules 2024
- Required checklist items: [from IKP QA Policy]
```

---

## 3. Confidence-Aware Reasoning

Every AI agent response citing ADIP knowledge must attach confidence metadata:

```json
{
  "finding": "The module folder does not contain a Moderation Report.",
  "severity": "HIGH",
  "evidence_basis": {
    "requirement_source": {
      "text": "Internal moderation is required for all summative assessments.",
      "citation": "TUT Students' Rules and Regulations 2026, Section 5.3",
      "confidence": 0.89
    },
    "gap_detection": {
      "method": "evidence_category_scan",
      "searched_for": "INTERNAL_MODERATION",
      "found": false
    }
  },
  "recommendation": "Upload the internal moderation report for each summative assessment.",
  "confidence_in_finding": 0.89,
  "note": "Requirement sourced from medium-confidence OCR extraction. Human verification recommended."
}
```

When a finding is based on ADIP data with confidence < 0.85, the AI agent's output includes a transparency notice: `"Note: This finding is based on data with medium confidence (0.82). The source document should be verified by a QA Officer."`

---

## 4. Source-Grounded Answers

ADIP enables AI agents to answer questions with exact citations:

```
Question: "What is the minimum APS for the Diploma in Computer Science at TUT?"

ADIP response (structured):
  value: 26 (Mathematics track)
  source: "2026 Prospectus Part 6, TUT Faculty of ICT, page 15"
  verbatim: "Diploma in Computer Science: APS 26 (Math)"
  confidence: 0.94
  last_verified: "2026-06-29"
  academic_year: "2026"
  warning: "APS for Mathematical Literacy track pending PDF extraction"
```

The AI agent never fabricates data — it only reports what ADIP has extracted with provenance.

---

## 5. Contradiction Detection

When an AI agent queries a field and ADIP has conflicting values from different sources:

```json
{
  "query": "credits for Advanced Diploma in Computer Systems Engineering",
  "result": "CONFLICT",
  "candidates": [
    {"value": 120, "source": "HEQSF standard minimum", "confidence": 0.82},
    {"value": 140, "source": "briefly.co.za (secondary)", "confidence": 0.35}
  ],
  "resolution": "Use HEQSF standard (120 credits) pending PDF extraction",
  "ai_action": "return_lower_confidence_value_with_warning"
}
```

---

## 6. Document Comparison Engine

ADIP supports year-on-year document comparison:

```
Compare: TUT ICT Prospectus 2025 vs 2026
→ Fields added: 3
→ Fields changed: 7 (APS values adjusted for 2 programmes)
→ Fields removed: 0
→ New programmes: 0
→ Discontinued programmes: 0

Changed fields:
  Diploma in Computer Science → APS (Math): 25 → 26 (+1)
  Diploma in Information Technology → campus added: Polokwane
```

This powers year-on-year compliance trend reporting.

---

## 7. Compliance Reasoning Templates

ADIP pre-computes structured reasoning templates for common audit questions:

| Template | Query | ADIP Response |
|----------|-------|---------------|
| `nqf_evidence_requirements` | "What evidence is required for NQF Level 6 modules?" | Checklist from QA Policy (Layer 4 IKP) |
| `programme_admission_check` | "Does this module's programme require Pure Maths?" | AdmissionRequirement.mathematics_required |
| `wil_required` | "Is WIL required for this programme?" | QAPolicy.wil.hours_required |
| `pass_mark_policy` | "What is the pass mark for this institution?" | QAPolicy.assessment.pass_mark |
| `moderation_requirements` | "What moderation is required?" | QAPolicy.moderation.internal_required |

These templates make AI audit agents faster and more consistent — they retrieve from ADIP rather than re-deriving from raw text each run.
