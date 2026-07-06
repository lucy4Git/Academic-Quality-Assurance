# South African Public University Registry

This directory contains the foundational registry of South Africa's **26 public
universities**, used to seed real institutional *profiles* into AQAA.

## Files

| File | Purpose |
|------|---------|
| `south_africa_public_universities.json` | The 26 universities: name, code, province, type, website, founding year, data-quality metadata. |
| `sources.json` | The public data sources used to compile the registry. |
| `README.md` | This file. |

## Public vs synthetic data — read this first

AQAA is a quality-assurance platform. The institutions listed here are **real**,
but AQAA does **not** hold any real internal QA data for them.

- **Real (public):** institution name, abbreviation/code, province, institution
  type, official website, year established. These are drawn from public sources
  (DHET, USAf, CHE, institutional websites). Marked `data_status: "public_verified"`.
- **Synthetic (demo):** every faculty, department, programme, module, user,
  audit run, finding, or compliance figure attached to these institutions is
  **fabricated for demonstration** and is **not** the institution's real data.

Because only the *profile* is real, **every registry entry is marked
`is_demo: true`**. This flag tells the platform (and any UI badges) that the
institution's operational QA data must be treated as demonstration data.

## Data confidence levels

`data_confidence` is a float in `[0, 1]` describing confidence in the **public
profile fields only** (never the QA data):

| Range | Meaning |
|-------|---------|
| `0.95 – 1.00` | Cross-verified against multiple public sources. |
| `0.80 – 0.94` | Verified against a single authoritative public source. |
| `< 0.80` | Partially verified / best-effort. |

All current entries sit at `0.95` (or `0.99` for University of Pretoria, the
verification reference institution).

## Institution types

`institution_type` uses one of: `comprehensive`, `university_of_technology`,
`distance`, `specialised`.

## Seeding

Seed the registry into the database (idempotent, safe to re-run):

```bash
cd backend
python ../database/seed_data/seed_sa_universities.py
```

Only institution profile/metadata fields are upserted — existing pilot data
relationships (faculties, departments, etc.) are never modified.
