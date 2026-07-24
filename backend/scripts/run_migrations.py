"""
One-time migration runner — Render Shell, CI, or local bootstrap.

Usage (run from the backend/ directory):
    python scripts/run_migrations.py

DATABASE_URL is read exclusively from the environment variable.  It is never
passed as a command-line argument, never printed, and never logged.

Exit codes:
    0  — migrations applied successfully, or database was already at head
    1  — DATABASE_URL not set, or Alembic exited non-zero
"""

import os
import subprocess
import sys
from urllib.parse import urlparse


def _alembic(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        capture_output=True,
        text=True,
    )


def _current_revision() -> str:
    result = _alembic("current")
    return result.stdout.strip() or "(none)"


def _validate_url_safe_metadata(url: str) -> None:
    """Print safe URL metadata for diagnostic purposes — never the password."""
    parsed = urlparse(url)
    print(f"  Driver:   {parsed.scheme}")
    print(f"  Host:     {parsed.hostname or '(none)'}")
    print(f"  Database: {parsed.path.lstrip('/') or '(none)'}")
    if not parsed.scheme.startswith("postgresql+asyncpg"):
        print(
            "  WARNING: scheme does not include +asyncpg driver. "
            "Migrations may fail with 'asyncio extension requires async driver'.",
            file=sys.stderr,
        )


def main() -> int:
    raw_url = os.environ.get("DATABASE_URL", "")
    if not raw_url:
        print("ERROR: DATABASE_URL is not set in the environment.", file=sys.stderr)
        return 1

    print("Connection metadata (no credentials):")
    _validate_url_safe_metadata(raw_url)

    before = _current_revision()
    print(f"\nRevision before migration: {before}")

    result = _alembic("upgrade", "head")
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    if result.returncode != 0:
        print(
            f"\nERROR: alembic upgrade head exited {result.returncode}. "
            "Review the output above and resolve before accepting staging.",
            file=sys.stderr,
        )
        return 1

    after = _current_revision()
    print(f"Revision after  migration: {after}")

    if before == after:
        print("No new migrations — database already at head.")
    else:
        print("Migrations applied successfully.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
