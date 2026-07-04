# Knowledge Review Centre — User Guide

**Version:** 1.0.0 | **Last Updated:** 2026-07-01  
**Audience:** QA Officers

---

## Overview

The Knowledge Review Centre lets QA officers review extracted academic knowledge before it enters the institutional knowledge base. You can approve values that look correct, reject incorrect ones, or edit them to the right value.

---

## Getting Started

1. Log in as a QA Officer or System Administrator.
2. Click **Knowledge Review** in the left sidebar.
3. You will see a list of review batches.

---

## Creating a Review Batch from TUT ICT 2026 Data

1. Click **Load TUT ICT 2026 Batch**.
2. The system reads the ADIP extraction output and creates one item per unique (entity, field) pair.
3. You are taken to the batch review page.

---

## Reviewing Items

On the batch detail page you will see a table of all extracted field values. Each row shows:

- **Entity** — the programme or module name
- **Field** — the field (e.g. `nqf_level`, `total_credits`)
- **Value** — the extracted (or edited) value
- **Confidence** — green (high, auto-approvable), yellow (medium), red (low)
- **Status** — current decision state
- **Source** — source document and page number

### Approving an Item

Click **Approve** on the row. The item status changes to `approved`.

### Rejecting an Item

1. Enter a rejection reason in the field next to the row.
2. Click **Reject**. A reason is mandatory to reject an item.

### Editing an Item

1. Click **Edit** on any row (including already-approved items).
2. The Edit dialog opens with the current value pre-filled.
3. Correct the value and optionally add a reason.
4. Click **Save Edit**. The item status becomes `edited`.

---

## Bulk Auto-Approve

Click **Approve High-Confidence** to automatically approve all pending items with a confidence score of 90% or above. This is useful for a first pass when most extractions are reliable.

---

## Filtering Items

Use the filter bar above the table to narrow down:
- **Type**: All / Programme / Module / Admission
- **Status**: All / Pending / Approved / Rejected / Edited
- **Confidence**: All / High (≥90%) / Medium (70–89%)

---

## Exporting the Approved IKP

Once you have reviewed items, click **Export Approved IKP**. The system:
1. Collects all approved and edited items.
2. Groups them by entity and writes structured JSON files.
3. Updates the batch status to `Exported`.

The export is written to `ikp/institutions/tut/2026/v1.1.0/approved/`.

---

## Item Detail Page

Click any entity name in the table to open the full item detail page. You can:
- See the extracted value, confidence score, extraction method, source document, and page number.
- View decision history if the item has already been reviewed.
- Approve, reject, or edit the item from this page.
