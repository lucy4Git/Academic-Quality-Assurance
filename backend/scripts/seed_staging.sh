#!/usr/bin/env bash
# seed_staging.sh — safe one-time synthetic data seeder for Windows Git Bash.
#
# Usage — invoke from the repository root OR from backend/:
#   bash backend/scripts/seed_staging.sh   # from repo root
#   bash scripts/seed_staging.sh            # from backend/
#
# Prerequisites: run migrate_staging.sh first (schema must exist at head).
#
# The script:
#   1. Prompts for the Neon connection string without echoing it.
#   2. Exports it as DATABASE_URL.
#   3. Validates safe metadata (scheme, host, database — never password).
#   4. Runs database/seed_data/run_all.py from the backend/ directory.
#   5. Clears DATABASE_URL immediately after (success or failure).
#
# The seed process is idempotent — re-running it skips rows that already exist.
# All seeded data is synthetic (GFU, RCT fictional institutions; no real PII).
#
# Exit codes:
#   0  — seeding completed successfully
#   1  — validation failed or seed script failed

set -euo pipefail

# ---------------------------------------------------------------------------
# Locate backend/ and repo root regardless of invocation directory.
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$BACKEND_DIR/.." && pwd)"

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

export DATABASE_URL="$RAW_URL"
unset RAW_URL

# ---------------------------------------------------------------------------
# 2. Validate safe metadata — Python normalizes and displays scheme/host/db
# ---------------------------------------------------------------------------
echo "Validating connection metadata..."
python - <<'PYEOF'
import os, re, sys
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

url = os.environ.get("DATABASE_URL", "")
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
# 3. Run seed from backend/ so app.config picks up the correct paths.
#    The seed scripts add backend/ to sys.path themselves.
# ---------------------------------------------------------------------------
echo ""
echo "Running seed (idempotent — safe to re-run)..."

(cd "$BACKEND_DIR" && python "$REPO_ROOT/database/seed_data/run_all.py")
EXIT_CODE=$?

# ---------------------------------------------------------------------------
# 4. Clear DATABASE_URL immediately — success or failure
# ---------------------------------------------------------------------------
unset DATABASE_URL

if [[ $EXIT_CODE -ne 0 ]]; then
    echo "Seed failed (exit $EXIT_CODE). DATABASE_URL has been cleared." >&2
    exit $EXIT_CODE
fi

echo ""
echo "DATABASE_URL cleared. Seed complete."
exit 0
