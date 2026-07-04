"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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

    # --- Database ---
    DATABASE_URL: str
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # --- Redis (caching, JWT revocation, background job state) ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Qdrant (vector store for document embeddings / semantic search) ---
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None

    # --- Storage ---
    STORAGE_BACKEND: str = "local"          # "local" | "s3" | "azure"
    STORAGE_LOCAL_PATH: str = "./storage"   # root dir for LocalStorageBackend
    VIRUS_SCAN_ENABLED: bool = False        # set True to enable ClamAV / AV hook
    MAX_UPLOAD_SIZE_MB: int = 50            # per-file cap sent to validate_upload

    # --- AI Provider ---
    AI_PROVIDER: str = "LOCAL_DEV"        # OPENAI | ANTHROPIC | OLLAMA | LOCAL_DEV
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str = "claude-haiku-4-5-20251001"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
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

    # --- Registration ---
    REGISTRATION_OPEN: bool = True          # allow public self-registration
    REGISTRATION_AUTO_APPROVE: bool = False  # require admin approval if False
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


@lru_cache
def get_settings() -> Settings:
    """Return a cached `Settings` instance.

    Cached so the environment is parsed once per process; tests can clear the
    cache with `get_settings.cache_clear()` to reload with different values.
    """
    return Settings()


settings = get_settings()
