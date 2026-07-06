# Split 1 — Testing Guide

**Document ID:** TEST-SPLIT1-001
**Status:** Active
**Introduced:** Split 1 (2026-07-06)

---

## Automated tests

### Registry tests

```bash
cd backend
python -m pytest tests/test_split1_sa_registry.py -q
```

Covers (`tests/test_split1_sa_registry.py`):

- Registry file exists and contains exactly 26 universities.
- No duplicate `abbreviation` codes.
- Required fields present on every entry.
- TUT and UP present.
- Valid `institution_type` values only.
- `data_confidence` within `[0, 1]`.
- Every `country == "South Africa"`.
- Every entry `is_demo == true`.
- `Institution` model exposes the six new columns.

Expected: **10 passed**.

### Full backend suite

```bash
cd backend
python -m pytest -q
```

Requires `backend/.env` (with `SECRET_KEY`, `DATABASE_URL`) present so
`app.config.Settings` loads. Two pre-existing DOCX-parser tests
(`test_adip.py::TestDOCXExtractor::test_extract_docx_table`,
`test_parsers.py::TestDocxParser::test_extracts_paragraphs`) may fail on
memory-constrained machines with "Unable to allocate output buffer" — this is
unrelated to Split 1.

### Frontend type check

```bash
cd frontend
npx tsc --noEmit          # add --skipLibCheck on low-memory machines
```

Expected: **0 errors**.

## Manual verification

1. **Migration** — `python -m alembic upgrade head`; confirm the `institutions`
   table has `province`, `website`, `source_url`, `data_status`,
   `data_confidence`, `is_demo`.
2. **Seed** — `python ../database/seed_data/seed_sa_universities.py`; re-run and
   confirm the second run reports `created=0` (idempotent).
3. **Sidebar** — log in as different roles and confirm the 7-item nav shows only
   permitted workspaces (Student sees none of them).
4. **Workspace pages** — open `/institution`, `/quality`, `/knowledge`, `/ai`,
   `/administration`; confirm role-filtered cards and working links.
5. **Dashboard** — `/dashboard` shows greeting, 3 "Demo data" KPI cards, quick
   actions.
6. **AI error UX** — in `/ai-workspace`, trigger a failed request (e.g. no
   institution context) and confirm the `AiErrorCard` appears with a friendly
   message and Try Again / Browse Knowledge / Open AI Workspace actions (AI
   Settings action visible only to System Admin).

## Sign-off checklist

- [ ] `test_split1_sa_registry.py` — 10 passed
- [ ] Full suite — only the 2 known DOCX failures, if any
- [ ] `tsc --noEmit` — 0 errors
- [ ] Migration applied and columns present
- [ ] Seed idempotent
- [ ] Sidebar + workspace pages role-correct
