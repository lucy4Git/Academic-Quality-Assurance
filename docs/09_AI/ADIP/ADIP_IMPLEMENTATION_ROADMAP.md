# ADIP — Implementation Roadmap

**Document ID:** ADIP-ROAD-001  
**Version:** 1.0.0  
**Status:** Active — Architecture Approved  
**Last Updated:** 2026-06-29

---

## Overview

ADIP is implemented in phases aligned with AQAA's overall roadmap. The architecture is fully designed (Phase 5.4F — this document set). Implementation begins in Phase 5.4G with the minimum viable ADIP needed to unlock TUT module-level data.

---

## Phase 5.4F — Architecture (Current)
**Status:** ✅ Complete  
**Deliverable:** ADIP architecture documentation (15 files + ADR-0008)  
**No code changes, no database changes**

---

## Phase 5.4G — Minimum Viable ADIP (PDF + HTML + Tables)

**Goal:** Extract TUT ICT Prospectus PDF and populate IKP v1.1.0  
**Status:** ✅ Complete (2026-06-29)  
**Scope:** Layers 1–7 for PDF and HTML only; no video/audio; no vector index in this phase

### Tasks

| Task | Layer | Library | Priority |
|------|-------|---------|---------|
| Install `pdfminer.six` | L4 | `pip install pdfminer.six` | Critical |
| Install `camelot-py[cv]` | L4 | `pip install camelot-py[cv]` | Critical |
| Install `pymupdf` (for OCR prep) | L4 | `pip install pymupdf` | Medium |
| Install `easyocr` | L4/OCR | `pip install easyocr` | Medium |
| Write `adip/extractors/pdf_extractor.py` | L4 | pdfminer.six | Critical |
| Write `adip/extractors/table_extractor.py` | L4 | camelot-py | Critical |
| Write `adip/mappers/tut_ict_mapper.py` | L6 | regex patterns | Critical |
| Write `adip/pipeline/run_tut_ict.py` | L1–L7 | orchestration | Critical |
| Extract Part6_ICT_Prospectus.pdf | L4 | pdfminer.six | Critical |
| Extract Part1_Students_Rules.pdf | L4 | pdfminer.six | High |
| Extract Chapter_4_Exam_Rules.pdf | L4 | pdfminer.six | High |
| Extract 2026_Calendar.pdf | L4 | camelot | High |
| Validate extracted data vs Phase 5.4B secondary sources | L5 | manual review | High |
| Assemble IKP v1.1.0 | L7–L8 | JSON assembly | Critical |
| Write Alembic migration for ADIP tables | L2 | Alembic | Critical |
| Write `seed_tut.py` from IKP v1.1.0 | External | SQLAlchemy | Critical |
| Run 432 backend tests (no regressions) | — | pytest | Mandatory |
| Run frontend lint/build | — | npm | Mandatory |

### 5.4G Deliverables

- IKP v1.1.0 for TUT/ICT (25 programmes with APS, credits, ~75 modules)
- `adip/` Python package with PDF + table extractors
- `adip/pipeline/run_tut_ict.py` — one-command TUT pilot extraction
- `database/seed_data/seed_tut.py` — load IKP v1.1.0 into AQAA
- New Alembic migration for ADIP registry tables
- Updated CHANGELOG.md and PHASE_TRACKER.md

### 5.4G Out of Scope

- DOCX, PPTX, XLSX extractors (defer to 5.4H)
- Video/audio extraction (defer to Phase 7)
- Vector index / Qdrant integration (defer to Phase 7)
- Human review queue UI (defer to Phase 6)
- Full ADIP API endpoints (defer to Phase 6)

---

## Phase 5.4H — ADIP Table Extraction & TUT ICT Completion

**Goal:** Add table extraction support and complete TUT ICT programme/module/admission data  
**Status:** ✅ Complete (2026-07-01)  
**Scope:** pdfplumber + tab-format extraction; 22 programmes; 174 modules; 16 admission requirements

### What Was Discovered

TUT prospectus tables are **not bordered PDF tables** — they are tab-separated text lines where each cell ends with `\t\n`. Standard lattice-mode table extraction (pdfplumber, camelot) finds only 1 real bordered table (the APS conversion table on page 4). All module curriculum tables are tab-separated text that requires the following approach:

1. Extract page text via pymupdf (`page.get_text("text")`)
2. `join_tab_lines()` — merge `\t\n` → `\t` to collapse multi-line cells
3. `MODULE_TAB_RE` — `([A-Z]{2,4}\d{3}[A-Z])\t+([^\t\n()]+?)\t+\((\d)\)\t+\((\d+)\)` — extract code, name, NQF, credits

### Completed Tasks

| Task | Status | Notes |
|------|--------|-------|
| `table_extractor.py` — pdfplumber + tab-format engine | ✅ | 107 tables extracted |
| `pdf_extractor.py` — tables included in ExtractionResult | ✅ | |
| `document_classifier.py` — institution filename overrides | ✅ | 12 pattern entries |
| `tut_ict_mapper.py` — PDF-direct mode with qual code anchoring | ✅ | 22 programmes, 174 modules |
| `run_tut_ict_extraction.py` — 8-file output + conflict detection | ✅ | |
| AcademicPlanning misclassification fixed | ✅ | Now `academic_calendar` conf=0.96 |
| 18 new tests | ✅ | 490 total |

---

## Phase 5.4I — TUT ICT Pilot Database Load

**Goal:** Load IKP v1.1.0 extracted data into AQAA PostgreSQL database  
**Status:** ⏳ Planned  
**Scope:** `database/seed_data/seed_tut.py` — idempotent seed from JSON candidates

### Tasks

| Task | Priority |
|------|---------|
| Write `database/seed_data/seed_tut.py` | Critical |
| Map programme_candidates.json → Programme + QA fields | Critical |
| Map module_candidates.json → Module records | Critical |
| Map admission_candidates.json → programme metadata | High |
| Idempotency: skip existing records, update on conflict | Critical |
| Run seed on Docker postgres | Critical |
| Verify with `GET /api/v1/programmes` | High |

---

## Phase 5.4J — Full Document Type Coverage (TUT Complete)

**Goal:** Extract all remaining TUT PDFs (all 8 faculty prospectuses)  
**Status:** ⏳ Planned  
**Scope:** Complete IKP for all 8 TUT faculties + DOCX/XLSX support

### Additional Tasks

| Task | Priority |
|------|---------|
| Extract Parts 2–5, 7, 8, 10 (remaining faculty prospectuses) | High |
| Write DOCX extractor (python-docx) | Medium |
| Write XLSX extractor (openpyxl) | Medium |
| Write HTML extractor with Playwright support | Medium |
| Update TUT IKP to v1.2.0 (full institution) | High |
| Add ADIP monitoring dashboard (basic) | Low |

---

## Phase 6 — ADIP Management UI

**Goal:** Build human review queue and ADIP admin UI in AQAA frontend

### Tasks

| Task |
|------|
| Human Review Queue page (`/admin/adip/review`) |
| Document Registry page (`/admin/adip/documents`) |
| Knowledge Candidate browser (`/admin/adip/candidates`) |
| Provenance explorer (`/admin/adip/provenance`) |
| ADIP ingestion status dashboard |
| Backend API endpoints for all ADIP management operations |
| Second institution IKP (UP or DUT) |

---

## Phase 7 — AI Knowledge Base and Vector Integration

**Goal:** Connect ADIP to AQAA's AI audit agents via RAG

### Tasks

| Task |
|------|
| Integrate Qdrant vector index with ADIP extraction pipeline |
| Sentence transformer embedding generation for all indexed chunks |
| RAG context retrieval for AI audit agents |
| IKP-aware audit templates (agents load institution rules from ADIP) |
| Semantic search API endpoint |
| Contradiction detection engine |
| Year-on-year document comparison |
| Video/audio transcript extraction (Whisper integration) |

---

## Phase 8 — Production ADIP

**Goal:** Enterprise-grade, monitored, backed-up ADIP deployment

### Tasks

| Task |
|------|
| Replace PostgreSQL FTS with Elasticsearch for full-text search |
| Multi-institution ADIP (UP, DUT, CPUT active simultaneously) |
| Institutional repository import connectors (SharePoint, Moodle) |
| Automated periodic re-ingestion (detect updated documents at source URL) |
| Cold storage archival for documents > 3 years old |
| POPIA-compliant deletion workflow |
| ADIP audit compliance reporting |

---

## Dependency Graph

```
Phase 5.4F (Architecture) ← CURRENT
    ↓
Phase 5.4G (PDF extraction — pdfminer.six + camelot)
    ↓
Phase 5.4H (Full TUT + DOCX/XLSX)
    ↓
Phase 6 (ADIP management UI + second institution)
    ↓
Phase 7 (RAG + vector + AI integration)
    ↓
Phase 8 (Production deployment)
```

---

## Library Installation Summary

### Immediately Required (Phase 5.4G)

```bash
cd backend
pip install pdfminer.six        # PDF text extraction
pip install camelot-py[cv]      # PDF table extraction (requires OpenCV)
pip install pymupdf             # PDF page rendering (no Poppler dependency)
pip install tabula-py           # PDF table fallback
pip install easyocr             # OCR for scanned pages/images
```

### Phase 5.4H

```bash
pip install python-docx         # DOCX extraction
pip install python-pptx         # PPTX extraction
pip install openpyxl            # XLSX extraction
pip install beautifulsoup4 lxml # HTML extraction
pip install playwright          # Dynamic HTML rendering
pip install httpx               # Async HTTP client
```

### Phase 7

```bash
pip install sentence-transformers  # Text embeddings
pip install openai-whisper         # Audio/video transcription
pip install ffmpeg-python          # Video audio extraction
# Qdrant client already in stack
```

### Platform Notes (Windows)

- `camelot-py[cv]` requires OpenCV — may need `pip install opencv-python-headless` separately
- `pymupdf` prefers to `pdfminer.six` for PDF rendering; use pdfminer for text extraction
- `playwright install chromium` required after playwright install
- `easyocr` downloads model weights (~100 MB) on first use — ensure internet access
- `ffmpeg` must be installed system-wide: `winget install ffmpeg`
