# AQAA Sprint E0 — Implementation Dependency Register

**Date:** 2026-07-20
**Branch:** `feature/phase-e-sprint-e0`
**Prepared by:** AQAA Engineering — Principal Software Architect

> **No dependency is installed during Sprint E0.** This register documents what is currently installed and what is proposed for Phase E. All proposed dependencies require owner approval and online verification before installation.

---

## 1. Currently Installed Backend Dependencies (Python)

Source: `backend/requirements.txt` — verified 2026-07-20.

| Package | Version pin | Purpose | License | Notes |
|---------|------------|---------|---------|-------|
| fastapi | >=0.115,<1.0 | Web framework | MIT | Stable; no Phase E change planned |
| uvicorn[standard] | >=0.32,<1.0 | ASGI server | BSD | — |
| pydantic / pydantic-settings | >=2.9,<3.0 | Schema validation + settings | MIT | — |
| python-dotenv | >=1.0,<2.0 | .env loading | BSD | — |
| PyJWT | >=2.9,<3.0 | JWT encode/decode | MIT | — |
| bcrypt | >=4.0,<5.0 | Password hashing | Apache 2.0 | — |
| pypdf | >=4.0,<6.0 | PDF text extraction | MIT | — |
| python-docx | >=1.1,<2.0 | DOCX extraction (existing) | MIT | Also needed for E-FR-034 export |
| openpyxl | >=3.1,<4.0 | XLSX extraction + export | MIT | Already covers E-FR-035 |
| python-pptx | >=1.0,<2.0 | PPTX extraction | MIT | — |
| Pillow | >=10.0,<12.0 | Image decode | HPND | — |
| pytesseract | >=0.3,<1.0 | OCR binding | Apache 2.0 | Requires Tesseract binary on host |
| pdfminer.six | >=20221105 | PDF layout extraction | MIT | — |
| pymupdf | >=1.24 | PDF metadata + rendering | AGPL-3.0 | AGPL — commercial use requires license review |
| beautifulsoup4 | >=4.12 | HTML extraction | MIT | — |
| lxml | >=5.0 | XML/HTML parser | BSD | — |
| pdfplumber | >=0.11 | PDF table extraction | MIT | — |
| aiofiles | >=24.0,<25.0 | Async file I/O | Apache 2.0 | — |
| python-multipart | >=0.0.9,<1.0 | Form + file upload | Apache 2.0 | — |
| sqlalchemy | >=2.0.36,<3.0 | ORM | MIT | — |
| asyncpg | >=0.30,<1.0 | Async PostgreSQL driver | Apache 2.0 | — |
| psycopg2-binary | >=2.9 | Sync PostgreSQL (Alembic, seeds) | LGPL | — |
| alembic | >=1.14,<2.0 | Database migrations | MIT | — |
| qdrant-client | >=1.12,<1.14 | Qdrant REST + gRPC | Apache 2.0 | Pinned to match server 1.12.x |
| fastembed | >=0.3,<1.0 | Local ONNX embeddings | Apache 2.0 | Avoids PyTorch dependency |
| pytest | >=8.3,<9.0 | Test runner | MIT | — |
| pytest-asyncio | >=0.24,<1.0 | Async test support | Apache 2.0 | — |
| httpx | >=0.27,<1.0 | HTTP test client | BSD | — |

**PyMuPDF / AGPL flag:** PyMuPDF (fitz) is AGPL-3.0. Commercial use in a proprietary product requires a commercial license or removal. This must be reviewed before commercial launch (Phase F). No action required for pilot.

---

## 2. Proposed Backend Dependencies (Phase E — NOT YET INSTALLED)

All items below require online verification of current version, changelog, and security advisories before installation.

### 2.1 ARQ — Async Redis Queue (ADR-0009)

| Field | Value |
|-------|-------|
| **Package** | `arq` |
| **Current version on PyPI** | ~0.26 (verify before install) |
| **Proposed purpose** | Background task queue, scheduled jobs, dead-letter mechanism |
| **Required sprint** | E1 |
| **Security risk** | MEDIUM — task input must be validated; Redis must not be publicly exposed |
| **License** | MIT |
| **Maintenance status** | Active (verify — PyPI release date) |
| **Windows compatibility** | Yes (asyncio-based; no POSIX-only APIs) |
| **Docker compatibility** | Yes — ARQ worker runs as a separate container |
| **Operational burden** | New `aqaa-worker` container; health check required; worker restart policy |
| **Alternative** | Celery + Redis (heavier, synchronous-first) |
| **Approval status** | PENDING — E0-OD-001 |
| **Online verification required** | YES — check latest release, open CVEs, compatibility with Python 3.13 |

### 2.2 structlog (ADR-0011)

| Field | Value |
|-------|-------|
| **Package** | `structlog` |
| **Current version** | ~24.x (verify) |
| **Proposed purpose** | Structured JSON logging with correlation IDs |
| **Required sprint** | E1 |
| **Security risk** | LOW — output library; must sanitise log values to exclude PII and tokens |
| **License** | MIT |
| **Maintenance status** | Active, widely used |
| **Windows compatibility** | Yes |
| **Docker compatibility** | Yes |
| **Operational burden** | Minimal — replaces Python `logging` calls |
| **Alternative** | loguru; python-json-logger |
| **Approval status** | PENDING — E0-OD-003 |
| **Online verification required** | YES |

### 2.3 prometheus-fastapi-instrumentator (ADR-0011)

| Field | Value |
|-------|-------|
| **Package** | `prometheus-fastapi-instrumentator` |
| **Current version** | ~7.x (verify) |
| **Proposed purpose** | Auto-instrument FastAPI routes with Prometheus metrics |
| **Required sprint** | E1 |
| **Security risk** | LOW — /metrics endpoint must be protected by API key, not user auth |
| **License** | ISC |
| **Maintenance status** | Active |
| **Windows compatibility** | Yes |
| **Docker compatibility** | Yes — Prometheus scrapes /metrics from backend container |
| **Operational burden** | New `aqaa-prometheus` container in docker-compose |
| **Alternative** | opentelemetry-sdk + prometheus exporter |
| **Approval status** | PENDING — E0-OD-003 |
| **Online verification required** | YES |

### 2.4 sentry-sdk (ADR-0011)

| Field | Value |
|-------|-------|
| **Package** | `sentry-sdk[fastapi]` |
| **Current version** | ~2.x (verify) |
| **Proposed purpose** | Error tracking and alerting (Sentry SaaS free/team tier) |
| **Required sprint** | E1 |
| **Security risk** | MEDIUM — Sentry receives error context which may include PII; `send_default_pii = False` must be set; Sentry DSN is not a secret but must not expose user data |
| **License** | MIT |
| **Maintenance status** | Active |
| **Windows compatibility** | Yes |
| **Docker compatibility** | Yes |
| **Operational burden** | Requires Sentry account (free tier sufficient for pilot) |
| **Alternative** | GlitchTip (self-hosted Sentry alternative) |
| **Approval status** | PENDING — E0-OD-003 |
| **Online verification required** | YES |

### 2.5 slowapi (Rate Limiting)

| Field | Value |
|-------|-------|
| **Package** | `slowapi` |
| **Current version** | ~0.1.9 (verify) |
| **Proposed purpose** | Rate limiting middleware for FastAPI; uses Redis as storage |
| **Required sprint** | E1 |
| **Security risk** | LOW — limits requests; requires Redis for distributed rate limiting across multiple backend instances |
| **License** | MIT |
| **Maintenance status** | Actively maintained (verify) |
| **Windows compatibility** | Yes |
| **Docker compatibility** | Yes |
| **Operational burden** | Low — middleware registration only |
| **Alternative** | limits + redis; fastapi-limiter |
| **Approval status** | PENDING |
| **Online verification required** | YES |

### 2.6 WeasyPrint (ADR-0012)

| Field | Value |
|-------|-------|
| **Package** | `weasyprint` |
| **Current version** | ~62.x (verify) |
| **Proposed purpose** | HTML/CSS → PDF conversion for audit reports (E-FR-033) |
| **Required sprint** | E3 |
| **Security risk** | HIGH — must sanitise HTML template inputs to prevent SVG/CSS injection; must disable external URL fetching in WeasyPrint config |
| **License** | BSD |
| **Maintenance status** | Active |
| **Windows compatibility** | YES — requires Cairo + Pango system libraries; on Windows these are installed via MSYS2 or a pre-built wheel. Docker is the recommended deployment path |
| **Docker compatibility** | YES — requires `libcairo2 libpango1.0-0 libpangocairo-1.0-0 libffi-dev` in Dockerfile; adds ~150MB to image |
| **Operational burden** | Significant — Dockerfile changes required; image rebuild |
| **Alternative** | ReportLab (no system deps); xhtml2pdf (simpler CSS); Playwright headless Chrome (large) |
| **Approval status** | PENDING — ADR-0012 (decide by Sprint E2) |
| **Online verification required** | YES — validate Docker image size impact |

### 2.7 python-magic (MIME type validation)

| Field | Value |
|-------|-------|
| **Package** | `python-magic` |
| **Current version** | ~0.4.27 (verify) |
| **Proposed purpose** | Binary-header MIME type detection for file upload security (E-FR-043) |
| **Required sprint** | E1 |
| **Security risk** | LOW — read-only file inspection |
| **License** | MIT |
| **Maintenance status** | Stable |
| **Windows compatibility** | Requires `libmagic` DLL on Windows; use `python-magic-bin` on Windows or rely on Docker |
| **Docker compatibility** | YES — `libmagic1` in Dockerfile |
| **Operational burden** | Dockerfile change required |
| **Alternative** | `filetype` (pure Python, no system deps) — preferred on Windows |
| **Approval status** | PENDING |
| **Online verification required** | YES |

### 2.8 pyotp (MFA / TOTP)

| Field | Value |
|-------|-------|
| **Package** | `pyotp` |
| **Current version** | ~2.9.x (verify) |
| **Proposed purpose** | TOTP-based MFA for QA Officer and above (E-FR-045) |
| **Required sprint** | E2 |
| **Security risk** | LOW — pure Python; generates TOTP secrets that must be stored encrypted |
| **License** | MIT |
| **Maintenance status** | Active |
| **Windows compatibility** | Yes |
| **Docker compatibility** | Yes |
| **Operational burden** | Requires QR code generation for TOTP enrollment |
| **Alternative** | django-otp (Django-specific, not applicable) |
| **Approval status** | PENDING |
| **Online verification required** | YES |

### 2.9 redis (Python redis client for ARQ)

| Field | Value |
|-------|-------|
| **Package** | `redis[hiredis]` |
| **Current version** | ~5.x (verify) |
| **Proposed purpose** | Redis client for ARQ worker + JWT deny-list + analytics caching |
| **Required sprint** | E1 |
| **Security risk** | LOW — client library; Redis itself must not be publicly exposed |
| **License** | MIT |
| **Maintenance status** | Official redis-py from Redis Inc. — actively maintained |
| **Windows compatibility** | Yes |
| **Docker compatibility** | Yes |
| **Operational burden** | Minimal |
| **Alternative** | aioredis (now merged into redis-py) |
| **Approval status** | PENDING — E0-OD-001 (ARQ decision) |
| **Online verification required** | YES |

---

## 3. Proposed Frontend Dependencies (NOT YET INSTALLED)

| Package | Purpose | Sprint | Approval |
|---------|---------|--------|----------|
| `@playwright/test` | End-to-end browser testing (E0-OD-008) | E1 | PENDING |
| `@axe-core/playwright` | WCAG accessibility scanning in Playwright | E4 | PENDING |

No other frontend dependencies are proposed for Phase E. All existing frontend dependencies (React 18, Next.js 14, Tailwind CSS, ShadCN, TanStack Query, Zustand, react-markdown, etc.) are sufficient for Phase E UI work.

---

## 4. Docker Services (Proposed)

| Service | Image | Purpose | Required sprint | Status |
|---------|-------|---------|----------------|--------|
| `aqaa-postgres` | postgres:16-alpine | Primary database | Existing | OPERATIONAL |
| `aqaa-redis` | redis:7-alpine | Cache + task broker | Existing | OPERATIONAL (not actively used for ARQ yet) |
| `aqaa-qdrant` | qdrant/qdrant:v1.12.4 | Vector store | Existing | OPERATIONAL |
| `aqaa-backend` | custom build | FastAPI application | Existing | OPERATIONAL |
| `aqaa-worker` | same as backend | ARQ background worker | E1 | PROPOSED — ADR-0009 |
| `aqaa-caddy` | caddy:2-alpine | TLS reverse proxy | E1 | PROPOSED — ADR-0015 |
| `aqaa-prometheus` | prom/prometheus | Metrics collection | E1 | PROPOSED — ADR-0011 |
| `aqaa-clamav` | clamav/clamav | Malware scanning | E1 | PROPOSED — E-FR-041 |
| `aqaa-grafana` | grafana/grafana | Metrics visualisation | E3 | PROPOSED — optional |

---

## 5. External API Dependencies

| Service | Purpose | Auth mechanism | Current usage | Phase E usage | Risk |
|---------|---------|---------------|--------------|--------------|------|
| OpenAI API | LLM inference (gpt-4o-mini) | API key in config | AI assistant (configurable) | Continued — AI Workspace + audit summaries | MEDIUM — key exposure; cost control |
| Anthropic API | LLM inference (claude-haiku) | API key in config | Configurable alternative | Same | MEDIUM |
| Ollama | Local LLM (development) | None | LOCAL_DEV mode | Same | LOW |
| Gemini API | LLM inference | API key in config | Configurable alternative | Same | MEDIUM |
| Sentry SaaS | Error tracking | DSN key | Not yet integrated | E1+ | LOW (no user PII sent) |
| Let's Encrypt | TLS certificates (via Caddy) | None — ACME protocol | Not yet integrated | E1 (Caddy) | LOW |

---

## 6. PyMuPDF License Note (Existing Dependency)

PyMuPDF (`pymupdf>=1.24`) is currently in `requirements.txt` and is licensed under **AGPL-3.0**. AGPL requires that any software linking to it that is distributed or offered as a service must also be open-sourced under AGPL, or a commercial license must be purchased from Artifex.

**Action required before commercial launch (Phase F):** Assess whether PyMuPDF commercial license is required or replace with an MIT-licensed alternative (`pypdf` is already installed and handles most use cases).

**No action required for Phase E pilot** — AGPL applies to distribution; pilot with a single institution under a data-processing agreement is not typically considered distribution requiring AGPL compliance. Legal review recommended.

---

*Prepared by: AQAA Engineering — Principal Software Architect*
*Date: 2026-07-20*
*No dependencies were installed during the preparation of this document.*
