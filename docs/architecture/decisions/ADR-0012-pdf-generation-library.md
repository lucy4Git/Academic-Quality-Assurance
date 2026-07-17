# ADR-0012 — PDF Generation Library

**Date:** 2026-07-17
**Status:** PROPOSED
**Author:** AQAA Engineering
**Deciders:** AQAA Engineering — Principal Systems Architect

---

## Context

Phase D has a placeholder PDF export endpoint (`GET /api/v1/reports/{id}?format=pdf`) that returns a stub response. Phase E requires a real implementation producing audit reports with:
- Cover page (institution name, report date, audit type, scope)
- Executive summary section
- Findings table (ID, title, severity, status, regulatory clause)
- Evidence matrix (module, evidence submitted, evidence required)
- Regulatory citation list with source_status badges

The library must work inside the FastAPI Docker container (no external browser process).

---

## Options Considered

### Option A — WeasyPrint

- Python library: renders HTML/CSS to PDF via Cairo graphics engine
- Approach: generate HTML template → pass to WeasyPrint → PDF bytes
- HTML templates can be styled with Tailwind-like CSS or custom CSS
- System dependency: `libcairo2`, `libpango1.0-0`, `libpangocairo-1.0-0`, `libffi-dev`
- Must be installed in Docker image; adds ~150 MB to image
- Handles tables, multi-page layout, headers/footers natively

### Option B — ReportLab

- Python library: imperative PDF drawing API (not HTML-based)
- Very mature; no system dependencies; pure Python
- Requires building the layout programmatically (no HTML/CSS)
- More verbose code for complex layouts
- No dependency on system graphics libraries

### Option C — Playwright (headless browser)

- Renders HTML in a real Chromium browser, saves to PDF
- Highest rendering fidelity (pixel-perfect)
- Heavyweight: Chromium binary is ~300 MB; startup time ~2–3s per report
- Requires a separate Playwright install in the Docker image
- Overkill for structured document output

---

## Decision

**WeasyPrint (Option A)** with HTML Jinja2 templates.

### Rationale

1. **HTML-based templates**: Report templates are HTML with CSS, making them maintainable by engineers familiar with web development. Changing report layout does not require understanding ReportLab's drawing primitives.

2. **Native table and multi-page support**: Findings tables and evidence matrices map cleanly to HTML `<table>` elements. WeasyPrint handles page breaks, headers, and footers via CSS `@page` rules.

3. **Sufficient for pilot scale**: Reports at pilot scale are modest (< 200 findings). WeasyPrint generates such reports in 2–10 seconds.

4. **Jinja2 already in stack**: FastAPI's ecosystem uses Jinja2 for templates. No new templating engine required.

### Accepted Trade-offs

- System dependencies increase Docker image size (~150 MB)
- Complex CSS may not render identically across WeasyPrint versions; report templates must be tested after WeasyPrint upgrades
- Playwright is superior for pixel-perfect fidelity, but fidelity is not required for audit reports (structured content, not design-sensitive)

### Implementation

- `backend/app/services/report_generation_service.py` (new file)
- Templates: `backend/app/templates/reports/audit_report.html.j2` (new directory)
- `weasyprint` added to `backend/requirements.txt`
- Docker image `backend/Dockerfile` updated to install system dependencies via `apt-get`

---

**Decision recorded by:** AQAA Engineering — 2026-07-17
