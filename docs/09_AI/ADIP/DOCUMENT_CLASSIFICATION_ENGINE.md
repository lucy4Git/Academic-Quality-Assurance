# ADIP — Document Classification Engine (Layer 3)

**Document ID:** ADIP-L3-001  
**Version:** 1.0.0  
**Status:** Architecture Design  
**Last Updated:** 2026-06-29

---

## 1. Purpose

The Classification Engine determines **what type of document** has been received and **what extraction strategy** to apply. Classification happens before extraction — the wrong extractor on the wrong document type wastes compute and produces garbage.

Classification also determines the routing decision: which extraction pipeline to activate, which IKP layer the document populates, and which compliance domain the content relates to.

---

## 2. Classification Taxonomy

```
ADIP Document Type
│
├── INSTITUTIONAL_KNOWLEDGE
│   ├── PROSPECTUS_FACULTY          → Extraction: PDF/DOCX full-text + tables; maps to Programme/Dept
│   ├── PROSPECTUS_INSTITUTION      → Extraction: PDF full-text; maps to Institution profile
│   ├── ACADEMIC_CALENDAR           → Extraction: PDF tables + date extraction; maps to Calendar
│   ├── POLICY_ASSESSMENT           → Extraction: full-text; maps to QA Policy (Layer 4 IKP)
│   ├── POLICY_EXAMINATION          → Extraction: full-text; maps to QA Policy
│   ├── POLICY_WIL                  → Extraction: full-text; maps to QA Policy
│   ├── POLICY_RPL                  → Extraction: full-text; maps to QA Policy
│   ├── REGULATIONS_ACADEMIC        → Extraction: full-text; maps to Institutional Policy (Layer 6 IKP)
│   ├── REGULATIONS_STUDENT         → Extraction: full-text; maps to Institutional Policy
│   ├── PROGRAMME_GUIDE             → Extraction: full-text + tables; maps to Programme
│   ├── MODULE_GUIDE                → Extraction: full-text; maps to Module + Outcomes
│   └── QUALIFICATION_SPECIFICATION → Extraction: structured tables; maps to Qualification (Layer 5 IKP)
│
├── QA_EVIDENCE
│   ├── ASSESSMENT_BRIEF            → Extraction: full-text; maps to AuditChecklistItem
│   ├── MARKING_GUIDE               → Extraction: full-text + tables; maps to AuditChecklistItem
│   ├── MARKING_RUBRIC              → Extraction: tables; maps to AuditChecklistItem
│   ├── MODERATION_INTERNAL         → Extraction: full-text; maps to AuditChecklistItem
│   ├── MODERATION_EXTERNAL         → Extraction: full-text; maps to AuditChecklistItem
│   ├── ATTENDANCE_REGISTER         → Extraction: tables; maps to AuditChecklistItem
│   ├── LEARNER_EVIDENCE_SAMPLE     → Extraction: full-text; maps to AuditEvidence
│   ├── LECTURER_EVIDENCE           → Extraction: full-text; maps to AuditEvidence
│   └── APPROVAL_SIGNOFF            → Extraction: signature/date detection; maps to AuditChecklistItem
│
├── ACCREDITATION
│   ├── ACCREDITATION_EVIDENCE      → Extraction: full-text; maps to AuditRun (accreditation type)
│   ├── PROGRAMME_REVIEW_REPORT     → Extraction: full-text; maps to AuditRun
│   └── SITE_VISIT_DOCUMENT         → Extraction: full-text; maps to AuditRun
│
├── QUALIFICATIONS
│   ├── CERTIFICATE                 → Extraction: OCR; maps to User qualification record
│   ├── TRANSCRIPT                  → Extraction: OCR + tables; maps to User qualification record
│   └── DIPLOMA_DOCUMENT            → Extraction: OCR; maps to User qualification record
│
└── UNKNOWN
    └── → Routes to manual classification queue
```

---

## 3. Classification Methods

ADIP uses a three-pass classification approach:

### Pass 1: Admin-Provided Hint
When a document is submitted with an explicit `document_category`, that hint is used as the initial classification with confidence 0.95 (institution admin knows their own documents).

The classification engine may override this if the content strongly contradicts the hint (e.g., admin says "assessment_brief" but content contains an academic calendar).

### Pass 2: Filename and Metadata Heuristics
```
Filename heuristics (examples):
"Part6_ICT_Prospectus.pdf"              → PROSPECTUS_FACULTY (0.92)
"Students_Rules_and_Regulations.pdf"    → REGULATIONS_STUDENT (0.94)
"Chapter_4_Examination_Rules.pdf"       → POLICY_EXAMINATION (0.93)
"2026-AcademicCore-Calendar.pdf"        → ACADEMIC_CALENDAR (0.96)
"assessment_brief_CS101.docx"           → ASSESSMENT_BRIEF (0.91)
"attendance_register_sem1.xlsx"         → ATTENDANCE_REGISTER (0.93)
```

Filename rules use:
1. Keyword matching against known term lists per document type
2. Institution-specific known filename patterns (stored in IKP)
3. Date/year patterns suggesting calendar documents
4. Module code patterns suggesting QA evidence

### Pass 3: Content Sampling
For documents where Pass 1 and Pass 2 produce low confidence, ADIP extracts the first 500 words (or first slide/sheet) and runs content classification:

```python
# Conceptual content classifier
signals = {
    "PROSPECTUS": ["NQF level", "APS", "admission requirements", "programme", "diploma", "faculty"],
    "ACADEMIC_CALENDAR": ["semester", "registration", "examination", "vacation", "recess"],
    "POLICY_EXAMINATION": ["supplementary", "pass mark", "re-examination", "deferral", "invigilation"],
    "ASSESSMENT_BRIEF": ["assessment task", "weighting", "due date", "submission", "marks"],
    "ATTENDANCE_REGISTER": ["date", "signature", "absent", "present", "student number"],
    "MARKING_GUIDE": ["total marks", "criteria", "rubric", "descriptor", "performance level"],
}
# Count keyword matches → highest score → classification with count-proportional confidence
```

---

## 4. Classification Output

```json
{
  "document_id": "UUID",
  "document_type": "PROSPECTUS_FACULTY",
  "classification_confidence": 0.94,
  "classification_method": "filename_heuristic + content_sample",
  "extraction_strategy": "pdf_native_text + table_extraction",
  "ikp_layer_target": ["academic_structure", "qualification", "curriculum"],
  "routing_decision": {
    "extraction_pipeline": "pdf_structured",
    "requires_ocr": false,
    "requires_table_extraction": true,
    "requires_human_review": false
  },
  "override_reason": null,
  "classified_at": "2026-06-29T10:01:00Z"
}
```

---

## 5. Unknown Document Handling

Documents that cannot be classified above 0.60 confidence are:
1. Stored in the Document Registry with `document_type = UNKNOWN`
2. Added to the **Manual Classification Queue**
3. An ADIP Admin is notified
4. No extraction is attempted until classification is confirmed

Manual classification is performed by an ADIP Admin (System Admin role) via a future ADIP Management UI (Phase 6).

---

## 6. Classification Rules for TUT Documents

Pre-configured classification rules for TUT pilot documents:

| Filename Pattern | Classified As | Confidence |
|-----------------|--------------|-----------|
| `Part2_Arts-and-Design_Prospectus.pdf` | PROSPECTUS_FACULTY | 0.97 |
| `Part3_Economics-and-Finance_Prospectus.pdf` | PROSPECTUS_FACULTY | 0.97 |
| `Part4_FEBE_Prospectus.pdf` | PROSPECTUS_FACULTY | 0.97 |
| `PART_5_Humanities_Prospectus_-2026.pdf` | PROSPECTUS_FACULTY | 0.97 |
| `Part6_ICT_Prospectus.pdf` | PROSPECTUS_FACULTY | 0.97 |
| `Part7_Management-Sciences_Prospectus.pdf` | PROSPECTUS_FACULTY | 0.97 |
| `Part8_Science.pdf` | PROSPECTUS_FACULTY | 0.97 |
| `PART_10_TSB_Prospectus_2026.pdf` | PROSPECTUS_FACULTY | 0.97 |
| `Part1_Students_Rules_and_Regulations.pdf` | REGULATIONS_STUDENT | 0.98 |
| `Chapter_4_2024.pdf` | POLICY_EXAMINATION | 0.96 |
| `2026-AcademicCore-Calendar.pdf` | ACADEMIC_CALENDAR | 0.97 |
| `First-Year-Course_Information.pdf` | INSTITUTIONAL_KNOWLEDGE | 0.90 |
| `tut.ac.za/ict/computer-science/` | INSTITUTIONAL_KNOWLEDGE | 0.96 |
