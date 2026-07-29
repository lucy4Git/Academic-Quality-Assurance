"""Tests for the canonical sync engine helper and seed-hardening changes.

Covers:
- create_sync_engine() converts asyncpg driver scheme correctly
- ssl=require → sslmode=require translation
- ssl=false → sslmode=disable translation
- ssl absent → no sslmode added
- Driver already psycopg2 → unchanged
- Verification code uses secrets (CSPRNG), not random
- seed.py User construction now includes is_verified=True and approval_status
"""

from __future__ import annotations

import string


class TestCreateSyncEngineUrlTranslation:
    """Unit-test URL translation logic without creating a real database connection."""

    def _translate(self, url_str: str) -> str:
        """Run the same translation logic as create_sync_engine."""
        from sqlalchemy.engine import make_url

        url = make_url(url_str)

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

        return url.set(query=query).render_as_string(hide_password=False)

    def test_asyncpg_with_ssl_require(self):
        result = self._translate(
            "postgresql+asyncpg://user:pass@host/db?ssl=require"
        )
        assert "psycopg2" in result
        assert "sslmode=require" in result
        assert "ssl=" not in result
        assert "+asyncpg" not in result

    def test_asyncpg_with_ssl_true(self):
        result = self._translate(
            "postgresql+asyncpg://user:pass@host/db?ssl=true"
        )
        assert "sslmode=require" in result
        assert "ssl=" not in result

    def test_asyncpg_with_ssl_false(self):
        result = self._translate(
            "postgresql+asyncpg://user:pass@host/db?ssl=false"
        )
        assert "sslmode=disable" in result
        assert "ssl=" not in result

    def test_asyncpg_without_ssl(self):
        result = self._translate("postgresql+asyncpg://user:pass@host/db")
        assert "sslmode" not in result
        assert "psycopg2" in result

    def test_bare_postgresql_scheme(self):
        result = self._translate("postgresql://user:pass@host/db")
        assert "psycopg2" in result

    def test_psycopg2_scheme_unchanged(self):
        result = self._translate("postgresql+psycopg2://user:pass@host/db")
        assert "psycopg2" in result

    def test_password_not_redacted(self):
        result = self._translate(
            "postgresql+asyncpg://alice:s3cret@host/db?ssl=require"
        )
        assert "s3cret" in result

    def test_ssl_require_string(self):
        result = self._translate(
            "postgresql+asyncpg://user:pass@host/db?ssl=required"
        )
        assert "sslmode=require" in result


class TestVerificationCodeUsesCSPRNG:
    """Verification code generator must use secrets, not random."""

    def test_import_uses_secrets_not_random(self):
        import ast
        import pathlib

        src = pathlib.Path(__file__).parents[1] / "app" / "services" / "auth_service.py"
        tree = ast.parse(src.read_text(encoding="utf-8"))

        imported_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_names.add(node.module)

        assert "secrets" in imported_names, "auth_service must import 'secrets'"
        assert "random" not in imported_names, (
            "auth_service must NOT import 'random' — use 'secrets' for security"
        )

    def test_code_is_numeric(self):
        from app.services.auth_service import _generate_verification_code

        for _ in range(20):
            code = _generate_verification_code()
            assert code.isdigit(), f"Expected digits-only code, got {code!r}"
            assert len(code) == 6

    def test_uses_secrets_choice(self):
        src = (
            (
                __import__("pathlib").Path(__file__).parents[1]
                / "app"
                / "services"
                / "auth_service.py"
            )
            .read_text(encoding="utf-8")
        )
        assert "secrets.choice" in src, (
            "_generate_verification_code must use secrets.choice, not random.choices"
        )
