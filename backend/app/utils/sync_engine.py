"""Shared helper: build a psycopg2-compatible synchronous SQLAlchemy engine.

All seed scripts, admin utilities, and Alembic env.py must import this
function instead of converting the DATABASE_URL inline.

Why this exists
---------------
The app's DATABASE_URL uses the ``postgresql+asyncpg`` driver scheme and may
carry an ``ssl=require`` query parameter (Neon, Supabase, etc.).  psycopg2
does not understand either — it needs ``postgresql+psycopg2`` and
``sslmode=require``.  Simple ``.replace("+asyncpg", "")`` calls silently drop
the SSL requirement, causing Neon connections to fail or fall back to
unencrypted transport.  This helper handles every known variant correctly.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.engine.base import Engine

from app.config import settings


def create_sync_engine(echo: bool = False) -> Engine:
    """Return a synchronous psycopg2 engine for the configured database.

    Converts the async driver URL and translates ssl→sslmode so psycopg2
    can connect to Neon (and any other TLS-enforcing PostgreSQL host).
    """
    url = make_url(settings.DATABASE_URL)

    if url.drivername in {"postgres", "postgresql", "postgresql+asyncpg"}:
        url = url.set(drivername="postgresql+psycopg2")

    query = dict(url.query)
    ssl_value = query.pop("ssl", None)

    if ssl_value is not None:
        value = str(ssl_value).strip().lower()
        if value in {"true", "1", "require", "required"}:
            query["sslmode"] = "require"
        elif value in {"false", "0", "disable", "disabled"}:
            query["sslmode"] = "disable"

    return create_engine(
        url.set(query=query).render_as_string(hide_password=False),
        echo=echo,
        pool_pre_ping=True,
    )
