"""AI QA Assistant service.

Retrieves context from the Qdrant IKP knowledge base, constructs a grounded
system prompt, and calls the configured AI provider to generate an answer.

Provider selection
------------------
`get_provider()` reads AI_PROVIDER from settings and returns the appropriate
backend (OpenAI, Anthropic, Ollama, or LOCAL_DEV fallback).  When LOCAL_DEV
is active, the response is assembled from templates (original Sprint 4 behaviour)
and `is_placeholder_mode` is True.

Tenant isolation
----------------
The calling route handler is responsible for resolving and validating the
institution_code before calling this service.  This service assumes the
institution_code has already been authorised for the current user.
"""

from __future__ import annotations

import logging
from typing import Any

from app.ai_assistant.prompt_templates import (
    ANSWER_NO_CONTEXT,
    ANSWER_WITH_CONTEXT,
    CONTEXT_CHUNK_TEMPLATE,
    DEV_MODE_NOTICE,
    INTENT_PREAMBLES,
    SUGGESTED_PROMPTS_ADMIN,
    SUGGESTED_PROMPTS_QA,
    SUGGESTED_PROMPTS_STAFF,
    build_system_prompt,
)
from app.ai_providers.base_provider import AIMessage, BaseAIProvider
from app.ai_providers.provider_factory import get_provider
from app.knowledge_indexing.embedding_service import embedding_service
from app.knowledge_indexing.search_service import (
    ACTIVE_INSTITUTION_CODES,
    search_knowledge,
)

logger = logging.getLogger(__name__)

_EXCERPT_LEN = 300


# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------

_INTENT_KEYWORDS: dict[str, list[str]] = {
    "programme_query": [
        "programme", "qualification", "degree", "diploma", "bsc", "btech",
        "nqf", "bachelor", "hons", "honours", "phd", "masters", "msc",
        "course", "study", "offered", "offer",
    ],
    "module_query": [
        "module", "subject", "course code", "credits", "semester",
        "taught", "learn",
    ],
    "compliance_query": [
        "compliance", "compliant", "non-compliant", "at risk", "risk",
        "checklist", "requirement", "standard", "accreditation", "che",
        "saqa", "dhet", "policy",
    ],
    "audit_query": [
        "audit", "evidence", "missing", "upload", "document", "file",
        "finding", "gap", "corrective", "action", "moderation", "assessment",
        "attendance", "outcome",
    ],
}


def classify_intent(question: str) -> str:
    """Classify question intent via keyword scoring.

    Returns one of: programme_query | module_query | compliance_query |
    audit_query | general.
    """
    q = question.lower()
    scores: dict[str, int] = {
        intent: sum(1 for kw in keywords if kw in q)
        for intent, keywords in _INTENT_KEYWORDS.items()
    }
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "general"


# ---------------------------------------------------------------------------
# Context retrieval
# ---------------------------------------------------------------------------


def _get_entity_type_filter(intent: str) -> str | None:
    return {
        "programme_query": "programme",
        "module_query": "module",
        "compliance_query": None,
        "audit_query": None,
        "general": None,
    }.get(intent)


def retrieve_context(
    question: str,
    institution_code: str,
    top_k: int = 5,
    intent: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve relevant knowledge chunks from Qdrant.

    Returns [] for inactive institutions or on Qdrant errors.
    """
    if institution_code.upper() not in ACTIVE_INSTITUTION_CODES:
        logger.warning("retrieve_context: '%s' is not an active pilot institution", institution_code)
        return []

    if intent is None:
        intent = classify_intent(question)

    try:
        return search_knowledge(
            query=question,
            institution_code=institution_code,
            entity_type=_get_entity_type_filter(intent),
            top_k=top_k,
        )
    except (ValueError, Exception) as exc:
        logger.warning("retrieve_context: search failed for %s: %s", institution_code, exc)
        return []


# ---------------------------------------------------------------------------
# Template answer assembly (LOCAL_DEV / fallback)
# ---------------------------------------------------------------------------


def _truncate(text: str, max_len: int = _EXCERPT_LEN) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "…"


def assemble_answer(
    question: str,
    chunks: list[dict[str, Any]],
    institution_code: str,
    intent: str,
) -> str:
    """Assemble a template-based answer from retrieved chunks (LOCAL_DEV path)."""
    preamble = INTENT_PREAMBLES.get(intent, INTENT_PREAMBLES["general"]).format(
        institution_code=institution_code.upper()
    )
    ikp_version = chunks[0].get("ikp_version", "v1.x.x") if chunks else "v1.x.x"
    academic_year = chunks[0].get("academic_year", "2026") if chunks else "2026"

    if not chunks:
        body = ANSWER_NO_CONTEXT.format(
            institution_code=institution_code.upper(),
            ikp_version=ikp_version,
        )
    else:
        context_parts = [
            CONTEXT_CHUNK_TEMPLATE.format(
                index=i,
                entity_key=chunk.get("title") or chunk.get("entity_id") or "—",
                entity_type=chunk.get("entity_type", "unknown"),
                text_excerpt=_truncate(chunk.get("text", "")),
                source_document=chunk.get("source_document") or "IKP",
            )
            for i, chunk in enumerate(chunks, start=1)
        ]
        body = ANSWER_WITH_CONTEXT.format(
            institution_code=institution_code.upper(),
            ikp_version=ikp_version,
            academic_year=academic_year,
            context_block="\n".join(context_parts),
        )

    suffix = DEV_MODE_NOTICE if embedding_service.IS_PLACEHOLDER else ""
    return preamble + body + suffix


# ---------------------------------------------------------------------------
# Suggested follow-ups
# ---------------------------------------------------------------------------

_FOLLOWUPS_BY_INTENT: dict[str, list[str]] = {
    "programme_query": [
        "What modules are linked to this programme?",
        "What are the NQF level and credits for this programme?",
        "What are the admission requirements for this programme?",
    ],
    "module_query": [
        "What is the credit value of this module?",
        "Which programme does this module belong to?",
        "What evidence documents are required for this module?",
    ],
    "compliance_query": [
        "What corrective actions are recommended?",
        "Which modules are at risk of non-compliance?",
        "How do I improve the compliance score for this module?",
    ],
    "audit_query": [
        "What evidence is missing for this audit?",
        "How can I improve the audit outcome?",
        "What are the most common findings in recent audits?",
    ],
    "general": [
        "What programmes does this institution offer?",
        "How do I start a QA audit?",
        "What evidence types are required for module folder compliance?",
    ],
}


def generate_suggested_followups(intent: str, institution_code: str) -> list[str]:
    return _FOLLOWUPS_BY_INTENT.get(intent, _FOLLOWUPS_BY_INTENT["general"])


# ---------------------------------------------------------------------------
# Main ask function (async)
# ---------------------------------------------------------------------------


async def ask(
    question: str,
    institution_code: str,
    context_limit: int = 5,
    mode: str = "qa_assistant",
    provider: BaseAIProvider | None = None,
) -> dict[str, Any]:
    """Process a natural language QA question through the full AI pipeline.

    Flow:
        1. Classify intent
        2. Retrieve context from Qdrant (tenant-scoped)
        3. If provider is LOCAL_DEV → template assembly
           Else → build grounded system prompt → call AI provider
        4. Return structured response dict

    Args:
        question: The user's natural language question.
        institution_code: Validated, authorised institution code (e.g. "TUT").
        context_limit: Max number of IKP chunks to retrieve (1–20).
        mode: Agent mode (controls system prompt focus).
        provider: Explicit provider override (defaults to settings-configured provider).

    Returns:
        Dict compatible with AskResponse schema.
    """
    context_limit = min(max(context_limit, 1), 20)
    intent = classify_intent(question)
    chunks = retrieve_context(question, institution_code, top_k=context_limit, intent=intent)

    _provider = provider if provider is not None else get_provider()

    retrieval_mode = "placeholder" if embedding_service.IS_PLACEHOLDER else "semantic"
    emb_provider_name = embedding_service.MODEL_NAME if not embedding_service.IS_PLACEHOLDER else "dev-sha256"
    generation_mode: str
    generation_provider: str
    evidence_support: str

    if _provider.is_local_dev:
        answer = assemble_answer(question, chunks, institution_code, intent)
        generation_mode = "deterministic_template"
        generation_provider = "none"
        evidence_support = "chunks_retrieved" if chunks else "no_chunks"
    else:
        ikp_version = chunks[0].get("ikp_version", "v1.x.x") if chunks else "v1.x.x"
        system_prompt = build_system_prompt(institution_code, mode, chunks, ikp_version)
        messages = [
            AIMessage(role="system", content=system_prompt),
            AIMessage(role="user", content=question),
        ]
        try:
            answer = await _provider.complete(
                messages,
                temperature=_get_temperature(),
                max_tokens=_get_max_tokens(),
            )
            generation_mode = "llm"
            generation_provider = _provider.provider_name
            evidence_support = "grounded" if chunks else "no_chunks"
        except Exception as exc:
            logger.error(
                "AI provider '%s' error — falling back to template: %s",
                _provider.provider_name,
                exc,
            )
            answer = assemble_answer(question, chunks, institution_code, intent)
            generation_mode = "deterministic_template"
            generation_provider = "none"
            evidence_support = "chunks_retrieved" if chunks else "no_chunks"

    sources = [
        {
            "entity_type": c.get("entity_type", ""),
            "entity_key": c.get("entity_id", ""),
            "title": c.get("title", ""),
            "text": c.get("text", ""),
            "source_document": c.get("source_document", ""),
            "confidence_score": float(c.get("confidence_score", 0.0)),
            "relevance_score": round(float(c.get("score", 0.0)), 4),
        }
        for c in chunks
    ]

    avg_confidence = (
        sum(c.get("confidence_score", 0.0) for c in chunks) / len(chunks) if chunks else 0.0
    )

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "confidence_score": round(avg_confidence, 4),
        "institution_code": institution_code.upper(),
        # is_placeholder_mode reflects ONLY embedding placeholder state, not generation fallback
        "is_placeholder_mode": embedding_service.IS_PLACEHOLDER,
        "suggested_followups": generate_suggested_followups(intent, institution_code),
        "query_mode": intent,
        "provider": _provider.provider_name,
        "model": _provider.model_name,
        "mode": mode,
        "retrieval_mode": retrieval_mode,
        "embedding_provider": emb_provider_name,
        "generation_mode": generation_mode,
        "generation_provider": generation_provider,
        "evidence_support_status": evidence_support,
    }


def _get_temperature() -> float:
    try:
        from app.config import settings
        return settings.AI_TEMPERATURE
    except Exception:
        return 0.3


def _get_max_tokens() -> int:
    try:
        from app.config import settings
        return settings.AI_MAX_TOKENS
    except Exception:
        return 1024


# ---------------------------------------------------------------------------
# Suggested prompts helper
# ---------------------------------------------------------------------------


def get_suggested_prompts(
    role: str,
    institution_code: str | None,
) -> list[dict[str, str]]:
    """Return role-aware suggested prompts, formatted for the given institution."""
    code = institution_code or "your institution"

    base = [
        {
            "prompt": p["prompt"].format(institution_code=code),
            "category": p["category"],
        }
        for p in SUGGESTED_PROMPTS_STAFF
    ]

    if role in ("quality_assurance_officer", "system_admin", "faculty_dean"):
        base += [
            {
                "prompt": p["prompt"].format(institution_code=code),
                "category": p["category"],
            }
            for p in SUGGESTED_PROMPTS_QA
        ]

    if role == "system_admin":
        base += [
            {"prompt": p["prompt"], "category": p["category"]}
            for p in SUGGESTED_PROMPTS_ADMIN
        ]

    return base
