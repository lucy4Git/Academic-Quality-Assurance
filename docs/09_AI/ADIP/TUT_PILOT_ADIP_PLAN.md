# ADIP — TUT Pilot Implementation Plan

**Document ID:** ADIP-TUT-001  
**Version:** 1.0.0  
**Status:** Active — Pilot Plan  
**Last Updated:** 2026-06-29

---

## 1. Pilot Scope

The TUT ADIP pilot processes all downloaded TUT official documents to populate IKP v1.1.0 with complete, PDF-extracted data. This is the bridge from the HTML-only IKP v1.0.0 (25 programmes, no APS, no credits confirmed, no modules) to a full IKP v1.1.0 (25 programmes + APS + credits + modules).

---

## 2. Documents in Scope (Phase 5.4G)

### Priority 1 — Already Downloaded, Processing Blocked

| Document | File | Size | Blocked By | ADIP Layer Path |
|----------|------|------|-----------|----------------|
| TUT ICT Prospectus 2026 | `Part6_ICT_Prospectus.pdf` | 1.3 MB | `pdftoppm` not available | PDF native text + table extraction |
| TUT Students' Rules 2026 | `Part1_Students_Rules_and_Regulations.pdf` | 1.3 MB | Same | PDF native text |
| TUT Examination Rules 2024 | `Chapter_4_2024.pdf` | 355 KB | Same | PDF native text |
| TUT Academic Calendar 2026 | `2026-AcademicCore-Calendar.pdf` | 291 KB | Same | PDF tables + date extraction |
| TUT First Year Course Info | `First-Year-Course_Information.pdf` | 2.0 MB | Same | PDF native text + tables |
| TUT General Enrolment Info | `General-Information-First-Year-Enrolment.pdf` | 2.6 MB | Same | PDF native text + tables |

**Current storage location:** `C:\Users\Staff 101\.claude\projects\...\tool-results\`

**Action required:** Copy to `ikp/institutions/tut/2026/v1.0.0/provenance/source-documents/`

### Priority 2 — To Be Downloaded

| Document | URL | Priority | Notes |
|----------|-----|---------|-------|
| Arts and Design Prospectus | `...Part2_Arts-and-Design_Prospectus.pdf` | Medium | Future faculty expansion |
| Economics and Finance Prospectus | `...Part3_Economics-and-Finance_Prospectus.pdf` | Medium | Future |
| FEBE Prospectus | `...Part4_FEBE_Prospectus.pdf` | Medium | Future |
| Humanities Prospectus | `...PART_5_Humanities_Prospectus_-2026.pdf` | Medium | Future |
| Management Sciences Prospectus | `...Part7_Management-Sciences_Prospectus.pdf` | Medium | Future |
| Science Prospectus | `...Part8_Science.pdf` | Medium | Future |
| TSB Prospectus | `...PART_10_TSB_Prospectus_2026.pdf` | Low | Future |

### Priority 3 — Official HTML Pages (Already Verified)

| Page | URL | Status |
|------|-----|--------|
| ICT Faculty | `tut.ac.za/ict/` | ✅ Extracted — in IKP v1.0.0 |
| Computer Science | `tut.ac.za/ict/computer-science/` | ✅ Extracted |
| CSE | `tut.ac.za/ict/computer-systems-engineering/` | ✅ Extracted |
| Informatics | `tut.ac.za/ict/informatics/` | ✅ Extracted |
| Information Technology | `tut.ac.za/ict/information-technology/` | ✅ Extracted |
| About TUT | `tut.ac.za/about/` | ✅ Extracted |
| Campus Visits | `tut.ac.za/campus-visits/` | ✅ Extracted |

---

## 3. Expected Extraction Output from Part6_ICT_Prospectus.pdf

Based on the document's known content (from Phase 5.4B research), ADIP should extract:

### From Tables (camelot lattice mode expected):

| Table Type | Expected Output | IKP Fields Populated |
|-----------|----------------|---------------------|
| Programme listing table | 25 programmes × 5 fields | `programme.nqf_level`, `programme.total_credits` (TUT-specific), `programme.duration_years`, `admission_req.aps_minimum_math`, `admission_req.aps_minimum_math_literacy` |
| Campus allocation table | Programme × campus matrix | `programme.campus_primary`, `programme.campus_additional` |
| Entry requirement table | Subject requirements per programme | `admission_req.english_level`, `admission_req.mathematics_level`, `admission_req.additional_subjects` |
| Module listing tables (per programme) | Module codes, names, credits, NQF | `module.code`, `module.name`, `module.credits`, `module.nqf_level`, `module.semester` |

### From Body Text (pdfminer.six):

| Content Type | Expected | IKP Fields |
|-------------|---------|-----------|
| Faculty description | Dean name, assistant deans | `faculty.dean`, `faculty.assistant_deans` |
| Department descriptions | HOD names, contact details | `department.hod_name`, `department.hod_email` |
| Programme descriptions | Programme overview, objectives | `programme.description` |
| Career pathways sections | Career opportunities per programme | `programme.career_outcomes` |
| Contact information | Admin staff contacts per dept | `department.admin_contact` |

### Extended Curriculum Programmes

The official HTML pages do not confirm Extended Curriculum variants. ADIP should search Part6 for:
- "Extended Curriculum" text → confirm existence per department
- APS values 3 below standard → confirm ECP APS

---

## 4. ADIP Configuration for TUT

TUT-specific ADIP configuration (to be stored in `ikp/institutions/tut/2026/v1.0.0/adip-config.json`):

```json
{
  "institution_code": "TUT",
  "academic_year": "2026",
  "official_domains": ["tut.ac.za", "tsb.ac.za", "online.tut.ac.za"],
  "programme_code_patterns": ["[A-Z]{2,4}-[A-Z]{2,6}"],
  "module_code_patterns": ["[A-Z]{2,4}[0-9]{3}"],
  "nqf_level_patterns": ["NQF\\s+[Ll]evel\\s+(\\d)", "NQF:\\s*(\\d)"],
  "credit_patterns": ["(\\d{2,3})\\s+credits", "[Cc]redits?:\\s*(\\d{2,3})"],
  "aps_table_headers": {
    "math_variants": ["APS (Math)", "APS Mathematics", "Min APS (Maths)", "APS with Maths"],
    "mathlit_variants": ["APS (ML)", "APS Mathematical Literacy", "Min APS (ML)", "APS with Math Lit"]
  },
  "known_faculty_abbreviations": {
    "ICT": "Faculty of Information and Communication Technology",
    "FEBE": "Faculty of Engineering and the Built Environment",
    "FHS": "Faculty of Health Sciences",
    "FAH": "Faculty of Arts and Humanities",
    "FBM": "Faculty of Business and Management"
  },
  "campus_name_normalisation": {
    "Sosh South": "Soshanguve South",
    "Soshanguve": "Soshanguve South",
    "eMalahleni": "eMalahleni",
    "Witbank": "eMalahleni"
  },
  "documents": {
    "Part6_ICT_Prospectus.pdf": {
      "pre_classified_as": "PROSPECTUS_FACULTY",
      "faculty_scope": "ICT",
      "expected_tables": ["programme_listing", "module_listing", "admission_requirements"]
    },
    "Part1_Students_Rules_and_Regulations.pdf": {
      "pre_classified_as": "REGULATIONS_STUDENT",
      "ikp_layer_target": "layer_6_institutional_policy"
    },
    "Chapter_4_2024.pdf": {
      "pre_classified_as": "POLICY_EXAMINATION",
      "ikp_layer_target": "layer_4_qa_policy"
    },
    "2026-AcademicCore-Calendar.pdf": {
      "pre_classified_as": "ACADEMIC_CALENDAR",
      "ikp_layer_target": "layer_6_institutional_policy"
    }
  }
}
```

---

## 5. Confidence Expectations per Document

| Document | Expected Avg Confidence | Key Fields |
|----------|------------------------|-----------|
| Part6_ICT_Prospectus.pdf (tables) | 0.88–0.94 | APS, credits, campus |
| Part6_ICT_Prospectus.pdf (text) | 0.90–0.96 | Programme names, NQF levels |
| Part1_Students_Rules (text) | 0.88–0.93 | Pass mark, assessment rules |
| Chapter_4 Exam Rules (text) | 0.88–0.93 | Examination procedures |
| Academic Calendar (tables) | 0.85–0.93 | Dates, events |
| HTML pages (already done) | 0.96–0.99 | Already in IKP v1.0.0 |

---

## 6. IKP Version Progression

```
IKP v1.0.0 (HTML only — current)
  ├── 1 institution
  ├── 3 campuses
  ├── 1 faculty
  ├── 4 departments
  ├── 25 programmes (name + NQF only)
  └── 0 modules

↓ After ADIP Phase 5.4G extraction

IKP v1.1.0 (HTML + PDF)
  ├── 1 institution (confirmed details)
  ├── 3 campuses (confirmed details)
  ├── 1 faculty (confirmed details)
  ├── 4 departments (HODs confirmed)
  ├── 25 programmes (name + NQF + credits confirmed + APS confirmed)
  ├── ~75 modules (3 per programme × 25 = 75 modules if fully extracted)
  ├── Academic calendar dates
  ├── Assessment policy (pass mark, grading)
  └── Examination rules (Chapter 4)
```

---

## 7. Validation Plan

After ADIP extraction, validate key fields against secondary source claims from Phase 5.4B:

| Field | Secondary Claim | Validate Against | Action if Different |
|-------|----------------|-----------------|-------------------|
| APS (CS, standard) | 26 (studychoices) | Part6 PDF extraction | Trust PDF; document discrepancy |
| APS (CSE standard) | 26 (studychoices) | Part6 PDF extraction | Same |
| CSE Adv Diploma credits | 140 (briefly.co.za) | Part6 PDF extraction | CRITICAL: 120 vs 140 — trust PDF |
| Programme duration (Diploma) | 3 years | Part6 PDF extraction | Standard; expect confirmation |
| Extended Curriculum variants | Exist for 4 depts | Part6 PDF extraction | Confirm/reject ECP existence |

All validation results logged in `ikp/institutions/tut/2026/v1.1.0/validation-report.json`.
