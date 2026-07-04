# AQAA — Product Strategy

**Document ID:** STRAT-001  
**Version:** 1.0.0  
**Status:** Active  
**Last Updated:** 2026-06-29  
**Classification:** Internal — Confidential

---

## 1. Market Positioning

### 1.1 Target Market

**Primary:** South African public universities and universities of technology

| Segment | Institutions | Modules (est.) | Market Need |
|---------|-------------|-----------------|------------|
| Universities of Technology | 6 (TUT, DUT, CPUT, VUT, MUT, WSU) | 1,500–3,000 each | Diploma/BEngTech QA at scale |
| Traditional Universities | 11 (UP, UJ, UCT, Wits, etc.) | 2,000–5,000 each | Research + undergraduate QA |
| Comprehensive Universities | 6 (UNISA, UFS, NWU, etc.) | 3,000–10,000 each | Multi-mode, multi-campus QA |
| TVET Colleges | 50 | 200–500 each | NC(V) and NATED compliance |

**Secondary:** Private higher education institutions (CHE-accredited)  
**Tertiary:** International universities in English-speaking Africa (Zimbabwe, Kenya, Ghana, Nigeria)

### 1.2 Market Problem

South African higher education institutions are legally required to demonstrate continuous quality assurance to CHE and DHET. The current QA process is:

- Manual (paper/email-based)
- Inconsistent (no platform standard)
- Under-resourced (QA teams cannot audit 300+ modules manually)
- Undocumented (no audit trail)
- Reactive (problems found at accreditation visits, not in-year)

**Market readiness signal:** CHE has been tightening evidence requirements in accreditation cycles since 2022. Institutions are under increasing pressure to digitise QA documentation.

---

## 2. Competitor Overview

### 2.1 Competitive Landscape

| Competitor | Type | Strength | Weakness vs AQAA |
|-----------|------|---------|-----------------|
| Manual spreadsheets | Current state | Familiar, free | No automation, no audit trail, no AI |
| Generic LMS (Moodle, Blackboard) | Learning platforms | Wide adoption | Not purpose-built for QA; no CHE alignment |
| UK-based QA systems (Quartz, ARC) | International | Mature product | Not SA NQF-aware; CHE compliance not built in; expensive import |
| SharePoint/Teams custom builds | DIY | Institution-controlled | Requires internal IT investment; no AI; no standard |
| IQMS (teacher management) | School-focused | Government adoption | School context only; not higher education |
| Custom internal systems | Institution-built | Institution-specific | No AI; no multi-tenant; expensive to maintain |

### 2.2 AQAA's Competitive Position

AQAA occupies a currently **uncontested niche**: AI-augmented, NQF-aware, CHE-aligned academic QA for South African higher education.

No existing product combines:
- South African NQF (Levels 5–10) native support
- CHE evidence requirement alignment
- AI-assisted evidence gap detection
- IKP-based institutional knowledge management
- Multi-tenant SaaS deployment

---

## 3. Unique Value Proposition

> **AQAA is the only platform built specifically for South African academic quality assurance — combining AI-powered evidence gap detection, NQF-native compliance intelligence, and institutional knowledge management in a single, multi-tenant platform.**

### 3.1 Value Pillars

| Pillar | Benefit to Institution |
|--------|----------------------|
| **AI-powered gap detection** | QA teams review exceptions, not entire module catalogues |
| **IKP institutional intelligence** | All academic data versioned, provenance-tracked, and AI-ready |
| **NQF-native compliance** | Checklists and thresholds adapt to NQF level of each programme |
| **CHE evidence alignment** | Evidence categories match CHE audit criteria |
| **Complete audit trail** | Immutable history of all QA activities for accreditation submissions |
| **Multi-institution** | Single platform for a consortium without data mixing |

### 3.2 Key Differentiators

1. **Provenance-first data:** AQAA never loads institutional data without tracing it to an official source. This is unique — no competitor has an IKP system.
2. **Hybrid AI architecture:** AI generates findings; humans approve. This makes AQAA CHE-compatible (human accountability maintained).
3. **South African-native:** Built for SA regulatory context from the ground up — NQF, APS, CHE, DHET, SAQA, ECSA.

---

## 4. SaaS Vision

### 4.1 Deployment Model

AQAA is designed as a **multi-tenant SaaS platform** — a single deployment serves multiple institutions with complete data isolation.

**SaaS tiers (planned):**

| Tier | Institutions | Features | Pricing Model |
|------|-------------|---------|---------------|
| Pilot | 1 | All features; white-glove onboarding | Fixed fee |
| Institutional | 1 per contract | All features; standard onboarding | Per-user or per-module annual licence |
| Consortium | 3–10 | All features; consortium management | Consortium fee + per-institution |
| National | 10+ | All features; government reporting | Government tender / framework agreement |

### 4.2 SaaS Architecture Readiness

Current architecture is already SaaS-ready:
- Multi-tenant by design (row-level isolation)
- Stateless backend (horizontal scaling ready)
- Docker containerisation
- Environment-variable configuration (no hardcoded values)
- IKP system allows institution onboarding without code changes

**Remaining for production SaaS:**
- Cloud storage backend (S3 / Azure Blob)
- SMTP email delivery
- SSL/TLS termination
- Monitoring and alerting
- Automated backup
- User self-registration (admin-invited, not open)

---

## 5. Multi-Tenant Deployment Strategy

### 5.1 Onboarding a New Institution

With the IKP architecture, onboarding a new institution follows a defined pipeline:

1. **Source discovery** — collect all official website and PDF sources
2. **IKP assembly** — build versioned JSON package with provenance
3. **Confidence scoring** — validate all fields against 0.85 threshold
4. **Human verification** — review flagged medium-confidence fields
5. **Database import** — run `seed-from-ikp.py` to load verified records
6. **User creation** — create institution users (SA role assigns roles)
7. **Validation** — verify audit engine works correctly for the institution

**Target onboarding time:** 2–4 weeks for a new institution (including PDF extraction and data verification).

### 5.2 Data Isolation Guarantee

Each institution's data is completely isolated:
- Different `institution_id` on all rows
- Service-layer filter enforced on every query
- API-layer `assert_institution_access()` check
- Frontend `RoleGuard` and `useRole()` prevent cross-institution UI access

---

## 6. Licensing Considerations

### 6.1 Current Status

AQAA is a proprietary product in development. No open-source licence has been applied.

### 6.2 Licensing Options Under Consideration

| Model | Pros | Cons |
|-------|------|------|
| Proprietary SaaS | Maximum commercial control; recurring revenue | Slower adoption in resource-constrained institutions |
| Open core (free base + paid enterprise) | Fast adoption; community contribution | Requires clear feature boundary between free/paid |
| Government framework agreement | Guaranteed volume; stable revenue | Long procurement cycles; requires government relationship |
| Per-institution annual licence | Predictable revenue; aligns cost to value | Pricing model complexity for consortium |

### 6.3 Recommendation

**Near-term:** Proprietary SaaS with a pilot agreement. After 3+ institutions are operational, evaluate open-core model to accelerate national adoption.

**POPIA note:** Licensing agreements must include data processing agreements (DPA) specifying that AQAA is a data processor and the institution is the data controller.

---

## 7. Future Institutional Expansion

### 7.1 South African Expansion Roadmap

| Institution | Code | Type | Priority | Notes |
|-------------|------|------|---------|-------|
| Tshwane University of Technology | TUT | UoT | ✅ Pilot | ICT Faculty — in progress |
| University of Pretoria | UP | Traditional | High | Large, complex; strong QA office |
| Durban University of Technology | DUT | UoT | High | Similar profile to TUT; ECSA programmes |
| Cape Peninsula UoT | CPUT | UoT | High | Multiple campuses; Western Cape focus |
| University of Johannesburg | UJ | Comprehensive | Medium | High student numbers; complex structure |
| UNISA | UNISA | Distance | Low → High | Largest student body; distance model unique |
| Walter Sisulu University | WSU | Comprehensive | Medium | Eastern Cape; CHE compliance focus |
| Mangosuthu University of Technology | MUT | UoT | Medium | KZN; engineering and science focus |
| Vaal University of Technology | VUT | UoT | Medium | Gauteng/NW; manufacturing and engineering |
| Ekurhuleni East TVET College | EETC | TVET | Future | TVET pilot when model is mature |

### 7.2 TVET College Expansion

TVET colleges present a different challenge:
- NC(V) (National Certificate Vocational) qualifications at NQF 2–4
- NATED (Report 191) programmes
- Different evidence requirements (less emphasis on research, more on practical)
- UMALUSI accreditation (not CHE)
- 50 public TVET colleges across South Africa

AQAA's IKP architecture supports TVET via a dedicated `tvet.template.json` configuration. TVET pilot planned for Phase 9.

---

## 8. Government and Accreditation Adoption

### 8.1 Government Relationship

AQAA has potential for direct relationship with DHET as:
- A technology platform supporting the national QA mandate
- An evidence base for DHET institutional audits
- A reporting tool for the Institutional Audits Framework

**Target:** DHET awareness by end of national pilot phase (Phase 8).

### 8.2 CHE Integration

The Council on Higher Education does not currently have a digital evidence submission platform. AQAA could become the bridge between institutional QA practice and CHE audit preparation.

**Future capability:** Export audit reports in CHE-specified evidence format directly from AQAA.

### 8.3 SAQA Integration

SAQA's qualification database is publicly accessible. A future SAQA API integration would allow AQAA to automatically verify:
- NQF levels for loaded programmes
- Credit values against SAQA registration
- Programme status (active/cancelled)

This would raise IKP confidence scores for NQF and credit fields from HEQSF-inferred (0.82) to SAQA-verified (0.97).

---

## 9. International Roadmap

### 9.1 Priority Markets

| Market | Regulatory Framework | AQAA Adaptation Required |
|--------|---------------------|--------------------------|
| Zimbabwe (ZIMCHE) | Zimbabwe Accreditation System | NQF mapping + ZIMCHE criteria |
| Kenya (CUE) | Commission for University Education | NQF equivalent mapping |
| Ghana (NAB) | National Accreditation Board | Local framework mapping |
| Nigeria (NUC) | National Universities Commission | NUC minimum academic standards |
| Botswana (HRDC) | Human Resource Development Council | Local QA framework |

### 9.2 International Architecture

The IKP system supports international institutions via:
```json
{
  "nqf_mapping": {
    "institution_country": "Zimbabwe",
    "local_framework": "ZIMCHE Qualifications Framework",
    "local_level": "Level 7",
    "sa_nqf_equivalent": 7,
    "mapping_source": "SAQA_international_comparability_2024",
    "confidence": 0.82
  }
}
```

No code changes are required to onboard an international institution — only a new IKP package with the appropriate `nqf_mapping` object.

---

## 10. Strategic Decisions

| Decision | Status | Reference |
|---------|--------|-----------|
| AQAA is standalone | Active | DEC-0001, ADR-0001 |
| Multi-tenant architecture | Active | DEC-0002, ADR-0002 |
| TUT as pilot institution | Active | DEC-0003, ADR-0003 |
| IKP as knowledge gateway | Active | DEC-0004, ADR-0004 |
| AI-first hybrid (humans decide) | Active | DEC-0006, ADR-0005 |
| Secondary source data blocked | Active | DEC-0007 |
| SaaS deployment model | **PROPOSED** | This document — requires ADR |
| Open-core licensing evaluation | **DEFERRED** | Post Phase 8 |
| DHET relationship | **FUTURE** | Phase 8+ |

---

*This strategy document should be reviewed at the start of each commercial phase.*  
*Any decision in this document that affects architecture must be converted to an ADR.*
