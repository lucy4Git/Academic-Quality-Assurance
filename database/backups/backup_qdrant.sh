#!/usr/bin/env bash
# AQAA Qdrant snapshot backup script
# E1-OPS-003: Backup and restore procedures
#
# Usage:
#   ./backup_qdrant.sh [BACKUP_DIR]
#
# Environment variables:
#   QDRANT_URL             default: http://localhost:6333
#   QDRANT_API_KEY         optional; set if Qdrant API key auth is enabled
#
# Creates a Qdrant snapshot for every collection and downloads it
# to BACKUP_DIR/qdrant/<collection>/<timestamp>.snapshot

set -euo pipefail

BACKUP_DIR="${1:-/var/backups/aqaa}"
QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")

AUTH_HEADER=""
if [[ -n "${QDRANT_API_KEY:-}" ]]; then
  AUTH_HEADER="api-key: ${QDRANT_API_KEY}"
fi

snapshot_collection() {
  local name="$1"
  local dest="${BACKUP_DIR}/qdrant/${name}"
  mkdir -p "${dest}"

  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Creating snapshot for collection: ${name}"

  # Trigger snapshot creation
  if [[ -n "${AUTH_HEADER}" ]]; then
    SNAPSHOT_RESPONSE=$(curl -sf -X POST \
      "${QDRANT_URL}/collections/${name}/snapshots" \
      -H "${AUTH_HEADER}")
  else
    SNAPSHOT_RESPONSE=$(curl -sf -X POST \
      "${QDRANT_URL}/collections/${name}/snapshots")
  fi

  SNAPSHOT_NAME=$(echo "${SNAPSHOT_RESPONSE}" | python3 -c \
    "import sys,json; print(json.load(sys.stdin)['result']['name'])")

  # Download the snapshot file
  local outfile="${dest}/${TIMESTAMP}_${SNAPSHOT_NAME}"
  if [[ -n "${AUTH_HEADER}" ]]; then
    curl -sf \
      "${QDRANT_URL}/collections/${name}/snapshots/${SNAPSHOT_NAME}" \
      -H "${AUTH_HEADER}" \
      -o "${outfile}"
  else
    curl -sf \
      "${QDRANT_URL}/collections/${name}/snapshots/${SNAPSHOT_NAME}" \
      -o "${outfile}"
  fi

  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Snapshot saved: ${outfile} ($(du -sh "${outfile}" | cut -f1))"
}

# List all collections
if [[ -n "${AUTH_HEADER}" ]]; then
  COLLECTIONS_JSON=$(curl -sf "${QDRANT_URL}/collections" -H "${AUTH_HEADER}")
else
  COLLECTIONS_JSON=$(curl -sf "${QDRANT_URL}/collections")
fi

COLLECTIONS=$(echo "${COLLECTIONS_JSON}" | python3 -c \
  "import sys,json; [print(c['name']) for c in json.load(sys.stdin)['result']['collections']]")

if [[ -z "${COLLECTIONS}" ]]; then
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] No Qdrant collections found — nothing to back up."
  exit 0
fi

for col in ${COLLECTIONS}; do
  snapshot_collection "${col}"
done

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] All Qdrant snapshots complete."
