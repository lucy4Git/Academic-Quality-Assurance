# ADIP — Academic Document Intelligence Platform
## Master Architecture

**Document ID:** ADIP-ARCH-001  
**Version:** 1.0.0  
**Status:** Active — Architecture Design  
**Last Updated:** 2026-06-29  
**Owner:** AQAA Engineering  
**Related ADR:** ADR-0008

---

## 1. What Is ADIP?

The **Academic Document Intelligence Platform (ADIP)** is AQAA's core subsystem for ingesting, classifying, extracting, validating, mapping, and indexing all institutional knowledge documents — regardless of format, source, or institution.

ADIP is the bridge between raw institutional documents (PDFs, Word files, websites, spreadsheets, images, audio, video) and the structured, provenance-tagged Institutional Knowledge Package (IKP) that AQAA uses for compliance reasoning and AI-powered audit.

ADIP answers the fundamental question: **"Given this document, what does AQAA now know — and how confident is it?"**

### 1.1 Why ADIP Exists

Without ADIP, AQAA faces an unsolvable data problem:

- TUT's 8 faculty prospectuses are binary PDFs (not extractable without tooling)
- Academic calendars are PDFs with embedded tables
- Module guides are Word documents
- Assessment briefs are PowerPoint files
- Attendance registers are Excel spreadsheets
- Accreditation evidence may be scanned paper documents (images only)
- Policy documents are HTML web pages
- Evidence packs are ZIP archives containing mixed formats

A PDF-only extraction tool fails for all non-PDF documents. A per-format tool per institution does not scale. ADIP is a unified, format-agnostic intelligence layer.

### 1.2 What ADIP Is Not

- ADIP is **not** the AQAA evidence storage system (`AuditEvidence` model) — that handles module-level QA evidence uploads
- ADIP is **not** a document management system — it does not replace institutional repositories
- ADIP is **not** a static importer — it supports live URL capture, periodic re-ingestion, and change detection
- ADIP is **not** a replacement for human verification — every ADIP extraction goes through the confidence gate and human review queue before entering the IKP

---

## 2. ADIP Scope

ADIP processes documents from two operational contexts:

### Context A: Institutional Knowledge Ingestion (IKP Pipeline)
Documents that define institutional knowledge — prospectuses, policies, regulations, academic calendars, programme guides. Output feeds the IKP for long-lived institutional knowledge.

### Context B: QA Evidence Ingestion (Audit Context)
Documents uploaded as QA audit evidence — assessment briefs, marking guides, moderation reports, attendance registers, learner samples. Output feeds the `AuditEvidence` model and AI audit agents.

Both contexts share ADIP infrastructure but have different downstream consumers.

---

## 3. ADIP Architecture — 10-Layer Model

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ADIP — 10-LAYER ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 10: SECURITY AND GOVERNANCE                                  │
│  Tenant isolation · RBAC · Audit logs · Retention · Permissions    │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 9: AI READINESS                                              │
│  RAG chunks · Vector embeddings · Confidence reasoning · Comparison │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 8: KNOWLEDGE INDEXING                                        │
│  Structured DB · Full-text index · Vector index · Knowledge graph  │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 7: PROVENANCE ENGINE                                         │
│  Source URL · Page/slide/cell · Hash · OCR confidence · Verifier  │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 6: KNOWLEDGE MAPPING                                         │
│  Map extracted fields → IKP entities (Programme, Module, Policy…)  │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 5: VALIDATION ENGINE                                         │
│  Schema · Duplicate detection · Confidence scoring · Review queue  │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 4: EXTRACTION ENGINE                                         │
│  PDF · DOCX · PPTX · XLSX · HTML · OCR · Tables · Audio · Video   │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 3: CLASSIFICATION ENGINE                                     │
│  Document type detection · Confidence tagging · Routing decision   │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 2: DOCUMENT REGISTRY                                         │
│  Identity · Hash · Version · Tenant · Storage path · Retention     │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 1: DOCUMENT SOURCE                                           │
│  Upload · URL · Web capture · ZIP · Repository · Manual entry      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.1 Data Flow

```
Document enters via Source Layer (Layer 1)
    ↓
Registered in Document Registry (Layer 2)
    ↓
Classified by type and routing (Layer 3)
    ↓
Content extracted per format (Layer 4)
    ↓
Validated + confidence-scored (Layer 5)
    ↓  [Low confidence → Human Review Queue]
    ↓  [High confidence → Auto-proceed]
Mapped to IKP entities (Layer 6)
    ↓
Provenance anchored per field (Layer 7)
    ↓
Indexed: structured + full-text + vector (Layer 8)
    ↓
AI Readiness prepared (Layer 9)
    ↓
Security + governance enforced at all layers (Layer 10)
```

---

## 4. ADIP Component Map

| Layer | Primary File | Key Concepts |
|-------|-------------|-------------|
| L1: Source | `DOCUMENT_SOURCE_LAYER.md` | Upload adapters, URL ingestion, ZIP unpacking |
| L2: Registry | `DOCUMENT_SOURCE_LAYER.md` | DocumentRecord, hash, version, tenant |
| L3: Classification | `DOCUMENT_CLASSIFICATION_ENGINE.md` | Document type taxonomy, classifier, routing |
| L4: Extraction | `DOCUMENT_EXTRACTION_ENGINE.md` | Format-specific extractors, chunk model |
| L5: Validation | `DOCUMENT_VALIDATION_ENGINE.md` | Schema gates, duplicate detection, confidence |
| L6: Knowledge Mapping | `KNOWLEDGE_MAPPING_ENGINE.md` | Field-to-IKP entity mapping, candidate records |
| L7: Provenance | `PROVENANCE_ENGINE.md` | ProvenanceAnchor, confidence formula |
| L8: Indexing | `KNOWLEDGE_INDEXING_ENGINE.md` | DB records, FTS, vector, knowledge graph |
| L9: AI Readiness | `AI_READINESS_ENGINE.md` | RAG chunks, Qdrant, reasoning context |
| L10: Governance | `SECURITY_AND_GOVERNANCE.md` | RBAC, retention, immutability, audit |
| OCR/Multimodal | `OCR_AND_MULTIMODAL_STRATEGY.md` | OCR engines, image, visual layout |
| Tables | `TABLE_EXTRACTION_STRATEGY.md` | Table detection, header inference |
| Video/Audio | `VIDEO_AUDIO_EXTRACTION_STRATEGY.md` | Whisper, ffmpeg, transcript model |
| TUT Pilot | `TUT_PILOT_ADIP_PLAN.md` | TUT-specific ingestion plan |
| Roadmap | `ADIP_IMPLEMENTATION_ROADMAP.md` | Phase-by-phase implementation |

---

## 5. ADIP Supported Formats

### 5.1 Text-Based Formats

| Format | Extension | Extractor | Confidence Range |
|--------|-----------|-----------|-----------------|
| PDF (native text) | `.pdf` | pdfminer.six | 0.88–0.96 |
| PDF (scanned/image) | `.pdf` | pdf2image + EasyOCR | 0.60–0.82 |
| Word Document | `.docx` | python-docx | 0.90–0.96 |
| PowerPoint | `.pptx` | python-pptx | 0.85–0.93 |
| Excel / CSV | `.xlsx`, `.csv` | openpyxl / pandas | 0.90–0.96 |
| HTML page (static) | `.html`, URL | BeautifulSoup4 | 0.88–0.95 |
| HTML page (dynamic) | URL | Playwright | 0.82–0.92 |
| Plain text | `.txt`, `.md` | built-in | 0.95–0.99 |
| Rich text | `.rtf` | striprtf | 0.80–0.90 |
| XML / JSON | `.xml`, `.json` | built-in parsers | 0.92–0.99 |

### 5.2 Image and Scanned Formats

| Format | Extractor | Confidence Range |
|--------|-----------|-----------------|
| PNG, JPG, TIFF, BMP | EasyOCR or Tesseract | 0.55–0.82 |
| Scanned PDF | pdf2image + OCR | 0.60–0.82 |
| Handwritten documents | EasyOCR (handwriting mode) | 0.30–0.60 |

### 5.3 Media Formats

| Format | Extractor | Confidence Range |
|--------|-----------|-----------------|
| MP4, MOV, AVI (video) | ffmpeg + Whisper | 0.70–0.88 (transcript) |
| MP3, WAV, AAC (audio) | Whisper | 0.72–0.90 (transcript) |

### 5.4 Archive Formats

| Format | Handler |
|--------|---------|
| ZIP evidence pack | Unpack + process each file individually |
| TAR / GZIP | Unpack + process |

---

## 6. ADIP Document Type Taxonomy

```
ADIP_DOCUMENT_TYPE
│
├── INSTITUTIONAL_KNOWLEDGE
│   ├── PROSPECTUS (faculty, institution)
│   ├── ACADEMIC_CALENDAR
│   ├── POLICY_DOCUMENT (assessment, examination, WIL, RPL)
│   ├── REGULATIONS (academic, student)
│   ├── PROGRAMME_GUIDE
│   ├── MODULE_GUIDE
│   └── QUALIFICATION_SPECIFICATION
│
├── QA_EVIDENCE
│   ├── ASSESSMENT_BRIEF
│   ├── MARKING_GUIDE
│   ├── MODERATION_REPORT (internal / external)
│   ├── ATTENDANCE_REGISTER
│   ├── LEARNER_EVIDENCE (sample submissions)
│   ├── LECTURER_EVIDENCE
│   └── APPROVAL_SIGNOFF
│
├── ACCREDITATION
│   ├── ACCREDITATION_EVIDENCE
│   ├── PROGRAMME_REVIEW_REPORT
│   └── SITE_VISIT_DOCUMENT
│
├── QUALIFICATIONS
│   ├── CERTIFICATE
│   ├── TRANSCRIPT
│   └── DIPLOMA_DOCUMENT
│
└── UNKNOWN
    └── Routed to manual classification queue
```

---

## 7. ADIP Confidence Model

ADIP assigns confidence scores at two levels:

### 7.1 Document-Level Confidence

Assigned when a document is registered. Based on source type:

| Source Type | Confidence Band |
|-------------|----------------|
| Official institution website (HTTPS, verified domain) | 0.90–1.00 |
| Official PDF from institution domain | 0.85–0.96 |
| Official PDF from third-party host (linked from official site) | 0.75–0.88 |
| Document uploaded by institution user (authenticated) | 0.82–0.92 |
| Scanned document | 0.60–0.80 |
| Unknown/external source | 0.30–0.60 |

### 7.2 Field-Level Confidence

Assigned per extracted field. Combines document-level confidence with extraction quality:

```
field_confidence = document_confidence × extraction_quality × position_clarity

extraction_quality:
  exact string match from clear text   → 1.00
  regex extraction from clean text     → 0.95
  table cell extraction (identified)   → 0.90
  OCR from high-quality scan           → 0.80
  OCR from low-quality scan            → 0.60
  AI inference from surrounding text   → 0.55

position_clarity:
  explicit label ("NQF Level: 6")      → 1.00
  contextual label ("offered at NQF")  → 0.85
  implicit (inferred from structure)   → 0.65
```

### 7.3 Gate Rules

| Field Confidence | ADIP Action |
|-----------------|-------------|
| ≥ 0.90 | Auto-load to IKP |
| 0.80–0.89 | Load with `verified = false`; flag for periodic review |
| 0.70–0.79 | Load to human review queue only; IKP not updated until reviewed |
| < 0.70 | Quarantine; ADIP records the candidate but does not propose it |

---

## 8. ADIP Integration with AQAA

### 8.1 IKP Integration

```
ADIP Pipeline Output
    │
    ├── High confidence fields → IKP Assembly (Stage 7)
    ├── Medium confidence → Human Review Queue → IKP after approval
    └── Low confidence → Quarantine log → Manual investigation
```

ADIP does not directly write to the AQAA PostgreSQL database. It produces structured JSON output that is consumed by:
- `seed-from-ikp.py` (batch import) for institutional knowledge
- The evidence ingestion API for audit evidence

### 8.2 AI Agent Integration

```
ADIP Knowledge Index
    │
    ├── Vector index (Qdrant) → AI agents retrieve relevant context
    ├── Full-text index → compliance keyword search
    └── Structured records → direct field lookup (NQF level, credits, etc.)
```

ADIP's AI Readiness Layer (Layer 9) prepares all extracted content for retrieval-augmented generation (RAG) by the AI audit agents.

### 8.3 Audit Evidence Integration

When a lecturer uploads a file via `POST /api/v1/evidence/upload`, the file flows through:
1. `AuditEvidence` model (existing) — links file to checklist item
2. ADIP Layer 1–5 (new) — classifies and extracts content
3. ADIP Layer 8 (new) — indexes for AI retrieval
4. AI agent (existing, enhanced) — retrieves ADIP-indexed content during audit run

---

## 9. ADIP Processing States

Every document registered in ADIP has a processing state:

```
PENDING → CLASSIFYING → EXTRACTING → VALIDATING → MAPPING → INDEXING → READY
                            ↓                   ↓
                         QUARANTINED        REVIEW_QUEUE
                            ↓                   ↓
                         REJECTED          AWAITING_HUMAN_REVIEW
                                               ↓
                                         HUMAN_APPROVED → MAPPING
                                         HUMAN_REJECTED → QUARANTINED
```

---

## 10. ADIP Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Format-agnostic** | Unified document registry regardless of format; format-specific extractors behind a common interface |
| **Source-preserving** | Original documents are stored immutably; ADIP never modifies source files |
| **Provenance-first** | Every extracted field has a `ProvenanceAnchor` with location (page, slide, cell, timestamp) |
| **Confidence-gated** | No unverified data reaches the IKP; confidence thresholds enforced at Layer 5 |
| **Tenant-isolated** | Every ADIP record is scoped to `institution_id`; cross-tenant access blocked |
| **AI-ready by design** | All indexed content is structured for retrieval-augmented generation from day one |
| **Human-in-the-loop** | Medium-confidence extractions require human review before IKP loading |
| **Institution-neutral** | ADIP serves TUT, UP, DUT, CPUT, and any future institution without code changes |

---

## 11. Relationships to Existing AQAA Systems

| Existing System | ADIP Relationship |
|----------------|------------------|
| IKP (`ikp/institutions/`) | ADIP populates IKP JSON packages via extraction + mapping |
| `AuditEvidence` model | ADIP classifies and indexes evidence files uploaded via evidence API |
| `AuditRun` / AI agents | AI agents query ADIP's vector index for relevant context during audit runs |
| `File` model | ADIP wraps file storage; uses the existing storage abstraction (`backend/app/storage/`) |
| `DocumentRecord` model | ADIP extends the existing document record concept (or creates a new registry) |
| Qdrant vector store | ADIP writes to Qdrant as the AI Readiness Layer |

---

*See individual layer documents for detailed specifications.*  
*See `TUT_PILOT_ADIP_PLAN.md` for the immediate TUT implementation plan.*  
*See `ADIP_IMPLEMENTATION_ROADMAP.md` for phased delivery.*
