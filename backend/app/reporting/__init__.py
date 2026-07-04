"""Reporting and Analytics subsystem.

Provides institution-scoped dashboard aggregates, faculty/programme/module
summaries, compliance overviews, and data exports (CSV, Excel, PDF placeholder).

Entry points
------------
- report_service.py  — async DB aggregation functions
- export_service.py  — CSV and Excel export helpers
- routes/reporting.py — FastAPI route handlers (HOD+ for most; QA+ for exports)
"""
