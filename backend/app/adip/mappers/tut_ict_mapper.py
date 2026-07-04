"""TUT ICT Faculty knowledge mapper.

Extracts structured academic data from TUT ICT Prospectus PDFs:
  - All 28 programme entries (22 unique qualifications + Master/Doctor listed per dept)
  - NQF levels and credit values
  - Qualification codes (SAQA codes)
  - APS requirements (Mathematics and Mathematical Literacy)
  - Campus offerings
  - Module codes, names, NQF levels, and credit values

Two extraction modes:
  1. pdf_path mode (preferred): reads PDF directly with pymupdf for highest fidelity
  2. chunk mode (fallback): uses pre-extracted ExtractionResult chunks

The PDF mode is used when the pipeline provides the source file path.
The chunk mode is retained for testing without a real PDF.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from app.adip.extractors.base import ExtractedChunk, ExtractedTable, ExtractionResult
from app.adip.extractors.table_extractor import join_tab_lines, flatten_para, MODULE_TAB_RE
from app.adip.validators.confidence import calculate_confidence, gate_status

# ── Programme catalogue ─────────────────────────────────────────────────────

# Canonical names for all 28 TUT ICT programme entries.
# Master / Doctor appear once per department but share qual codes.
KNOWN_ICT_PROGRAMMES: set[str] = {
    "Diploma in Computer Science",
    "Diploma in Computer Science (Extended Curriculum)",
    "Advanced Diploma in Computer Science",
    "Postgraduate Diploma in Computer Science",
    "Diploma in Multimedia Computing",
    "Diploma in Multimedia Computing (Extended Curriculum)",
    "Advanced Diploma in Multimedia Computing",
    "Postgraduate Diploma in Multimedia Computing",
    "Master of Computing",
    "Doctor of Computing",
    "Diploma in Computer Systems Engineering",
    "Diploma in Computer Systems Engineering (Extended Curriculum)",
    "Advanced Diploma in Computer Systems Engineering",
    "Postgraduate Diploma in Computer Systems Engineering",
    "Diploma in Informatics",
    "Diploma in Informatics (Extended Curriculum)",
    "Advanced Diploma in Informatics",
    "Postgraduate Diploma in Informatics",
    "Diploma in Information Technology",
    "Diploma in Information Technology (Extended Curriculum)",
    "Advanced Diploma in Information Technology",
    "Postgraduate Diploma in Information Technology",
}

ICT_DEPARTMENTS: set[str] = {
    "Computer Science",
    "Computer Systems Engineering",
    "Informatics",
    "Information Technology",
    "Multimedia Computing",
}

TUT_CAMPUSES: dict[str, str] = {
    "soshanguve south": "Soshanguve South",
    "soshanguve north": "Soshanguve North",
    "soshanguve": "Soshanguve South",
    "emahleni": "eMalahleni",
    "emalahleni": "eMalahleni",
    "witbank": "eMalahleni",
    "polokwane": "Polokwane",
    "pretoria": "Pretoria",
    "arcadia": "Pretoria",
    "ga-rankuwa": "Ga-Rankuwa",
    "ga rankuwa": "Ga-Rankuwa",
    "mbombela": "Mbombela",
    "nelspruit": "Mbombela",
}

# Section headings that indicate a new programme section on a DETAIL page.
# Used to distinguish programme names from extended/mixed content on the same page.
_SECTION_HEADING_RE = re.compile(
    r"^(\d+\.\d+)\s+(.+?)$",
    re.M,
)

# Qualification code on detail pages (not in TOC).
_QUAL_CODE_RE = re.compile(r"Qualification code[:\s]+([A-Z]{2,6}\d{2,})", re.I)

# NQF level + credits in programme header line.
_NQF_CREDITS_RE = re.compile(
    r"NQF\s*Level\s*(\d{1,2})\s*\((\d{2,3})\s*credits?\)",
    re.I,
)

# Campus line following "Campus where offered:".
_CAMPUS_OFFERED_RE = re.compile(
    r"Campus(?:es)? where offered[:\s]*\n?(.+?)(?:\nREMARKS|\na\.|\nb\.|\n\n)",
    re.I | re.S,
)

# APS requirements — explicit patterns on full flattened text.
# The TUT prospectus format is:
#   "(APS) of at least 26 (with Mathematics or Technical Mathematics) or 28 (with Mathematical Literacy)"
# The (APS) is written in parens in the PDF; we accept both parenthesized and bare forms.
# Note: ML value follows "or N" not "at least N", hence separate patterns.
# The extended programme threshold uses "score of N" not "at least N" — excluded by these patterns.
_APS_MATH_RE = re.compile(
    r"\(?APS\)?\s+of\s+at\s+least\s+(\d+)\s*\(with (?:Technical\s+)?Mathematics\b[^)]*\)",
    re.I,
)
_APS_ML_RE = re.compile(
    r"\bor\s+(\d+)\s*\(with Mathematical\s*Literacy\)",
    re.I,
)

# Extended curriculum detection.
_EXTENDED_RE = re.compile(r"extended\s+curriculum", re.I)

# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass
class ExtractionCandidateData:
    """Data for one proposed IKP field value — not yet persisted."""

    document_id: str
    institution_id: str
    ikp_entity_type: str
    ikp_entity_key: str
    ikp_field_name: str
    raw_value: str
    coerced_value: str | None
    value_type: str
    extraction_method: str
    source_verbatim: str | None
    source_page: int | None
    confidence: float
    status: str
    chunk_id: str | None = None
    provenance_extra: dict = field(default_factory=dict)


@dataclass
class ProgrammeRecord:
    """Intermediate record assembled during PDF extraction."""

    section_num: str
    title: str
    page: int
    qual_code: str | None = None
    nqf_level: str | None = None
    credits: str | None = None
    campus: str | None = None
    aps_math: str | None = None
    aps_ml: str | None = None
    is_extended: bool = False
    modules: list[dict] = field(default_factory=list)


# ── Mapper class ─────────────────────────────────────────────────────────────


class TUTICTMapper:
    """Maps extracted TUT ICT content to IKP entity candidates."""

    INSTITUTION_CODE = "TUT"
    FACULTY_NAME = "Faculty of Information and Communication Technology"

    def __init__(self, document_id: str, institution_id: str, source_type: str = "official_pdf"):
        self.document_id = document_id
        self.institution_id = institution_id
        self.source_type = source_type
        self._candidates: list[ExtractionCandidateData] = []

    def map(
        self,
        extraction: ExtractionResult,
        pdf_path: Path | None = None,
    ) -> list[ExtractionCandidateData]:
        """Run all mapping passes on an extraction result.

        If pdf_path is provided, enhanced PDF-direct extraction is used.
        Chunk-based extraction is used as fallback.
        """
        self._candidates = []

        if pdf_path and pdf_path.exists():
            self._map_from_pdf(pdf_path)
        else:
            self._map_chunks(extraction.useful_chunks)
            self._map_tables(extraction.tables)

        return self._candidates

    # ── PDF-direct extraction (preferred) ───────────────────────────────────

    def _map_from_pdf(self, pdf_path: Path) -> None:
        """Extract structured data directly from PDF using pymupdf."""
        try:
            import fitz
        except ImportError:
            # Fallback: use pre-extracted chunks
            return

        doc = fitz.open(str(pdf_path))
        pages: list[tuple[int, str]] = []
        for page_num in range(doc.page_count):
            raw = doc[page_num].get_text("text")
            joined = join_tab_lines(raw)
            pages.append((page_num + 1, joined))
        doc.close()

        programmes = self._find_programme_sections(pages)
        for prog in programmes:
            self._emit_programme_candidates(prog)

    def _find_programme_sections(self, pages: list[tuple[int, str]]) -> list[ProgrammeRecord]:
        """Identify programme sections and extract their data.

        A programme section is anchored by 'Qualification code: XXXX' on a detail page.
        For extended curriculum programmes (no separate qual code), the section is anchored
        by the 'Extended curriculum' heading on its detail page.
        """
        records: list[ProgrammeRecord] = []
        n = len(pages)

        for i, (page_num, text) in enumerate(pages):
            qual_code_match = _QUAL_CODE_RE.search(text)
            has_extended = bool(_EXTENDED_RE.search(text))
            nqf_match = _NQF_CREDITS_RE.search(text)

            if not qual_code_match and not (has_extended and nqf_match):
                continue

            # Find programme heading on this page or previous page
            is_extended_section = has_extended and not bool(qual_code_match)
            title, section_num = self._find_title(text, pages, i, is_extended=is_extended_section)
            if not title:
                continue

            # Gather context text: this page + next 5 pages
            context_pages = pages[i: min(i + 6, n)]
            context_text = "\n".join(t for _, t in context_pages)
            flat_context = flatten_para(context_text)

            # NQF + credits
            nqf_m = _NQF_CREDITS_RE.search(context_text)
            nqf_level = nqf_m.group(1) if nqf_m else None
            credits = nqf_m.group(2) if nqf_m else None

            # Qual code
            qc = qual_code_match.group(1) if qual_code_match else None

            # Campus
            campus = self._extract_campus(context_text)

            # APS
            aps_math = self._extract_aps_math(flat_context)
            aps_ml = self._extract_aps_ml(flat_context)

            # Modules: gather from this page to next anchor (up to 12 pages ahead)
            next_anchor = self._find_next_qual_code_page(pages, i + 1)
            module_pages = pages[i: min(next_anchor, i + 12, n)]
            modules = self._extract_modules_from_pages(module_pages)

            records.append(ProgrammeRecord(
                section_num=section_num or "",
                title=title,
                page=page_num,
                qual_code=qc,
                nqf_level=nqf_level,
                credits=credits,
                campus=campus,
                aps_math=aps_math,
                aps_ml=aps_ml,
                is_extended=has_extended and not bool(qual_code_match),
                modules=modules,
            ))

        return records

    def _find_title(
        self,
        page_text: str,
        pages: list[tuple[int, str]],
        page_idx: int,
        is_extended: bool = False,
    ) -> tuple[str | None, str | None]:
        """Find the programme title heading on this or the previous page."""
        # Look in current page first, then the previous page
        search_texts = [page_text]
        if page_idx > 0:
            search_texts.append(pages[page_idx - 1][1])

        for text in search_texts:
            for match in _SECTION_HEADING_RE.finditer(text):
                sec_num = match.group(1)
                raw_title = match.group(2).strip()
                # Skip TOC entries (they have trailing dots or ellipsis)
                if raw_title.count(".") > 3:
                    continue
                kws = ["DIPLOMA", "DEGREE", "CERTIFICATE", "BACHELOR", "ADVANCED",
                       "POSTGRADUATE", "MASTER", "DOCTOR"]
                if any(kw in raw_title.upper() for kw in kws):
                    title = self._canonicalise_title(raw_title)
                    # Extended curriculum programmes get a disambiguating suffix
                    if is_extended and "(Extended" not in title:
                        title = title + " (Extended Curriculum)"
                    return title, sec_num
        return None, None

    def _canonicalise_title(self, raw: str) -> str:
        """Convert uppercase section title to title case."""
        # Strip any trailing dots / whitespace from TOC-style headings
        raw = re.sub(r"\.{3,}.*$", "", raw).strip()
        # Trim any parenthetical if it spans beyond a reasonable length
        raw = re.sub(r"\s*\(Extended curriculum programme.*?\)", "", raw, flags=re.I)
        return raw.title()

    def _extract_campus(self, text: str) -> str | None:
        m = _CAMPUS_OFFERED_RE.search(text)
        if not m:
            return None
        campus_raw = m.group(1).replace("\n", " ").strip()
        # Normalise known campus names
        for key, canonical in TUT_CAMPUSES.items():
            if key in campus_raw.lower():
                return canonical
        return campus_raw[:120]  # cap length

    def _extract_aps_math(self, flat_text: str) -> str | None:
        m = _APS_MATH_RE.search(flat_text)
        if m:
            return m.group(1)
        return None

    def _extract_aps_ml(self, flat_text: str) -> str | None:
        m = _APS_ML_RE.search(flat_text)
        if m:
            return m.group(1)
        return None

    def _find_next_qual_code_page(self, pages: list[tuple[int, str]], start_idx: int) -> int:
        """Return page index of the next qualification code anchor."""
        for i in range(start_idx, len(pages)):
            if _QUAL_CODE_RE.search(pages[i][1]):
                return i
        return len(pages)

    def _extract_modules_from_pages(
        self,
        pages: list[tuple[int, str]],
    ) -> list[dict]:
        """Extract module entries from tab-formatted curriculum tables."""
        modules: list[dict] = []
        seen_codes: set[str] = set()
        for page_num, text in pages:
            for code, name, nqf, credits in MODULE_TAB_RE.findall(text):
                code = code.strip()
                if code in seen_codes:
                    continue
                seen_codes.add(code)
                modules.append({
                    "code": code,
                    "name": name.strip(),
                    "nqf_level": nqf.strip(),
                    "credits": credits.strip(),
                    "page": page_num,
                })
        return modules

    # ── Candidate emission ───────────────────────────────────────────────────

    def _emit_programme_candidates(self, prog: ProgrammeRecord) -> None:
        """Convert a ProgrammeRecord into ExtractionCandidateData entries."""
        entity_key = prog.title
        base_conf = calculate_confidence(
            source_type=self.source_type,
            extraction_method="regex_clean_text",
            position_clarity="explicit_label",
        )
        high_conf = calculate_confidence(
            source_type=self.source_type,
            extraction_method="verbatim_match",
            position_clarity="explicit_label",
        )

        # Programme name
        self._add(
            ikp_entity_type="programme",
            ikp_entity_key=entity_key,
            ikp_field_name="name",
            raw_value=prog.title,
            coerced_value=prog.title,
            value_type="string",
            verbatim=prog.title,
            page=prog.page,
            conf=high_conf.final_score,
            method="section_heading_match",
        )

        # Qualification code
        if prog.qual_code:
            self._add(
                ikp_entity_type="programme",
                ikp_entity_key=entity_key,
                ikp_field_name="qualification_code",
                raw_value=prog.qual_code,
                coerced_value=prog.qual_code,
                value_type="string",
                verbatim=f"Qualification code: {prog.qual_code}",
                page=prog.page,
                conf=high_conf.final_score,
                method="qual_code_extraction",
            )

        # NQF level
        if prog.nqf_level:
            self._add(
                ikp_entity_type="programme",
                ikp_entity_key=entity_key,
                ikp_field_name="nqf_level",
                raw_value=prog.nqf_level,
                coerced_value=prog.nqf_level,
                value_type="integer",
                verbatim=f"NQF Level {prog.nqf_level} ({prog.credits} credits)",
                page=prog.page,
                conf=high_conf.final_score,
                method="nqf_credits_pattern",
            )

        # Credits
        if prog.credits:
            self._add(
                ikp_entity_type="programme",
                ikp_entity_key=entity_key,
                ikp_field_name="total_credits",
                raw_value=prog.credits,
                coerced_value=prog.credits,
                value_type="integer",
                verbatim=f"NQF Level {prog.nqf_level} ({prog.credits} credits)",
                page=prog.page,
                conf=high_conf.final_score,
                method="nqf_credits_pattern",
            )

        # Campus
        if prog.campus:
            self._add(
                ikp_entity_type="programme",
                ikp_entity_key=entity_key,
                ikp_field_name="campus_primary",
                raw_value=prog.campus,
                coerced_value=prog.campus,
                value_type="string",
                verbatim=f"Campus where offered: {prog.campus}",
                page=prog.page,
                conf=base_conf.final_score,
                method="campus_extraction",
            )

        # APS requirements
        if prog.aps_math:
            self._add(
                ikp_entity_type="admission_requirement",
                ikp_entity_key=entity_key,
                ikp_field_name="aps_minimum_math",
                raw_value=prog.aps_math,
                coerced_value=prog.aps_math,
                value_type="integer",
                verbatim=f"APS of at least {prog.aps_math} (with Mathematics or Technical Mathematics)",
                page=prog.page,
                conf=base_conf.final_score,
                method="aps_math_pattern",
            )

        if prog.aps_ml:
            self._add(
                ikp_entity_type="admission_requirement",
                ikp_entity_key=entity_key,
                ikp_field_name="aps_minimum_math_literacy",
                raw_value=prog.aps_ml,
                coerced_value=prog.aps_ml,
                value_type="integer",
                verbatim=f"or {prog.aps_ml} (with Mathematical Literacy)",
                page=prog.page,
                conf=base_conf.final_score,
                method="aps_ml_pattern",
            )

        # Extended curriculum flag
        if prog.is_extended:
            self._add(
                ikp_entity_type="programme",
                ikp_entity_key=entity_key,
                ikp_field_name="has_extended_curriculum",
                raw_value="true",
                coerced_value="true",
                value_type="boolean",
                verbatim="Extended curriculum programme with foundation provision",
                page=prog.page,
                conf=base_conf.final_score,
                method="extended_curriculum_detection",
            )

        # Modules
        module_conf = calculate_confidence(
            source_type=self.source_type,
            extraction_method="table_cell_identified",
            position_clarity="column_header",
        )
        for mod in prog.modules:
            mod_key = mod["code"]

            self._add(
                ikp_entity_type="module",
                ikp_entity_key=mod_key,
                ikp_field_name="code",
                raw_value=mod["code"],
                coerced_value=mod["code"],
                value_type="string",
                verbatim=f"{mod['code']} {mod['name']}",
                page=mod["page"],
                conf=module_conf.final_score,
                method="tab_format_modules",
            )
            self._add(
                ikp_entity_type="module",
                ikp_entity_key=mod_key,
                ikp_field_name="name",
                raw_value=mod["name"],
                coerced_value=mod["name"],
                value_type="string",
                verbatim=f"{mod['code']} {mod['name']} ({mod['nqf_level']}) ({mod['credits']})",
                page=mod["page"],
                conf=module_conf.final_score,
                method="tab_format_modules",
            )
            self._add(
                ikp_entity_type="module",
                ikp_entity_key=mod_key,
                ikp_field_name="nqf_level",
                raw_value=mod["nqf_level"],
                coerced_value=mod["nqf_level"],
                value_type="integer",
                verbatim=f"({mod['nqf_level']})",
                page=mod["page"],
                conf=module_conf.final_score,
                method="tab_format_modules",
            )
            self._add(
                ikp_entity_type="module",
                ikp_entity_key=mod_key,
                ikp_field_name="credits",
                raw_value=mod["credits"],
                coerced_value=mod["credits"],
                value_type="integer",
                verbatim=f"({mod['credits']})",
                page=mod["page"],
                conf=module_conf.final_score,
                method="tab_format_modules",
            )

    # ── Chunk-based fallback ─────────────────────────────────────────────────

    def _map_chunks(self, chunks: list[ExtractedChunk]) -> None:
        for chunk in chunks:
            text = chunk.text.strip()
            if len(text) < 5:
                continue
            self._extract_nqf_from_text(text, chunk)
            self._extract_credits_from_text(text, chunk)
            self._extract_aps_from_text(text, chunk)
            self._extract_programme_name(text, chunk)

    def _extract_nqf_from_text(self, text: str, chunk: ExtractedChunk) -> None:
        m = _NQF_CREDITS_RE.search(text)
        if not m:
            return
        nqf_val = m.group(1)
        if not 1 <= int(nqf_val) <= 10:
            return
        prog_key = self._match_programme_name(" ".join(chunk.section_path) + " " + text)
        if not prog_key:
            return
        conf = calculate_confidence(self.source_type, "regex_clean_text", "explicit_label")
        self._add("programme", prog_key, "nqf_level", nqf_val, nqf_val, "integer",
                  text[:200], chunk.page_number, conf.final_score, "regex_nqf_pattern")

    def _extract_credits_from_text(self, text: str, chunk: ExtractedChunk) -> None:
        m = _NQF_CREDITS_RE.search(text)
        if not m:
            return
        credits_val = m.group(2)
        prog_key = self._match_programme_name(" ".join(chunk.section_path) + " " + text)
        if not prog_key:
            return
        conf = calculate_confidence(self.source_type, "regex_clean_text", "explicit_label")
        self._add("programme", prog_key, "total_credits", credits_val, credits_val, "integer",
                  text[:200], chunk.page_number, conf.final_score, "regex_credits_pattern")

    def _extract_aps_from_text(self, text: str, chunk: ExtractedChunk) -> None:
        flat = flatten_para(text)
        prog_key = self._match_programme_name(" ".join(chunk.section_path) + " " + text)
        if not prog_key:
            return
        conf = calculate_confidence(self.source_type, "regex_clean_text", "contextual_label")
        m_math = _APS_MATH_RE.search(flat)
        if m_math:
            self._add("admission_requirement", prog_key, "aps_minimum_math",
                      m_math.group(1), m_math.group(1), "integer",
                      flat[:200], chunk.page_number, conf.final_score, "regex_aps_pattern")
        m_ml = _APS_ML_RE.search(flat)
        if m_ml:
            self._add("admission_requirement", prog_key, "aps_minimum_math_literacy",
                      m_ml.group(1), m_ml.group(1), "integer",
                      flat[:200], chunk.page_number, conf.final_score, "regex_aps_ml_pattern")

    def _extract_programme_name(self, text: str, chunk: ExtractedChunk) -> None:
        matched = self._match_programme_name(text)
        if not matched:
            return
        conf = calculate_confidence(self.source_type, "verbatim_match", "explicit_label")
        self._add("programme", matched, "name", matched, matched, "string",
                  text[:200], chunk.page_number, conf.final_score, "known_name_match")

    # ── Table mapping ────────────────────────────────────────────────────────

    def _map_tables(self, tables: list[ExtractedTable]) -> None:
        for table in tables:
            if table.extraction_method == "tab_format_modules":
                self._map_module_table(table)
            else:
                header_lower = {h.lower().strip(): h for h in table.header_row}
                self._map_programme_table(table, header_lower)

    def _map_module_table(self, table: ExtractedTable) -> None:
        module_conf = calculate_confidence(
            source_type=self.source_type,
            extraction_method="table_cell_identified",
            position_clarity="column_header",
        )
        for row in table.data_rows:
            code = row.get("code", "").strip()
            name = row.get("name", "").strip()
            nqf = row.get("nqf_level", "").strip()
            credits = row.get("credits", "").strip()
            if not code:
                continue
            self._add("module", code, "code", code, code, "string",
                      f"{code} {name}", table.page_number, module_conf.final_score, "tab_format_modules")
            if name:
                self._add("module", code, "name", name, name, "string",
                          f"{code} {name}", table.page_number, module_conf.final_score, "tab_format_modules")
            if nqf:
                self._add("module", code, "nqf_level", nqf, nqf, "integer",
                          f"({nqf})", table.page_number, module_conf.final_score, "tab_format_modules")
            if credits:
                self._add("module", code, "credits", credits, credits, "integer",
                          f"({credits})", table.page_number, module_conf.final_score, "tab_format_modules")

    def _map_programme_table(self, table: ExtractedTable, header_lower: dict) -> None:
        programme_col = next((v for k, v in header_lower.items()
                              if "programme" in k or "qualification" in k), None)
        nqf_col = next((v for k, v in header_lower.items() if "nqf" in k), None)
        credit_col = next((v for k, v in header_lower.items() if "credit" in k), None)
        aps_math_col = next((v for k, v in header_lower.items()
                             if "aps" in k and "math" in k and "lit" not in k and "acy" not in k), None)
        aps_ml_col = next((v for k, v in header_lower.items()
                           if "aps" in k and ("lit" in k or "ml" in k)), None)
        campus_col = next((v for k, v in header_lower.items() if "campus" in k), None)

        if not programme_col:
            return

        conf_base = calculate_confidence(
            source_type=self.source_type,
            extraction_method="table_cell_identified",
            position_clarity="column_header",
        )
        for row in table.data_rows:
            prog_name = row.get(programme_col, "").strip()
            if not prog_name:
                continue
            entity_key = self._match_programme_name(prog_name) or prog_name

            if nqf_col and row.get(nqf_col, "").strip():
                nqf_m = re.search(r"\d{1,2}", row[nqf_col])
                if nqf_m:
                    self._add("programme", entity_key, "nqf_level",
                              row[nqf_col].strip(), nqf_m.group(), "integer",
                              str(row), table.page_number, conf_base.final_score, "table_nqf")
            if credit_col and row.get(credit_col, "").strip():
                cr_m = re.search(r"\d{2,3}", row[credit_col])
                if cr_m:
                    self._add("programme", entity_key, "total_credits",
                              row[credit_col].strip(), cr_m.group(), "integer",
                              str(row), table.page_number, conf_base.final_score, "table_credits")
            if aps_math_col and row.get(aps_math_col, "").strip():
                aps_m = re.search(r"\d{2}", row[aps_math_col])
                if aps_m:
                    self._add("admission_requirement", entity_key, "aps_minimum_math",
                              row[aps_math_col].strip(), aps_m.group(), "integer",
                              str(row), table.page_number, conf_base.final_score, "table_aps_math")
            if aps_ml_col and row.get(aps_ml_col, "").strip():
                aps_ml_m = re.search(r"\d{2}", row[aps_ml_col])
                if aps_ml_m:
                    self._add("admission_requirement", entity_key, "aps_minimum_math_literacy",
                              row[aps_ml_col].strip(), aps_ml_m.group(), "integer",
                              str(row), table.page_number, conf_base.final_score * 0.95, "table_aps_ml")
            if campus_col and row.get(campus_col, "").strip():
                campus_raw = row[campus_col].strip()
                self._add("programme", entity_key, "campus_primary",
                          campus_raw, self._normalise_campus(campus_raw), "string",
                          str(row), table.page_number, conf_base.final_score * 0.92, "table_campus")

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _match_programme_name(self, text: str) -> str | None:
        for prog in KNOWN_ICT_PROGRAMMES:
            if prog.lower() in text.lower():
                return prog
        return None

    def _normalise_campus(self, raw: str) -> str:
        raw_lower = raw.lower().strip()
        for k, v in TUT_CAMPUSES.items():
            if k in raw_lower:
                return v
        return raw.title()

    def _add(
        self,
        ikp_entity_type: str,
        ikp_entity_key: str,
        ikp_field_name: str,
        raw_value: str,
        coerced_value: str | None,
        value_type: str,
        verbatim: str | None,
        page: int | None,
        conf: float,
        method: str,
    ) -> None:
        self._candidates.append(ExtractionCandidateData(
            document_id=self.document_id,
            institution_id=self.institution_id,
            ikp_entity_type=ikp_entity_type,
            ikp_entity_key=ikp_entity_key,
            ikp_field_name=ikp_field_name,
            raw_value=raw_value,
            coerced_value=coerced_value,
            value_type=value_type,
            extraction_method=method,
            source_verbatim=verbatim,
            source_page=page,
            confidence=round(conf, 4),
            status=gate_status(conf),
        ))
