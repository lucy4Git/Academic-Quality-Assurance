# AQAA Phase D — Qdrant Snapshot

**Date:** 2026-07-17
**Qdrant Endpoint:** `http://localhost:6333`

---

## Collections

| Collection | Institution | Points | Dimensions | Distance | Status |
|-----------|------------|--------|-----------|---------|--------|
| `tut_2026_v1_1_0` | TUT | 196 | 384 | Cosine | green ✅ |
| `up_2026_v1_0_0` | UP | 28 | 384 | Cosine | green ✅ |

---

## Embedding Configuration

| Property | Value |
|----------|-------|
| Provider | `sentence-transformers` |
| Model | `all-MiniLM-L6-v2` |
| Dimensions | 384 |
| Distance | Cosine |
| Normalisation | L2 (by model default) |

---

## Collection Details

### tut_2026_v1_1_0

- **Institution:** Tshwane University of Technology
- **Knowledge package version:** v1.1.0 (2026)
- **Points:** 196 (module descriptions, programme summaries, faculty overviews)
- **Tenant field:** `institution_id = "46bb6ff4-2ad8-4abe-9ace-6422d9b7636c"`
- **HNSW config:** m=16, ef_construct=100, full_scan_threshold=10000

### up_2026_v1_0_0

- **Institution:** University of Pretoria
- **Knowledge package version:** v1.0.0 (2026)
- **Points:** 28 (initial load — UP knowledge package)
- **Tenant field:** `institution_id = "a3294995-a14e-4574-950a-8d77031d8310"`
- **HNSW config:** m=16, ef_construct=100, full_scan_threshold=10000

---

## Data Sensitivity

Content is test institutional knowledge packages (module/programme descriptions). No confidential student data, no personal records, no sensitive documents. **Safe for backup and restoration.**

---

## Backup Strategy

### Option A: Qdrant Snapshot API (preferred if data volume grows)

```bash
# Create snapshot
curl -X POST http://localhost:6333/collections/tut_2026_v1_1_0/snapshots
# Returns: { "result": { "name": "tut_2026_v1_1_0-...-snapshot" } }

# Download snapshot
curl -O http://localhost:6333/collections/tut_2026_v1_1_0/snapshots/{snapshot_name}
```

### Option B: Reindex from source (current recommended approach)

Since all indexed data comes from institutional knowledge package files, rebuilding the collection from source is simpler and guaranteed to be current:

```bash
# Delete and recreate collection
curl -X DELETE http://localhost:6333/collections/tut_2026_v1_1_0
python backend/scripts/reindex_knowledge_packages.py --institution TUT

# Or via the seeding pipeline
cd backend && python ../database/seed_data/run_all.py
```

---

## Restore Strategy

```bash
# 1. Verify Qdrant is running
curl http://localhost:6333/health

# 2. Create collection with correct params
curl -X PUT http://localhost:6333/collections/tut_2026_v1_1_0 \
  -H "Content-Type: application/json" \
  -d '{"vectors": {"size": 384, "distance": "Cosine"}}'

# 3. Reindex
python backend/scripts/reindex_knowledge_packages.py --institution TUT UP

# 4. Verify
curl http://localhost:6333/collections/tut_2026_v1_1_0
# Expected: points_count > 0
```

---

## Manifest File

`database/snapshots/phase-d/qdrant_collection_manifest.json`
