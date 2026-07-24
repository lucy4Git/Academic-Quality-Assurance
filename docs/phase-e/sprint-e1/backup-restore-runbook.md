# AQAA Sprint E1 — Backup & Restore Runbook

## Backup Schedule (recommended)

| Store | Frequency | Retention |
|-------|-----------|-----------|
| PostgreSQL | Daily (02:00 UTC) | 14 backups |
| Qdrant snapshots | Weekly (Sunday 03:00 UTC) | 4 snapshots per collection |
| File storage | Daily rsync or S3 sync | Provider-defined |

## PostgreSQL Backup

```bash
# Set credentials in environment (never hard-code)
export PGPASSWORD="<db_password>"
export BACKUP_POSTGRES_HOST=localhost
export BACKUP_POSTGRES_USER=aqaa
export BACKUP_POSTGRES_DB=aqaa

# Run backup script
./database/backups/backup_postgres.sh /var/backups/aqaa
```

Output: `/var/backups/aqaa/aqaa_YYYY-MM-DD_HHMMSS.dump` (pg_dump custom format, compressed).

## PostgreSQL Restore

```bash
# Full restore (drops and recreates all objects)
pg_restore \
  --host=localhost \
  --username=aqaa \
  --dbname=aqaa \
  --clean \
  --if-exists \
  --no-password \
  /var/backups/aqaa/aqaa_2026-07-24_020000.dump

# Re-apply any migrations applied after the backup was taken
cd backend
python -m alembic upgrade head
```

## Qdrant Snapshot Backup

```bash
export QDRANT_URL=http://localhost:6333
# export QDRANT_API_KEY=<key>  # if API key auth is enabled

./database/backups/backup_qdrant.sh /var/backups/aqaa
```

Output: `/var/backups/aqaa/qdrant/<collection>/YYYY-MM-DD_HHMMSS_<name>.snapshot`

## Qdrant Snapshot Restore

```bash
# Upload a snapshot to restore a collection
curl -X POST \
  "http://localhost:6333/collections/<collection>/snapshots/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "snapshot=@/var/backups/aqaa/qdrant/<collection>/<snapshot_file>"
```

## File Storage Backup

For the `./storage/` volume (uploaded evidence files):

```bash
# Using rsync to a remote host
rsync -avz --delete ./storage/ backup-host:/mnt/aqaa-storage/

# Or sync to S3-compatible storage
aws s3 sync ./storage/ s3://aqaa-backups/storage/ --delete
```

## Automated Backups via Cron (production)

Add to crontab on the host running Docker:

```cron
# PostgreSQL daily at 02:00 UTC
0 2 * * * PGPASSWORD="$AQAA_DB_PASSWORD" /opt/aqaa/database/backups/backup_postgres.sh /var/backups/aqaa >> /var/log/aqaa-backup.log 2>&1

# Qdrant weekly Sunday 03:00 UTC
0 3 * * 0 /opt/aqaa/database/backups/backup_qdrant.sh /var/backups/aqaa >> /var/log/aqaa-backup.log 2>&1
```

## Backup Verification

After each backup, verify integrity:

```bash
# PostgreSQL — list objects in backup without restoring
pg_restore --list /var/backups/aqaa/aqaa_YYYY-MM-DD_HHMMSS.dump | head -20
```
