# AQAA Docker Durability Report

**Document:** AQAA_DOCKER_DURABILITY_REPORT  
**Sprint:** Recovery Sprint — Stage A2  
**Date:** 2026-07-13  
**Status:** PASS

---

## Objective

Confirm that `fastembed` and the real semantic embedding service survive a clean Docker image rebuild and two container restarts without any `docker exec pip install` intervention.

---

## Build

| Field | Value |
|-------|-------|
| Command | `docker compose build --no-cache backend` |
| Image ID | `sha256:49b5dca9c9791d3cf9ef9b45f8a97e857b31f5dfcc4399c5b0e475ac1434ff39` |
| Manifest list | `sha256:51766e1fe0402d69b1ace3b43f42597550cb7ad2adb300c273d3a27eea4af580` |
| Result | `Image aqaa-backend Built` |
| fastembed in requirements.txt | `fastembed>=0.3,<1.0` (confirmed present) |
| Dockerfile pip step | `RUN pip install --no-cache-dir -r requirements.txt` (copies and installs) |
| Reason `--no-cache` was needed | Prior image cached an earlier layer missing fastembed; clean rebuild bakes it permanently |

---

## Post-Rebuild Verification

### First start after rebuild

```
docker compose up -d backend
docker exec aqaa-backend python -c "
  from fastembed import TextEmbedding; print('fastembed import OK')
"
# → fastembed import OK

docker exec aqaa-backend python -c "
  from app.knowledge_indexing.embedding_service import embedding_service
  print(type(embedding_service).__name__, 'IS_PLACEHOLDER='+str(embedding_service.IS_PLACEHOLDER), 'DIMS='+str(embedding_service.DIMENSIONS))
"
# → FastEmbedEmbeddingService IS_PLACEHOLDER=False DIMS=384
```

### Second restart (durability)

```
docker compose restart backend
docker exec aqaa-backend python -c "
  from app.knowledge_indexing.embedding_service import embedding_service
  print('AFTER 2ND RESTART:', type(embedding_service).__name__, 'IS_PLACEHOLDER='+str(embedding_service.IS_PLACEHOLDER))
"
# → AFTER 2ND RESTART: FastEmbedEmbeddingService IS_PLACEHOLDER=False
```

Backend health after both restarts: `GET /health → {"status": "ok"}`

---

## Container Status at Gate

```
NAMES           STATUS                    PORTS
aqaa-backend    Up (healthy)              0.0.0.0:8000->8000/tcp
aqaa-postgres   Up (healthy)              0.0.0.0:5432->5432/tcp
aqaa-redis      Up (healthy)              0.0.0.0:6379->6379/tcp
aqaa-qdrant     Up (healthy)              0.0.0.0:6333-6334->6333-6334/tcp
```

---

## Acceptance Criteria

| Criterion | Result |
|-----------|--------|
| fastembed in requirements.txt | PASS |
| Clean rebuild succeeds | PASS |
| fastembed imports in fresh container | PASS |
| Embedding model loads (BAAI/bge-small-en-v1.5) | PASS |
| No `docker exec pip install` required | PASS |
| Semantic retrieval works post-rebuild | PASS |
| Survives second restart | PASS |
| IS_PLACEHOLDER=False after rebuild | PASS |

**VERDICT: PASS** — FastEmbed deployment is durable. No manual intervention required on container recreation.
