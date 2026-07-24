#!/usr/bin/env bash
# migrate_staging.sh — safe one-time migration runner for Windows Git Bash.
#
# Usage (from the backend/ directory):
#   bash scripts/migrate_staging.sh
#
# The script prompts for the full Neon connection string without echo,
# normalizes it to the asyncpg format expected by SQLAlchemy, validates
# safe metadata only (never the password), runs the migration, then
# immediately clears DATABASE_URL from the environment.
#
# Normalization applied:
#   postgres://     → postgresql+asyncpg://
#   postgresql://   → postgresql+asyncpg://
#   sslmode=require → ssl=require
#
# Exit codes:
#   0  — migration completed successfully
#   1  — validation failed or migration failed

set -euo pipefail

# ---------------------------------------------------------------------------
# 1. Prompt — hidden input, no echo, nothing written to disk or history
# ---------------------------------------------------------------------------
echo "Enter the Neon connection string (input hidden):"
read -rsp "" RAW_URL
echo  # newline after hidden input

if [[ -z "$RAW_URL" ]]; then
    echo "ERROR: no connection string entered." >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# 2. Normalize — all substitutions happen in memory, never printed
# ---------------------------------------------------------------------------
NORM_URL="$RAW_URL"

# postgres:// → postgresql+asyncpg://
NORM_URL="${NORM_URL/postgres:\/\//postgresql+asyncpg://}"

# postgresql:// (bare, without driver) → postgresql+asyncpg://
# Only rewrite if not already postgresql+asyncpg://
if [[ "$NORM_URL" == postgresql://* ]]; then
    NORM_URL="postgresql+asyncpg://${NORM_URL#postgresql://}"
fi

# sslmode= → ssl=  (asyncpg uses ssl=, not sslmode=)
NORM_URL="${NORM_URL//sslmode=/ssl=}"

# ---------------------------------------------------------------------------
# 3. Validate safe metadata only — scheme, host, database (no password)
# ---------------------------------------------------------------------------
echo "Validating connection metadata..."
DATABASE_URL="$NORM_URL" python - <<'PYEOF'
import os, sys
from urllib.parse import urlparse

url = os.environ.get("DATABASE_URL", "")
p = urlparse(url)

errors = []
if not p.scheme.startswith("postgresql+asyncpg"):
    errors.append(f"scheme '{p.scheme}' is not postgresql+asyncpg")
if not p.hostname:
    errors.append("no host found in URL")
if not p.path or p.path == "/":
    errors.append("no database name found in URL")

if errors:
    for e in errors:
        print(f"  ERROR: {e}", file=sys.stderr)
    sys.exit(1)

print(f"  Driver:   {p.scheme}")
print(f"  Host:     {p.hostname}")
print(f"  Database: {p.path.lstrip('/')}")
PYEOF

# ---------------------------------------------------------------------------
# 4. Export and run migrations
# ---------------------------------------------------------------------------
echo ""
echo "Running migrations..."
export DATABASE_URL="$NORM_URL"

python scripts/run_migrations.py
EXIT_CODE=$?

# ---------------------------------------------------------------------------
# 5. Clear — DATABASE_URL removed from environment immediately
# ---------------------------------------------------------------------------
unset DATABASE_URL
unset NORM_URL
unset RAW_URL

if [[ $EXIT_CODE -ne 0 ]]; then
    echo "Migration failed (exit $EXIT_CODE). DATABASE_URL has been cleared." >&2
    exit $EXIT_CODE
fi

echo ""
echo "DATABASE_URL cleared. Migration complete."
exit 0
