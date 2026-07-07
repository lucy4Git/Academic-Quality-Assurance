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
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_assistant import assistant_service
from app.ai_assistant.llm_router_service import llm_route_prompt
from app.ai_assistant.prompt_templates import AGENT_MODE_LABELS, AGENT_MODES
from app.ai_assistant.recommendation_engine import get_recommendations
from app.ai_providers.manager import get_provider_manager
from app.rag.advanced_rag_service import advanced_ask
from app.ai_providers.provider_factory import get_provider
from app.database import get_db
from app.dependencies import LecturerRequired
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
)

router = APIRouter(prefix="/ai-assistant", tags=["AI QA Assistant"])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _resolve_institution_code(
    db: AsyncSession,
    current_user: User,
    requested_code: str | None,
) -> str:
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
) -> None:
    """Persist user question and assistant response to the chat session."""
    now = datetime.now(tz=timezone.utc)

    user_msg = AiChatMessage(
        id=uuid.uuid4(),
        session_id=session_id,
        role="user",
        content=question,
        created_at=now,
        updated_at=now,
    )
    db.add(user_msg)

    assistant_msg = AiChatMessage(
        id=uuid.uuid4(),
        session_id=session_id,
        role="assistant",
        content=result["answer"],
        sources=result.get("sources"),
        confidence_score=result.get("confidence_score"),
        provider=result.get("provider"),
        model_name=result.get("model"),
        query_mode=result.get("query_mode"),
        intent=result.get("query_mode"),
        created_at=now,
        updated_at=now,
    )
    db.add(assistant_msg)

    # Update session provider/model
    session = await db.get(AiChatSession, session_id)
    if session:
        session.provider = result.get("provider")
        session.model_name = result.get("model")

    await db.commit()


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
    current_user: User = LecturerRequired,
) -> dict[str, Any]:
    institution_code = await _resolve_institution_code(db, current_user, body.institution_code)

    try:
        result = await advanced_ask(
            question=body.question,
            institution_code=institution_code,
            context_limit=body.context_limit,
            mode=body.mode if body.mode in AGENT_MODES else "qa_assistant",
            provider=get_provider(),
        )
    except Exception as exc:  # noqa: BLE001 — convert to a safe 503, no stack trace leak
        import logging
        logging.getLogger(__name__).exception("AI ask failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable. Please try again.",
        )

    if body.session_id:
        try:
            await _persist_message_pair(db, body.session_id, body.question, result)
            result["session_id"] = body.session_id
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
    institution_code: str,
    context_limit: int,
    mode: str,
) -> Any:
    """Async generator that yields SSE lines for one ask-stream request.

    Stream shape:
        start   — routing decision (intent, agents, confidence, routing_reason)
        chunk   — incremental answer text (simulated from full LLM response)
        sources — Qdrant sources and follow-up data
        done    — provider/model metadata
        error   — emitted instead of chunk/sources/done on failure
    """
    # 1. LLM-assisted routing (with keyword fallback built-in)
    try:
        router = await llm_route_prompt(question)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("ask-stream: llm_route_prompt failed: %s", exc)
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

    # 3. Get full LLM response via Advanced RAG pipeline
    try:
        manager = get_provider_manager()
        provider = await manager.get_healthy_provider()

        result = await advanced_ask(
            question=question,
            institution_code=institution_code,
            context_limit=context_limit,
            mode=effective_mode,
            provider=provider,
        )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("ask-stream: advanced_ask failed: %s", exc)
        yield _sse("error", {"message": "An error occurred while generating a response."})
        return

    # 4. Simulate streaming: split answer into word-level token events
    answer: str = result.get("answer", "")
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
    current_user: User = LecturerRequired,
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
    institution_code = await _resolve_institution_code(db, current_user, body.institution_code)
    effective_mode = body.mode if body.mode in AGENT_MODES else "qa_assistant"

    return StreamingResponse(
        _stream_ask(body.question, institution_code, body.context_limit, effective_mode),
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
    current_user: User = LecturerRequired,
) -> ChatSessionBrief:
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
        created_at=session.created_at,
        message_count=0,
    )


@router.get(
    "/sessions",
    response_model=list[ChatSessionBrief],
    summary="List the current user's chat sessions",
)
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> list[ChatSessionBrief]:
    result = await db.execute(
        select(AiChatSession)
        .where(
            AiChatSession.user_id == current_user.id,
            AiChatSession.is_active.is_(True),
        )
        .order_by(AiChatSession.created_at.desc())
        .limit(50)
    )
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
    current_user: User = LecturerRequired,
) -> ChatSessionDetail:
    session = await db.get(AiChatSession, session_id)
    if session is None or not session.is_active:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.user_id != current_user.id and current_user.role != UserRole.SYSTEM_ADMIN:
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
    current_user: User = LecturerRequired,
) -> dict[str, Any]:
    session = await db.get(AiChatSession, session_id)
    if session is None or not session.is_active:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    institution_code = await _resolve_institution_code(db, current_user, body.institution_code)

    result = await assistant_service.ask(
        question=body.question,
        institution_code=institution_code,
        context_limit=body.context_limit,
        mode=session.mode,
        provider=get_provider(),
    )

    await _persist_message_pair(db, session_id, body.question, result)
    result["session_id"] = session_id
    return result


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Soft-delete a chat session",
)
async def delete_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> None:
    session = await db.get(AiChatSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.user_id != current_user.id and current_user.role != UserRole.SYSTEM_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied.")
    session.is_active = False
    await db.commit()


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
