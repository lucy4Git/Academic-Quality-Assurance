# ADIP — Document Extraction Engine (Layer 4)

**Document ID:** ADIP-L4-001  
**Version:** 1.0.0  
**Status:** Architecture Design  
**Last Updated:** 2026-06-29

---

## 1. Purpose

The Extraction Engine converts raw document content into structured, machine-readable data. It is format-aware: each document type gets the extractor that best suits its structure. All extractors produce a common output format (`DocumentChunk`) regardless of source format.

---

## 2. Extraction Abstraction

All format-specific extractors implement a single interface:

```python
# Conceptual — not production code
class DocumentExtractor(ABC):
    @abstractmethod
    async def extract(self, document_record: DocumentRecord) -> ExtractionResult:
        """
        Returns:
            ExtractionResult containing:
              - chunks: list[DocumentChunk]
              - tables: list[DocumentTable]
              - metadata: DocumentMetadata
              - extraction_quality: float (0.0–1.0)
              - warnings: list[str]
        """
        ...
```

---

## 3. DocumentChunk Model

Every piece of extracted content is a `DocumentChunk`:

```json
{
  "id": "UUID",
  "document_id": "UUID",
  "institution_id": "UUID",
  "chunk_type": "paragraph | heading | table_row | caption | list_item | slide_text | cell_value | transcript_segment",
  "text": "Diploma in Computer Science (NQF level 6)",
  "page_number": 12,
  "slide_number": null,
  "sheet_name": null,
  "cell_range": null,
  "bounding_box": null,
  "section_path": ["Programmes Offered", "Computer Science"],
  "heading_level": null,
  "char_offset_start": 4520,
  "char_offset_end": 4562,
  "extraction_method": "pdfminer_native",
  "ocr_confidence": null,
  "language": "en",
  "sequence_index": 42
}
```

---

## 4. Format-Specific Extractors

### 4.1 PDF — Native Text (Primary Extractor)

**Library:** `pdfminer.six`  
**When used:** PDFs with embedded selectable text (not scanned)  
**Confidence contribution:** 0.90–0.96  
**Installs as:** `pip install pdfminer.six`

**Extraction steps:**
1. Open PDF with `pdfminer.high_level.extract_text()` for full-document text
2. Use `pdfminer.high_level.extract_pages()` for page-by-page layout analysis
3. Identify LTTextBox elements → paragraphs
4. Identify font-size changes → heading detection
5. Identify LTAnon/LTFigure elements → flag for separate table/image handling
6. Produce `DocumentChunk` per paragraph with `page_number` from pdfminer layout

**Heading detection heuristic:**
- Font size ≥ 1.4× body text → `heading_level: 1`
- Font size 1.2–1.4× body text → `heading_level: 2`
- Bold + font size ≥ body → `heading_level: 3`

**Pre-conditions for this extractor:**
- `pypdf.PdfReader(path).pages[0].extract_text()` returns non-empty string
- If empty → fall back to OCR extractor

### 4.2 PDF — Table Extraction

**Library:** `camelot-py` (lattice mode for bordered tables; stream mode for borderless)  
**When used:** After native text extraction, for pages detected to contain tables  
**Confidence contribution:** 0.88–0.94  
**Installs as:** `pip install camelot-py[cv]`

**Table detection heuristic:**
- Pages where keywords like "APS", "NQF Level", "Credits", "Duration", "Campus" appear
- Pages with grid-like layout detected by camelot's lattice mode

**Table output format:**
```json
{
  "id": "UUID",
  "document_id": "UUID",
  "page_number": 15,
  "table_index": 0,
  "header_row": ["Programme", "NQF Level", "Credits", "APS (Math)", "Campus"],
  "data_rows": [
    ["Diploma in Computer Science", "6", "360", "26", "Soshanguve South"],
    ["Advanced Diploma in Computer Science", "7", "120", "—", "Soshanguve South"]
  ],
  "extraction_accuracy": 0.91,
  "camelot_parse_report": { "accuracy": 91.3, "whitespace": 8.7 }
}
```

**Fallback for table extraction failure:** Use `tabula-py` as secondary library.

### 4.3 DOCX — Word Document Extraction

**Library:** `python-docx`  
**Confidence contribution:** 0.90–0.96

**Extraction steps:**
1. `docx.Document(path).paragraphs` → text chunks with style names
2. Style name `Heading 1`, `Heading 2`, etc. → set `heading_level`
3. Tables → `DocumentTable` with full row/cell extraction
4. Metadata: author, created date, modified date from `doc.core_properties`

### 4.4 PPTX — PowerPoint Extraction

**Library:** `python-pptx`  
**Confidence contribution:** 0.85–0.93

**Extraction steps:**
1. Iterate slides → `slide_number`
2. Extract text from all `TextFrame` shapes → chunks
3. Extract table shapes → `DocumentTable`
4. Extract slide title → treated as heading
5. Extract speaker notes → separate chunk type `slide_notes`
6. Extract image descriptions from alt text

### 4.5 XLSX / CSV — Spreadsheet Extraction

**Libraries:** `openpyxl` (XLSX), `csv` built-in or `pandas` (CSV)  
**Confidence contribution:** 0.90–0.96

**Extraction steps for XLSX:**
1. Iterate all sheets → `sheet_name` recorded per chunk
2. Detect header row (first non-empty row or programmatic detection)
3. Extract all data rows as `DocumentTable`
4. Identify merged cells → flatten appropriately
5. Extract cell comments → separate chunk type `cell_comment`
6. Detect formula cells → flag as `requires_interpretation`

**Use case:** TUT attendance registers (row per student, column per date/session)

### 4.6 HTML — Web Page Extraction

**Primary library:** `beautifulsoup4` + `lxml`  
**Dynamic rendering:** `playwright` (headless Chromium) for JavaScript-heavy pages  
**Confidence contribution:** 0.88–0.95

**Extraction steps:**
1. Fetch page (static: `httpx`; dynamic: Playwright)
2. Remove navigation, headers, footers, sidebars (CSS selector-based or boilerplate detection)
3. Extract `<h1>–<h6>` → headings with level
4. Extract `<p>`, `<li>` → paragraph/list chunks
5. Extract `<table>` → `DocumentTable`
6. Extract `<meta>` tags → document metadata
7. Record canonical URL, last-modified header

**TUT-specific selectors** (stored in TUT IKP configuration):
```json
{
  "institution": "TUT",
  "content_selector": "main, .content-area, article",
  "remove_selectors": ["nav", "header", "footer", ".cookie-banner", ".breadcrumb"]
}
```

### 4.7 Images (Standalone)

**See:** `OCR_AND_MULTIMODAL_STRATEGY.md`  
**Libraries:** `easyocr`, `pytesseract`  
**Confidence contribution:** 0.55–0.82

### 4.8 Video

**See:** `VIDEO_AUDIO_EXTRACTION_STRATEGY.md`  
**Library:** `openai-whisper` + `ffmpeg`  
**Output:** Transcript as timed `DocumentChunk` objects

### 4.9 Audio

**See:** `VIDEO_AUDIO_EXTRACTION_STRATEGY.md`  
**Library:** `openai-whisper`  
**Output:** Transcript as timed `DocumentChunk` objects

### 4.10 ZIP Archives

**Handler:** Unzip → classify each member file → route to appropriate extractor  
**Special:** Parent ZIP's metadata (submission date, submitter) propagates to all child chunks

---

## 5. Extraction Output

All extractors produce `ExtractionResult`:

```json
{
  "document_id": "UUID",
  "extraction_method": "pdfminer_native",
  "total_pages": 48,
  "total_chunks": 342,
  "total_tables": 12,
  "extraction_quality": 0.93,
  "language_detected": "en",
  "warnings": [],
  "chunks": [ ... ],
  "tables": [ ... ],
  "metadata": {
    "title": "2026 Prospectus Part 6 Faculty of Information and Communication Technology",
    "author": "Tshwane University of Technology",
    "created": "2025-08-15",
    "modified": "2025-11-20",
    "page_count": 48
  }
}
```

---

## 6. Extractor Selection Logic

```python
# Conceptual — not production code
def select_extractor(document_record: DocumentRecord, classification: Classification) -> DocumentExtractor:
    mime = document_record.mime_type
    doc_type = classification.document_type

    if mime == "application/pdf":
        if has_selectable_text(document_record):
            return PDFNativeTextExtractor()   # pdfminer.six
        else:
            return PDFOCRExtractor()          # pdf2image + EasyOCR
    elif mime in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",):
        return DOCXExtractor()               # python-docx
    elif mime in ("application/vnd.openxmlformats-officedocument.presentationml.presentation",):
        return PPTXExtractor()               # python-pptx
    elif mime in ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",):
        return XLSXExtractor()               # openpyxl
    elif mime == "text/csv":
        return CSVExtractor()
    elif mime in ("text/html", "application/xhtml+xml"):
        return HTMLExtractor()               # beautifulsoup4
    elif mime.startswith("image/"):
        return ImageOCRExtractor()           # easyocr
    elif mime.startswith("video/"):
        return VideoTranscriptExtractor()    # whisper + ffmpeg
    elif mime.startswith("audio/"):
        return AudioTranscriptExtractor()    # whisper
    elif mime == "application/zip":
        return ZIPBatchExtractor()
    else:
        return UnknownFormatExtractor()      # routes to manual queue
```

---

## 7. Extraction Parallelism

Large documents (> 20 pages or > 5 MB) are extracted in chunks using async background tasks:
- Pages 1–10 processed first (title, ToC, key structure)
- Remaining pages queued
- Results merged after all pages complete

Extraction is idempotent: re-running extraction on the same document version produces the same chunks.
