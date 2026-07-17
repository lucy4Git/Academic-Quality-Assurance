"""Intelligent metadata extractor for academic institutional pages.

Extracts structured academic metadata from cleaned page content.
Every field carries: value, confidence, source_text, extraction_method, data_status.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---- regex patterns --------------------------------------------------------

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"(?:\+27|0)[\d\s\-().]{8,14}")
_NQF_RE = re.compile(r"\bnqf\s*level\s*(\d+)\b", re.I)
_CREDITS_RE = re.compile(r"\b(\d{1,3})\s*credits?\b", re.I)
_MODULE_CODE_RE = re.compile(r"\b([A-Z]{2,6}[\s-]?\d{3,4}[A-Z]?)\b")
_POLICY_VERSION_RE = re.compile(
    r"(?:version|revision|rev\.?|v\.?)\s*(\d[\d.]*)", re.I
)
_POLICY_DATE_RE = re.compile(
    r"(?:revised?|approved?|updated?|dated?)\s*:?\s*(\d{1,2}[\s./]\w+[\s./]\d{2,4}|\w+\s+\d{4})",
    re.I,
)
_ACADEMIC_YEAR_RE = re.compile(r"\b(20\d{2})\s*[-/]\s*(20\d{2})\b|\b(20\d{2})\b")
_NQF_QUAL: dict[str, str] = {
    "certificate": "certificate",
    "diploma": "diploma",
    "advanced diploma": "advanced_diploma",
    "bachelor": "bachelor",
    "bachelor of technology": "b_tech",
    "honours": "honours",
    "postgraduate diploma": "pg_diploma",
    "master": "masters",
    "doctor": "doctoral",
    "phd": "doctoral",
}


@dataclass
class ExtractedField:
    value: str
    confidence: float
    source_text: str
    extraction_method: str
    data_status: str = "needs_review"


@dataclass
class ExtractedMetadata:
    institution_names: list[ExtractedField] = field(default_factory=list)
    faculty_names: list[ExtractedField] = field(default_factory=list)
    school_names: list[ExtractedField] = field(default_factory=list)
    department_names: list[ExtractedField] = field(default_factory=list)
    programme_names: list[ExtractedField] = field(default_factory=list)
    qualification_names: list[ExtractedField] = field(default_factory=list)
    module_codes: list[ExtractedField] = field(default_factory=list)
    module_names: list[ExtractedField] = field(default_factory=list)
    nqf_levels: list[ExtractedField] = field(default_factory=list)
    credits: list[ExtractedField] = field(default_factory=list)
    policy_names: list[ExtractedField] = field(default_factory=list)
    policy_versions: list[ExtractedField] = field(default_factory=list)
    academic_years: list[ExtractedField] = field(default_factory=list)
    contact_emails: list[ExtractedField] = field(default_factory=list)
    contact_phones: list[ExtractedField] = field(default_factory=list)
    contact_names: list[ExtractedField] = field(default_factory=list)
    source_links: list[ExtractedField] = field(default_factory=list)
    document_links: list[ExtractedField] = field(default_factory=list)


def _ef(value: str, confidence: float, source_text: str, method: str) -> ExtractedField:
    status = "public_verified" if confidence >= 0.8 else "needs_review"
    return ExtractedField(
        value=value,
        confidence=round(confidence, 3),
        source_text=source_text[:300],
        extraction_method=method,
        data_status=status,
    )


def _find_structure_names(
    text_lines: list[str],
    pattern: re.Pattern,
    label: str,
    confidence: float,
) -> list[ExtractedField]:
    """Extract 'Faculty of X', 'School of X', 'Department of X' etc."""
    results = []
    seen = set()
    for line in text_lines:
        for m in pattern.finditer(line):
            name = m.group(0).strip()
            if name not in seen:
                seen.add(name)
                results.append(_ef(name, confidence, line[:200], f"regex_{label}"))
    return results


def extract_metadata(
    title: str,
    headings: list[str],
    paragraphs: list[str],
    cleaned_text: str,
    document_links: list[dict] | None = None,
    url: str = "",
) -> ExtractedMetadata:
    """Extract structured academic metadata from cleaned page content."""
    meta = ExtractedMetadata()
    all_text_lines = [title] + headings + paragraphs
    full_text = "\n".join(all_text_lines)

    # ---- institution name from title / h1 ----------------------------------
    # Pattern: "Welcome to XYZ University" or "XYZ University of Technology"
    inst_re = re.compile(
        r"(?:university|institute|college|technikon|tut|uct|wits|uj|unisa|nmu|uwc)"
        r"[^.\n]{0,80}",
        re.I,
    )
    for line in all_text_lines[:5]:
        for m in inst_re.finditer(line):
            meta.institution_names.append(_ef(m.group(0).strip(), 0.7, line, "regex_institution"))
            break

    # ---- faculty names -----------------------------------------------------
    fac_re = re.compile(r"Faculty of [A-Z][A-Za-z &,]{3,60}", re.I)
    meta.faculty_names = _find_structure_names(all_text_lines, fac_re, "faculty", 0.85)

    # ---- school names -------------------------------------------------------
    school_re = re.compile(r"School of [A-Z][A-Za-z &,]{3,60}", re.I)
    meta.school_names = _find_structure_names(all_text_lines, school_re, "school", 0.8)

    # ---- department names --------------------------------------------------
    dept_re = re.compile(r"Department of [A-Z][A-Za-z &,]{3,60}", re.I)
    meta.department_names = _find_structure_names(all_text_lines, dept_re, "department", 0.8)

    # ---- programme names ---------------------------------------------------
    prog_re = re.compile(
        r"(?:Bachelor|BTech|BEng|BSc|BA|BCom|Diploma|Advanced Diploma|"
        r"Higher Certificate|Postgraduate Diploma|Master|PhD|Doctor)"
        r"[^.\n]{0,80}",
        re.I,
    )
    seen_prog: set[str] = set()
    for line in all_text_lines:
        for m in prog_re.finditer(line):
            val = m.group(0).strip()
            if val not in seen_prog:
                seen_prog.add(val)
                meta.programme_names.append(_ef(val, 0.75, line[:200], "regex_programme"))
    meta.programme_names = meta.programme_names[:20]

    # ---- qualification names -----------------------------------------------
    seen_qual: set[str] = set()
    for phrase, q_type in _NQF_QUAL.items():
        for m in re.finditer(rf"\b{re.escape(phrase)}\b[^.\n]{{0,60}}", full_text, re.I):
            val = m.group(0).strip()
            if val not in seen_qual:
                seen_qual.add(val)
                meta.qualification_names.append(_ef(val, 0.7, val, f"regex_{q_type}"))
    meta.qualification_names = meta.qualification_names[:20]

    # ---- module codes -------------------------------------------------------
    seen_mc: set[str] = set()
    for m in _MODULE_CODE_RE.finditer(full_text):
        code = m.group(1).strip()
        if code not in seen_mc:
            seen_mc.add(code)
            snippet = full_text[max(0, m.start() - 30):m.end() + 30]
            meta.module_codes.append(_ef(code, 0.8, snippet, "regex_module_code"))
    meta.module_codes = meta.module_codes[:30]

    # ---- NQF levels ---------------------------------------------------------
    seen_nqf: set[str] = set()
    for m in _NQF_RE.finditer(full_text):
        val = m.group(1)
        if val not in seen_nqf and 1 <= int(val) <= 10:
            seen_nqf.add(val)
            snippet = full_text[max(0, m.start() - 20):m.end() + 30]
            meta.nqf_levels.append(_ef(f"NQF {val}", 0.9, snippet, "regex_nqf"))
    meta.nqf_levels = meta.nqf_levels[:10]

    # ---- credits ------------------------------------------------------------
    seen_cr: set[str] = set()
    for m in _CREDITS_RE.finditer(full_text):
        val = m.group(1)
        if val not in seen_cr:
            seen_cr.add(val)
            snippet = full_text[max(0, m.start() - 20):m.end() + 30]
            meta.credits.append(_ef(f"{val} credits", 0.85, snippet, "regex_credits"))
    meta.credits = meta.credits[:10]

    # ---- policy names -------------------------------------------------------
    pol_re = re.compile(r"[A-Z][A-Za-z ]{3,50}Policy\b|Policy on [A-Za-z ]{3,50}", re.I)
    seen_pol: set[str] = set()
    for m in pol_re.finditer(full_text):
        val = m.group(0).strip()
        if val not in seen_pol:
            seen_pol.add(val)
            meta.policy_names.append(_ef(val, 0.75, val, "regex_policy_name"))
    meta.policy_names = meta.policy_names[:10]

    # ---- policy versions ---------------------------------------------------
    for m in _POLICY_VERSION_RE.finditer(full_text):
        val = f"v{m.group(1)}"
        snippet = full_text[max(0, m.start() - 20):m.end() + 30]
        meta.policy_versions.append(_ef(val, 0.8, snippet, "regex_policy_version"))
    meta.policy_versions = meta.policy_versions[:5]

    # ---- academic years ----------------------------------------------------
    seen_yr: set[str] = set()
    for m in _ACADEMIC_YEAR_RE.finditer(full_text):
        if m.group(1) and m.group(2):
            val = f"{m.group(1)}/{m.group(2)}"
        else:
            val = m.group(3) or m.group(0)
        if val not in seen_yr:
            seen_yr.add(val)
            meta.academic_years.append(_ef(val, 0.7, m.group(0), "regex_year"))
    meta.academic_years = meta.academic_years[:5]

    # ---- contact emails ----------------------------------------------------
    seen_em: set[str] = set()
    for m in _EMAIL_RE.finditer(full_text):
        val = m.group(0).lower()
        if val not in seen_em:
            seen_em.add(val)
            snippet = full_text[max(0, m.start() - 30):m.end() + 30]
            meta.contact_emails.append(_ef(val, 0.95, snippet, "regex_email"))
    meta.contact_emails = meta.contact_emails[:20]

    # ---- contact phones ----------------------------------------------------
    seen_ph: set[str] = set()
    for m in _PHONE_RE.finditer(full_text):
        val = re.sub(r"\s+", " ", m.group(0)).strip()
        if val not in seen_ph:
            seen_ph.add(val)
            snippet = full_text[max(0, m.start() - 20):m.end() + 30]
            meta.contact_phones.append(_ef(val, 0.8, snippet, "regex_phone"))
    meta.contact_phones = meta.contact_phones[:20]

    # ---- document links from acquisition pass ------------------------------
    if document_links:
        for link in document_links[:30]:
            meta.document_links.append(
                _ef(link["href"], 0.9, link.get("text", ""), "link_href")
            )

    return meta
