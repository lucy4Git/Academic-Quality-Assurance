"""Application configuration loaded from environment variables."""

import re
from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from typing import Annotated

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_WEAK_SECRETS = frozenset(
    {
        "change-me-to-a-long-random-string",
        "changeme",
        "change_me",
        "aqaa",
        "secret",
        "password",
        "supersecret",
        "devsecret",
        "testsecret",
        "your-secret-key",
        "your_secret_key",
        "insecure",
    }
)

_STRICT_ENVS = frozenset({"staging", "pilot", "production"})


class Settings(BaseSettings):
    """Centralized, environment-driven application settings.

    Values are read from process environment variables first, falling back to
    a local `.env` file. See `.env.example` at the project root for the full
    list of variables an environment must provide.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Application ---
    APP_NAME: str = "Academic Quality Assurance Agent"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # --- Security ---
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10_080  # 7 days

    # --- Rate limiting (Sprint E1 — E1-SEC-002) ---
    RATE_LIMIT_PER_MINUTE: int = 60  # requests per IP per minute
    RATE_LIMIT_AUTH_PER_MINUTE: int = 10  # tighter limit for auth endpoints

    # --- Metrics (Sprint E1 — E0-OD-003) ---
    METRICS_API_KEY: str | None = None  # required to expose /metrics in non-dev envs

    # --- Sentry (Sprint E1 — E0-OD-003; disabled by default) ---
    SENTRY_ENABLED: bool = False
    SENTRY_DSN: str | None = None
    SENTRY_ENVIRONMENT: str | None = None  # defaults to APP_ENV if unset

    # --- Database ---
    DATABASE_URL: str
    DATABASE_ECHO: bool = False

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _normalize_database_url(cls, value: object) -> object:
        """Normalize DATABASE_URL for the asyncpg driver used throughout the app.

        Providers such as Neon return connection strings that require several
        fixes before SQLAlchemy's async engine can use them:

        Scheme normalization (string prefix, applied first):
          postgres://     → postgresql+asyncpg://
          postgresql://   → postgresql+asyncpg://

        Query-parameter normalization (via urllib.parse — no naive substitution):
          sslmode=<v>         → ssl=<v>   (asyncpg uses ssl=, not sslmode=)
          channel_binding=*   → removed   (asyncpg does not support channel_binding)

        All other query parameters are preserved exactly.  Transformations are
        idempotent: already-correct URLs pass through unchanged.
        """
        if not isinstance(value, str):
            return value

        # Step 1 — normalize scheme (must happen before URL parsing so that the
        # netloc separator is correctly identified as "://").
        value = re.sub(r"^postgres(?:ql)?://", "postgresql+asyncpg://", value)

        # Step 2 — fix query parameters via proper URL parsing so that
        # channel_binding removal cannot leave malformed ? / & separators
        # regardless of the parameter's position in the query string.
        parsed = urlparse(value)
        params = [
            ("ssl" if k == "sslmode" else k, v)
            for k, v in parse_qsl(parsed.query, keep_blank_values=True)
            if k != "channel_binding"
        ]
        return urlunparse(parsed._replace(query=urlencode(params)))
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # --- Redis (caching, JWT revocation, background job state, rate limiting) ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Qdrant (vector store for document embeddings / semantic search) ---
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None

    # --- Storage ---
    STORAGE_BACKEND: str = "local"          # "local" | "s3"
    STORAGE_LOCAL_PATH: str = "./storage"   # root dir for LocalStorageBackend
    # S3-compatible storage (AWS S3, Cloudflare R2, MinIO, …)
    S3_BUCKET: str = ""
    S3_REGION: str = "auto"                 # "auto" works for Cloudflare R2
    S3_ENDPOINT_URL: str | None = None      # None = AWS; set for R2/MinIO
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    VIRUS_SCAN_ENABLED: bool = False        # set True to enable ClamAV / AV hook
    MAX_UPLOAD_SIZE_MB: int = 50            # per-file cap sent to validate_upload

    # --- AI Provider ---
    AI_PROVIDER: str = "LOCAL_DEV"        # OPENAI | ANTHROPIC | OLLAMA | GEMINI | LOCAL_DEV
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"   # embedding model (fastembed default)
    EMBEDDING_PROVIDER: str = "fastembed"              # "fastembed" | "sentence_transformers" | "huggingface" | "openai"
    USE_REAL_EMBEDDINGS: bool = False                  # set True to enable real embeddings
    HF_TOKEN: str | None = None               # optional HuggingFace API token
    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str = "claude-haiku-4-5-20251001"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    LOCAL_MODEL_PATH: str | None = None   # reserved for future local model support
    AI_TEMPERATURE: float = 0.3
    AI_MAX_TOKENS: int = 1024

    # --- Email (SMTP optional — console mode if unset) ---
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None
    SMTP_TLS: bool = True

    # --- Frontend ---
    FRONTEND_BASE_URL: str = "http://localhost:3000"  # used in activation/verification email links

    # --- Registration ---
    REGISTRATION_OPEN: bool = True          # allow public self-registration

    # When False (default), verified users are activated immediately after email
    # verification. When True, an administrator must explicitly approve each
    # registration before the account becomes active. Keep True for privileged
    # institutional accounts managed via admin invitation.
    REGISTRATION_REQUIRES_ADMIN_APPROVAL: bool = False

    # Legacy alias — kept for env files that still set REGISTRATION_AUTO_APPROVE.
    # Ignored when REGISTRATION_REQUIRES_ADMIN_APPROVAL is explicitly set.
    REGISTRATION_AUTO_APPROVE: bool = False

    # When True (default), a verified email address is required before login is
    # permitted. Must not be set to False in production.
    EMAIL_VERIFICATION_REQUIRED: bool = True

    # When True (default) and REGISTRATION_REQUIRES_ADMIN_APPROVAL=False,
    # the account is activated immediately after the verification code is
    # confirmed. Setting False leaves accounts in an inactive-but-verified
    # state (useful for custom post-verification workflows).
    REGISTRATION_AUTO_ACTIVATE_AFTER_EMAIL_VERIFICATION: bool = True

    VERIFICATION_CODE_EXPIRE_HOURS: int = 24

    # --- CORS ---
    CORS_ORIGINS: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: str | list[str]) -> list[str]:
        """Allow CORS_ORIGINS to be provided as a comma-separated string in `.env`."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def _reject_weak_secrets_in_strict_envs(self) -> "Settings":
        """Reject known-weak SECRET_KEY values in staging, pilot, and production.

        E0-OD-002: 'Reject known default or weak secrets in staging, pilot and
        production environments.'
        """
        if self.APP_ENV in _STRICT_ENVS:
            key_lower = self.SECRET_KEY.lower().strip()
            if key_lower in _WEAK_SECRETS or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    f"SECRET_KEY is weak or uses a known default value. "
                    f"A minimum 32-character random secret is required in "
                    f"APP_ENV={self.APP_ENV!r}. Generate one with: "
                    f"python -c \"import secrets; print(secrets.token_hex(32))\""
                )
            if self.METRICS_API_KEY is None:
                raise ValueError(
                    f"METRICS_API_KEY must be set in APP_ENV={self.APP_ENV!r} "
                    "to prevent unauthenticated access to Prometheus metrics."
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return a cached `Settings` instance.

    Cached so the environment is parsed once per process; tests can clear the
    cache with `get_settings.cache_clear()` to reload with different values.
    """
    return Settings()


settings = get_settings()
