# AQAA Regulatory Engine — Seed Guide

**Phase C | Version 1.0 | 2026-07-14**

---

## Prerequisites

1. Backend services running: `docker compose up -d`
2. Database migrated to head: `cd backend && python -m alembic upgrade head`
3. Base seed data loaded: `python database/seed_data/run_all.py`
4. Environment variable: `DATABASE_URL` set in `backend/.env`

---

## Running the Regulatory Seed

```bash
# From repo root
python database/seed_data/seed_regulatory_framework.py
```

The script is **idempotent** — safe to re-run. Existing records are detected by `code` and skipped.

---

## What Gets Seeded

### Regulatory Authorities (7)

| Code | Authority | Type |
|------|-----------|------|
| CHE-ZA | [TEST FIXTURE] Council on Higher Education | quality_council |
| SAQA-ZA | [TEST FIXTURE] South African Qualifications Authority | qualification_authority |
| DHET-ZA | [TEST FIXTURE] Department of Higher Education and Training | government_department |
| ECSA-ZA | [TEST FIXTURE] Engineering Council of South Africa | professional_council |
| HPCSA-ZA | [TEST FIXTURE] Health Professions Council of South Africa | professional_council |
| SACE-ZA | [TEST FIXTURE] South African Council for Educators | professional_council |
| QCTO-ZA | [TEST FIXTURE] Quality Council for Trades and Occupations | quality_council |

### Quality Frameworks (5)

Each framework includes: 1 active version, 1–2 standards, 1–2 criteria, 1 evidence requirement per criterion.

| Code | Framework | Standards |
|------|-----------|----------|
| CHE-IQA-2024 | [TEST FIXTURE] IQA Framework 2024 | S1: Governance, S2: Teaching & Learning |
| ECSA-E-2022 | [TEST FIXTURE] Engineering Accreditation 2022 | S1: Programme Educational Objectives |
| HPCSA-MED-2023 | [TEST FIXTURE] Health Professions Accreditation 2023 | S1: Clinical Training |
| SACE-PGCE-2022 | [TEST FIXTURE] Professional Teacher Education 2022 | S1: Professional Practice |
| QCTO-OQF-2021 | [TEST FIXTURE] Occupational Qualifications Framework 2021 | S1: Competency Standards |

---

## DSN Note

The seed script uses `asyncpg` directly (not SQLAlchemy). It strips `+asyncpg` from `DATABASE_URL`:

```python
DATABASE_URL = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://", 1)
```

This is required because asyncpg does not accept the SQLAlchemy-specific scheme prefix.

---

## Verifying the Seed

After running, verify in the Framework Management UI:

1. Navigate to `/quality` → Framework Management
2. Check `Frameworks (5)` tab — all 5 frameworks visible with TEST FIXTURE badges
3. Check `Authorities (7)` tab — all 7 authorities visible with TEST FIXTURE badges

Or via API:

```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/regulatory-authorities | python -m json.tool | grep '"code"'
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/quality-frameworks | python -m json.tool | grep '"code"'
```
