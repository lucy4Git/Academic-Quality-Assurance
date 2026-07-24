#!/usr/bin/env bash
# AQAA PostgreSQL backup script
# E1-OPS-003: Backup and restore procedures
#
# Usage:
#   ./backup_postgres.sh [BACKUP_DIR]
#
# Environment variables (or set in .env):
#   BACKUP_POSTGRES_HOST   default: localhost
#   BACKUP_POSTGRES_PORT   default: 5432
#   BACKUP_POSTGRES_USER   default: aqaa
#   BACKUP_POSTGRES_DB     default: aqaa
#   PGPASSWORD             required (do NOT hard-code — set in environment)
#
# Output:
#   <BACKUP_DIR>/aqaa_<YYYY-MM-DD_HHMMSS>.dump  (pg_dump custom format)
#
# Retention: keep the 14 most recent backups, delete older ones.
#
# Restore:
#   pg_restore -h <host> -U <user> -d <db> --clean --if-exists \
#              <backup_file>.dump

set -euo pipefail

BACKUP_DIR="${1:-/var/backups/aqaa}"
HOST="${BACKUP_POSTGRES_HOST:-localhost}"
PORT="${BACKUP_POSTGRES_PORT:-5432}"
USER="${BACKUP_POSTGRES_USER:-aqaa}"
DB="${BACKUP_POSTGRES_DB:-aqaa}"
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
FILENAME="${BACKUP_DIR}/aqaa_${TIMESTAMP}.dump"
KEEP=14  # keep the 14 most recent backups

if [[ -z "${PGPASSWORD:-}" ]]; then
  echo "ERROR: PGPASSWORD environment variable is not set." >&2
  exit 1
fi

mkdir -p "${BACKUP_DIR}"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting PostgreSQL backup: ${FILENAME}"

pg_dump \
  --host="${HOST}" \
  --port="${PORT}" \
  --username="${USER}" \
  --dbname="${DB}" \
  --format=custom \
  --compress=9 \
  --no-password \
  --file="${FILENAME}"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Backup complete: $(du -sh "${FILENAME}" | cut -f1)"

# Prune old backups — keep only the $KEEP most recent
BACKUP_COUNT=$(ls -1 "${BACKUP_DIR}"/aqaa_*.dump 2>/dev/null | wc -l)
if (( BACKUP_COUNT > KEEP )); then
  ls -1t "${BACKUP_DIR}"/aqaa_*.dump | tail -n +"$((KEEP + 1))" | xargs rm -f
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Pruned old backups; ${KEEP} most recent retained."
fi
