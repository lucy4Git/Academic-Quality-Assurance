#!/usr/bin/env bash
# rotate_staging_passwords.sh — replace the known seeded development password
# for all demo/seeded users in the staging database.
#
# Run this ONCE after seeding and BEFORE granting any staging access to other
# parties. The default seeded password (ChangeMe123!) is publicly documented
# and must not remain in any shared staging or pilot environment.
#
# Usage — invoke from the repository root OR from backend/:
#   bash backend/scripts/rotate_staging_passwords.sh
#   bash scripts/rotate_staging_passwords.sh
#
# Prerequisites: migrations and seed must already have been applied.
#
# Exit codes:
#   0  — all demo-user passwords updated successfully
#   1  — validation failed or update failed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# ---------------------------------------------------------------------------
# 1. Connection string (hidden)
# ---------------------------------------------------------------------------
echo "Enter the Neon connection string (input hidden):"
read -rsp "" RAW_URL
echo

# Strip carriage returns that Windows copy-paste inserts before the newline.
# Without this, a pasted URL ends with \r which corrupts urlparse's scheme
# detection ("postgresql\r+asyncpg" is not a valid scheme).
RAW_URL="$(printf '%s' "$RAW_URL" | tr -d '\r')"

if [[ -z "$RAW_URL" ]]; then
    echo "ERROR: no connection string entered." >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# 2. New password (hidden, confirmed)
# ---------------------------------------------------------------------------
echo "Enter the new staging password for all demo users (input hidden):"
read -rsp "" NEW_PASS
echo

echo "Confirm the new password (input hidden):"
read -rsp "" NEW_PASS_CONFIRM
echo

if [[ -z "$NEW_PASS" ]]; then
    echo "ERROR: new password cannot be empty." >&2
    exit 1
fi

if [[ "$NEW_PASS" != "$NEW_PASS_CONFIRM" ]]; then
    echo "ERROR: passwords do not match." >&2
    exit 1
fi

export DATABASE_URL="$RAW_URL"
export _AQAA_NEW_PASS="$NEW_PASS"
unset RAW_URL NEW_PASS NEW_PASS_CONFIRM

# ---------------------------------------------------------------------------
# 3. Validate connection metadata (never print password or URL)
# ---------------------------------------------------------------------------
echo "Validating connection metadata..."
python - <<'PYEOF'
import os, re, sys
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

raw = os.environ.get("DATABASE_URL", "").strip()

# Always report whether anything was received so a silent empty-paste is obvious.
print(f"  URL received: {'yes' if raw else 'no'} ({len(raw)} characters)")

if not raw:
    print("  ERROR: DATABASE_URL is empty — nothing was captured by read.", file=sys.stderr)
    sys.exit(1)

url = re.sub(r"^postgres(?:ql)?://", "postgresql+asyncpg://", raw)
parsed = urlparse(url)
params = [
    ("ssl" if k == "sslmode" else k, v)
    for k, v in parse_qsl(parsed.query, keep_blank_values=True)
    if k != "channel_binding"
]
url = urlunparse(parsed._replace(query=urlencode(params)))
parsed = urlparse(url)

scheme   = parsed.scheme              or "(empty)"
host     = parsed.hostname            or "(empty)"
database = parsed.path.lstrip("/")    or "(empty)"

# Print all four diagnostics before deciding to abort so the caller can see
# exactly what was parsed even when validation fails.
print(f"  Scheme:   {scheme}")
print(f"  Host:     {host}")
print(f"  Database: {database}")

errors = []
if not parsed.scheme.startswith("postgresql+asyncpg"):
    errors.append(f"scheme '{scheme}' is not postgresql+asyncpg — "
                  "check the URL starts with postgres:// or postgresql://")
if host == "(empty)":
    errors.append("no host found — the URL may have been truncated or mis-pasted")
if database == "(empty)":
    errors.append("no database name found — URL path is missing or is just '/'")
if errors:
    print("", file=sys.stderr)
    for e in errors:
        print(f"  ERROR: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF

# ---------------------------------------------------------------------------
# 4. Update passwords via Python (bcrypt hash, never SQL plaintext)
# ---------------------------------------------------------------------------
echo ""
echo "Rotating demo-user passwords..."

(cd "$BACKEND_DIR" && python - <<'PYEOF'
import asyncio, os, sys
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add backend to path (already in cwd, but be explicit)
sys.path.insert(0, ".")
from app.config import settings
from app.models.user import User
from app.security import hash_password

KNOWN_DEMO_EMAILS = [
    # seed.py
    "lecturer1@gfu.ac.uk", "lecturer2@gfu.ac.uk", "lecturer3@gfu.ac.uk",
    "qa@gfu.ac.uk",
    # seed_extended.py — GFU extras
    "qa.officer2@gfu.ac.uk",
    "dean.fce@gfu.ac.uk", "dean.fba@gfu.ac.uk", "dean.fhs@gfu.ac.uk", "dean.fns@gfu.ac.uk",
    "hod.cs@gfu.ac.uk", "hod.se@gfu.ac.uk", "hod.ba@gfu.ac.uk", "hod.fin@gfu.ac.uk",
    "hod.nur@gfu.ac.uk", "hod.phy@gfu.ac.uk", "hod.mat@gfu.ac.uk", "hod.che@gfu.ac.uk",
    "coordinator.bsc_cs@gfu.ac.uk", "coordinator.bsc_se@gfu.ac.uk",
    "coordinator.bba@gfu.ac.uk", "coordinator.bfin@gfu.ac.uk",
    "coordinator.bsc_nur@gfu.ac.uk", "coordinator.bsc_phy@gfu.ac.uk",
    "coordinator.bsc_mat@gfu.ac.uk", "coordinator.bsc_che@gfu.ac.uk",
    # seed_extended.py — RCT
    "qa.officer1@rct.ac.uk", "qa.officer2@rct.ac.uk",
    "dean.fict@rct.ac.uk", "dean.fbe@rct.ac.uk",
    "dean.fes@rct.ac.uk", "dean.fhss@rct.ac.uk",
    "hod.it@rct.ac.uk", "hod.net@rct.ac.uk",
    "hod.acc@rct.ac.uk", "hod.mkt@rct.ac.uk",
    "hod.civ@rct.ac.uk", "hod.mec@rct.ac.uk",
    "hod.soc@rct.ac.uk", "hod.psy@rct.ac.uk",
    "coordinator.bsc_it@rct.ac.uk", "coordinator.bsc_net@rct.ac.uk",
    "coordinator.bacc@rct.ac.uk", "coordinator.bmkt@rct.ac.uk",
    "coordinator.bsc_civ@rct.ac.uk", "coordinator.bsc_mec@rct.ac.uk",
    "coordinator.ba_soc@rct.ac.uk", "coordinator.ba_psy@rct.ac.uk",
]

new_pass = os.environ.get("_AQAA_NEW_PASS", "")
if not new_pass:
    print("ERROR: _AQAA_NEW_PASS not set.", file=sys.stderr)
    sys.exit(1)

new_hash = hash_password(new_pass)

async def rotate() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    updated = 0
    not_found = []

    async with async_session() as session:
        async with session.begin():
            for email in KNOWN_DEMO_EMAILS:
                result = await session.execute(
                    select(User).where(User.email == email)
                )
                user = result.scalar_one_or_none()
                if user is None:
                    not_found.append(email)
                    continue
                user.hashed_password = new_hash
                updated += 1

    await engine.dispose()

    print(f"  Updated:   {updated} user(s)")
    if not_found:
        print(f"  Not found: {len(not_found)} (may not have been seeded)")
        for e in not_found:
            print(f"    - {e}")

asyncio.run(rotate())
PYEOF
)
EXIT_CODE=$?

unset DATABASE_URL
unset _AQAA_NEW_PASS

if [[ $EXIT_CODE -ne 0 ]]; then
    echo "Password rotation failed (exit $EXIT_CODE). Credentials cleared." >&2
    exit $EXIT_CODE
fi

echo ""
echo "Credentials cleared. Password rotation complete."
echo "Record the new password securely — it is not stored anywhere by this script."
exit 0
