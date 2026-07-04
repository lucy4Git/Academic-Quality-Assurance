# ADR-0008 — Academic Document Intelligence Platform (ADIP)

**Status:** Accepted  
**Date:** 2026-06-29  
**Deciders:** Phase 5.4F architecture session  
**Supersedes:** None  
**Superseded by:** —

---

## Context

Phase 5.4G requires extracting structured data from TUT's official PDF documents — primarily the ICT Faculty Prospectus (Part 6), Students' Rules (Part 1), Examination Rules (Chapter 4), and Academic Calendar. These PDFs cannot be read by AQAA's current tooling.

The simplest solution would be a PDF-only extraction script: install `pdfminer.six`, extract text from the 4–6 TUT PDFs, and parse programme/module data with regex patterns. This solves the immediate problem (Phase 5.4G) in the minimum time.

However, AQAA's product roadmap (Phase 8+) requires ingesting institutional knowledge from:
- Word documents (module guides, assessment briefs)
- Excel spreadsheets (attendance registers, mark sheets)
- HTML websites (institutional web pages)
- Scanned PDFs (older policy documents)
- PowerPoint files (lecture evidence)
- ZIP evidence packs (bundled QA evidence)
- Video recordings (WIL visits, oral examinations)
- Audio recordings (moderation meetings)

A PDF-only tool would need to be replaced or significantly extended for each new format, creating technical debt proportional to the number of document types encountered.

Additionally, AQAA requires:
- Field-level provenance on every extracted value (ADR-0006)
- Confidence scoring per field (IKP architecture, ADR-0004)
- Multi-institution support without code changes (ADR-0002 extension)
- AI-readiness: vector embeddings and RAG context for AI agents (ADR-0005 extension)
- Human review queue for medium-confidence extractions

A PDF-only scraper cannot satisfy these requirements.

---

## Decision

AQAA will implement the **Academic Document Intelligence Platform (ADIP)** as a core subsystem, replacing the planned PDF-only extraction script.

ADIP is a 10-layer, format-agnostic document intelligence system:
1. Document Source Layer (file upload, URL, ZIP, web capture)
2. Document Registry (hash, tenant, version, immutable storage)
3. Document Classification Engine (type detection, routing)
4. Document Extraction Engine (format-specific extractors behind common interface)
5. Document Validation Engine (schema gate, duplicate detection, confidence scoring)
6. Knowledge Mapping Engine (extracted text → IKP entity candidates)
7. Provenance Engine (per-field source anchors with exact location)
8. Knowledge Indexing Engine (PostgreSQL + FTS + Qdrant vector + knowledge graph)
9. AI Readiness Engine (RAG chunks, confidence-aware reasoning)
10. Security and Governance (tenant isolation, RBAC, retention, audit log)

ADIP is implemented incrementally:
- **Phase 5.4G:** PDF + HTML + table extraction (minimum viable — solves TUT ICT pilot)
- **Phase 5.4H:** DOCX, XLSX, PPTX support
- **Phase 6:** ADIP management UI + human review queue
- **Phase 7:** Vector integration + RAG + video/audio
- **Phase 8:** Production hardening + institutional repository connectors

---

## Consequences

### Positive

- **Single architecture** serves all current and future document types — no format-specific rewrites
- **Provenance by design** — every extracted field has a `ProvenanceAnchor` with exact source location (page, paragraph, table row, cell, timestamp)
- **Confidence-gated** — no unverified data enters the IKP regardless of format
- **Multi-institution** — TUT, UP, DUT and any future institution use the same ADIP pipeline
- **AI-ready** — all extracted content is prepared for RAG and vector search from day one
- **Incremental delivery** — Phase 5.4G delivers only what's needed for TUT pilot without building everything upfront
- **Human review integration** — medium-confidence extractions queue for human verification before loading

### Negative

- More complex architecture than a simple PDF script
- Phase 5.4G requires installing multiple libraries (`pdfminer.six`, `camelot-py`, `pymupdf`, `easyocr`)
- ADIP database tables require a new Alembic migration
- Full ADIP (all 10 layers) is delivered across multiple phases, not immediately

### Neutral

- ADIP replaces the previously planned "Phase 5.4D/G PDF extraction script" concept
- Existing `backend/app/parsers/` (document processing for AI agents) coexists with ADIP — both serve different purposes:
  - `parsers/` → processes evidence already in the system for AI agent classification
  - ADIP → ingests institutional knowledge documents into the IKP
- The `File` and `DocumentRecord` models in the existing codebase are related but distinct from ADIP's `DocumentRecord` registry
- No existing backend tests are affected

---

## Alternatives Considered

### Alternative 1 — PDF-Only Extraction Script

Write a one-off script: `python extract_tut_ict_pdf.py` using `pdfminer.six`.

**Rejected because:**
- Solves only TUT ICT Prospectus; every other institution and every other format needs a separate script
- No provenance tracking — extracted values have no source location
- No confidence scoring — cannot distinguish reliable extraction from guessed values
- Not AI-ready — no vector index, no RAG chunks
- Technical debt: each new format requires a new script with no shared infrastructure

### Alternative 2 — Third-Party Document Processing API

Use an external API (AWS Textract, Azure Form Recogniser, Google Document AI) for all extraction.

**Rejected for pilot because:**
- API cost: per-page pricing unsuitable for bulk institutional document processing
- Data privacy: institution documents (prospectuses, examination rules) should not leave the AQAA environment
- API dependency: offline or air-gapped institutions cannot use cloud APIs
- Vendor lock-in risk for core platform capability

**Reconsidered for Phase 8:** Cloud Document AI may be offered as an optional premium ingestion path for institutions with budget and no privacy constraints.

### Alternative 3 — LLM-Based Extraction Only

Use a large language model (GPT-4, Claude) to extract structured data from raw text.

**Rejected because:**
- LLMs are not deterministic — same document may produce different extractions on repeat runs
- LLMs can hallucinate field values (fabricate NQF levels, credits, APS that don't exist in the document)
- No guaranteed provenance — LLMs cannot reliably cite page number and verbatim quote for every extracted value
- High cost for bulk processing of large PDFs

**Complement, not replacement:** LLMs are used in ADIP's AI Readiness Layer for semantic question answering over already-indexed content, not for primary field extraction.

---

## Implementation Notes

ADIP Python package structure (planned):
```
backend/app/adip/
├── __init__.py
├── models/          — DocumentRecord, DocumentChunk, KnowledgeMappingCandidate, ProvenanceAnchor
├── extractors/      — pdf_extractor.py, docx_extractor.py, html_extractor.py, ...
├── classifiers/     — document_type_classifier.py
├── mappers/         — ikt_mapper.py, tut_ict_mapper.py, ...
├── validators/      — schema_validator.py, confidence_scorer.py
├── indexers/        — db_indexer.py, fts_indexer.py, vector_indexer.py
├── provenance/      — provenance_engine.py, anchor_model.py
└── pipeline/        — run_ingestion.py, run_tut_ict.py
```

---

## References

- `docs/09_AI/ADIP/ADIP_MASTER_ARCHITECTURE.md` — full architecture
- `docs/09_AI/ADIP/ADIP_IMPLEMENTATION_ROADMAP.md` — phased implementation
- `docs/09_AI/ADIP/TUT_PILOT_ADIP_PLAN.md` — TUT pilot specifics
- `docs/12_Decisions/ADR-0004-Institutional-Knowledge-Package.md` — IKP requires ADIP
- `docs/12_Decisions/ADR-0006-Provenance-and-Versioning.md` — provenance requirement
- `docs/00_Project/PROJECT_DECISIONS.md` — DEC-0011 (SaaS), DEC-0012 (ADIP)
