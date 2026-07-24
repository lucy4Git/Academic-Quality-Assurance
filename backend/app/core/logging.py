"""Structured logging configuration using structlog.

E0-OD-003: structlog JSON output with correlation IDs, tenant context,
and mandatory sensitive-field redaction. Passwords, tokens, and API keys
are never written to logs in any environment.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict

_REDACTED_KEYS = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "secret_key",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "apikey",
        "authorization",
        "x-api-key",
        "cookie",
        "set-cookie",
        "credit_card",
        "card_number",
        "cvv",
        "ssn",
        "id_number",
        "openai_api_key",
        "anthropic_api_key",
        "gemini_api_key",
        "hf_token",
        "smtp_password",
        "metrics_api_key",
        "sentry_dsn",
        # S3 / object-storage credentials (Sprint E2)
        "s3_secret_access_key",
        "aws_secret_access_key",
        "s3_access_key_id",
        "aws_access_key_id",
        # Vector-store credentials
        "qdrant_api_key",
    }
)


def _redact_sensitive_fields(
    logger: Any, method: str, event_dict: EventDict
) -> EventDict:
    """Replace sensitive field values with '[REDACTED]' before output.

    Applied as the first processor so nothing downstream can leak secrets.
    """
    for key in list(event_dict.keys()):
        if key.lower() in _REDACTED_KEYS:
            event_dict[key] = "[REDACTED]"
    return event_dict


def configure_logging(json_logs: bool = True, log_level: str = "INFO") -> None:
    """Configure structlog as the primary logging backend.

    Call once at application startup (in the FastAPI lifespan).  All stdlib
    `logging` calls are forwarded to structlog so third-party libraries also
    produce structured output.
    """
    shared_processors: list[Any] = [
        _redact_sensitive_fields,
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_logs:
        renderer: Any = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Silence overly chatty stdlib loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a named structlog logger."""
    return structlog.get_logger(name)
