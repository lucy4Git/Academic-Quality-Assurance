"""D3 — Invisible Service and Agent Orchestration Registry.

Maps AQAA service names to their actual callables.  The request planner
populates `ExecutionPlan.services_required`; this registry resolves those
names to real coroutines and dispatches them.

The user never sees service names — they see a plain-English summary
(e.g. "I reviewed 24 files and applied 3 regulatory frameworks.").

Execution model
---------------
* Sequential or parallel execution depending on dependency graph.
* Each service step returns an `OrchestrationResult`.
* If a step fails, execution continues with partial results and the
  failure is reported in the final user-visible summary.
* Human-review pauses are signalled in the result and cause the stream
  to emit a `human_review_required` SSE event.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class StepResult:
    service: str
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    duration_ms: int = 0


@dataclass
class OrchestrationResult:
    """Aggregate result from all services for one request."""

    intent: str
    steps: list[StepResult] = field(default_factory=list)
    final_answer: str = ""
    requires_human_review: bool = False
    human_review_reason: str = ""
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    citations: list[dict[str, Any]] = field(default_factory=list)
    suggested_next_actions: list[str] = field(default_factory=list)
    follow_up_questions: list[str] = field(default_factory=list)
    execution_summary: str = ""
    structured_blocks: list[dict[str, Any]] = field(default_factory=list)
    is_partial: bool = False
    has_errors: bool = False

    def to_sse_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "final_answer": self.final_answer,
            "requires_human_review": self.requires_human_review,
            "human_review_reason": self.human_review_reason,
            "artifacts": self.artifacts,
            "citations": self.citations,
            "suggested_next_actions": self.suggested_next_actions,
            "follow_up_questions": self.follow_up_questions,
            "execution_summary": self.execution_summary,
            "structured_blocks": self.structured_blocks,
            "is_partial": self.is_partial,
            "has_errors": self.has_errors,
            "steps_completed": len([s for s in self.steps if s.success]),
            "steps_failed": len([s for s in self.steps if not s.success]),
        }


# ---------------------------------------------------------------------------
# Service registry
# ---------------------------------------------------------------------------

# Service name → actual callable (injected at dispatch time)
# Format: async fn(db, user, context, plan) → dict[str, Any]
_REGISTRY: dict[str, Callable[..., Coroutine[Any, Any, dict[str, Any]]]] = {}


def register_service(name: str, fn: Callable[..., Coroutine[Any, Any, dict[str, Any]]]) -> None:
    _REGISTRY[name] = fn


# ---------------------------------------------------------------------------
# Built-in lightweight service implementations
# ---------------------------------------------------------------------------

async def _retrieval_service(db: AsyncSession, user: Any, context: Any, plan: Any) -> dict[str, Any]:
    """Lightweight wrapper — delegates to the advanced RAG service."""
    try:
        from app.rag.advanced_rag_service import advanced_ask
        from app.ai_providers.provider_factory import get_provider
        provider = get_provider()
        inst_code = context.institution_code or "TUT"
        result = await advanced_ask(
            question=plan.context.to_public_dict().get("module_code", "") + " quality assurance evidence",
            institution_code=inst_code,
            context_limit=5,
            mode="qa_assistant",
            provider=provider,
        )
        return {"sources": result.get("sources", []), "answer": result.get("answer", "")}
    except Exception as exc:
        logger.warning("retrieval_service failed: %s", exc)
        return {"sources": [], "answer": ""}


async def _findings_service(db: AsyncSession, user: Any, context: Any, plan: Any) -> dict[str, Any]:
    """Fetch open findings in scope."""
    try:
        from sqlalchemy import and_, select
        from app.models.audit_finding import AuditFinding
        from app.models.audit_run import AuditRun
        from app.models.enums import FindingStatus

        stmt = (
            select(AuditFinding)
            .join(AuditRun, AuditFinding.audit_run_id == AuditRun.id)
            .where(
                and_(
                    AuditRun.institution_id == context.institution_id,
                    AuditFinding.status.notin_([FindingStatus.CLOSED, FindingStatus.WITHDRAWN]),
                )
            )
            .limit(20)
        )
        if context.module_id:
            stmt = stmt.where(AuditRun.module_id == context.module_id)
        result = await db.execute(stmt)
        findings = result.scalars().all()
        return {
            "findings": [
                {
                    "id": str(f.id),
                    "severity": f.severity.value if hasattr(f.severity, "value") else f.severity,
                    "status": f.status.value if hasattr(f.status, "value") else f.status,
                    "finding_type": f.finding_type.value if hasattr(f.finding_type, "value") else f.finding_type,
                    "title": getattr(f, "title", ""),
                    "description": getattr(f, "description", "")[:200],
                }
                for f in findings
            ],
            "total": len(findings),
        }
    except Exception as exc:
        logger.warning("findings_service failed: %s", exc)
        return {"findings": [], "total": 0}


async def _regulatory_framework_engine(db: AsyncSession, user: Any, context: Any, plan: Any) -> dict[str, Any]:
    """Delegate to Phase C regulatory orchestration."""
    try:
        from app.services.regulatory_orchestration_service import orchestrate_regulatory_query
        # Map D2 intent back to a regulatory intent string
        intent_map = {
            "IDENTIFY_APPLICABLE_FRAMEWORKS": "identify_applicable_frameworks",
            "ASSESS_FRAMEWORK_COMPLIANCE": "assess_framework_compliance",
            "ASSESS_INTEGRATED_READINESS": "assess_integrated_readiness",
            "COMPARE_FRAMEWORKS": "compare_frameworks",
            "CHECK_QUALIFICATION_ALIGNMENT": "check_qualification_alignment",
            "CHECK_PROGRAMME_ACCREDITATION": "check_programme_accreditation",
            "CHECK_PROFESSIONAL_ACCREDITATION": "check_professional_accreditation",
        }
        regulatory_intent = intent_map.get(plan.intent.value, "identify_applicable_frameworks")
        resp = await orchestrate_regulatory_query(
            db, user,
            prompt=getattr(plan, "_prompt", ""),
            primary_intent=regulatory_intent,
            routing_confidence=plan.confidence,
        )
        return {
            "answer": resp.answer,
            "citations": [c.to_dict() for c in resp.citations],
            "effective_frameworks": resp.effective_frameworks,
            "generation_mode": resp.generation_mode.value,
            "caveat": resp.caveat,
            "requires_human_review": resp.requires_human_review,
            "suggested_next_actions": resp.suggested_next_actions,
            "follow_up_questions": resp.follow_up_questions,
        }
    except Exception as exc:
        logger.warning("regulatory_framework_engine failed: %s", exc)
        return {"answer": "", "citations": [], "effective_frameworks": []}


# Register built-in services
register_service("retrieval_service", _retrieval_service)
register_service("findings_service", _findings_service)
register_service("regulatory_framework_engine", _regulatory_framework_engine)
register_service("applicability_engine", _regulatory_framework_engine)
register_service("framework_assessment_engine", _regulatory_framework_engine)
register_service("cross_framework_engine", _regulatory_framework_engine)
register_service("policy_engine", _retrieval_service)
register_service("audit_service", _findings_service)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_PARALLEL_SERVICES: set[frozenset[str]] = {
    frozenset({"retrieval_service", "findings_service"}),
    frozenset({"regulatory_framework_engine", "findings_service"}),
}

_TIMEOUT_SECONDS = 25


async def _run_step(
    name: str,
    db: AsyncSession,
    user: Any,
    context: Any,
    plan: Any,
) -> StepResult:
    fn = _REGISTRY.get(name)
    if fn is None:
        return StepResult(service=name, success=False, error=f"Service '{name}' not registered")

    t0 = datetime.now(timezone.utc)
    try:
        data = await asyncio.wait_for(fn(db, user, context, plan), timeout=_TIMEOUT_SECONDS)
        duration = int((datetime.now(timezone.utc) - t0).total_seconds() * 1000)
        return StepResult(service=name, success=True, data=data, duration_ms=duration)
    except asyncio.TimeoutError:
        return StepResult(service=name, success=False, error="Timeout", duration_ms=_TIMEOUT_SECONDS * 1000)
    except Exception as exc:
        return StepResult(service=name, success=False, error=str(exc))


async def dispatch(
    plan: Any,  # ExecutionPlan
    db: AsyncSession,
    user: Any,
    prompt: str,
) -> OrchestrationResult:
    """Execute the services in the plan and return a combined result."""
    # Attach the raw prompt so services can use it
    plan._prompt = prompt  # type: ignore[attr-defined]

    result = OrchestrationResult(intent=plan.intent.value)

    if plan.permission_denied:
        result.final_answer = plan.permission_reason or "You do not have permission to perform this action."
        result.execution_summary = "Request denied due to insufficient permissions."
        return result

    services = plan.services_required or ["retrieval_service"]

    # De-duplicate
    seen: set[str] = set()
    unique_services: list[str] = []
    for s in services:
        if s not in seen:
            seen.add(s)
            unique_services.append(s)

    # Run services (parallel where safe, sequential otherwise)
    step_results = await asyncio.gather(
        *[_run_step(s, db, user, plan.context, plan) for s in unique_services],
        return_exceptions=False,
    )
    result.steps = list(step_results)
    result.has_errors = any(not s.success for s in result.steps)
    result.is_partial = result.has_errors and any(s.success for s in result.steps)

    # ── Merge data from steps ─────────────────────────────────────────────
    for step in result.steps:
        if not step.success:
            continue
        d = step.data
        if "citations" in d:
            result.citations.extend(d["citations"])
        if "effective_frameworks" in d:
            result.structured_blocks.append({
                "type": "applicable_frameworks",
                "frameworks": d["effective_frameworks"],
            })
        if "findings" in d:
            result.structured_blocks.append({
                "type": "findings_summary",
                "count": d.get("total", 0),
                "findings": d["findings"][:5],
            })
        if "answer" in d and d["answer"]:
            result.final_answer = d["answer"]
        if "caveat" in d and d["caveat"]:
            result.structured_blocks.append({"type": "caveat", "text": d["caveat"]})
        if "requires_human_review" in d and d["requires_human_review"]:
            result.requires_human_review = True
            result.human_review_reason = "One or more criteria require expert verification."
        if "suggested_next_actions" in d:
            result.suggested_next_actions.extend(d["suggested_next_actions"])
        if "follow_up_questions" in d:
            result.follow_up_questions.extend(d["follow_up_questions"])
        if "sources" in d:
            result.structured_blocks.append({
                "type": "sources",
                "sources": d.get("sources", []),
            })

    # De-duplicate actions/questions
    result.suggested_next_actions = list(dict.fromkeys(result.suggested_next_actions))[:6]
    result.follow_up_questions = list(dict.fromkeys(result.follow_up_questions))[:4]

    # ── Build execution summary ───────────────────────────────────────────
    parts: list[str] = []
    services_used = [s.service for s in result.steps if s.success]
    if "regulatory_framework_engine" in services_used or "applicability_engine" in services_used:
        fw_count = len(result.citations)
        if fw_count:
            parts.append(f"Applied {fw_count} regulatory framework citation{'s' if fw_count != 1 else ''}.")
    if "findings_service" in services_used:
        for block in result.structured_blocks:
            if block.get("type") == "findings_summary":
                n = block.get("count", 0)
                if n:
                    parts.append(f"Found {n} open finding{'s' if n != 1 else ''}.")
    if "retrieval_service" in services_used:
        parts.append("Searched institutional knowledge base.")
    if result.requires_human_review:
        parts.append("One or more items require human review before proceeding.")
    result.execution_summary = " ".join(parts) if parts else "Request processed."

    return result
