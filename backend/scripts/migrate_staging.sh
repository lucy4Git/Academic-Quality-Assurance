#!/usr/bin/env bash
# migrate_staging.sh — safe one-time migration runner for Windows Git Bash.
#
# Usage — invoke from the repository root OR from backend/:
#   bash backend/scripts/migrate_staging.sh   # from repo root
#   bash scripts/migrate_staging.sh            # from backend/
#
# The script:
#   1. Prompts for the Neon connection string without echoing it.
#   2. Exports it as DATABASE_URL (raw, un-modified in the shell).
#   3. Delegates ALL URL normalization to backend/app/config.py via Python —
#      there is exactly one normalization implementation.
#   4. Validates safe metadata only (scheme, host, database — never password).
#   5. Runs scripts/run_migrations.py from the backend/ directory.
#   6. Clears DATABASE_URL immediately after (success or failure).
#
# Normalizations applied by Python (Settings._normalize_database_url):
#   postgres://       → postgresql+asyncpg://
#   postgresql://     → postgresql+asyncpg://
#   sslmode=<v>       → ssl=<v>
#   channel_binding=* → removed
#
# Exit codes:
#   0  — migration completed successfully
#   1  — validation failed or migration failed

set -euo pipefail

# ---------------------------------------------------------------------------
# Locate backend/ regardless of invocation directory.
# BASH_SOURCE[0] is the path of this script file itself.
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

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

# Export the raw URL. Python's Settings validator normalizes it — the shell
# never needs to manipulate the URL value.
export DATABASE_URL="$RAW_URL"
unset RAW_URL

# ---------------------------------------------------------------------------
# 2. Validate safe metadata — Python applies normalization and prints only
#    scheme, host, and database name. The password is never printed.
# ---------------------------------------------------------------------------
echo "Validating connection metadata..."
python - <<'PYEOF'
import os, re, sys
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

url = os.environ.get("DATABASE_URL", "")

# Apply the same normalization as Settings._normalize_database_url so that
# the metadata display reflects what the application will actually use.
url = re.sub(r"^postgres(?:ql)?://", "postgresql+asyncpg://", url)
parsed = urlparse(url)
params = [
    ("ssl" if k == "sslmode" else k, v)
    for k, v in parse_qsl(parsed.query, keep_blank_values=True)
    if k != "channel_binding"
]
url = urlunparse(parsed._replace(query=urlencode(params)))
parsed = urlparse(url)

errors = []
if not parsed.scheme.startswith("postgresql+asyncpg"):
    errors.append(f"scheme '{parsed.scheme}' is not postgresql+asyncpg")
if not parsed.hostname:
    errors.append("no host found in URL")
if not parsed.path or parsed.path == "/":
    errors.append("no database name found in URL")

if errors:
    for e in errors:
        print(f"  ERROR: {e}", file=sys.stderr)
    sys.exit(1)

print(f"  Driver:   {parsed.scheme}")
print(f"  Host:     {parsed.hostname}")
print(f"  Database: {parsed.path.lstrip('/')}")
PYEOF

# ---------------------------------------------------------------------------
# 3. Run migrations from backend/ so that alembic.ini and app/ are on PATH
# ---------------------------------------------------------------------------
echo ""
echo "Running migrations..."

(cd "$BACKEND_DIR" && python scripts/run_migrations.py)
EXIT_CODE=$?

# ---------------------------------------------------------------------------
# 4. Clear DATABASE_URL immediately — success or failure
# ---------------------------------------------------------------------------
unset DATABASE_URL

if [[ $EXIT_CODE -ne 0 ]]; then
    echo "Migration failed (exit $EXIT_CODE). DATABASE_URL has been cleared." >&2
    exit $EXIT_CODE
fi

echo ""
echo "DATABASE_URL cleared. Migration complete."
exit 0
