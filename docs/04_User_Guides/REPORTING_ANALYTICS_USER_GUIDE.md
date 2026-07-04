# Reporting & Analytics — User Guide

## Overview

AQAA provides two analytics surfaces:

- **Analytics** (`/analytics`) — live institutional dashboard with counts, compliance overview, and knowledge index status.
- **Reports** (`/reports`) — export the dashboard data as CSV, Excel, or PDF.

---

## Analytics dashboard

Navigate to **Analytics** in the sidebar (visible to HOD and above).

### Platform summary cards

Shows aggregate counts: institutions, programmes, modules, evidence files, audit runs (with completed/failed split), faculties, departments, and an overall audit completion rate percentage.

### Compliance overview

Shows total modules in scope, number audited, compliance rate percentage, and unaudited count, scoped to your visible institutions.

### Knowledge index status

Shows the Qdrant indexing status for each active pilot institution (TUT, UP), including IKP version, collection name, and chunk count.

### Per-institution breakdown

Cards for each institution showing faculties, programmes, modules, audit runs, files, and Qdrant index status.

---

## Reports (export)

Navigate to **Reports** in the sidebar (visible to HOD and above).

Three export formats are available:

| Format | Description |
|--------|-------------|
| **CSV** | UTF-8 with BOM; opens in Excel without encoding issues |
| **Excel (.xlsx)** | Multi-sheet workbook; data sheet + metadata sheet |
| **PDF (text)** | Plain-text placeholder with a notice; full PDF is planned |

Click the **Download** button for your chosen format. The file downloads automatically with a timestamped filename (e.g. `aqaa_report_20260702_143000.csv`).

---

## Role access

| Role | Analytics | Reports |
|------|-----------|---------|
| System Admin | All institutions | All institutions |
| QA Officer | Own institution | Own institution |
| Faculty Dean | Own institution | Own institution |
| HOD | Own institution | Own institution |
| Coordinator and below | No access | No access |
