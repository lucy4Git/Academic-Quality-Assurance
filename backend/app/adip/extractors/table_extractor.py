"""ADIP Table Extractor.

Extracts structured tables from PDFs using pdfplumber (no system dependencies).
Also extracts tab-formatted curriculum tables that pdfminer treats as plain text.

Strategy:
  1. pdfplumber lattice mode — bordered tables (APS conversion tables, etc.)
  2. Tab-line joined extraction — module curriculum tables in TUT prospectuses
     (these are formatted with \\t separators, not drawn table borders)
"""

from __future__ import annotations

import re
from pathlib import Path

from app.adip.extractors.base import ExtractedTable


# Module code regex: 3-4 uppercase letters + 3 digits + 1 letter
# e.g. ISC216D, AOP216D, DTD117V
MODULE_CODE_RE = re.compile(r"^([A-Z]{2,4}\d{3}[A-Z])$")

# Tab-format module line: CODE\tNAME\t(NQF)\t(CREDITS)
MODULE_TAB_RE = re.compile(
    r"([A-Z]{2,4}\d{3}[A-Z])\t+([^\t\n()]+?)\t+\((\d)\)\t+\((\d+)\)"
)


def join_tab_lines(text: str) -> str:
    """Join lines that end with a tab character (TUT curriculum table format)."""
    return re.sub(r"\t\n", "\t", text)


def flatten_para(text: str) -> str:
    """Join mid-sentence line breaks to form complete sentences.

    Handles cases like:
        'APS of at least 26 (with Mathematics or Technical Mathematics) or 28 (with Mathematical\\n'
        'Literacy)'
    """
    # Join when previous char is a letter and next char is lowercase or open-paren
    text = re.sub(r"([a-zA-Z,;]) *\n([a-z(])", r"\1 \2", text)
    # Join when previous line ends mid-word (letter) and next line starts with uppercase
    text = re.sub(r"([a-zA-Z]) *\n([A-Z])", r"\1 \2", text)
    return text


def extract_tables_pdfplumber(file_path: Path) -> list[ExtractedTable]:
    """Extract bordered tables from a PDF using pdfplumber.

    Suitable for tables with visible grid lines (APS conversion tables, etc.).
    Returns empty list if pdfplumber is not installed.
    """
    try:
        import pdfplumber
    except ImportError:
        return []

    tables: list[ExtractedTable] = []
    table_index = 0

    try:
        with pdfplumber.open(str(file_path)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                raw_tables = page.extract_tables({
                    "vertical_strategy": "lines_strict",
                    "horizontal_strategy": "lines_strict",
                    "snap_tolerance": 5,
                    "join_tolerance": 3,
                })
                if not raw_tables:
                    continue

                for raw_table in raw_tables:
                    if not raw_table or len(raw_table) < 2:
                        continue

                    # Filter out mostly-empty tables
                    non_empty_rows = [
                        r for r in raw_table
                        if any(cell and str(cell).strip() for cell in r)
                    ]
                    if len(non_empty_rows) < 2:
                        continue

                    # Build header + data rows
                    header = [
                        str(cell).strip() if cell else f"Col{i}"
                        for i, cell in enumerate(non_empty_rows[0])
                    ]
                    data_rows: list[dict[str, str]] = []
                    for row in non_empty_rows[1:]:
                        row_dict: dict[str, str] = {}
                        for i, cell in enumerate(row):
                            col_name = header[i] if i < len(header) else f"Col{i}"
                            row_dict[col_name] = str(cell).strip() if cell else ""
                        data_rows.append(row_dict)

                    tables.append(ExtractedTable(
                        page_number=page_num,
                        table_index=table_index,
                        header_row=header,
                        data_rows=data_rows,
                        extraction_method="pdfplumber_lines",
                        accuracy_score=0.90,
                    ))
                    table_index += 1

    except Exception as exc:
        tables.append(ExtractedTable(
            page_number=None,
            table_index=0,
            header_row=[],
            data_rows=[],
            extraction_method="pdfplumber_lines",
            accuracy_score=0.0,
            warnings=[f"pdfplumber error: {exc}"],
        ))

    return tables


def extract_tab_modules(page_text: str, page_number: int, table_index_start: int = 0) -> list[ExtractedTable]:
    """Extract module curriculum tables from tab-formatted PDF text.

    TUT prospectuses lay out module tables as tab-separated text:
        CODE\\tNAME\\t(NQF-L)\\t(CREDITS)

    pdfminer extracts each tab-cell as a separate text box,
    producing lines ending with \\t. After join_tab_lines(), these become
    single parseable lines.
    """
    text = join_tab_lines(page_text)
    matches = MODULE_TAB_RE.findall(text)
    if not matches:
        return []

    rows: list[dict[str, str]] = []
    for code, name, nqf, credits in matches:
        rows.append({
            "code": code.strip(),
            "name": name.strip(),
            "nqf_level": nqf.strip(),
            "credits": credits.strip(),
        })

    if not rows:
        return []

    return [ExtractedTable(
        page_number=page_number,
        table_index=table_index_start,
        header_row=["code", "name", "nqf_level", "credits"],
        data_rows=rows,
        extraction_method="tab_format_modules",
        accuracy_score=0.92,
    )]


def extract_all_tables_from_pdf(file_path: Path) -> list[ExtractedTable]:
    """Combined table extraction: pdfplumber bordered + tab-format modules."""
    try:
        import fitz
    except ImportError:
        return extract_tables_pdfplumber(file_path)

    tables: list[ExtractedTable] = []

    # Pass 1: bordered tables via pdfplumber
    bordered = extract_tables_pdfplumber(file_path)
    tables.extend(bordered)
    table_index = len(tables)

    # Pass 2: tab-format module tables via pymupdf text extraction
    try:
        doc = fitz.open(str(file_path))
        for page_num in range(doc.page_count):
            page_text = doc[page_num].get_text("text")
            tab_tables = extract_tab_modules(page_text, page_num + 1, table_index)
            tables.extend(tab_tables)
            table_index += len(tab_tables)
        doc.close()
    except Exception:
        pass

    return tables
