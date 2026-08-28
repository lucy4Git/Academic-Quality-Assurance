"""AI QA Assistant routes.

Endpoints
---------
POST /ai-assistant/ask                         Stateless natural language Q&A
POST /ai-assistant/audit-summary               AI summary of a module audit
POST /ai-assistant/recommendations             Rule-based QA recommendations
GET  /ai-assistant/suggested-prompts           Role-aware prompt suggestions
GET  /ai-assistant/modes                       Available agent mode list

Chat sessions
POST /ai-assistant/sessions                    Create a new chat session
GET  /ai-assistant/sessions                    List current user's sessions
GET  /ai-assistant/sessions/{id}               Get session detail with messages
POST /ai-assistant/sessions/{id}/ask           Ask within a session (persists messages)
DELETE /ai-assistant/sessions/{id}             Soft-delete a session

Tenant isolation
----------------
- SYSTEM_ADMIN must supply institution_code in the request body.
- All other roles are locked to their own institution.
- GFU/RCT are excluded (not in ACTIVE_INSTITUTION_CODES).
- Students cannot access any endpoint (LecturerRequired minimum).
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_assistant import assistant_service
from app.ai_assistant.llm_router_service import llm_route_prompt
from app.ai_assistant.prompt_templates import AGENT_MODE_LABELS, AGENT_MODES
from app.ai_assistant.recommendation_engine import get_recommendations
from app.ai_providers.manager import get_provider_manager
from app.ai_providers.base_provider import AIMessage
from app.rag.advanced_rag_service import advanced_ask
from app.ai_providers.provider_factory import get_provider
from app.database import get_db
from app.dependencies import LecturerRequired, ConversationAccessRequired, get_external_scope
from app.core.external_scope import ExternalScope, deny_external_access
from app.knowledge_indexing.embedding_service import embedding_service
from app.knowledge_indexing.search_service import ACTIVE_INSTITUTION_CODES
from app.models.ai_chat import AiChatMessage, AiChatSession
from app.models.audit_run import AuditRun
from app.models.enums import UserRole
from app.models.institution import Institution
from app.models.module import Module
from app.models.user import User
from app.schemas.ai_assistant import (
    AskRequest,
    AskResponse,
    AuditSummaryRequest,
    AuditSummaryResponse,
    ChatMessageBrief,
    ChatSessionBrief,
    ChatSessionCreate,
    ChatSessionDetail,
    RecommendationItem,
    RecommendationRequest,
    RecommendationsResponse,
    SuggestedPrompt,
    SuggestedPromptsResponse,
    WorkspaceContextHint,
)

import logging as _logging_module

_logger = _logging_module.getLogger(__name__)

router = APIRouter(prefix="/ai-assistant", tags=["AI QA Assistant"])

# Attachment grounding stage labels
_STAGE_REQUESTED = "ATTACHMENT_REQUESTED"
_STAGE_FOUND = "ATTACHMENT_FOUND"
_STAGE_LOADED = "ATTACHMENT_LOADED"
_STAGE_PARSED = "ATTACHMENT_PARSED"
_STAGE_USED = "ATTACHMENT_USED"
_STAGE_FAILED = "ATTACHMENT_FAILED"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _resolve_institution_code(
    db: AsyncSession,
    current_user: User,
    requested_code: str | None,
) -> str | None:
    if current_user.role == UserRole.SYSTEM_ADMIN:
        if not requested_code:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="System Admin must supply institution_code in the request.",
            )
        code = requested_code.upper()
        if code not in ACTIVE_INSTITUTION_CODES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"'{code}' is not an active pilot institution. "
                    f"Active pilots: {sorted(ACTIVE_INSTITUTION_CODES)}"
                ),
            )
        return code

    if current_user.role == UserRole.GENERIC_USER:
        return None

    if current_user.institution_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Your account has no institution assigned. Contact your System Admin.",
        )

    inst = await db.get(Institution, current_user.institution_id)
    if inst is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found.")

    code = inst.code.upper()
    if code not in ACTIVE_INSTITUTION_CODES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Your institution '{code}' does not have an active IKP knowledge base. "
                "Contact your System Admin to set up vector indexing."
            ),
        )
    return code


async def _persist_message_pair(
    db: AsyncSession,
    session_id: uuid.UUID,
    question: str,
    result: dict[str, Any],
    structured_blocks: list | None = None,
    context_snapshot: dict | None = None,
    attached_file_ids: list[str] | None = None,
    referenced_finding_ids: list[str] | None = None,
    referenced_framework_ids: list[str] | None = None,
    citations: list | None = None,
) -> tuple[uuid.UUID, uuid.UUID]:
    """Persist user question and assistant response to the chat session.

    Returns (user_message_id, assistant_message_id).
    """
    now = datetime.now(tz=timezone.utc)
    user_msg_id = uuid.uuid4()
    assistant_msg_id = uuid.uuid4()

    user_msg = AiChatMessage(
        id=user_msg_id,
        session_id=session_id,
        role="user",
        content=question,
        attached_file_ids=attached_file_ids,
        created_at=now,
        updated_at=now,
    )
    db.add(user_msg)

    assistant_msg = AiChatMessage(
        id=assistant_msg_id,
        session_id=session_id,
        role="assistant",
        content=result.get("answer", ""),
        sources=result.get("sources"),
        confidence_score=result.get("confidence_score"),
        provider=result.get("provider"),
        model_name=result.get("model"),
        query_mode=result.get("query_mode"),
        intent=result.get("query_mode"),
        structured_blocks=structured_blocks,
        citations=citations,
        referenced_finding_ids=referenced_finding_ids,
        referenced_framework_ids=referenced_framework_ids,
        created_at=now,
        updated_at=now,
    )
    db.add(assistant_msg)

    # Update session metadata
    session = await db.get(AiChatSession, session_id)
    if session:
        session.provider = result.get("provider")
        session.model_name = result.get("model")
        if context_snapshot:
            session.context_snapshot = context_snapshot

    await db.commit()
    return user_msg_id, assistant_msg_id


# ---------------------------------------------------------------------------
# GET /ai-assistant/modes
# ---------------------------------------------------------------------------


@router.get(
    "/modes",
    summary="List available agent modes",
)
async def list_modes(
    current_user: User = LecturerRequired,
) -> list[dict[str, str]]:
    """Return all available agent modes with their labels."""
    return [{"mode": m, "label": AGENT_MODE_LABELS[m]} for m in AGENT_MODES]


# ---------------------------------------------------------------------------
# POST /ai-assistant/ask
# ---------------------------------------------------------------------------


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask the AI QA Assistant a natural language question",
)
async def ask_assistant(
    body: AskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = ConversationAccessRequired,
    ext_scope: ExternalScope | None = Depends(get_external_scope),
) -> dict[str, Any]:
    # External moderators cannot access the tenant-wide AI workspace.
    # The RAG pipeline has no module-level scope; granting access would expose
    # other modules' evidence from the same institution's knowledge index.
    if ext_scope is not None:
        deny_external_access(ext_scope, "the AI assistant (tenant-wide RAG access is unavailable to external reviewers)")
    if current_user.role == UserRole.GENERIC_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Generic conversations must use /ai-assistant/ask-stream.",
        )
    institution_code = await _resolve_institution_code(db, current_user, body.institution_code)

    try:
        manager = get_provider_manager()
        provider = await manager.get_healthy_provider()
        result = await advanced_ask(
            question=body.question,
            institution_code=institution_code,
            context_limit=body.context_limit,
            mode=body.mode if body.mode in AGENT_MODES else "qa_assistant",
            provider=provider,
        )
    except Exception as exc:  # noqa: BLE001 — convert to a safe 503, no stack trace leak
        exc_str = str(exc).lower()
        _logger.exception("AI ask failed: %s", exc)
        if "401" in exc_str or "unauthorized" in exc_str or "authentication" in exc_str:
            detail = "AI provider authentication failed. The service API key may be invalid or expired."
        elif "429" in exc_str or "rate limit" in exc_str or "quota" in exc_str:
            detail = "AI provider quota exceeded. Please try again shortly."
        elif "timeout" in exc_str or "timed out" in exc_str:
            detail = "AI request timed out. Please try again."
        elif "403" in exc_str or "permission" in exc_str or "model" in exc_str:
            detail = "AI provider denied access to the requested model."
        else:
            detail = "AI service temporarily unavailable. Please try again."
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

    if body.session_id:
        try:
            await _persist_message_pair(db, body.session_id, body.question, result)
            result["session_id"] = str(body.session_id)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Failed to persist to session %s: %s", body.session_id, exc)

    return result


# ---------------------------------------------------------------------------
# POST /ai-assistant/ask-stream  (Server-Sent Events)
# ---------------------------------------------------------------------------


def _sse(event_type: str, data: dict[str, Any]) -> str:
    """Format a single SSE data line."""
    return f"data: {json.dumps({'type': event_type, **data})}\n\n"


async def _stream_ask(
    question: str,
    institution_code: str | None,
    context_limit: int,
    mode: str,
    db: AsyncSession | None = None,
    current_user: User | None = None,
    workspace_context: WorkspaceContextHint | None = None,
    file_chunks: list[dict] | None = None,
    conversation_history: list[AIMessage] | None = None,
) -> Any:
    """Async generator that yields SSE lines for one ask-stream request.

    Stream shape:
        context    — resolved context (institution, module, programme, frameworks)
        start      — routing decision (intent, agents, confidence, routing_reason)
        plan       — D2 execution plan (intent, services, permissions)
        token      — incremental answer text
        structured — D5 structured response blocks
        regulatory — regulatory-specific data (citations, frameworks, caveat) [regulatory mode only]
        sources    — Qdrant sources and follow-up data [non-regulatory mode only]
        metadata   — Advanced RAG citation data [non-regulatory mode only]
        done       — provider/model metadata
        error      — emitted instead of other events on failure
    """
    import logging as _log
    _logger = _log.getLogger(__name__)

    # Generic users have personal workspaces, not a null/global institution.
    # They deliberately bypass institution-scoped context, orchestration and RAG.
    if current_user is not None and current_user.role == UserRole.GENERIC_USER:
        try:
            manager = get_provider_manager()
            provider = await manager.get_healthy_provider()
            system_prompt = (
                "You are AQAA, an Academic Quality Assurance Agent for a personal, "
                "non-institutional workspace. Help with module/course folders, learning "
                "outcomes, teaching plans and content, assessments, memoranda, marking "
                "guides, rubrics, moderation, attendance, results, QA findings, remediation, "
                "readiness and reporting. Use only these evidence statuses: PRESENT, MISSING, "
                "INCOMPLETE, NON-COMPLIANT, NOT APPLICABLE, UNABLE TO DETERMINE. Clearly "
                "distinguish general QA knowledge, facts stated by the user, actually retrieved "
                "evidence, and unknown or insufficient evidence. Never claim to have inspected "
                "evidence unless it was genuinely retrieved. Never invent the user's institution "
                "or institution-specific requirements."
            )
            messages = [AIMessage(role="system", content=system_prompt)]
            messages.extend(conversation_history or [])
            if file_chunks:
                evidence_sections: list[str] = []
                remaining = 16000
                for chunk in file_chunks:
                    excerpt = str(chunk.get("text") or "")[:remaining]
                    evidence_sections.append(
                        f"SOURCE: {chunk.get('source_document') or chunk.get('title')}\n{excerpt}"
                    )
                    remaining -= len(excerpt)
                    if remaining <= 0:
                        break
                messages.append(AIMessage(
                    role="system",
                    content=(
                        "The following evidence was retrieved from files owned by this user. "
                        "Ground claims only in these excerpts, cite source filenames, and say "
                        "when extraction is insufficient.\n\n" + "\n\n".join(evidence_sections)
                    ),
                ))
            messages.append(AIMessage(role="user", content=question))
            answer = await provider.complete(messages, temperature=0.2, max_tokens=1400)
            yield _sse("start", {
                "intent": "qa_general", "agents": ["AQAA"], "confidence": 1.0,
                "routing_reason": "Generic personal workspace", "used_llm": not provider.is_local_dev,
            })
            words = answer.split(" ")
            for i in range(0, len(words), 6):
                content = " ".join(words[i:i + 6])
                yield _sse("token", {"content": content if i == 0 else " " + content})
                await asyncio.sleep(0.02)
            sources = [
                {
                    "entity_type": chunk.get("entity_type", "owned_file"),
                    "entity_key": chunk.get("entity_id"),
                    "title": chunk.get("title"),
                    "source_document": chunk.get("source_document"),
                    "relevance_score": 1.0,
                }
                for chunk in (file_chunks or [])
            ]
            yield _sse("sources", {
                "sources": sources, "confidence_score": 1.0 if sources else 0.0, "suggested_followups": [],
                "suggested_next_actions": [], "follow_up_questions": [],
            })
            if sources:
                yield _sse("metadata", {
                    "citations": [
                        {
                            "source_id": source["entity_key"],
                            "title": source["title"],
                            "entity_type": source["entity_type"],
                            "snippet": "User-owned retrieved evidence",
                            "relevance_score": 1.0,
                            "source_document": source["source_document"],
                        }
                        for source in sources
                    ],
                    "unsupported_claims": [],
                    "grounding_status": "grounded",
                })
            yield _sse("done", {
                "provider": provider.provider_name, "model": provider.model_name,
                "query_mode": "generic_qa", "is_placeholder_mode": provider.is_local_dev,
            })
        except Exception as exc:
            _logger.error("generic ask-stream failed: %s", exc)
            yield _sse("error", {"message": "The AI service could not complete the request. Please try again."})
        return

    # D1 — Resolve context
    resolved_ctx = None
    if db is not None and current_user is not None:
        try:
            from app.services.context_engine import resolve_context
            ws_dict: dict = {}
            if workspace_context:
                ws_dict = {
                    k: str(v) for k, v in workspace_context.model_dump().items() if v is not None
                }
            resolved_ctx = await resolve_context(
                db, current_user, question, workspace_context=ws_dict
            )
            yield _sse("context", resolved_ctx.to_public_dict())
        except Exception as exc:
            _logger.warning("context_engine failed: %s", exc)

    # D2 — Build execution plan
    execution_plan = None
    if resolved_ctx is not None:
        try:
            from app.services.request_planner import build_execution_plan
            execution_plan = build_execution_plan(question, resolved_ctx)
            yield _sse("plan", execution_plan.to_sse_dict())
        except Exception as exc:
            _logger.warning("request_planner failed: %s", exc)

    # 1. LLM-assisted routing (with keyword fallback built-in)
    try:
        router = await llm_route_prompt(question)
    except Exception as exc:
        _logger.error("ask-stream: llm_route_prompt failed: %s", exc)
        router = {
            "intent": "qa_general",
            "agents": ["QA General Assistant"],
            "confidence": 0.5,
            "routing_reason": "Routing failed — using default QA assistant.",
            "agent_mode": "general",
            "suggested_next_actions": [],
            "follow_up_questions": [],
            "used_llm": False,
        }

    yield _sse("start", {
        "intent": router["intent"],
        "agents": router["agents"],
        "confidence": router["confidence"],
        "routing_reason": router["routing_reason"],
        "used_llm": router["used_llm"],
    })

    # 2. Resolve effective mode from router (override request body mode)
    effective_mode = router.get("agent_mode", mode)
    if effective_mode not in AGENT_MODES:
        effective_mode = "qa_assistant"

    # D3 — Orchestrate via registry when plan exists and not regulatory
    if execution_plan is not None and not execution_plan.is_regulatory and db is not None and current_user is not None:
        if execution_plan.intent.value in {
            "LIST_FINDINGS", "EXPLAIN_FINDING", "ASSIGN_FINDING",
            "SUBMIT_RESOLUTION", "REVIEW_RESOLUTION", "ESCALATE_FINDING",
            "GENERATE_CORRECTIVE_ACTION_PLAN",
        }:
            try:
                from app.services.orchestration_registry import dispatch
                orch_result = await dispatch(execution_plan, db, current_user, question)
                if orch_result.final_answer:
                    words = orch_result.final_answer.split(" ")
                    for i in range(0, len(words), 6):
                        chunk = " ".join(words[i:i+6])
                        if i > 0:
                            chunk = " " + chunk
                        yield _sse("token", {"content": chunk})
                        await asyncio.sleep(0.02)
                if orch_result.structured_blocks:
                    yield _sse("structured", {
                        "blocks": orch_result.structured_blocks,
                        "execution_summary": orch_result.execution_summary,
                        "requires_human_review": orch_result.requires_human_review,
                        "human_review_reason": orch_result.human_review_reason,
                    })
                yield _sse("done", {
                    "provider": "orchestration_registry",
                    "model": "deterministic",
                    "query_mode": execution_plan.intent.value.lower(),
                    "is_placeholder_mode": False,
                })
                return
            except Exception as exc:
                _logger.warning("orchestration_registry dispatch failed: %s", exc)

    # 3a. Regulatory branch — invoke orchestration service
    if effective_mode == "regulatory" and db is not None and current_user is not None:
        try:
            from app.services.regulatory_orchestration_service import orchestrate_regulatory_query
            regulatory_resp = await orchestrate_regulatory_query(
                db,
                current_user,
                prompt=question,
                primary_intent=router.get("intent", "identify_applicable_frameworks"),
                routing_confidence=float(router.get("confidence", 0.7)),
            )
        except Exception as exc:
            import logging
            logging.getLogger(__name__).error("ask-stream: regulatory orchestration failed: %s", exc)
            yield _sse("error", {"message": "The regulatory AI service could not complete the request. Please try again."})
            return

        answer: str = regulatory_resp.answer
        words = answer.split(" ")
        CHUNK_WORDS = 6
        for i in range(0, len(words), CHUNK_WORDS):
            chunk_words = words[i : i + CHUNK_WORDS]
            content = " ".join(chunk_words)
            if i > 0:
                content = " " + content
            yield _sse("token", {"content": content})
            await asyncio.sleep(0.02)

        yield _sse("regulatory", {
            "citations": [c.to_dict() for c in regulatory_resp.citations],
            "effective_frameworks": regulatory_resp.effective_frameworks,
            "requires_human_review": regulatory_resp.requires_human_review,
            "generation_mode": regulatory_resp.generation_mode.value,
            "caveat": regulatory_resp.caveat,
            "suggested_next_actions": regulatory_resp.suggested_next_actions,
            "follow_up_questions": regulatory_resp.follow_up_questions,
        })

        yield _sse("done", {
            "provider": "regulatory_orchestration",
            "model": "deterministic+hybrid",
            "query_mode": effective_mode,
            "is_placeholder_mode": False,
        })
        return

    # 3b. Standard branch — Advanced RAG pipeline
    try:
        manager = get_provider_manager()
        provider = await manager.get_healthy_provider()

        # Surface cascade-to-local-dev as a visible warning rather than silent template.
        # Guard fires only when an external provider was intentionally configured (not "LOCAL_DEV")
        # but all failed, causing a silent fallback to the placeholder provider.
        # isinstance guard keeps the check test-safe: MagicMock is not str.
        _cfg = getattr(manager, "_configured_name", None)
        if getattr(provider, "is_local_dev", False) and isinstance(_cfg, str) and _cfg.upper() != "LOCAL_DEV":
            yield _sse("error", {
                "message": (
                    "AI provider authentication failed. All configured providers are unavailable. "
                    "Please contact your system administrator."
                ),
            })
            return

        result = await advanced_ask(
            question=question,
            institution_code=institution_code,
            context_limit=context_limit,
            mode=effective_mode,
            provider=provider,
            injected_chunks=file_chunks,
        )
    except Exception as exc:
        exc_str = str(exc).lower()
        _logger.error("ask-stream: advanced_ask failed: %s", exc)
        if "401" in exc_str or "unauthorized" in exc_str or "authentication" in exc_str:
            msg = "AI provider authentication failed. The service API key may be invalid or expired."
        elif "429" in exc_str or "rate limit" in exc_str or "quota" in exc_str:
            msg = "AI provider quota exceeded. Please try again shortly."
        elif "timeout" in exc_str or "timed out" in exc_str:
            msg = "AI request timed out. Please try again."
        elif "403" in exc_str or "permission" in exc_str:
            msg = "AI provider denied access to the requested model."
        else:
            msg = "An error occurred while generating a response. Please try again."
        yield _sse("error", {"message": msg})
        return

    # 4. Simulate streaming: split answer into word-level token events
    answer = result.get("answer", "")
    words = answer.split(" ")
    CHUNK_WORDS = 6
    for i in range(0, len(words), CHUNK_WORDS):
        chunk_words = words[i : i + CHUNK_WORDS]
        content = " ".join(chunk_words)
        if i > 0:
            content = " " + content
        yield _sse("token", {"content": content})
        await asyncio.sleep(0.02)

    # 5. Sources event
    yield _sse("sources", {
        "sources": result.get("sources", []),
        "confidence_score": result.get("confidence_score", 0.0),
        "suggested_followups": result.get("suggested_followups", []),
        "suggested_next_actions": router.get("suggested_next_actions", []),
        "follow_up_questions": router.get("follow_up_questions", []),
    })

    # 6. Metadata event (Advanced RAG citation data)
    yield _sse("metadata", {
        "citations": result.get("citations", []),
        "unsupported_claims": result.get("unsupported_claims", []),
        "grounding_status": result.get("grounding_status", "no_source_found"),
    })

    # 7. Done event
    yield _sse("done", {
        "provider": result.get("provider", "unknown"),
        "model": result.get("model", "unknown"),
        "query_mode": result.get("query_mode", effective_mode),
        "is_placeholder_mode": result.get("is_placeholder_mode", False),
    })


@router.post(
    "/ask-stream",
    summary="Ask the AI QA Assistant — streaming SSE response",
    response_model=None,
)
async def ask_assistant_stream(
    body: AskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = ConversationAccessRequired,
    ext_scope: ExternalScope | None = Depends(get_external_scope),
):
    """POST /ai-assistant/ask-stream

    Returns a text/event-stream response.  Each SSE event is a JSON object
    with a 'type' field: start | chunk | sources | done | error.

    Client usage (fetch + ReadableStream):
        const res = await fetch('/api/proxy/ai-assistant/ask-stream', {
            method: 'POST', credentials: 'include',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ question, institution_code, context_limit, mode }),
        });
        const reader = res.body.getReader();
    """
    if ext_scope is not None:
        deny_external_access(ext_scope, "the AI assistant (tenant-wide RAG access is unavailable to external reviewers)")
    # Authorize every attachment before resolving or creating a session. This
    # makes guessed IDs side-effect free and prevents partial mixed-owner use.
    if body.attached_file_ids:
        from app.services.file_service import get_file_for_user
        for file_id in body.attached_file_ids:
            await get_file_for_user(db, file_id, current_user)
    institution_code = await _resolve_institution_code(db, current_user, body.institution_code)
    effective_mode = body.mode if body.mode in AGENT_MODES else "qa_assistant"

    # Resolve or create a session for message persistence
    session_id: uuid.UUID
    if body.session_id is not None:
        existing = await db.get(AiChatSession, body.session_id)
        if (
            existing is None
            or existing.user_id != current_user.id
            or not existing.is_active
            or existing.is_deleted
        ):
            raise HTTPException(status_code=404, detail="Session not found.")
        session_id = existing.id
    else:
        new_session = AiChatSession(
            id=uuid.uuid4(),
            user_id=current_user.id,
            institution_id=current_user.institution_id,
            title=body.question[:80],
        )
        db.add(new_session)
        await db.commit()
        session_id = new_session.id

    attached_ids = [str(fid) for fid in body.attached_file_ids] if body.attached_file_ids else None

    history_result = await db.execute(
        select(AiChatMessage)
        .where(AiChatMessage.session_id == session_id)
        .order_by(AiChatMessage.created_at.desc())
        .limit(20)
    )
    prior_messages = list(reversed(history_result.scalars().all()))
    conversation_history = [
        AIMessage(role=message.role, content=message.content)
        for message in prior_messages
        if message.role in {"user", "assistant"}
    ]

    # ---------------------------------------------------------------------------
    # Attachment grounding pipeline
    # States per file: REQUESTED → FOUND → LOADED → PARSED → USED / FAILED
    # When injected_chunks is non-None, advanced_ask skips Qdrant entirely.
    # When all attachments fail, file_chunks stays [] (not None) so Qdrant is
    # also bypassed — the assistant must not silently query the knowledge base
    # when the user pinned scope to specific files.
    # ---------------------------------------------------------------------------
    from app.services.file_service import get_file_content_for_user
    from app.parsers.factory import get_parser, is_supported

    file_chunks: list[dict] | None = None
    attachment_report: dict = {
        "attachment_grounding_status": "not_requested",
        "requested_count": 0,
        "used_count": 0,
        "failed_count": 0,
        "files": [],
    }

    if body.attached_file_ids:
        attachment_report["attachment_grounding_status"] = "requested"
        attachment_report["requested_count"] = len(body.attached_file_ids)
        file_chunks = []

        for fid in body.attached_file_ids:
            file_status: dict = {
                "file_id": str(fid),
                "stage": _STAGE_REQUESTED,
                "success": False,
            }
            try:
                # FOUND — fetch DB record and raw bytes from storage
                db_file, raw_bytes = await get_file_content_for_user(db, fid, current_user)
                file_status["filename"] = db_file.original_filename
                file_status["stage"] = _STAGE_FOUND

                # LOADED — bytes available; determine text extraction path
                mime = db_file.mime_type or ""
                file_status["stage"] = _STAGE_LOADED

                # PARSED — extract plain text
                if is_supported(mime):
                    parser = get_parser(mime)
                    extraction = await parser.extract(raw_bytes, db_file.original_filename)
                    text = extraction.text[:8000]
                else:
                    text = raw_bytes.decode("utf-8", errors="replace")[:8000]
                file_status["stage"] = _STAGE_PARSED

                # USED — build knowledge chunk
                file_chunks.append({
                    "entity_type": "attached_file",
                    "entity_id": str(fid),
                    "title": db_file.original_filename,
                    "text": text,
                    "source_document": db_file.original_filename,
                    "confidence_score": 1.0,
                    "combined_score": 1.0,
                    "institution_id": (
                        str(db_file.institution_id) if db_file.institution_id else None
                    ),
                    "owner_user_id": (
                        str(db_file.owner_user_id) if db_file.owner_user_id else None
                    ),
                })
                file_status["stage"] = _STAGE_USED
                file_status["success"] = True

            except Exception as exc:
                file_status["stage"] = _STAGE_FAILED
                file_status["error_type"] = type(exc).__name__
                _logger.warning(
                    "ask-stream: attachment extraction failed | "
                    "file_id=%s filename=%s stage_reached=%s exc_type=%s msg=%s",
                    fid,
                    file_status.get("filename", "unknown"),
                    file_status.get("stage", _STAGE_REQUESTED),
                    type(exc).__name__,
                    exc,
                )

            attachment_report["files"].append(file_status)

        _used = sum(1 for f in attachment_report["files"] if f["success"])
        _failed = len(attachment_report["files"]) - _used
        attachment_report["used_count"] = _used
        attachment_report["failed_count"] = _failed

        if _used == 0:
            attachment_report["attachment_grounding_status"] = "failed"
        elif _failed > 0:
            attachment_report["attachment_grounding_status"] = "partial"
        else:
            attachment_report["attachment_grounding_status"] = "success"

    # Generic personal workspaces may retrieve only from the signed-in user's
    # own ready files. Explicit attachments remain authoritative; automatic
    # retrieval runs only when the user has not pinned the scope.
    if current_user.role == UserRole.GENERIC_USER and file_chunks is None:
        from app.services.generic_retrieval_service import retrieve_owned_chunks

        file_chunks = await retrieve_owned_chunks(db, current_user, body.question)

    async def _persist_and_stream():
        # Emit attachment status before the LLM stream begins so the client
        # can display grounding state (success / partial / failed) immediately.
        if body.attached_file_ids:
            yield _sse("attachment", attachment_report)

        answer_parts: list[str] = []
        result_meta: dict[str, Any] = {}
        context_snapshot: dict | None = None
        structured_blocks: list | None = None
        citations_data: list | None = None
        sources_data: list | None = None

        async for chunk in _stream_ask(
            body.question,
            institution_code,
            body.context_limit,
            effective_mode,
            db=db,
            current_user=current_user,
            workspace_context=body.workspace_context,
            file_chunks=file_chunks,
            conversation_history=conversation_history,
        ):
            # Accumulate tokens and metadata for persistence
            try:
                raw = chunk.removeprefix("data: ").strip()
                if raw:
                    evt = json.loads(raw)
                    etype = evt.get("type")
                    if etype == "token":
                        answer_parts.append(evt.get("content", ""))
                    elif etype == "done":
                        result_meta = evt
                    elif etype == "context":
                        context_snapshot = evt
                    elif etype == "structured":
                        structured_blocks = evt.get("blocks")
                    elif etype == "metadata":
                        citations_data = evt.get("citations")
                    elif etype == "sources":
                        sources_data = evt.get("sources")
                    elif etype == "regulatory":
                        # Persist regulatory citations as structured blocks
                        # so they survive session restoration.
                        reg_cits = evt.get("citations", [])
                        if reg_cits and citations_data is None:
                            citations_data = reg_cits
            except Exception:
                pass
            yield chunk

        # After stream: persist message pair to DB
        try:
            await _persist_message_pair(
                db=db,
                session_id=session_id,
                question=body.question,
                result={
                    "answer": "".join(answer_parts),
                    "provider": result_meta.get("provider"),
                    "model": result_meta.get("model"),
                    "query_mode": result_meta.get("query_mode"),
                    "sources": sources_data,
                    "confidence_score": result_meta.get("confidence"),
                },
                context_snapshot=context_snapshot,
                attached_file_ids=attached_ids,
                structured_blocks=structured_blocks,
                citations=citations_data,
            )
        except Exception as exc:
            _logger.error("ask-stream: message persistence failed: %s", exc)

        # Emit session_id so the client can restore the session
        yield _sse("session", {"session_id": str(session_id)})

    return StreamingResponse(
        _persist_and_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# POST /ai-assistant/audit-summary
# ---------------------------------------------------------------------------


@router.post(
    "/audit-summary",
    response_model=AuditSummaryResponse,
    summary="Get an AI-assisted summary of a module audit",
)
async def get_audit_summary(
    body: AuditSummaryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> AuditSummaryResponse:
    module_name: str | None = None
    compliance_pct: float | None = None
    risk_level: str | None = None
    audit_status: str | None = None
    findings: list[str] = []

    if body.audit_run_id:
        run = await db.get(AuditRun, body.audit_run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Audit run not found.")
        if current_user.role != UserRole.SYSTEM_ADMIN:
            if run.institution_id != current_user.institution_id:
                raise HTTPException(status_code=403, detail="Access denied.")
        audit_status = run.run_status
        findings = [f"Agent: {run.agent_type}", f"Status: {run.run_status}"]

    if body.module_id:
        mod = await db.get(Module, body.module_id)
        if mod:
            module_name = mod.name
            stmt = (
                select(AuditRun)
                .where(AuditRun.module_id == body.module_id)
                .order_by(AuditRun.created_at.desc())
                .limit(1)
            )
            result = await db.execute(stmt)
            latest_run = result.scalar_one_or_none()
            if latest_run:
                audit_status = latest_run.run_status
                if not findings:
                    findings = [
                        f"Most recent audit: {latest_run.agent_type}",
                        f"Status: {latest_run.run_status}",
                    ]

    recs = get_recommendations(
        audit_status=audit_status if audit_status in ("compliant", "at_risk", "non_compliant") else None,
    )

    return AuditSummaryResponse(
        module_name=module_name,
        compliance_percentage=compliance_pct,
        risk_level=risk_level,
        audit_status=audit_status,
        key_findings=findings,
        recommendations=[r["action"] for r in recs[:3]],
        is_placeholder_mode=embedding_service.IS_PLACEHOLDER,
    )


# ---------------------------------------------------------------------------
# POST /ai-assistant/recommendations
# ---------------------------------------------------------------------------


@router.post(
    "/recommendations",
    response_model=RecommendationsResponse,
    summary="Get rule-based QA improvement recommendations",
)
async def get_qa_recommendations(
    body: RecommendationRequest,
    current_user: User = LecturerRequired,
) -> RecommendationsResponse:
    recs = get_recommendations(
        audit_status=body.audit_status,
        missing_evidence_types=body.missing_evidence_types,
    )
    return RecommendationsResponse(
        recommendations=[RecommendationItem(**r) for r in recs],
        is_placeholder_mode=embedding_service.IS_PLACEHOLDER,
    )


# ---------------------------------------------------------------------------
# GET /ai-assistant/suggested-prompts
# ---------------------------------------------------------------------------


@router.get(
    "/suggested-prompts",
    response_model=SuggestedPromptsResponse,
    summary="Get role-aware suggested questions for the AI assistant",
)
async def get_suggested_prompts(
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> SuggestedPromptsResponse:
    institution_code: str | None = None
    if current_user.role != UserRole.SYSTEM_ADMIN and current_user.institution_id:
        inst = await db.get(Institution, current_user.institution_id)
        institution_code = inst.code if inst else None

    prompts_raw = assistant_service.get_suggested_prompts(
        role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        institution_code=institution_code,
    )

    return SuggestedPromptsResponse(
        prompts=[SuggestedPrompt(**p) for p in prompts_raw],
        institution_code=institution_code,
    )


# ---------------------------------------------------------------------------
# Chat session endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/sessions",
    response_model=ChatSessionBrief,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new AI chat session",
)
async def create_session(
    body: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = ConversationAccessRequired,
    ext_scope: ExternalScope | None = Depends(get_external_scope),
) -> ChatSessionBrief:
    if ext_scope is not None:
        deny_external_access(ext_scope, "AI chat sessions (tenant-wide RAG access is unavailable to external reviewers)")
    institution_id: uuid.UUID | None = None

    if body.institution_code:
        resolved_code = body.institution_code.upper()
        if resolved_code in ACTIVE_INSTITUTION_CODES:
            result = await db.execute(
                select(Institution).where(Institution.code == resolved_code)
            )
            inst = result.scalar_one_or_none()
            if inst:
                institution_id = inst.id
    elif current_user.institution_id:
        institution_id = current_user.institution_id

    provider = get_provider()
    now = datetime.now(tz=timezone.utc)

    session = AiChatSession(
        id=uuid.uuid4(),
        user_id=current_user.id,
        institution_id=institution_id,
        mode=body.mode if body.mode in AGENT_MODES else "qa_assistant",
        title=body.title,
        provider=provider.provider_name,
        model_name=provider.model_name,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return ChatSessionBrief(
        id=session.id,
        mode=session.mode,
        title=session.title,
        provider=session.provider,
        model_name=session.model_name,
        is_active=session.is_active,
        is_pinned=session.is_pinned,
        is_archived=session.is_archived,
        created_at=session.created_at,
        message_count=0,
    )


@router.get(
    "/sessions",
    response_model=list[ChatSessionBrief],
    summary="List the current user's chat sessions",
)
async def list_sessions(
    pinned_only: bool = False,
    archived: bool = False,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = ConversationAccessRequired,
) -> list[ChatSessionBrief]:
    stmt = select(AiChatSession).where(
        AiChatSession.user_id == current_user.id,
        AiChatSession.is_active.is_(True),
        AiChatSession.is_deleted.is_(False),
    )
    if pinned_only:
        stmt = stmt.where(AiChatSession.is_pinned.is_(True))
    if archived:
        stmt = stmt.where(AiChatSession.is_archived.is_(True))
    else:
        stmt = stmt.where(AiChatSession.is_archived.is_(False))
    stmt = stmt.order_by(AiChatSession.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(stmt)
    sessions = result.scalars().all()

    out: list[ChatSessionBrief] = []
    for s in sessions:
        count_result = await db.execute(
            select(func.count()).select_from(AiChatMessage).where(
                AiChatMessage.session_id == s.id
            )
        )
        msg_count = count_result.scalar_one() or 0
        out.append(
            ChatSessionBrief(
                id=s.id,
                mode=s.mode,
                title=s.title,
                provider=s.provider,
                model_name=s.model_name,
                is_active=s.is_active,
                is_pinned=s.is_pinned,
                is_archived=s.is_archived,
                created_at=s.created_at,
                message_count=msg_count,
            )
        )
    return out


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionDetail,
    summary="Get a chat session with all messages",
)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = ConversationAccessRequired,
) -> ChatSessionDetail:
    session = await db.get(AiChatSession, session_id)
    if session is None or not session.is_active:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.user_id != current_user.id:
        admin_can_read_institutional = (
            current_user.role == UserRole.SYSTEM_ADMIN
            and session.institution_id is not None
        )
        if not admin_can_read_institutional:
            raise HTTPException(status_code=403, detail="Access denied.")

    result = await db.execute(
        select(AiChatMessage)
        .where(AiChatMessage.session_id == session_id)
        .order_by(AiChatMessage.created_at.asc())
    )
    messages = result.scalars().all()

    return ChatSessionDetail(
        id=session.id,
        mode=session.mode,
        title=session.title,
        provider=session.provider,
        model_name=session.model_name,
        is_active=session.is_active,
        is_pinned=session.is_pinned,
        is_archived=session.is_archived,
        created_at=session.created_at,
        messages=[
            ChatMessageBrief(
                id=m.id,
                role=m.role,
                content=m.content,
                confidence_score=m.confidence_score,
                provider=m.provider,
                query_mode=m.query_mode,
                intent=m.intent,
                created_at=m.created_at,
                sources=m.sources,
                attached_file_ids=m.attached_file_ids,
                structured_blocks=m.structured_blocks,
                citations=m.citations,
            )
            for m in messages
        ],
    )


@router.post(
    "/sessions/{session_id}/ask",
    response_model=AskResponse,
    summary="Ask a question within a chat session (persists messages)",
)
async def ask_in_session(
    session_id: uuid.UUID,
    body: AskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = ConversationAccessRequired,
) -> dict[str, Any]:
    session = await db.get(AiChatSession, session_id)
    if session is None or not session.is_active:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    if current_user.role == UserRole.GENERIC_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Generic conversations must use /ai-assistant/ask-stream.",
        )

    institution_code = await _resolve_institution_code(db, current_user, body.institution_code)

    result = await assistant_service.ask(
        question=body.question,
        institution_code=institution_code,
        context_limit=body.context_limit,
        mode=session.mode,
        provider=get_provider(),
    )

    await _persist_message_pair(db, session_id, body.question, result)
    result["session_id"] = str(session_id)
    return result


@router.get(
    "/session-search",
    response_model=list[ChatSessionBrief],
    summary="Search conversation history (D12)",
)
async def search_sessions(
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = ConversationAccessRequired,
) -> list[ChatSessionBrief]:
    """Search the current user's active, non-deleted conversation history by title."""
    stmt = (
        select(AiChatSession)
        .where(
            AiChatSession.user_id == current_user.id,
            AiChatSession.is_active.is_(True),
            AiChatSession.is_deleted.is_(False),
        )
        .order_by(AiChatSession.created_at.desc())
        .limit(100)
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()

    # Filter by keyword if provided
    if q:
        lower_q = q.lower()
        sessions = [s for s in sessions if s.title and lower_q in s.title.lower()]

    out: list[ChatSessionBrief] = []
    for s in sessions[:50]:
        count_result = await db.execute(
            select(func.count()).select_from(AiChatMessage).where(
                AiChatMessage.session_id == s.id
            )
        )
        msg_count = count_result.scalar_one() or 0
        out.append(
            ChatSessionBrief(
                id=s.id,
                mode=s.mode,
                title=s.title,
                provider=s.provider,
                model_name=s.model_name,
                is_active=s.is_active,
                is_pinned=s.is_pinned,
                is_archived=s.is_archived,
                created_at=s.created_at,
                message_count=msg_count,
            )
        )
    return out


# ---------------------------------------------------------------------------
# D1 — Context resolution endpoint
# ---------------------------------------------------------------------------


class ContextRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    workspace_context: WorkspaceContextHint | None = None


@router.post(
    "/resolve-context",
    summary="Resolve context for a prompt (D1 context engine)",
)
async def resolve_context_endpoint(
    body: ContextRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> dict:
    """Return the resolved context for a prompt without executing a query."""
    from app.services.context_engine import resolve_context
    ws_dict: dict = {}
    if body.workspace_context:
        ws_dict = {
            k: str(v) for k, v in body.workspace_context.model_dump().items() if v is not None
        }
    ctx = await resolve_context(db, current_user, body.prompt, workspace_context=ws_dict)
    return ctx.to_public_dict()


# ---------------------------------------------------------------------------
# D6 — Conversational action execution endpoint
# ---------------------------------------------------------------------------


class ConversationalActionRequest(BaseModel):
    action: str = Field(..., description="Natural-language action description")
    entity_type: str = Field(..., description="finding | session | report")
    entity_id: uuid.UUID | None = None
    parameters: dict | None = None
    confirm: bool = Field(default=False, description="User has confirmed this action")


class ConversationalActionResponse(BaseModel):
    action: str
    success: bool
    message: str
    entity_id: uuid.UUID | None = None
    requires_confirmation: bool = False
    confirmation_prompt: str = ""


@router.post(
    "/action",
    response_model=ConversationalActionResponse,
    summary="Execute a conversational action (D6)",
)
async def execute_conversational_action(
    body: ConversationalActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> ConversationalActionResponse:
    """Execute a user-permitted action expressed as natural language.

    Actions that mutate state (assign, approve, reject, close) require
    confirm=true before executing.  Read-only actions execute immediately.
    """
    from app.services.request_planner import _REQUIRES_CONFIRMATION, Intent, _detect_intent

    intent, _conf = _detect_intent(body.action)
    needs_confirm = intent in _REQUIRES_CONFIRMATION

    if needs_confirm and not body.confirm:
        return ConversationalActionResponse(
            action=body.action,
            success=False,
            message="This action requires confirmation.",
            requires_confirmation=True,
            confirmation_prompt=f"Are you sure you want to {body.action.lower()}? This cannot be undone.",
        )

    # Route action to the appropriate service
    if body.entity_type == "finding" and body.entity_id:
        try:
            from app.models.audit_finding import AuditFinding
            finding = await db.get(AuditFinding, body.entity_id)
            if finding is None:
                return ConversationalActionResponse(
                    action=body.action, success=False, message="Finding not found."
                )

            # Permission: check institution
            from app.models.audit_run import AuditRun
            run = await db.get(AuditRun, finding.audit_run_id)
            if run and run.institution_id != current_user.institution_id and current_user.role != UserRole.SYSTEM_ADMIN:
                return ConversationalActionResponse(
                    action=body.action, success=False, message="Access denied."
                )

            # Apply transition based on intent
            from app.models.enums import FindingStatus
            status_map: dict[Intent, FindingStatus] = {
                Intent.ASSIGN_FINDING: FindingStatus.IN_PROGRESS,
                Intent.SUBMIT_RESOLUTION: FindingStatus.PENDING_REVIEW,
                Intent.APPROVE_RESOLUTION: FindingStatus.CLOSED,
                Intent.REJECT_RESOLUTION: FindingStatus.REOPENED,
                Intent.ESCALATE_FINDING: FindingStatus.ESCALATED,
            }
            new_status = status_map.get(intent)
            if new_status:
                finding.status = new_status
                await db.commit()
                return ConversationalActionResponse(
                    action=body.action,
                    success=True,
                    message=f"Finding updated to {new_status.value}.",
                    entity_id=finding.id,
                )
        except Exception as exc:
            import logging
            logging.getLogger(__name__).error("conversational action failed: %s", exc)
            return ConversationalActionResponse(
                action=body.action, success=False, message="Action failed. Please try again."
            )

    return ConversationalActionResponse(
        action=body.action,
        success=False,
        message="This action type is not yet supported conversationally.",
    )


@router.delete(
    "/sessions/{session_id}",
    response_model=None,
    summary="Soft-delete a chat session",
)
async def delete_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = ConversationAccessRequired,
) -> None:
    session = await db.get(AiChatSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.user_id != current_user.id:
        admin_can_delete_institutional = (
            current_user.role == UserRole.SYSTEM_ADMIN
            and session.institution_id is not None
        )
        if not admin_can_delete_institutional:
            raise HTTPException(status_code=403, detail="Access denied.")
    session.is_active = False
    session.is_deleted = True
    await db.commit()


class SessionRenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


@router.patch(
    "/sessions/{session_id}/rename",
    response_model=ChatSessionBrief,
    summary="Rename a chat session",
)
async def rename_session(
    session_id: uuid.UUID,
    body: SessionRenameRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = ConversationAccessRequired,
) -> ChatSessionBrief:
    session = await db.get(AiChatSession, session_id)
    if session is None or session.is_deleted:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    session.title = body.title
    await db.commit()
    count_result = await db.execute(
        select(func.count()).select_from(AiChatMessage).where(AiChatMessage.session_id == session_id)
    )
    return ChatSessionBrief(
        id=session.id, mode=session.mode, title=session.title, provider=session.provider,
        model_name=session.model_name, is_active=session.is_active, created_at=session.created_at,
        message_count=count_result.scalar_one() or 0,
    )


@router.post(
    "/sessions/{session_id}/pin",
    response_model=ChatSessionBrief,
    summary="Pin or unpin a conversation",
)
async def pin_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = ConversationAccessRequired,
) -> ChatSessionBrief:
    session = await db.get(AiChatSession, session_id)
    if session is None or session.is_deleted:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    session.is_pinned = not session.is_pinned
    await db.commit()
    count_result = await db.execute(
        select(func.count()).select_from(AiChatMessage).where(AiChatMessage.session_id == session_id)
    )
    return ChatSessionBrief(
        id=session.id, mode=session.mode, title=session.title, provider=session.provider,
        model_name=session.model_name, is_active=session.is_active, created_at=session.created_at,
        message_count=count_result.scalar_one() or 0,
    )


@router.post(
    "/sessions/{session_id}/archive",
    response_model=ChatSessionBrief,
    summary="Archive or restore a conversation",
)
async def archive_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = ConversationAccessRequired,
) -> ChatSessionBrief:
    session = await db.get(AiChatSession, session_id)
    if session is None or session.is_deleted:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    session.is_archived = not session.is_archived
    await db.commit()
    count_result = await db.execute(
        select(func.count()).select_from(AiChatMessage).where(AiChatMessage.session_id == session_id)
    )
    return ChatSessionBrief(
        id=session.id, mode=session.mode, title=session.title, provider=session.provider,
        model_name=session.model_name, is_active=session.is_active, created_at=session.created_at,
        message_count=count_result.scalar_one() or 0,
    )


# ---------------------------------------------------------------------------
# GET /ai-assistant/provider-status
# ---------------------------------------------------------------------------


class ProviderStatusResponse(BaseModel):
    provider: str
    model: str
    is_local_dev: bool
    status: str
    message: str


@router.get(
    "/provider-status",
    response_model=ProviderStatusResponse,
    summary="Verify current AI provider connectivity (no secrets exposed)",
)
async def get_provider_status(
    current_user: User = LecturerRequired,
) -> ProviderStatusResponse:
    """Return the active provider name/model and a connectivity check result.

    Never exposes API keys or other secrets.
    """
    from app.ai_providers.base_provider import AIMessage

    provider = get_provider()

    if provider.is_local_dev:
        return ProviderStatusResponse(
            provider=provider.provider_name,
            model=provider.model_name,
            is_local_dev=True,
            status="ok",
            message="LOCAL_DEV provider active. Configure AI_PROVIDER in backend/.env to enable real AI.",
        )

    try:
        test_messages = [AIMessage(role="user", content="Reply OK")]
        response = await provider.complete(test_messages, temperature=0.0, max_tokens=10)
        return ProviderStatusResponse(
            provider=provider.provider_name,
            model=provider.model_name,
            is_local_dev=False,
            status="ok",
            message=f"Provider reachable. Preview: {response[:40]!r}",
        )
    except Exception as exc:
        return ProviderStatusResponse(
            provider=provider.provider_name,
            model=provider.model_name,
            is_local_dev=False,
            status="error",
            message=f"Provider unreachable: {type(exc).__name__}",
        )


# ---------------------------------------------------------------------------
# Intelligent Agent Router
# ---------------------------------------------------------------------------


class AgentRouterRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=2000)


@router.post(
    "/route",
    summary="Intelligent agent router — detect intent and route to the correct agent",
)
async def route_to_agent(
    body: AgentRouterRequest,
    current_user: User = LecturerRequired,
) -> dict:
    """Accept a free-text prompt, auto-detect intent, and return a routing response.

    Returns the detected agent_mode, confidence score, answer, sources, suggested
    next actions, and follow-up questions.  No LLM call is made — intent detection
    uses keyword heuristics for deterministic, low-latency routing.
    """
    from app.services.agent_router_service import route_prompt
    result = route_prompt(body.prompt)
    return result.to_dict()


# ---------------------------------------------------------------------------
# Multi-agent orchestration
# ---------------------------------------------------------------------------


class MultiAgentRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=2000)
    institution_code: str | None = Field(default=None, max_length=20)
    context_limit: int = Field(default=5, ge=1, le=20)
    session_id: uuid.UUID | None = None


class AgentContribution(BaseModel):
    agent: str
    mode: str
    answer: str
    confidence: float
    sources: list[str]


class MultiAgentResponse(BaseModel):
    prompt: str
    agents_used: list[str]
    contributions: list[AgentContribution]
    final_answer: str
    overall_confidence: float
    suggested_next_actions: list[str]
    follow_up_questions: list[str]
    is_multi_agent: bool
    provider: str
    model: str


_MULTI_INTENT_THRESHOLD = 0.55


@router.post(
    "/multi-agent",
    response_model=MultiAgentResponse,
    summary="Multi-agent orchestration — route complex prompts to multiple agents",
)
async def multi_agent_ask(
    body: MultiAgentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> MultiAgentResponse:
    """Analyse a complex prompt, engage multiple agents, and merge their responses.

    For simple prompts, a single agent is used (same as /route + /ask).
    For compound prompts that span multiple domains, each matched agent
    contributes an answer; results are merged into a unified response.

    No cross-tenant data is ever mixed — institution scoping is enforced on
    every agent call.
    """
    from app.services.agent_router_service import detect_intent, _INTENT_PATTERNS, _NEXT_ACTIONS, _FOLLOW_UP_QUESTIONS, _INTENT_TO_MODE

    import re
    lower = body.prompt.lower()

    matched_intents: list[tuple[str, float]] = []
    for intent, patterns in _INTENT_PATTERNS:
        hits = sum(1 for p in patterns if re.search(p, lower))
        if hits:
            total = len(patterns)
            conf = min(0.95, 0.5 + (hits / max(total, 1)) * 0.5)
            matched_intents.append((intent, round(conf, 2)))

    if not matched_intents:
        matched_intents = [("qa_general", 0.5)]

    matched_intents.sort(key=lambda x: x[1], reverse=True)
    active_intents = [i for i in matched_intents if i[1] >= _MULTI_INTENT_THRESHOLD]
    if not active_intents:
        active_intents = [matched_intents[0]]
    active_intents = active_intents[:4]

    institution_code = await _resolve_institution_code(db, current_user, body.institution_code)
    provider = get_provider()

    contributions: list[AgentContribution] = []
    all_actions: list[str] = []
    all_followups: list[str] = []
    agents_used: list[str] = []

    for intent, conf in active_intents:
        mode = _INTENT_TO_MODE.get(intent, "general")
        try:
            result = await assistant_service.ask(
                question=body.prompt,
                institution_code=institution_code,
                context_limit=body.context_limit,
                mode=mode,
                provider=provider,
            )
            contributions.append(AgentContribution(
                agent=intent,
                mode=mode,
                answer=result.get("answer", ""),
                confidence=conf,
                sources=result.get("sources", []),
            ))
            agents_used.append(intent)
        except Exception:
            pass

        all_actions.extend(_NEXT_ACTIONS.get(intent, []))
        all_followups.extend(_FOLLOW_UP_QUESTIONS.get(intent, []))

    if not contributions:
        result = await assistant_service.ask(
            question=body.prompt,
            institution_code=institution_code,
            context_limit=body.context_limit,
            mode="qa_assistant",
            provider=provider,
        )
        contributions.append(AgentContribution(
            agent="qa_general",
            mode="qa_assistant",
            answer=result.get("answer", ""),
            confidence=0.5,
            sources=result.get("sources", []),
        ))
        agents_used = ["qa_general"]

    if len(contributions) == 1:
        final_answer = contributions[0].answer
    else:
        parts = [f"**{c.agent.replace('_', ' ').title()} Agent:**\n{c.answer}" for c in contributions]
        final_answer = "\n\n---\n\n".join(parts)

    overall_confidence = round(sum(c.confidence for c in contributions) / len(contributions), 2)

    unique_actions = list(dict.fromkeys(all_actions))[:6]
    unique_followups = list(dict.fromkeys(all_followups))[:4]

    if body.session_id and contributions:
        try:
            await _persist_message_pair(
                db,
                body.session_id,
                body.prompt,
                {
                    "answer": final_answer,
                    "sources": [s for c in contributions for s in c.sources],
                    "confidence_score": overall_confidence,
                    "provider": provider.provider_name,
                    "model": provider.model_name,
                    "query_mode": ",".join(agents_used),
                },
            )
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Failed to persist multi-agent to session: %s", exc)

    return MultiAgentResponse(
        prompt=body.prompt,
        agents_used=agents_used,
        contributions=contributions,
        final_answer=final_answer,
        overall_confidence=overall_confidence,
        suggested_next_actions=unique_actions,
        follow_up_questions=unique_followups,
        is_multi_agent=len(contributions) > 1,
        provider=provider.provider_name,
        model=provider.model_name,
    )


# ---------------------------------------------------------------------------
# POST /ai-assistant/attach  — Workspace file attachment (D4)
# ---------------------------------------------------------------------------


class WorkspaceAttachmentResponse(BaseModel):
    """Typed response for a workspace file attachment upload.

    Returns file_id (the database File.id) rather than the ambiguous "id".
    frontend must track this as file_id and pass it in attached_file_ids on ask.
    """

    file_id: uuid.UUID
    name: str
    mime_type: str
    size_bytes: int
    upload_state: str
    module_id: uuid.UUID


@router.post(
    "/attach",
    response_model=WorkspaceAttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file attachment from the AI Workspace prompt composer (D4)",
)
async def workspace_attach(
    module_id: Annotated[
        uuid.UUID,
        Form(description="Module UUID this file belongs to. Required — attach files within an active module context."),
    ],
    file: Annotated[UploadFile, File(description="File to attach.")],
    category: Annotated[str, Form(description="File category (FileCategory value).")] = "other",
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> WorkspaceAttachmentResponse:
    """Upload a file from the AI Workspace prompt composer.

    Contract
    --------
    - module_id is **required**.  If the workspace has no module context selected
      the frontend should prompt the user to choose one before attaching files.
    - category defaults to 'other' when no explicit classification is needed.
    - The returned file_id is the canonical identifier to pass in
      attached_file_ids on the next ask-stream request.
    - Role minimum: LecturerRequired (students cannot attach files).
    - Tenant: file is scoped to the module's institution; cross-tenant rejected by
      file_service.upload_file via _resolve_module_institution.
    """
    from app.models.enums import FileCategory
    from app.services import file_service
    from app.services.validation_service import UploadValidationError

    # Validate category enum — default to OTHER if invalid
    try:
        file_category = FileCategory(category)
    except ValueError:
        file_category = FileCategory.OTHER

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Empty file — attach a non-empty document.",
        )

    try:
        db_file = await file_service.upload_file(
            db=db,
            module_id=module_id,
            category=file_category,
            original_filename=file.filename or "attachment",
            content=content,
            current_user=current_user,
        )
    except Exception as exc:
        from app.core.exceptions import NotFoundError
        from app.services.validation_service import UploadValidationError
        if isinstance(exc, NotFoundError):
            raise HTTPException(status_code=404, detail=str(exc))
        if isinstance(exc, UploadValidationError):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
        import logging
        logging.getLogger(__name__).error("workspace_attach: upload failed: %s", exc)
        raise HTTPException(status_code=500, detail="File upload failed. Please try again.")

    return WorkspaceAttachmentResponse(
        file_id=db_file.id,
        name=db_file.original_filename,
        mime_type=db_file.mime_type,
        size_bytes=db_file.size_bytes,
        upload_state=db_file.upload_state.value,
        module_id=db_file.module_id,
    )
