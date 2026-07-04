# ADIP — OCR and Multimodal Strategy

**Document ID:** ADIP-OCR-001  
**Version:** 1.0.0  
**Status:** Architecture Design  
**Last Updated:** 2026-06-29

---

## 1. When OCR Is Required

OCR (Optical Character Recognition) is required when documents contain text as image pixels rather than selectable characters:

| Scenario | Detection Method | OCR Required |
|---------|-----------------|-------------|
| Scanned paper documents (PDF) | `pypdf` returns empty string | Yes |
| Native PDF | `pypdf` returns non-empty text | No |
| Image files (PNG, JPG, TIFF) | MIME type check | Always |
| PDF with embedded images only | Layout analysis — no LTTextBox elements | Yes |
| Handwritten documents | Detected via OCR confidence < 0.60 | Special handling |
| Stamped/signed documents | Contains signature or stamp elements | Partial OCR |

---

## 2. OCR Engine Selection

### Primary Engine: EasyOCR

**Reason selected:**
- Pure Python — no system Poppler dependency (critical for Windows dev environment)
- Supports 80+ languages including Afrikaans (relevant for some SA documents)
- GPU-accelerated when available; CPU fallback
- Good accuracy on clean printed text (>90% character accuracy on quality scans)
- Open source, no API cost

**Install:** `pip install easyocr`

**Limitation:** Higher memory usage than Tesseract; slower on CPU-only systems

### Secondary Engine: Tesseract (via pytesseract)

**Reason as secondary:**
- Faster than EasyOCR on CPU
- Lower memory footprint
- Requires Tesseract binary system installation (`winget install tesseract`)
- Lower accuracy on degraded scans vs EasyOCR

**Install:** `pip install pytesseract` + Tesseract binary

### OCR Engine Selection Logic

```python
# Conceptual — not production code
def select_ocr_engine(image_quality_estimate: float) -> OCREngine:
    if image_quality_estimate > 0.80:
        return TesseractEngine()     # Fast, sufficient for good quality
    else:
        return EasyOCREngine()       # Better accuracy on degraded scans
```

---

## 3. PDF-to-Image Pipeline (Scanned PDFs)

For scanned PDF documents, ADIP converts pages to images before OCR:

**Library:** `pdf2image` (requires Poppler on system) OR `pymupdf` (fitz) — no system dependency  
**Recommended for AQAA (Windows):** `pymupdf` (no Poppler needed)  
**Install:** `pip install pymupdf`

**Process:**
```
Scanned PDF
    │
    ▼ pymupdf → render each page as PNG at 300 DPI
    │
    ▼ Image preprocessing pipeline:
    │   - Convert to grayscale
    │   - Apply adaptive threshold (remove shadows)
    │   - Deskew (correct rotation up to 5°)
    │   - Remove borders
    │   - Sharpen text
    │
    ▼ EasyOCR → text extraction per page
    │
    ▼ DocumentChunk per paragraph, with:
        page_number, bounding_box, ocr_confidence
        chunk_type = "ocr_paragraph"
```

**DPI recommendation:** 300 DPI minimum; 600 DPI for handwritten or stamped documents.

---

## 4. OCR Confidence Handling

EasyOCR returns confidence per detected text block. ADIP uses this to set chunk confidence:

| OCR Confidence | ADIP Field Confidence Adjustment | Action |
|----------------|--------------------------------|--------|
| ≥ 0.92 | × 0.88 | Accept; include in extraction |
| 0.80–0.91 | × 0.82 | Accept with lower confidence |
| 0.70–0.79 | × 0.75 | Accept; flag for review |
| 0.60–0.69 | × 0.65 | Quarantine; manual review required |
| < 0.60 | × 0.50 | Reject from field extraction; retain raw OCR text |

---

## 5. Layout Analysis (Visual Understanding)

For complex PDF layouts (multi-column, tables with merged cells, forms):

**Library:** `pdfminer.six` layout analysis + `pymupdf` coordinates

**Layout elements detected:**
- Multi-column text → reorder columns left-to-right before extraction
- Header/footer zones → exclude from body text extraction
- Text boxes (non-table) → paragraphs in reading order
- Table regions → route to Table Extraction Engine

**Bounding box storage:**
Every OCR chunk stores `bounding_box: { x, y, width, height }` in PDF coordinate space (points from bottom-left).

---

## 6. Image Documents (Non-PDF)

For standalone image files (PNG, JPG, TIFF):

**Process:**
1. MIME type check → confirm image
2. Load with `Pillow` (PIL)
3. Preprocessing: grayscale, threshold, deskew if needed
4. Pass to EasyOCR
5. Produce `DocumentChunk` objects with `page_number = 1`

**Supported formats:** PNG, JPG, JPEG, TIFF, BMP, GIF (first frame only), WebP

---

## 7. Handwritten Documents

ADIP supports handwritten documents with reduced confidence:

| Scenario | Approach | Confidence Cap |
|---------|---------|---------------|
| Handwritten signatures | Detect presence only (is a signature present?) | N/A — boolean flag |
| Handwritten dates | EasyOCR handwriting mode + date regex | 0.65 max |
| Handwritten annotations | EasyOCR handwriting mode | 0.55 max |
| Full handwritten document | EasyOCR + human review always required | 0.45 max |

All handwritten content always routes to Human Review Queue regardless of confidence score.

---

## 8. Visual Content (Non-Text)

For documents containing diagrams, charts, or photos:

| Content Type | ADIP Action |
|-------------|------------|
| Diagram/flowchart | Extract any text via OCR; store as image chunk; no semantic analysis in pilot |
| Photograph | Store as image chunk; describe as "contains photograph (no text extracted)" |
| Chart/graph | Extract axis labels and title via OCR; mark as `requires_human_interpretation` |
| Institution logo | Detect presence; use as source credibility signal (+0.03 confidence) |

**Future (Phase 7):** Vision-language models (e.g., LLaVA, GPT-4V) for chart interpretation and diagram description.

---

## 9. Quality Metrics

ADIP tracks OCR quality across documents for monitoring:

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| Average OCR confidence | ≥ 0.82 | < 0.70 |
| Pages requiring human review | ≤ 15% | > 30% |
| Extraction failure rate | ≤ 2% | > 5% |
| Handwritten detection accuracy | ≥ 90% | < 80% |
