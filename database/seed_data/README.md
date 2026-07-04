# AQAA Seed Data

Scripts populate a freshly migrated database with sample and pilot data.
All scripts are **idempotent** and can be re-run safely.

| Script | Purpose |
|---|---|
| `seed.py` | Minimal single-institution hierarchy for local development. |
| `seed_extended.py` | Expands the dataset into a realistic, multi-institution, multi-campus environment. |
| `seed_audit_history.py` | Adds sample audit history, findings, and compliance reports across multiple cycles. |
| `generators.py` | Deterministic data-generation utilities used by the scripts above (no randomness). |
| `run_all.py` | Runs `seed.py` → `seed_extended.py` → `seed_audit_history.py` in order. |
| `seed_tut.py` | **Pilot**: Seeds TUT ICT faculty from approved IKP v1.1.0. |
| `seed_up.py` | **Pilot**: Seeds UP EBIT faculty from IKP v1.0.0 (CS, Informatics, Information Science). Programme codes derived from entity_key when SAQA code is `pending_verification`. |
| `seed_pilot_users.py` | **Pilot**: Creates one user per role for TUT and UP (idempotent). |
| `deactivate_demo_users.py` | **Ops**: Sets `is_active=False` on all GFU/RCT users. Supports `--dry-run`. |

## Pilot institution seeds

Run individually (from repo root):

```bash
python database/seed_data/seed_tut.py
python database/seed_data/seed_up.py
```

These scripts read from the IKP packages in `ikp/institutions/` and require
the database to be migrated to at least revision `a1b2c3d4e5f6`
(`python -m alembic upgrade head` from `backend/`).

## Pilot user setup

Run in order after institutional seeds:

```bash
python database/seed_data/seed_pilot_users.py    # create TUT + UP users
python database/seed_data/deactivate_demo_users.py  # lock GFU/RCT users out
```

To verify before applying the deactivation:

```bash
python database/seed_data/deactivate_demo_users.py --dry-run
```

See `docs/06_Administration/PILOT_LOGIN_CREDENTIALS.md` for the full
credentials reference.

## 1. `seed.py` -- minimal core hierarchy

| Entity | Count | Details |
|---|---|---|
| Institution | 1 | `GFU` -- Greenfield University |
| Faculty | 1 | `FCE` -- Faculty of Computing and Engineering |
| Department | 1 | `CS` -- Department of Computer Science |
| Programme | 1 | `BSC-CS` -- BSc (Hons) Computer Science (undergraduate) |
| Modules | 3 | `CS101`, `CS201`, `CS301` (2025/2026), each assigned a lecturer |
| Lecturers | 3 | `lecturer1@gfu.ac.uk`, `lecturer2@gfu.ac.uk`, `lecturer3@gfu.ac.uk` |
| Quality Assurance Officer | 1 | `qa.officer@gfu.ac.uk` |

## 2. `seed_extended.py` -- multi-institution, multi-campus expansion

This script does **not** remove or modify any data created by `seed.py`. It
only adds new rows, plus backfilling the new `Faculty.campus` column on the
existing `FCE` faculty (set to `"Main Campus"` if not already set).

| Entity | Count (added) | Details |
|---|---|---|
| Institutions | +1 | `RCT` -- Riverside College of Technology |
| Campuses (via `Faculty.campus`) | 5 distinct values | GFU: `Main Campus`, `City Campus`, `North Campus`. RCT: `Riverside Main Campus`, `Riverside Park Campus` |
| Faculties | +7 (GFU now has 4 total: `FCE`, `FBM`, `FHS`, `FAH`; RCT has 4: `FET`, `FCS`, `FBA`, `FAS`) | Business, Health Sciences, Arts & Humanities (GFU); Engineering & Technology, Computing Sciences, Business Administration, Applied Sciences (RCT) |
| Departments | +9 | 2 per new/expanded faculty (1 extra department, `EEE`, added under the existing `FCE` faculty) |
| Programmes | +9 | 1 per new department (mix of undergraduate and postgraduate) |
| Modules | +27 | 3 per new programme (`<ABBR>101`/`201`/`301`, 2025/2026), each assigned a lecturer |
| Lecturers | +27 | 3 per new programme, generated via `generators.generate_lecturers` |
| Students | +18 | 2 per new programme, generated via `generators.generate_students` |
| Quality Assurance Officers | +3 | `qa.officer1@gfu.ac.uk` (GFU); `qa.officer1@rct.ac.uk`, `qa.officer2@rct.ac.uk` (RCT) |

Combined with `seed.py`, the database ends up with:

- **2 institutions** (GFU, RCT)
- **5 distinct campuses** across both institutions
- **4 faculties per institution**
- **2 departments per faculty** (FCE has 2: `CS`, `EEE`; the rest have 2 each)
- **1-2 programmes per department**
- **3 modules per programme**
- **30 lecturers**, **21 students**, **4 QA officers** in total

## 3. `seed_audit_history.py` -- sample audit history & compliance reports

Adds `AuditRun` / `AuditFinding` rows for one "flagship" module + programme
per institution (`GFU`/`CS101`/`BSC-CS` and `RCT`/`SEN101`/`BSC-SEN`), across
**two accreditation cycles** (`2024/2025` and `2025/2026`):

- `MODULE_FOLDER_AUDIT` runs with findings (some resolved between cycles,
  showing compliance improving from ~64% to ~92%).
- `ASSESSMENT_COMPLIANCE` runs.
- `ACCREDITATION_READINESS` runs (module-scoped "compliance reports") with
  findings.
- `PROGRAMME_REVIEW` runs (programme-scoped "compliance reports").

Each run is tagged with a unique marker at the start of its `summary` (e.g.
`[SEED:GFU-CS101-MFA-2024]`) so re-running the script does not create
duplicates.

## All seeded users

All seeded users (lecturers, QA officers, students) share the password
`ChangeMe123!` (see `DEFAULT_PASSWORD` in `seed.py` / `seed_extended.py`).
This is for local development only -- change or remove these accounts before
using the seed scripts against any shared environment.

## Running it

1. Start the datastores and apply migrations -- see
   [`../migrations/README.md`](../migrations/README.md).

2. From the `backend/` directory, run all three scripts in order:

   ```bash
   python ../database/seed_data/run_all.py
   ```

   Or run them individually:

   ```bash
   python ../database/seed_data/seed.py
   python ../database/seed_data/seed_extended.py
   python ../database/seed_data/seed_audit_history.py
   ```

   (or from the repo root, prefix each with `cd backend &&`)

Each script reads `DATABASE_URL` from `backend/.env` via `app.config.settings`,
so it connects to the same database the backend uses.

## Idempotency

Every script looks up each row by its natural key (institution code, faculty
code within the institution, department code within the faculty, programme
code within the department, module code + academic year within the
programme, user email, or -- for audit runs -- a `[SEED:...]` marker in
`summary`) before inserting. Re-running a script after the data already
exists prints "already exists, skipping" for each row and makes no changes.

## Resetting

To start over from an empty database, see the "Resetting the local database
from scratch" section in [`../migrations/README.md`](../migrations/README.md).
