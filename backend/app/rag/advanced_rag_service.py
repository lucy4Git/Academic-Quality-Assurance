"""Advanced RAG service — orchestrates source ranking, context building, citation verification."""
from __future__ import annotations
import logging
from typing import Any

from app.ai_assistant.assistant_service import (
    assemble_answer,
    classify_intent,
    generate_suggested_followups,
    _get_max_tokens,
    _get_temperature,
    _get_entity_type_filter,
)
from app.ai_assistant.prompt_templates import AGENT_MODES, build_grounded_system_prompt
from app.ai_providers.base_provider import AIMessage, BaseAIProvider
from app.ai_providers.provider_factory import get_provider
from app.knowledge_indexing.embedding_service import embedding_service
from app.knowledge_indexing.search_service import search_knowledge, ACTIVE_INSTITUTION_CODES
from app.rag.citation_verifier import verify_citations
from app.rag.context_builder import build_context
from app.rag.source_ranker import rank_sources

logger = logging.getLogger(__name__)


async def advanced_ask(
    question: str,
    institution_code: str,
    context_limit: int = 5,
    mode: str = "qa_assistant",
    provider: BaseAIProvider | None = None,
) -> dict[str, Any]:
    """Process a NL QA question through the Advanced RAG pipeline.

    Flow:
        1. Classify intent
        2. Retrieve context from Qdrant (tenant-scoped)
        3. Re-rank sources and enforce cross-tenant isolation
        4. Build numbered [SOURCE:N] context block + citation index
        5. If LOCAL_DEV → template assembly
           Else → build grounded system prompt requiring inline citations → call AI provider
        6. Verify citations in the answer
        7. Return structured response dict (superset of assistant_service.ask() output)
    """
    context_limit = min(max(context_limit, 1), 20)
    intent = classify_intent(question)

    raw_chunks: list[dict[str, Any]] = []
    if institution_code.upper() in ACTIVE_INSTITUTION_CODES:
        try:
            raw_chunks = search_knowledge(
                query=question,
                institution_code=institution_code,
                entity_type=_get_entity_type_filter(intent),
                top_k=context_limit,
            )
        except Exception as exc:
            logger.warning("advanced_ask: retrieval failed for %s: %s", institution_code, exc)

    ranked = rank_sources(raw_chunks, institution_code, intent=intent)
    context_block, citation_index = build_context(ranked)

    _provider = provider if provider is not None else get_provider()

    retrieval_mode = "placeholder" if embedding_service.IS_PLACEHOLDER else "semantic"
    emb_provider_name = embedding_service.MODEL_NAME if not embedding_service.IS_PLACEHOLDER else "dev-sha256"
    generation_mode: str
    generation_provider: str
    evidence_support: str

    if _provider.is_local_dev:
        answer = assemble_answer(question, ranked, institution_code, intent)
        generation_mode = "deterministic_template"
        generation_provider = "none"
        evidence_support = "chunks_retrieved" if ranked else "no_chunks"
    else:
        ikp_version = ranked[0].get("ikp_version", "v1.x.x") if ranked else "v1.x.x"
        system_prompt = build_grounded_system_prompt(
            institution_code=institution_code,
            mode=mode if mode in AGENT_MODES else "qa_assistant",
            context_block=context_block,
            citation_count=len(ranked),
            ikp_version=ikp_version,
        )
        messages = [
            AIMessage(role="system", content=system_prompt),
            AIMessage(role="user", content=question),
        ]
        try:
            answer = await _provider.complete(messages, temperature=_get_temperature(), max_tokens=_get_max_tokens())
            generation_mode = "llm"
            generation_provider = _provider.provider_name
            evidence_support = "grounded" if ranked else "no_chunks"
        except Exception as exc:
            logger.error("advanced_ask: provider '%s' error — falling back: %s", _provider.provider_name, exc)
            answer = assemble_answer(question, ranked, institution_code, intent)
            generation_mode = "deterministic_template"
            generation_provider = "none"
            evidence_support = "chunks_retrieved" if ranked else "no_chunks"

    verification = verify_citations(answer, citation_index)

    sources = [
        {
            "entity_type": c.get("entity_type", ""),
            "entity_key": c.get("entity_id", ""),
            "title": c.get("title", ""),
            "text": c.get("text", ""),
            "source_document": c.get("source_document", ""),
            "confidence_score": float(c.get("confidence_score", 0.0)),
            "relevance_score": round(float(c.get("combined_score", c.get("score", 0.0))), 4),
        }
        for c in ranked
    ]

    avg_confidence = (
        sum(c.get("confidence_score", 0.0) for c in ranked) / len(ranked) if ranked else 0.0
    )

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "confidence_score": round(avg_confidence, 4),
        "institution_code": institution_code.upper(),
        # is_placeholder_mode reflects ONLY embedding placeholder state, not LLM fallback
        "is_placeholder_mode": embedding_service.IS_PLACEHOLDER,
        "suggested_followups": generate_suggested_followups(intent, institution_code),
        "query_mode": intent,
        "provider": _provider.provider_name,
        "model": _provider.model_name,
        "mode": mode,
        "citations": verification["citations"],
        "unsupported_claims": verification["unsupported_claims"],
        "grounding_status": verification["grounding_status"],
        "retrieval_mode": retrieval_mode,
        "embedding_provider": emb_provider_name,
        "generation_mode": generation_mode,
        "generation_provider": generation_provider,
        "evidence_support_status": evidence_support,
    }
