"""staging_rotate_passwords.py — securely rotate passwords for staging users.

Replaces rotate_staging_passwords.sh.  Using Python eliminates the shell
carriage-return defect (\\r in pasted URLs) that affected the previous helper.

Features
--------
- Refuses to run when APP_ENV is 'production' or 'pilot'.
- Reads DATABASE_URL via getpass (hidden, cross-platform, no \\r issue).
- Optional --generate flag: creates a cryptographically secure password and
  prints it exactly once.  Owner must record it; it is never stored.
- Validates password strength (min 12 chars, at least one digit, one uppercase,
  one lowercase, one special character).
- Rotates selected users (--emails a@b.com c@d.com) or all staging users
  (--all).
- Never prints plaintext passwords after the one-time display.
- Never logs plaintext passwords.
- Rolls back the entire transaction on any database failure.
- Prints a success/failure summary with email and status only.

Usage
-----
Run from the backend/ directory:

    # rotate all staging users — prompts for password:
    python scripts/staging_rotate_passwords.py --all

    # rotate all with a generated password (shown once):
    python scripts/staging_rotate_passwords.py --all --generate

    # rotate specific accounts:
    python scripts/staging_rotate_passwords.py --emails qa.officer@gfu.ac.uk lecturer1@gfu.ac.uk

DATABASE_URL is read via hidden prompt.  Never pass it as an argument.

Exit codes:
    0 — all rotations succeeded
    1 — validation failure, DB error, or no accounts matched
"""

import argparse
import asyncio
import re
import secrets
import string
import sys

# Add backend/ to sys.path so app.* imports resolve when running from backend/
sys.path.insert(0, ".")


# ---------------------------------------------------------------------------
# Password utilities
# ---------------------------------------------------------------------------

_SPECIAL = "!@#$%^&*()-_=+[]{}|;:,.<>?"


def generate_secure_password(length: int = 20) -> str:
    alphabet = string.ascii_letters + string.digits + _SPECIAL
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        if _validate_strength(pwd) is None:
            return pwd


def _validate_strength(password: str) -> str | None:
    """Return an error message or None if the password is strong enough."""
    if len(password) < 12:
        return "Password must be at least 12 characters."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return "Password must contain at least one digit."
    if not re.search(r"[^A-Za-z0-9]", password):
        return "Password must contain at least one special character."
    return None


# ---------------------------------------------------------------------------
# Environment guard
# ---------------------------------------------------------------------------

def _check_environment() -> None:
    import os
    env = os.environ.get("APP_ENV", "development").lower()
    if env in ("production", "pilot"):
        print(
            f"ERROR: APP_ENV={env!r}. This script must never run against "
            "production or pilot environments.",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Credential input
# ---------------------------------------------------------------------------

def _read_database_url() -> str:
    import getpass
    import re as _re
    from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

    raw = getpass.getpass("Neon connection string (hidden): ").strip()
    if not raw:
        print("ERROR: no connection string entered.", file=sys.stderr)
        sys.exit(1)

    # Normalise (same logic as Settings._normalize_database_url)
    url = _re.sub(r"^postgres(?:ql)?://", "postgresql+asyncpg://", raw)
    parsed = urlparse(url)
    params = [
        ("ssl" if k == "sslmode" else k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k != "channel_binding"
    ]
    url = urlunparse(parsed._replace(query=urlencode(params)))
    parsed = urlparse(url)

    scheme = parsed.scheme or "(empty)"
    host = parsed.hostname or "(empty)"
    database = parsed.path.lstrip("/") or "(empty)"

    print(f"  URL received: yes ({len(raw)} chars)")
    print(f"  Scheme:   {scheme}")
    print(f"  Host:     {host}")
    print(f"  Database: {database}")

    errors = []
    if not parsed.scheme.startswith("postgresql+asyncpg"):
        errors.append(f"scheme '{scheme}' is not postgresql+asyncpg")
    if host == "(empty)":
        errors.append("no host found in URL")
    if database == "(empty)":
        errors.append("no database name found in URL")
    if errors:
        for e in errors:
            print(f"  ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    return url


def _read_new_password(generate: bool) -> str:
    import getpass

    if generate:
        pwd = generate_secure_password()
        print("\n*** GENERATED PASSWORD — record this now, it will not be shown again ***")
        print(f"    {pwd}")
        print("*" * 70)
        return pwd

    while True:
        pwd = getpass.getpass("New password (hidden): ")
        err = _validate_strength(pwd)
        if err:
            print(f"  Weak password: {err}")
            continue
        confirm = getpass.getpass("Confirm password (hidden): ")
        if pwd != confirm:
            print("  Passwords do not match. Try again.")
            continue
        return pwd


# ---------------------------------------------------------------------------
# Database rotation
# ---------------------------------------------------------------------------

async def _rotate(database_url: str, emails: list[str] | None, new_password: str) -> int:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    from app.models.user import User
    from app.security import hash_password

    engine = create_async_engine(database_url, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    new_hash = hash_password(new_password)
    results: list[tuple[str, str]] = []

    try:
        async with Session() as session:
            async with session.begin():
                if emails is not None:
                    q = select(User).where(User.email.in_(emails))
                else:
                    q = select(User)

                rows = (await session.execute(q)).scalars().all()

                if not rows:
                    print("  No matching accounts found in database.", file=sys.stderr)
                    await engine.dispose()
                    return 1

                for user in rows:
                    user.hashed_password = new_hash
                    results.append((user.email, "rotated"))

                # If emails were specified, flag any that were not found.
                if emails is not None:
                    found_emails = {user.email for user in rows}
                    for e in emails:
                        if e not in found_emails:
                            results.append((e, "NOT FOUND"))
    except Exception as exc:
        print(f"\nERROR: database operation failed — {exc}", file=sys.stderr)
        print("Transaction rolled back. No passwords were changed.", file=sys.stderr)
        await engine.dispose()
        return 1

    await engine.dispose()

    print("\nRotation summary:")
    print(f"  {'email':<50} status")
    print(f"  {'-'*50} ------")
    for email, status in sorted(results):
        print(f"  {email:<50} {status}")
    print(f"\n  {sum(1 for _, s in results if s == 'rotated')} account(s) updated.")
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rotate passwords for AQAA staging users."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all", action="store_true",
        help="Rotate passwords for ALL users in the staging database."
    )
    group.add_argument(
        "--emails", nargs="+", metavar="EMAIL",
        help="Rotate passwords for specific email addresses."
    )
    parser.add_argument(
        "--generate", action="store_true",
        help="Generate a cryptographically secure password instead of prompting."
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    _check_environment()

    print("=== AQAA Staging Password Rotation ===\n")
    database_url = _read_database_url()

    print()
    new_password = _read_new_password(args.generate)

    emails = args.emails if not args.all else None
    print(f"\nRotating {'all users' if emails is None else f'{len(emails)} user(s)'}...")

    sys.exit(asyncio.run(_rotate(database_url, emails, new_password)))
