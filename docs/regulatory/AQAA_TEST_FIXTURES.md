# AQAA Regulatory Engine — Test Fixtures

**Phase C | Version 1.0 | 2026-07-14**

---

## Purpose

Test fixtures provide representative regulatory data for development and testing. They are clearly labelled and must never be treated as authoritative regulatory text.

---

## Fixture Labelling Convention

All fixture data is prefixed with `[TEST FIXTURE]` in the `name` and `description` fields:

```
[TEST FIXTURE] Council on Higher Education
[TEST FIXTURE] Institutional Quality Assurance Framework 2024
[TEST FIXTURE] 2024 Edition
[TEST FIXTURE] Governance and Management
[TEST FIXTURE] Quality Assurance Policy
```

The `is_test_fixture` computed field returns `true` when `name` contains `[TEST FIXTURE]`.

---

## Seeded Authorities (7)

| Code | Name | Type |
|------|------|------|
| CHE-ZA | [TEST FIXTURE] Council on Higher Education | quality_council |
| SAQA-ZA | [TEST FIXTURE] South African Qualifications Authority | qualification_authority |
| DHET-ZA | [TEST FIXTURE] Department of Higher Education and Training | government_department |
| ECSA-ZA | [TEST FIXTURE] Engineering Council of South Africa | professional_council |
| HPCSA-ZA | [TEST FIXTURE] Health Professions Council of South Africa | professional_council |
| SACE-ZA | [TEST FIXTURE] South African Council for Educators | professional_council |
| QCTO-ZA | [TEST FIXTURE] Quality Council for Trades and Occupations | quality_council |

---

## Seeded Frameworks (5)

| Code | Authority | Scenario | Scope |
|------|-----------|----------|-------|
| CHE-IQA-2024 | CHE-ZA | General HE quality assurance | institutional |
| ECSA-E-2022 | ECSA-ZA | Engineering programme accreditation | programme |
| HPCSA-MED-2023 | HPCSA-ZA | Health professions accreditation | programme |
| SACE-PGCE-2022 | SACE-ZA | Teacher education accreditation | programme |
| QCTO-OQF-2021 | QCTO-ZA | Occupational qualifications | programme |

---

## Multi-Framework Scenarios

The 5 frameworks support testing across 4 professional domains:

| Domain | Applicable frameworks |
|--------|--------------------|
| Engineering | CHE-IQA-2024, ECSA-E-2022 |
| Health | CHE-IQA-2024, HPCSA-MED-2023 |
| Teacher Education | CHE-IQA-2024, SACE-PGCE-2022 |
| Occupational | QCTO-OQF-2021 |

Engineering and Health programmes face dual-framework compliance requirements (CHE + professional body), enabling cross-framework overlap and conflict testing.

---

## Seed Script

`database/seed_data/seed_regulatory_framework.py`

```bash
python database/seed_data/seed_regulatory_framework.py
```

The script is idempotent — re-running it skips existing records.

---

## Security Constraints on Fixtures

- **Do not hard-code incomplete or invented regulatory standards.** Use `[TEST FIXTURE]` prefix.
- **Do not automatically treat imported text as authoritative.** Fixtures are stubs only.
- **Do not allow AI to mark two standards as legally equivalent** without `human_verified = true`.
- The `is_test_fixture` flag must be disclosed in AI citations and API responses.
- Fixture data must not be used in production compliance decisions.

---

## Adding New Fixtures

1. Add authority to `AUTHORITIES` list in seed script with `[TEST FIXTURE]` prefix
2. Add framework to `FRAMEWORKS` list with `[TEST FIXTURE]` prefix and minimal standards/criteria
3. Run seed script
4. Verify in Framework Management UI that `TEST FIXTURE` badge appears
5. Document in this file under the appropriate domain section
