# Reporting & Analytics — Implementation Guide

## Package structure

```
backend/app/reporting/
├── __init__.py          package docstring
├── report_service.py    async DB aggregation (get_dashboard, summaries, compliance)
└── export_service.py    export_csv, export_excel, export_pdf_placeholder

backend/app/schemas/reporting.py    Pydantic models
backend/app/routes/reporting.py     router at /reporting

frontend/src/types/reporting.ts         TypeScript interfaces
frontend/src/hooks/useReporting.ts      TanStack Query hooks
frontend/src/app/(main)/analytics/      dashboard page + AnalyticsView
frontend/src/app/(main)/reports/        export page + ReportsView
```

---

## Key implementation notes

### Module count JOIN chain

`Module` has no `institution_id`. All module counts require a full JOIN chain:

```python
select(func.count())
    .select_from(Module)
    .join(Programme, Module.programme_id == Programme.id)
    .join(Department, Programme.department_id == Department.id)
    .join(Faculty, Department.faculty_id == Faculty.id)
    .where(Faculty.institution_id == iid)
```

Do not add `institution_id` to `Module` — this JOIN is the authoritative pattern.

### Tenant isolation

- `SYSTEM_ADMIN`: `get_dashboard()` queries all `is_active=True` institutions.
- Non-admin: scoped to `current_user.institution_id` — cross-institution access raises `PermissionError` (mapped to HTTP 403 in the route).

### CSV BOM

`export_csv()` prepends U+FEFF (the BOM character) before encoding as UTF-8, producing the 3-byte sequence `0xEF 0xBB 0xBF`. This makes the file open correctly in Microsoft Excel without a manual encoding dialog.

### Excel metadata sheet

`export_excel()` creates a second sheet called `Metadata` with report title, generation timestamp, platform name, and row count.

### PDF placeholder

`export_pdf_placeholder()` returns plain UTF-8 text with a header notice. The file downloads with `.txt` extension. Full PDF generation (reportlab) is planned.

### Compliance summary

`get_compliance_summary()` approximates compliance by equating completed audit runs with audited modules. The `compliant_count`, `at_risk_count`, and `non_compliant_count` fields are always 0 in the current implementation — they require per-finding aggregation which will be added in a future sprint.

---

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/reporting/dashboard` | HOD+ | Full aggregate dashboard |
| GET | `/reporting/institution-summary` | QA+ | Per-institution counts |
| GET | `/reporting/faculty-summary` | Dean+ | Per-faculty counts |
| GET | `/reporting/programme-summary` | Coordinator+ | Per-programme counts |
| GET | `/reporting/module-summary` | Lecturer+ | Per-module counts + latest audit |
| GET | `/reporting/compliance-summary` | QA+ | Compliance overview |
| GET | `/reporting/export/csv` | QA+ | Dashboard as CSV |
| GET | `/reporting/export/excel` | QA+ | Dashboard as Excel |
| GET | `/reporting/export/pdf` | QA+ | Dashboard as text (PDF placeholder) |

---

## Testing

```bash
cd backend
python -m pytest tests/test_reporting.py -q
```

Covers: CSV bytes/BOM/headers, Excel sheet validity, PDF placeholder notice, dashboard report lines, tenant isolation (own institution allowed, cross-institution denied), compliance rate formula.
