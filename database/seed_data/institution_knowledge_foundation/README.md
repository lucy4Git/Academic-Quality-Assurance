# Institution Knowledge Foundation — Data Package

Split 2 Wave 1 registry data for the 26 South African public universities.

## Provenance categories

Every record carries a `data_status` and (where applicable) `is_synthetic` flag:

| `data_status` | Meaning | `is_synthetic` |
|---------------|---------|----------------|
| `public_verified` | Sourced from official public sources (university websites, DHET, CHE, SAQA). | `false` |
| `needs_review`    | Publicly known but unconfirmed / may change (departments, programmes, policy titles). | `false` |
| `synthetic_demo`  | Realistic demo data — **NOT** real internal university data. Clearly labelled. | `true` |
| `customer_data`   | Real data uploaded by an institution. Never present in seed files; never overwritten by seeds. | — |

## Files

| File | Entities | Predominant provenance |
|------|----------|------------------------|
| `campuses.json` | Physical campuses | `public_verified` for 10 well-known unis; `synthetic_demo` main campus otherwise |
| `faculties.json` | Faculties | `public_verified` (TUT/UP/UCT/Wits/SU/UWC); `synthetic_demo` otherwise |
| `departments.json` | Departments | `needs_review` / `synthetic_demo` |
| `schools.json` | Schools (Wits/UKZN/NMU) | `needs_review` |
| `programmes.json` | Programmes (NQF + type) | `needs_review` / `synthetic_demo` |
| `qualifications.json` | Qualifications | `needs_review` / `synthetic_demo` |
| `modules.json` | Modules | `synthetic_demo` |
| `learning_outcomes.json` | Learning outcomes | `synthetic_demo` |
| `graduate_attributes.json` | CHE/HEQSF-based attributes | `needs_review` |
| `policies.json` | Policy titles | `needs_review` |
| `policy_versions.json` | Policy versions | `synthetic_demo` |
| `institution_documents.json` | Public documents | `public_verified` / `needs_review` |
| `accreditation_bodies.json` | SA/international bodies | `public_verified` |
| `accreditations.json` | Institution accreditations | `needs_review` / `synthetic_demo` |
| `contacts.json` | Institutional contacts | `synthetic_demo` |

## What is real vs synthetic

- **Real (public):** institution names/codes/provinces/websites, campus lists for the 10 major
  universities, faculty lists for TUT/UP/UCT/Wits/SU/UWC, accreditation bodies, published
  document titles (annual reports, strategic plans).
- **Synthetic (clearly labelled):** all modules, learning outcomes, contacts, policy version
  content, and most programme/department detail for smaller universities. These exist so the
  platform and RAG pipeline have a realistic knowledge graph to operate on — they must never be
  presented as authoritative internal university data.

## Updating with real data

1. Replace synthetic entries with verified data and set `data_status` to `public_verified`
   (or `needs_review` if partially confirmed) and `is_synthetic` to `false`.
2. Re-run the seed: `python ../database/seed_data/seed_institution_knowledge_foundation.py`.
   The seeder **never** downgrades `public_verified` → `synthetic_demo` and **never** overwrites
   `customer_data`, so verified edits are safe.
3. Customer-uploaded (`customer_data`) records are managed through the app, not this package.

## Natural keys (deduplication)

Institution code + name/code/title is the natural key for each entity (see
`seed_institution_knowledge_foundation.py`). Re-running the seed is idempotent.
