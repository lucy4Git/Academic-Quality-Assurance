# South African University Registry — Architecture

**Document ID:** ARCH-SA-REG-001
**Status:** Active
**Introduced:** Split 1 (2026-07-06)

---

## Purpose

Provide AQAA with a verifiable foundation of South Africa's 26 public
universities as real institution *profiles*, while keeping all quality-assurance
(QA) data for those institutions clearly marked as synthetic/demo.

## Data source of truth

The canonical registry is a static JSON file, version-controlled with the code:

```
database/seed_data/institution_registry/
├── south_africa_public_universities.json   # 26 universities
├── sources.json                            # provenance of the data
└── README.md                               # public vs synthetic policy
```

Each entry carries: `official_name`, `abbreviation` (code), `institution_type`,
`province`, `country`, `national_framework` (HEQSF), `regulator` (DHET),
`quality_body` (CHE), `website`, `established`, `source_url`, `data_confidence`,
`data_status`, `is_active`, `is_demo`.

## Institution model extension

The `institutions` table (model `app.models.institution.Institution`) gains six
provenance columns:

| Column | Type | Nullable | Meaning |
|--------|------|----------|---------|
| `province` | `String(100)` | yes | SA province |
| `website` | `String(500)` | yes | Official institution website |
| `source_url` | `String(500)` | yes | Where the profile data was sourced |
| `data_status` | `String(50)` | yes | e.g. `public_verified` |
| `data_confidence` | `Float` | yes | Confidence in the public profile, `[0,1]` |
| `is_demo` | `Boolean` | no (default `false`) | `true` = only the profile is real; QA data is synthetic |

Applied via Alembic migration `f7a8b9c0d1e2` (down_revision `e6f7a8b9c0d1`),
using `server_default="false"` for `is_demo` so existing rows backfill safely.

## Data classification

- **Public / verified** — profile fields (name, code, province, type, website,
  founding year). `data_status = "public_verified"`.
- **Synthetic / demo** — every faculty, department, programme, module, user,
  audit, or finding attached to a registry institution. Flagged by
  `is_demo = true` on the institution.

`data_confidence` describes confidence in the *public profile only*, never the
QA data.

## Seeding flow

`database/seed_data/seed_sa_universities.py` (sync SQLAlchemy):

1. Loads the JSON registry.
2. For each entry, upserts by `code` (`abbreviation`).
3. On existing institutions, updates only registry/metadata fields — never
   touching faculty/department/module/user relationships.
4. Idempotent — safe to re-run; reports created/updated/skipped counts.

Integrated as step 4/4 of `run_all.py`. Because it is synchronous, it is called
directly (not awaited) after the three async seeds.

## Security & correctness notes

- Only publicly available data is stored; no institution's private QA data.
- The seed never deletes or reassigns existing hierarchy relationships.
- Pilot institutions (TUT, UP) that already exist are updated in place; their
  `institution_type` from earlier pilot seeds is not downgraded (only non-null
  registry fields are written).

## Related

- Implementation guide: `docs/02_Implementation/SA_UNIVERSITY_REGISTRY_IMPLEMENTATION_GUIDE.md`
- Testing guide: `docs/05_Testing/SPLIT1_TESTING_GUIDE.md`
