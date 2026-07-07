# Public Knowledge Acquisition Engine — Architecture

**Split 2 Wave 2 · Status: Complete · 2026-07-07**

## Purpose

The Public Knowledge Acquisition Engine lets QA staff register **official, public**
institutional web sources and run acquisition jobs that fetch document metadata
from those sources, while strictly respecting `robots.txt`. It is the intake layer
that feeds the downstream Institutional Knowledge Foundation and RAG pipelines with
verifiable, provenance-tagged public material.

The engine never crawls internal or private university systems, never invents URLs,
and never persists raw document bytes in this wave — it captures metadata,
content-type, size, and a SHA-256 checksum used for deduplication and future
version tracking.

## Components (`backend/app/acquisition/`)

| Module | Responsibility |
|--------|----------------|
| `checksum.py` | SHA-256 over bytes / files. |
| `robots.py` | `robots.txt` compliance check. Fails **open** (logs and allows) on network error so transient failures never silently drop legitimate sources. |
| `document_detector.py` | Maps HTTP `Content-Type` to a coarse file type (`pdf`/`docx`/`html`/`txt`/`unknown`). |
| `classifier.py` | Rule-based document-type classifier from URL + title keywords (policy, prospectus, programme, …). |
| `downloader.py` | Safe httpx download: 15s timeout, 10 MB cap, follows redirects, extracts HTML `<title>`. Never raises — always returns a `DownloadResult`. |
| `deduplicator.py` | Skips documents already present for the institution by URL or checksum. |
| `job_manager.py` | Orchestrates a job: opens its **own** DB session, iterates active sources (max 5 downloads/job in local dev), logs each attempt, persists non-duplicate documents + an initial `DocumentVersion`, and records final job status. |

## Data model (migration `c3d4e5f6a7b8`)

- `acquisition_sources` — registered public sources (URL, name, type, provenance, active flag).
- `acquisition_jobs` — job runs (status, counts, timestamps, creator).
- `acquisition_logs` — per-URL attempt records (success, status code, robots-blocked).
- `downloaded_documents` — acquired document metadata (checksum, doc type, provenance).
- `document_versions` — version history per downloaded document.

All tables carry `institution_id` and are FK-cascaded to `institutions`.

## Tenant isolation & RBAC

- Every query filters by `institution_id`. System Admin may target any institution
  (or aggregate across all); other roles are locked to their own institution.
- Source create/delete: System Admin only. Job start/retry: QA officer and above.
- Students have no access to acquisition endpoints or the UI route.

## Safety constraints

- `robots.txt` is checked before every fetch; disallowed URLs are logged and skipped.
- Max 5 downloads per job (local-dev guard).
- 10 MB per-response content cap; 15s request timeout.
- No API keys or secrets are logged; HTTP responses never leak stack traces.

## Background execution

`POST /acquisition/jobs/start` returns HTTP 202 immediately with a `pending` job and
schedules `run_acquisition_job` as a FastAPI background task. The task opens a fresh
`AsyncSessionLocal` session (the request session is closed once the response is sent),
mirroring the audit-agent pattern. Poll `GET /acquisition/jobs/{id}` until status is
`completed` or `failed`.
