# Knowledge Review Centre — Maintenance Guide

**Version:** 1.0.0 | **Last Updated:** 2026-07-01

---

## Re-Running a Batch from Fresh ADIP Output

If the ADIP pipeline has been re-run and new extraction candidates are available:

1. In the KRC UI, note the existing batch ID.
2. Create a new batch via **POST /knowledge-review/batches/from-adip-output** with an updated `batch_name` that includes the new version.
3. Do not delete the old batch — it is the audit trail.

## Clearing Exported Data

The approved/ directory is written to but never cleaned up automatically. To re-export after additional reviews:

1. Make more item decisions (approve/reject/edit).
2. Call `POST /knowledge-review/batches/{id}/export-approved-ikp` again.
3. The new export will overwrite the previous approved/ files.

## Re-Seeding TUT Data

If the TUT database records need to be refreshed from the latest approved IKP:

```bash
# Ensure DB is running
docker compose up -d postgres

# From project root
cd backend
python ../database/seed_data/seed_tut.py
```

The script is idempotent — it will update existing records without creating duplicates or touching GFU/RCT records.

## Re-Building AI-Ready Outputs

After a new export:

```bash
python backend/app/adip/pipeline/build_ai_ready_outputs.py
```

This overwrites the ai/ directory with fresh knowledge chunks and manifests.

## Bootstrap Approved IKP (Development Only)

If you need the approved/ directory without going through the API review flow:

```bash
python backend/app/adip/pipeline/bootstrap_approved_ikp.py
```

This treats all ADIP extraction candidates as approved. For production, always use the KRC API.

## Monitoring Batch Status

Check the batch list in the KRC UI or via API:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/knowledge-review/batches
```

Watch for batches stuck in `in_review` state — they may need follow-up from QA officers.

## Database Cleanup

To remove all KRC data (e.g. for a fresh development reset):

```sql
DELETE FROM knowledge_review_items;
DELETE FROM knowledge_review_batches;
```

Then re-create batches from the extraction output.

## Sprint 1 Validation

Run at any time to check all expected files exist:

```bash
python backend/app/adip/pipeline/validate_sprint1.py
```

Exit code 0 = all OK. Exit code 1 = something missing.
