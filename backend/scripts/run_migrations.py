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


def _alembic(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        capture_output=True,
        text=True,
    )


def _current_revision() -> str:
    result = _alembic("current")
    return result.stdout.strip() or "(none)"


def main() -> int:
    if not os.environ.get("DATABASE_URL"):
        print("ERROR: DATABASE_URL is not set in the environment.", file=sys.stderr)
        return 1

    before = _current_revision()
    print(f"Revision before migration: {before}")

    result = _alembic("upgrade", "head")
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    if result.returncode != 0:
        print(
            f"ERROR: alembic upgrade head exited {result.returncode}. "
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
