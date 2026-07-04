# AQAA — Lessons Learned Register

**Document ID:** LL-001  
**Version:** 1.0.0  
**Status:** Active  
**Last Updated:** 2026-06-29

This register captures problems encountered during AQAA development, their root causes, solutions applied, and recommendations for preventing recurrence.

---

## Format

```
### LL-XXXX — [Title]
- **Phase:** Phase X.Y
- **Date:** YYYY-MM-DD
- **Severity:** Critical | High | Medium | Low
- **Category:** Architecture | Integration | Data | Frontend | Backend | Tooling | Process

**Problem**
[What went wrong]

**Cause**
[Root cause analysis]

**Solution**
[How it was resolved]

**Future Recommendation**
[How to prevent this in future phases]
```

---

## Lessons Learned

### LL-0001 — Faculty Table Name Pluralisation Bug
- **Phase:** Phase 2C
- **Date:** 2026-06-11
- **Severity:** Critical
- **Category:** Backend / Architecture

**Problem**  
The `Faculty` ORM model caused foreign key resolution failures. SQLAlchemy's `Base.__tablename__` naive pluralisation produced `"facultys"` instead of the correct English plural `"faculties"`. All FK references to `ForeignKey("faculties.id")` failed to resolve.

**Cause**  
SQLAlchemy's automatic `__tablename__` generation appends `"s"` to the class name without language-aware pluralisation.

**Solution**  
Added explicit `__tablename__ = "faculties"` to `backend/app/models/faculty.py`.

**Future Recommendation**  
All ORM models with irregular English plurals (e.g., `Category → categories`, `Country → countries`) must explicitly set `__tablename__`. Never rely on automatic pluralisation for any model where the class name does not produce the correct SQL table name.

---

### LL-0002 — Double-Wrapped Depends() in Audit Routes
- **Phase:** Phase 4A
- **Date:** 2026-06-25
- **Severity:** Critical
- **Category:** Backend / FastAPI

**Problem**  
FastAPI 0.136.3+ raises `TypeError: Depends(...) is not a callable object` when a dependency object is wrapped in an additional `Depends()`. This caused all audit agent routes to fail at startup.

**Cause**  
Named role shortcuts (`CoordinatorRequired`, `QAOfficerRequired`, etc.) in `backend/app/dependencies.py` return `Depends(_check)` objects. They are used directly as default values in route function signatures, not as arguments to `Depends()`. When refactoring copied incorrect patterns from older FastAPI versions that accepted double-wrapping.

**Solution**  
Replaced all occurrences of `current_user: User = Depends(CoordinatorRequired)` with `current_user: User = CoordinatorRequired` across all 7 affected audit route files.

**Future Recommendation**  
All named role shortcuts are already `Depends(...)` objects. Use them as direct default values:
```python
# CORRECT
current_user: User = CoordinatorRequired

# WRONG — causes TypeError
current_user: User = Depends(CoordinatorRequired)
```

---

### LL-0003 — run_status.value Crash on AuditRun
- **Phase:** Phase 4A
- **Date:** 2026-06-25
- **Severity:** High
- **Category:** Backend / Data Model

**Problem**  
Calling `.value` on `AuditRun.run_status` caused an `AttributeError`. The audit report endpoint crashed when attempting `f"'{run.run_status.value}'"`.

**Cause**  
`AuditRun.run_status` is stored as a plain `str` in PostgreSQL, not as a Python enum instance. SQLAlchemy returns it as a plain string from the database. Calling `.value` on a string fails.

**Solution**  
Removed `.value` call and used f-string interpolation directly: `f"...'{run.run_status}'..."`.

**Future Recommendation**  
When SQLAlchemy returns enum fields, check whether the field is declared with `native_enum=True` or stored as a string. For `run_status`, it is stored and returned as `str`. Never assume `.value` is safe — check the actual Python type returned from `await db.execute()`.

---

### LL-0004 — Login Form "Invalid Input" from @base-ui/react Field.Control
- **Phase:** Phase 1
- **Date:** 2026-06-11
- **Severity:** High
- **Category:** Frontend / ShadCN

**Problem**  
The login form displayed "Invalid input" on submit even when the email address was valid. The error appeared before any API call was made.

**Cause**  
ShadCN UI in this installation uses `@base-ui/react` (not Radix UI). The `Field.Control` component wraps inputs and engages the browser's native Constraint Validation API. An `<input type="email">` field triggers native browser validation, which intercepts the submit event and rejects values that pass custom validation but fail the browser's built-in email regex.

**Solution**  
Changed the email input from `type="email"` to `type="text"` with `inputMode="email"`. This prevents `Field.Control` from engaging native constraint validation while preserving mobile keyboard hints.

**Future Recommendation**  
When using ShadCN UI with `@base-ui/react`, do not use `type="email"`, `type="url"`, or `type="number"` inside `Field.Control` wrappers if custom validation is also applied. Use semantic `type="text"` + `inputMode` attribute for keyboard hints. Document this constraint in any onboarding guide.

---

### LL-0005 — react-hook-form + zod@4 Incompatibility
- **Phase:** Phase 1
- **Date:** 2026-06-11
- **Severity:** High
- **Category:** Frontend / Dependencies

**Problem**  
Login form validation was silently failing. `@hookform/resolvers` (v5) resolver was returning `undefined` for errors, making the form submit regardless of validation state.

**Cause**  
`@hookform/resolvers@5` expects Zod's error format from Zod v3, where errors are accessed via `.errors`. Zod v4 changed the format to `.issues`. The resolver reads `undefined` and treats all validation as passing.

**Solution**  
Removed `react-hook-form` entirely from the login form and replaced with plain `useState` for form state management. Custom `loginResolver` function implemented with `EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/`.

**Future Recommendation**  
Before using any form validation library, verify compatibility with the installed Zod version. In AQAA, the login form and other simple forms use plain `useState` to avoid dependency version mismatches. Use `react-hook-form` only for complex multi-field forms where its benefits justify the dependency risk — and pin versions explicitly.

---

### LL-0006 — api-client.ts Calling FastAPI Directly
- **Phase:** Phase 1
- **Date:** 2026-06-11
- **Severity:** Critical
- **Category:** Frontend / Security

**Problem**  
API calls from the frontend were reaching FastAPI directly (`http://localhost:8000/api/v1`), bypassing the Next.js API proxy. This meant the `access_token` cookie was never forwarded, causing all authenticated API calls to return 401.

**Cause**  
`frontend/src/lib/api-client.ts` was initialised with `baseURL: "http://localhost:8000/api/v1"` — a direct FastAPI URL. The architecture requires all frontend API calls to go through the Next.js proxy at `/api/proxy/{path}`.

**Solution**  
Changed `baseURL` to `/api/proxy` in `api-client.ts`. The Next.js proxy route at `src/app/api/proxy/[...path]/route.ts` reads the httpOnly cookie and injects the `Authorization: Bearer {token}` header before forwarding to FastAPI.

**Future Recommendation**  
The rule is absolute: **no frontend JavaScript ever calls FastAPI directly.** Always use `apiClient.get('/endpoint')` which resolves to `/api/proxy/endpoint`. Document this in onboarding materials and enforce in code review.

---

### LL-0007 — router.push() Redirect Loop After Login
- **Phase:** Phase 1
- **Date:** 2026-06-11
- **Severity:** High
- **Category:** Frontend / Next.js

**Problem**  
After successful login, the page entered an infinite redirect loop between `/login` and `/dashboard`. The user was never actually redirected to the dashboard.

**Cause**  
Using `router.push(safePath)` followed by `router.refresh()` after login caused a race condition. The middleware re-evaluated the request before the cookie was fully set, saw no cookie, and redirected back to `/login`.

**Solution**  
Replaced `router.push()` + `router.refresh()` with `window.location.href = safePath`. This forces a full page navigation, ensuring the cookie is present when the middleware evaluates the next request.

**Future Recommendation**  
For post-auth redirects (login, logout), always use `window.location.href` rather than Next.js router methods. The Next.js App Router `router.push()` performs a client-side navigation that may not re-evaluate httpOnly cookies correctly in the same tick as a `Set-Cookie` response.

---

### LL-0008 — PDF Files Not Readable Programmatically
- **Phase:** Phase 5.4B/5.4C
- **Date:** 2026-06-29
- **Severity:** High
- **Category:** Data / Tooling

**Problem**  
All 8 TUT faculty prospectus PDFs downloaded during Phase 5.4B could not be read by the WebFetch tool or the Read tool. They were returned as binary-encoded streams.

**Cause**  
The Read tool (using `pdftoppm`) requires Poppler to be installed. Poppler is not available in this environment. The WebFetch tool does not have a built-in PDF text extractor — it only processes HTML responses.

**Solution**  
Documented PDFs as "downloaded, requires text extraction" in the TUT IKP v1.0.0. Phase 5.4D specifies using `pdfminer.six` (Python library, no system dependency) for PDF text extraction in Phase 5.4D.

**Future Recommendation**  
For PDF extraction in AQAA:
1. Use `pdfminer.six` (`python -m pip install pdfminer.six`) — pure Python, no system dependencies
2. Use `camelot-py` for table extraction from PDFs
3. Never use `pdftoppm` — Poppler is not reliably available on Windows
4. Always test PDF extraction on a sample page before bulk processing

---

### LL-0009 — Database Provenance Gap (Unexplained Records)
- **Phase:** Phase 5.4A
- **Date:** 2026-06-29
- **Severity:** Medium
- **Category:** Data / Process

**Problem**  
Phase 5.4A database audit revealed 5 institutions in the database but only 2 seeded by scripts. Similarly: 11 faculties (8 seeded), 22 programmes (16 seeded), 83 users (~52 seeded). The provenance of the gap records was unknown.

**Cause**  
Records were created manually via the AQAA API during feature testing in prior sessions, with no record kept of what was created. The platform lacked a formal data governance process.

**Solution**  
Introduced the IKP architecture (Phase 5.4C) with mandatory provenance on all records. All future institutional data must pass through the IKP pipeline with source attribution before loading.

**Future Recommendation**  
Never create test institutional data directly via the live API without documenting it. Use seed scripts with idempotency checks. If manual API testing creates institutional records, document them in a test log or add them to the seed script immediately.

---

### LL-0010 — Migration Partial Application (notification_type Enum)
- **Phase:** Phase 5
- **Date:** 2026-06-29
- **Severity:** High
- **Category:** Backend / Database / Tooling

**Problem**  
A previous session partially applied the Phase 5 migration — the `notification_type` PostgreSQL enum type was created in the database but the migration script failed before completing table creation. Alembic's `current` revision still showed the prior migration. Subsequent attempts to apply the migration failed with `DuplicateObjectError: type "notification_type" already exists`.

**Cause**  
The migration used `sa.Enum.create(op.get_bind(), checkfirst=True)` for enum creation. With the `asyncpg` driver, `checkfirst=True` does not reliably check for enum existence before attempting creation. A previous session's failed migration left the enum partially created.

**Solution**  
Rewrote the migration to use raw SQL `DO $$ BEGIN IF NOT EXISTS ... END $$;` blocks for all enum creation, and `CREATE TABLE IF NOT EXISTS` for table creation. This makes the migration fully idempotent at the SQL level.

**Future Recommendation**  
For PostgreSQL migrations involving enum types with asyncpg:
- Never use `sa.Enum.create(..., checkfirst=True)` — it is unreliable with asyncpg
- Always use raw SQL `DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='..') THEN CREATE TYPE ... END IF; END $$;`
- Use `CREATE TABLE IF NOT EXISTS` for tables
- Test migrations against a database that has had a partial previous application

---

### LL-0011 — Pipeline Path Calculation Off by One Level
- **Phase:** Phase 5.4G
- **Date:** 2026-06-29
- **Severity:** Medium
- **Category:** Backend / Tooling

**Problem**
The ADIP pipeline script found no PDFs on first run despite files existing. Zero documents were processed.

**Cause**
`Path(__file__).resolve().parents[5]` was used to navigate from `backend/app/adip/pipeline/run_tut_ict_extraction.py` to the project root. The count was wrong:
- `parents[0]` = `pipeline/`
- `parents[1]` = `adip/`
- `parents[2]` = `app/`
- `parents[3]` = `backend/`
- `parents[4]` = `AQAA/` ← project root (correct)
- `parents[5]` = `Desktop/` ← one level too high (wrong)

**Solution**
Changed `parents[5]` to `parents[4]`.

**Future Recommendation**
When building relative paths from deeply nested files, always verify with `print(Path(__file__).resolve().parents[N])` before using in production. Write a test that asserts the SOURCE_DIR exists.

---

### LL-0012 — Windows cp1252 Encoding Error When Writing JSON
- **Phase:** Phase 5.4G
- **Date:** 2026-06-29
- **Severity:** High
- **Category:** Tooling / Windows

**Problem**
The pipeline crashed with `UnicodeEncodeError: 'charmap' codec can't encode character '‛'` when writing JSON output files. PDFs contained curly/smart quotation marks that Windows' default cp1252 encoding cannot represent.

**Cause**
`Path.write_text(json.dumps(..., ensure_ascii=False))` uses the platform default encoding on Windows (cp1252). Smart quotes from PDF extraction are outside cp1252's range.

**Solution**
Added explicit `encoding="utf-8"` to all `write_text()` calls. Also changed to `ensure_ascii=True` as a belt-and-suspenders approach (escapes all non-ASCII as `\uXXXX`).

**Future Recommendation**
Always pass `encoding="utf-8"` to `Path.write_text()` in all AQAA scripts. Never rely on platform default encoding, especially on Windows. Consider adding `# -*- coding: utf-8 -*-` as a reminder at the top of file-writing modules.

---

### LL-0013 — APS Text Uses Parenthesized APS Abbreviation
- **Phase:** Phase 5.4H
- **Date:** 2026-07-01
- **Severity:** High
- **Category:** Backend / Data

**Problem**
The APS minimum score was not being extracted from TUT ICT Prospectus pages. Zero APS Math values were returned despite the data being present in the PDF.

**Cause**
The initial regex `r"APS\s+of\s+at\s+least\s+(\d+)"` did not match TUT's actual text format. TUT writes `(APS) of at least 26` — the abbreviation is wrapped in parentheses in the running text.

**Solution**
Changed regex to `r"\(?APS\)?\s+of\s+at\s+least\s+(\d+)"` which matches both `APS of at least` and `(APS) of at least`.

**Future Recommendation**
When writing regex patterns for academic PDF text, always extract a verbatim sample from the real PDF before writing the pattern. Abbreviations and acronyms in institutional documents are frequently surrounded by parentheses on first use. Test the pattern against `re.findall(pattern, verbatim_page_text)` before embedding in production code.

---

### LL-0014 — APS Regex Alternation Order Causes Premature Match
- **Phase:** Phase 5.4H
- **Date:** 2026-07-01
- **Severity:** Medium
- **Category:** Backend / Data

**Problem**
The APS Math regex `(?:Mathematics|Technical Mathematics)` matched `Mathematics` first within `Technical Mathematics`, then failed at the trailing `)` because the full alternation `Technical Mathematics` was never tried.

**Cause**
Python `re` alternation is ordered and returns the first match. `Mathematics` appears as a substring of `Technical Mathematics`, so the engine accepts `Mathematics` and then finds the closing `)` is missing (because the actual text continues with `or Technical Mathematics`).

**Solution**
Changed alternation to `(?:Technical\s+)?Mathematics\b[^)]*\)` — a permissive match that accepts any content before the closing parenthesis. This handles `Mathematics)`, `Technical Mathematics)`, and any future variants.

**Future Recommendation**
In regex alternation, always place longer/more-specific alternatives before shorter ones (`Technical Mathematics` before `Mathematics`). Alternatively, use a permissive bracket-content match (`[^)]*`) when the exact suffix is variable. Document the verbatim PDF text being matched in a comment next to the pattern.

---

### LL-0015 — APS Mathematical Literacy Score Uses Different Sentence Structure
- **Phase:** Phase 5.4H
- **Date:** 2026-07-01
- **Severity:** Medium
- **Category:** Backend / Data

**Problem**
APS Mathematical Literacy (ML) values were not extracted. Zero ML admission requirements were returned despite being listed for most TUT ICT programmes.

**Cause**
The Math APS sentence structure is `(APS) of at least 26 (with Mathematics...)`. The ML sentence is structurally different: `or 23 (with Mathematical Literacy)`. The ML value is introduced by `or N`, not `at least N`. The initial regex looked for `at least N` for both, missing all ML values.

**Solution**
Wrote a separate regex for ML: `r"\bor\s+(\d+)\s*\(with Mathematical\s*Literacy\)"`. This correctly captures the `or 23` prefix pattern.

**Future Recommendation**
When extracting paired values (Math APS vs ML APS), verify the sentence structure for each independently using verbatim PDF text samples. Never assume two related fields use the same surrounding syntax. Write separate named regex patterns for each field and unit-test them individually.

---

## Template for Future Entries

```markdown
### LL-XXXX — [Title]
- **Phase:** Phase X.Y
- **Date:** YYYY-MM-DD
- **Severity:** Critical | High | Medium | Low
- **Category:** Architecture | Integration | Data | Frontend | Backend | Tooling | Process

**Problem**
[What went wrong — observable symptoms]

**Cause**
[Root cause — not symptoms, the underlying reason]

**Solution**
[Exact fix applied — file names, line numbers if applicable]

**Future Recommendation**
[Actionable rule or check to prevent recurrence]
```
