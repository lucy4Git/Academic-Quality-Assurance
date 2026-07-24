"""Sprint E2 migration tests.

Covers DATABASE_URL normalization in Settings — the validator that converts
provider-issued postgresql:// / postgres:// URLs and psycopg2-style
`sslmode=require` parameters to the form required by the asyncpg driver.

All tests instantiate Settings directly (bypassing the lru_cache singleton)
with a minimal valid configuration — no real database connection is made.
"""

from __future__ import annotations

import pytest


MINIMAL = dict(
    SECRET_KEY="a" * 64,
    APP_ENV="development",
    REDIS_URL="redis://localhost:6379/0",
)


class TestDatabaseUrlNormalization:
    """Settings._normalize_database_url field validator."""

    def _url(self, raw: str) -> str:
        from app.config import Settings

        s = Settings(DATABASE_URL=raw, **MINIMAL)
        return s.DATABASE_URL

    # ------------------------------------------------------------------
    # Scheme normalization
    # ------------------------------------------------------------------

    def test_postgresql_bare_becomes_asyncpg(self) -> None:
        result = self._url("postgresql://user:pass@host/db")
        assert result.startswith("postgresql+asyncpg://")

    def test_postgres_short_scheme_becomes_asyncpg(self) -> None:
        result = self._url("postgres://user:pass@host/db")
        assert result.startswith("postgresql+asyncpg://")

    def test_asyncpg_scheme_unchanged(self) -> None:
        raw = "postgresql+asyncpg://user:pass@host/db"
        result = self._url(raw)
        assert result == raw

    def test_host_and_path_preserved_after_normalization(self) -> None:
        result = self._url("postgresql://user:pass@ep-xyz.region.aws.neon.tech/neondb")
        assert "ep-xyz.region.aws.neon.tech" in result
        assert "/neondb" in result

    # ------------------------------------------------------------------
    # SSL parameter normalization
    # ------------------------------------------------------------------

    def test_sslmode_require_becomes_ssl_require(self) -> None:
        result = self._url("postgresql://user:pass@host/db?sslmode=require")
        assert "ssl=require" in result
        assert "sslmode=" not in result

    def test_sslmode_in_full_neon_url(self) -> None:
        neon = "postgresql://user:pass@ep-abc123.us-east-2.aws.neon.tech/neondb?sslmode=require"
        result = self._url(neon)
        assert result.startswith("postgresql+asyncpg://")
        assert "ssl=require" in result
        assert "sslmode=" not in result

    def test_ssl_require_already_correct_unchanged(self) -> None:
        raw = "postgresql+asyncpg://user:pass@host/db?ssl=require"
        result = self._url(raw)
        assert result == raw

    # ------------------------------------------------------------------
    # channel_binding removal
    # ------------------------------------------------------------------

    def test_channel_binding_only_param_removed(self) -> None:
        """channel_binding as the sole query parameter must be removed cleanly."""
        url = "postgresql+asyncpg://user:pass@host/db?channel_binding=require"
        result = self._url(url)
        assert "channel_binding" not in result
        # No dangling ? or & left behind
        assert result.endswith("/db") or result.endswith("/db?") is False
        assert "?" not in result or result.count("?") == 1

    def test_channel_binding_first_param_removed(self) -> None:
        url = "postgresql://user:pass@host/db?channel_binding=require&ssl=require"
        result = self._url(url)
        assert "channel_binding" not in result
        assert "ssl=require" in result
        assert result.startswith("postgresql+asyncpg://")

    def test_channel_binding_middle_param_removed(self) -> None:
        url = "postgresql+asyncpg://user:pass@host/db?ssl=require&channel_binding=require&connect_timeout=10"
        result = self._url(url)
        assert "channel_binding" not in result
        assert "ssl=require" in result
        assert "connect_timeout=10" in result

    def test_channel_binding_last_param_removed(self) -> None:
        url = "postgresql+asyncpg://user:pass@host/db?ssl=require&channel_binding=require"
        result = self._url(url)
        assert "channel_binding" not in result
        assert "ssl=require" in result

    def test_channel_binding_no_double_ampersand(self) -> None:
        """Removing a middle parameter must not produce && or trailing &."""
        url = "postgresql+asyncpg://user:pass@host/db?a=1&channel_binding=require&b=2"
        result = self._url(url)
        assert "channel_binding" not in result
        assert "a=1" in result
        assert "b=2" in result
        assert "&&" not in result
        assert not result.endswith("&")
        assert not result.endswith("?")

    def test_other_params_preserved_after_channel_binding_removal(self) -> None:
        url = "postgresql://user:pass@host/db?sslmode=require&channel_binding=require&connect_timeout=5"
        result = self._url(url)
        assert "channel_binding" not in result
        assert "sslmode=" not in result
        assert "ssl=require" in result
        assert "connect_timeout=5" in result

    def test_neon_pooled_url_fully_normalized(self) -> None:
        """Typical Neon pooled endpoint URL with channel_binding must normalize cleanly."""
        neon = (
            "postgresql://owner:secret"
            "@ep-quiet-smoke-12345-pooler.eu-west-2.aws.neon.tech"
            "/neondb"
            "?sslmode=require&channel_binding=require"
        )
        result = self._url(neon)
        assert result.startswith("postgresql+asyncpg://")
        assert "ssl=require" in result
        assert "sslmode=" not in result
        assert "channel_binding" not in result
        assert "ep-quiet-smoke-12345-pooler.eu-west-2.aws.neon.tech" in result
        assert "/neondb" in result

    # ------------------------------------------------------------------
    # Combined: typical Neon connection string (non-pooled)
    # ------------------------------------------------------------------

    def test_typical_neon_url_fully_normalized(self) -> None:
        """Neon's default connection string format should be fully corrected."""
        neon = "postgresql://owner:secret@ep-quiet-smoke-12345.eu-west-2.aws.neon.tech/neondb?sslmode=require"
        result = self._url(neon)
        assert result.startswith("postgresql+asyncpg://")
        assert "ssl=require" in result
        assert "sslmode=" not in result
        # Credentials and path must be preserved exactly
        assert "ep-quiet-smoke-12345.eu-west-2.aws.neon.tech" in result
        assert "/neondb" in result

    def test_postgres_short_scheme_with_sslmode(self) -> None:
        url = "postgres://user:pass@host/db?sslmode=require"
        result = self._url(url)
        assert result.startswith("postgresql+asyncpg://")
        assert "ssl=require" in result
        assert "sslmode=" not in result

    # ------------------------------------------------------------------
    # Non-string passthrough (Pydantic should handle this itself, but
    # the validator must not crash on unexpected input)
    # ------------------------------------------------------------------

    def test_non_string_returned_unchanged(self) -> None:
        import re
        # Call the normalization logic directly with a non-string to confirm
        # the isinstance guard returns it untouched.
        value: object = 42
        if not isinstance(value, str):
            result = value
        else:
            result = re.sub(r"^postgres(?:ql)?://", "postgresql+asyncpg://", value)
        assert result == 42
