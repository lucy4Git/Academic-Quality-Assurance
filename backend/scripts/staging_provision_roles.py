"""staging_provision_roles.py — idempotent staging account provisioner.

Creates one representative account per supported AQAA role for each staging
tenant (GFU and RCT).  Skips any account that already exists (identified by
email address).

Supported roles (from UserRole enum):
    SYSTEM_ADMIN, QUALITY_ASSURANCE_OFFICER, FACULTY_DEAN,
    HEAD_OF_DEPARTMENT, PROGRAMME_COORDINATOR, LECTURER, STUDENT

Unsupported / non-existent roles (not provisioned):
    INSTITUTION_ADMIN     — not in UserRole enum
    INTERNAL_MODERATOR    — not in UserRole enum (only ModerationType.INTERNAL_MODERATION)
    EXTERNAL_MODERATOR    — not in UserRole enum
    EXTERNAL_REVIEWER     — not in UserRole enum

SYSTEM_ADMIN:
    institution_id is NULL — the User model explicitly permits this for
    system administrators not bound to a single tenant.

All other roles:
    institution_id is set to the relevant tenant.

Passwords:
    Generated via secrets.token_urlsafe(16) for each account.
    Printed to stdout EXACTLY ONCE at the end of the run.
    Never stored in source code, committed to Git, or written to any file.
    The owner must record them immediately in a secure credential store.

Usage — run from the backend/ directory:
    python scripts/staging_provision_roles.py

DATABASE_URL is read via hidden prompt (getpass). Never pass as an argument.

Exit codes:
    0 — provisioning completed (some accounts may have been skipped)
    1 — environment guard triggered, DB error, or institutions not found
"""

import asyncio
import os
import re
import secrets
import sys

# Add backend/ to sys.path so app.* imports resolve when running from backend/
sys.path.insert(0, ".")


# ---------------------------------------------------------------------------
# Accounts to provision
# ---------------------------------------------------------------------------

# SYSTEM_ADMIN has no institution — institution_key is None.
# For all other roles, institution_key maps to the institution code in the DB.

STAGING_ACCOUNTS = [
    # -------------------------------------------------------------------------
    # Cross-tenant (no institution)
    # -------------------------------------------------------------------------
    {
        "email": "staging.admin@aqaa.internal",
        "full_name": "Staging System Administrator",
        "role": "system_admin",
        "institution_code": None,
    },
    # -------------------------------------------------------------------------
    # Greenfield University (GFU)
    # -------------------------------------------------------------------------
    {
        "email": "dean.fce@gfu.ac.uk",
        "full_name": "Dean — Faculty of Computing and Engineering (GFU)",
        "role": "faculty_dean",
        "institution_code": "GFU",
    },
    {
        "email": "hod.cs@gfu.ac.uk",
        "full_name": "Head of Department — Computer Science (GFU)",
        "role": "head_of_department",
        "institution_code": "GFU",
    },
    {
        "email": "coordinator.bsccs@gfu.ac.uk",
        "full_name": "Programme Coordinator — BSc Computer Science (GFU)",
        "role": "programme_coordinator",
        "institution_code": "GFU",
    },
    # -------------------------------------------------------------------------
    # Riverside College of Technology (RCT)
    # -------------------------------------------------------------------------
    {
        "email": "dean.fcs@rct.ac.uk",
        "full_name": "Dean — Faculty of Computing Sciences (RCT)",
        "role": "faculty_dean",
        "institution_code": "RCT",
    },
    {
        "email": "hod.sen@rct.ac.uk",
        "full_name": "Head of Department — Software Engineering (RCT)",
        "role": "head_of_department",
        "institution_code": "RCT",
    },
    {
        "email": "coordinator.bscsen@rct.ac.uk",
        "full_name": "Programme Coordinator — BSc Software Engineering (RCT)",
        "role": "programme_coordinator",
        "institution_code": "RCT",
    },
]

# Roles that were requested but do not exist in the UserRole enum.
UNSUPPORTED_ROLES = [
    ("INSTITUTION_ADMIN", "Not a value in UserRole enum."),
    ("INTERNAL_MODERATOR", "Not in UserRole. ModerationType.INTERNAL_MODERATION is an audit-process enum, not a user role."),
    ("EXTERNAL_MODERATOR", "Not in UserRole enum."),
    ("EXTERNAL_REVIEWER", "Not in UserRole enum."),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_environment() -> None:
    env = os.environ.get("APP_ENV", "development").lower()
    if env in ("production", "pilot"):
        print(
            f"ERROR: APP_ENV={env!r}. This script must never run against "
            "production or pilot environments.",
            file=sys.stderr,
        )
        sys.exit(1)


def _read_database_url() -> str:
    import getpass
    from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

    raw = getpass.getpass("Neon connection string (hidden): ").strip()
    if not raw:
        print("ERROR: no connection string entered.", file=sys.stderr)
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
        errors.append("no host found")
    if database == "(empty)":
        errors.append("no database name found")
    if errors:
        for e in errors:
            print(f"  ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    return url


def _gen_password() -> str:
    return secrets.token_urlsafe(16)


# ---------------------------------------------------------------------------
# Core provisioning
# ---------------------------------------------------------------------------

async def _provision(database_url: str) -> int:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    from app.models.institution import Institution
    from app.models.user import User
    from app.models.enums import UserRole
    from app.security import hash_password

    engine = create_async_engine(database_url, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    created: list[tuple[str, str, str, str]] = []   # (email, role, tenant, password)
    skipped: list[tuple[str, str]] = []              # (email, reason)

    try:
        async with Session() as session:
            async with session.begin():
                # Resolve institution IDs
                inst_rows = (await session.execute(select(Institution))).scalars().all()
                institution_by_code = {i.code: i for i in inst_rows}

                for account in STAGING_ACCOUNTS:
                    code = account["institution_code"]

                    # Resolve institution
                    institution = None
                    if code is not None:
                        institution = institution_by_code.get(code)
                        if institution is None:
                            skipped.append((account["email"], f"institution '{code}' not found in DB"))
                            continue

                    # Skip if already exists
                    existing = (await session.execute(
                        select(User).where(User.email == account["email"])
                    )).scalar_one_or_none()
                    if existing is not None:
                        skipped.append((account["email"], "already exists"))
                        continue

                    pwd = _gen_password()
                    role_enum = UserRole(account["role"])

                    user = User(
                        email=account["email"],
                        full_name=account["full_name"],
                        hashed_password=hash_password(pwd),
                        role=role_enum,
                        institution_id=institution.id if institution else None,
                        is_active=True,
                        is_verified=True,
                    )
                    session.add(user)

                    tenant = code or "(none)"
                    created.append((account["email"], account["role"], tenant, pwd))

    except Exception as exc:
        print(f"\nERROR: database operation failed — {exc}", file=sys.stderr)
        print("Transaction rolled back. No accounts were created.", file=sys.stderr)
        await engine.dispose()
        return 1

    await engine.dispose()

    # Summary — no passwords in the skipped/created lists printed below except
    # the one-time credential block.
    print(f"\n{'='*70}")
    print("Provisioning summary")
    print(f"{'='*70}")
    print(f"\nCreated: {len(created)}")
    for email, role, tenant, _ in created:
        print(f"  {email:<50} {role:<30} {tenant}")

    print(f"\nSkipped: {len(skipped)}")
    for email, reason in skipped:
        print(f"  {email:<50} {reason}")

    print(f"\nUnsupported roles (not in UserRole enum):")
    for role_name, reason in UNSUPPORTED_ROLES:
        print(f"  {role_name:<30} {reason}")

    if created:
        print(f"\n{'='*70}")
        print("ONE-TIME CREDENTIAL DISPLAY — record these now.")
        print("They are NOT stored anywhere and will not be shown again.")
        print(f"{'='*70}")
        print(f"  {'email':<50} {'role':<30} tenant    password")
        print(f"  {'-'*50} {'-'*30} --------  --------")
        for email, role, tenant, pwd in created:
            print(f"  {email:<50} {role:<30} {tenant:<10} {pwd}")
        print(f"{'='*70}")
        print("Store these in your password manager before closing this window.")

    return 0


if __name__ == "__main__":
    _check_environment()
    print("=== AQAA Staging Role Provisioner ===\n")
    database_url = _read_database_url()
    print()
    sys.exit(asyncio.run(_provision(database_url)))
