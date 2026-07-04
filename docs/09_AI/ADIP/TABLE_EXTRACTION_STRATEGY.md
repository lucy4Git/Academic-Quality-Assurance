# ADIP — Table Extraction Strategy

**Document ID:** ADIP-TBL-001  
**Version:** 1.1.0  
**Status:** Implementation Complete (Phase 5.4H)  
**Last Updated:** 2026-07-01

---

## 1. Why Tables Are Critical

The most valuable academic knowledge in TUT prospectuses exists in tables:
- Programme admission tables (APS, subject requirements by programme)
- Qualification progression tables (NQF ladder from HC → Doctorate)
- Module credit tables (module code, name, credits, NQF level per semester)
- Assessment weighting tables (assessment type, weighting, due date)
- Academic calendar tables (date, event, applicable programmes)

Failing to extract tables correctly means failing to extract APS requirements, credit values, and module codes — the core data AQAA needs for qualification intelligence.

---

## 2. Table Detection

### 2.1 PDF Tables — Empirical Findings (Phase 5.4H)

> **Important:** The original design assumed TUT prospectus tables are bordered PDF tables. Phase 5.4H implementation revealed this is **not the case**. TUT curriculum tables are tab-separated text, not bordered tables. The findings below reflect what was actually observed and implemented.

**Finding: TUT prospectus tables are tab-separated text**

The TUT ICT Prospectus (`Part6_ICT_Prospectus.pdf`) contains two kinds of tabular data:

1. **1 real bordered table** — the APS conversion table on page 4, extractable via pdfplumber lattice mode with `accuracy_score=0.98`
2. **~106 curriculum module tables** — NOT bordered. Each is a block of tab-separated lines where every cell ends with `\t\n`. Standard PDF table extractors (pdfplumber lattice/stream, camelot) cannot find these.

**Implementation (Phase 5.4H actual):**

```python
# backend/app/adip/extractors/table_extractor.py

MODULE_TAB_RE = re.compile(
    r"([A-Z]{2,4}\d{3}[A-Z])\t+([^\t\n()]+?)\t+\((\d)\)\t+\((\d+)\)"
)

def join_tab_lines(text: str) -> str:
    """Join lines ending with \\t\\n (TUT curriculum table format)."""
    return re.sub(r"\t\n", "\t", text)

def extract_tab_modules(page_text: str, page_number: int, ...) -> list[ExtractedTable]:
    """Extract module rows from tab-formatted text via MODULE_TAB_RE."""
    joined = join_tab_lines(page_text)
    for match in MODULE_TAB_RE.finditer(joined):
        code, name, nqf, credits = match.groups()
        # emit ExtractedTable(header_row=[...], data_rows=[{...}], accuracy_score=0.88)
```

**Extraction pipeline (hybrid approach):**
1. `extract_tables_pdfplumber()` — pdfplumber `lines_strict` strategy for any real bordered tables
2. `extract_tab_modules()` — pymupdf page text → `join_tab_lines()` → `MODULE_TAB_RE` for curriculum tables
3. `extract_all_tables_from_pdf()` — combines both; de-duplicates by page+index

**Results on Part6_ICT_Prospectus.pdf:**
- Bordered tables found by pdfplumber: 1 (APS conversion table, accuracy=0.98)
- Tab-format module tables found: 106
- Total: 107 tables, 174 unique module codes, 256 total module entries (82 duplicates across semesters)

**pdfplumber accuracy interpretation (for bordered tables):**
| Accuracy | Meaning | Action |
|---------|---------|--------|
| ≥ 90% | Excellent extraction | Accept; confidence 0.93 |
| 80–89% | Good | Accept; confidence 0.88 |
| 70–79% | Acceptable | Accept; flag for spot-check |
| 60–69% | Poor | Try stream mode; flag for review |
| < 60% | Failed | Manual entry queue |

**Tab-format confidence:** Fixed at `0.88` (table structure inferred, not bordered).

**Camelot:** Not currently installed — requires Ghostscript system dependency on Windows. Use pdfplumber for bordered tables and tab-format extraction for curriculum tables. Camelot may be added in a future phase if more complex bordered table layouts are encountered in other institutions' documents.

### 2.2 DOCX Tables

`python-docx` provides direct table access:
```python
for table in doc.tables:
    headers = [cell.text.strip() for cell in table.rows[0].cells]
    for row in table.rows[1:]:
        row_data = {headers[i]: cell.text.strip() for i, cell in enumerate(row.cells)}
```

### 2.3 PPTX Tables

`python-pptx` table shape iteration:
```python
for shape in slide.shapes:
    if shape.has_table:
        table = shape.table
        # Extract headers from row 0, data from rows 1+
```

### 2.4 XLSX Tables

`openpyxl` worksheet iteration with header detection:
```python
ws = wb.active
# Detect header row (first non-empty row where all cells are strings)
header_row = next(row for row in ws.iter_rows(values_only=True) 
                  if all(isinstance(c, str) for c in row if c))
```

---

## 3. Header Inference

When table headers are ambiguous or missing:

**Priority order for header resolution:**
1. Explicit header row (first row, different formatting)
2. Preceding paragraph text (e.g., "The following table shows APS requirements:")
3. Known column header patterns per document type (stored in IKP configuration)
4. Fallback: `Column_1`, `Column_2`, ... (flags for human review)

**TUT-specific known header patterns:**
```json
{
  "institution": "TUT",
  "known_table_headers": {
    "PROSPECTUS_FACULTY": {
      "programme_column_variants": ["Programme", "Qualification", "Course Name"],
      "nqf_column_variants": ["NQF Level", "NQF", "Level"],
      "credits_column_variants": ["Credits", "Total Credits", "Min Credits"],
      "aps_math_variants": ["APS (Math)", "APS Mathematics", "Min APS (with Maths)"],
      "aps_mathlit_variants": ["APS (ML)", "APS Mathematical Literacy", "Min APS (with ML)"],
      "campus_variants": ["Campus", "Campus Location", "Offered At"],
      "duration_variants": ["Duration", "Years", "Min Duration"]
    }
  }
}
```

---

## 4. Merged Cell Handling

Merged cells are common in SA prospectus tables (e.g., a faculty name spanning all programme rows):

```
┌─────────────────────────────────────────────┐
│  Faculty of ICT                             │  ← merged cell
├─────────────┬────────────┬──────────────────┤
│ Programme   │ NQF Level  │ Credits          │
├─────────────┼────────────┼──────────────────┤
│ Dip CS      │     6      │ 360              │
│ Adv Dip CS  │     7      │ 120              │
```

**ADIP handling:**
- Merged cells are detected by camelot and `python-docx`
- Vertical merges (spanning rows): value propagated to all rows in the merge group
- Horizontal merges (spanning columns): value assigned to leftmost column; other columns marked `merged_from_left`
- Resulting rows always have same column count as header

---

## 5. Table Output Format

Every extracted table produces a `DocumentTable` record:

```json
{
  "id": "UUID",
  "document_id": "UUID",
  "institution_id": "UUID",
  "page_number": 15,
  "table_index": 2,
  "extraction_method": "camelot_lattice",
  "accuracy_score": 0.93,
  "header_row": ["Programme", "NQF Level", "Credits", "APS (Math)", "APS (ML)", "Campus"],
  "data_rows": [
    {
      "Programme": "Diploma in Computer Science",
      "NQF Level": "6",
      "Credits": "360",
      "APS (Math)": "26",
      "APS (ML)": "28",
      "Campus": "Soshanguve South, eMalahleni, Polokwane"
    },
    {
      "Programme": "Advanced Diploma in Computer Science",
      "NQF Level": "7",
      "Credits": "120",
      "APS (Math)": "—",
      "APS (ML)": "—",
      "Campus": "Soshanguve South"
    }
  ],
  "merged_cells_detected": 0,
  "warnings": [],
  "knowledge_mapping_candidates": 12
}
```

---

## 6. Academic Calendar Table Extraction

Academic calendars have special table structures (date grids):

```
Event                              Date Range              Applies To
Senior students registration       3–14 February 2026      All campuses
First year orientation             16–18 February 2026     All campuses
Teaching commences (Sem 1)         19 February 2026        All campuses
```

**Date extraction strategy:**
1. Identify date patterns: `DD Month YYYY`, `DD/MM/YYYY`, `Month DD, YYYY`
2. Normalise to ISO 8601: `2026-02-19`
3. Map event descriptions to `AcademicCalendar` IKP fields
4. Flag events with ambiguous dates for human review

---

## 7. Table Quality Metrics

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| Table detection rate (pages with tables) | ≥ 95% | < 85% |
| Header identification accuracy | ≥ 90% | < 80% |
| Cell extraction accuracy (spot-check) | ≥ 92% | < 85% |
| Merged cell handling accuracy | ≥ 85% | < 75% |
| Camelot accuracy score (average) | ≥ 85% | < 75% |
