"""LLM-assisted intent router for the AQAA AI Workspace.

Calls the ProviderManager's healthy provider to classify a user prompt into
a structured routing decision (intent, agents, confidence, routing_reason).
Falls back to keyword-based detect_intent() when no LLM is available or the
response is not valid JSON.

Chain-of-thought is never exposed to the caller — only the user-facing
routing_reason is returned.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.ai_providers.base_provider import AIMessage
from app.ai_providers.manager import get_provider_manager
from app.services.agent_router_service import (
    _FOLLOW_UP_QUESTIONS,  # noqa: PLC2701
    _INTENT_TO_MODE,       # noqa: PLC2701
    _NEXT_ACTIONS,         # noqa: PLC2701
    detect_intent,
)

logger = logging.getLogger(__name__)

_KNOWN_INTENTS: frozenset[str] = frozenset(_INTENT_TO_MODE.keys())

AGENT_LABELS: dict[str, str] = {
    "assessment":    "Assessment Compliance Agent",
    "moderation":    "Moderation Compliance Agent",
    "attendance":    "Attendance Compliance Agent",
    "evidence":      "Evidence Verification Agent",
    "outcome":       "Outcome Alignment Agent",
    "accreditation": "Accreditation Readiness Agent",
    "programme":     "Programme Review Agent",
    "qualification": "Qualification Intelligence Agent",
    "knowledge":     "Knowledge Search Agent",
    "reporting":     "Reporting & Analytics Agent",
    "workflow":      "Workflow Agent",
    "qa_general":    "QA General Assistant",
    # Phase C — Regulatory intents
    "identify_applicable_frameworks":           "Regulatory Framework Identification Agent",
    "explain_applicability":                    "Framework Applicability Agent",
    "assess_framework_compliance":              "Framework Compliance Assessment Agent",
    "assess_integrated_readiness":              "Integrated Regulatory Readiness Agent",
    "explain_regulatory_requirement":           "Regulatory Requirement Agent",
    "find_missing_regulatory_evidence":         "Missing Evidence Detection Agent",
    "compare_frameworks":                       "Framework Comparison Agent",
    "explain_framework_overlap":                "Framework Overlap Agent",
    "explain_framework_conflict":               "Framework Conflict Agent",
    "generate_regulatory_report":               "Regulatory Report Agent",
    "generate_evidence_pack":                   "Evidence Pack Agent",
    "create_corrective_action_plan":            "Corrective Action Agent",
    "explain_regulatory_finding":               "Regulatory Finding Agent",
    "check_framework_version":                  "Framework Version Agent",
    "check_qualification_alignment":            "Qualification Alignment Agent",
    "check_programme_accreditation":            "Programme Accreditation Agent",
    "check_professional_accreditation":         "Professional Accreditation Agent",
    "check_institutional_audit_readiness":      "Institutional Audit Readiness Agent",
    "check_occupational_qualification_compliance": "Occupational Qualification Agent",
}

_ROUTER_SYSTEM_PROMPT = """\
You are the AQAA (Academic Quality Assurance Agent) routing assistant.

Given a user query, identify the most appropriate QA domain and respond with
ONLY a valid JSON object — no markdown, no explanation, no chain-of-thought.

Available intents:
- assessment: Assessment plans, marks, rubrics, exam papers, grade books
- moderation: Internal/external moderation, second marking, double marking
- attendance: Attendance registers, sign-in sheets, absence tracking
- evidence: Evidence portfolios, document verification, artefacts
- outcome: Learning outcomes, graduate attributes, curriculum alignment
- accreditation: SAQA/CHE/HEQSF standards, NQF levels, accreditation readiness
- programme: Programme review, periodic review, self-evaluation reports
- qualification: GPA, CGPA, degree classification, NQF advisory
- knowledge: Policy search, regulations, statutes, knowledge base queries
- reporting: Reports, analytics, dashboards, compliance statistics
- workflow: Approvals, submissions, deadlines, notifications
- qa_general: General quality assurance questions (default)
- identify_applicable_frameworks: Which frameworks apply to a programme or institution
- explain_applicability: Why a framework or standard applies to a specific entity
- assess_framework_compliance: Assess compliance against a named quality framework
- assess_integrated_readiness: Holistic readiness across multiple frameworks
- explain_regulatory_requirement: Explain what a specific criterion or standard requires
- find_missing_regulatory_evidence: Identify evidence gaps for framework criteria
- compare_frameworks: Compare or contrast two or more frameworks
- explain_framework_overlap: Shared criteria between two frameworks
- explain_framework_conflict: Conflicting or incompatible requirements across frameworks
- generate_regulatory_report: Generate a compliance or readiness report
- generate_evidence_pack: Assemble an evidence submission pack for an accrediting body
- create_corrective_action_plan: Create a remediation plan for findings or gaps
- explain_regulatory_finding: Explain what a regulatory finding means and how to respond
- check_framework_version: Check which version of a framework is current or was used
- check_qualification_alignment: Check NQF/HEQSF alignment for a qualification or programme
- check_programme_accreditation: Check CHE/DHET programme accreditation status or readiness
- check_professional_accreditation: Check ECSA/HPCSA/SACE professional body accreditation
- check_institutional_audit_readiness: CHE site visit or DHET inspection readiness
- check_occupational_qualification_compliance: QCTO/SETA occupational qualification compliance

Multiple intents may apply — list primary first in 'agents'.

Respond with this exact JSON shape:
{"intent":"<primary_intent>","agents":["<Agent Label>",...],"confidence":<0.0-1.0>,"routing_reason":"<one sentence user-facing explanation>"}
"""


async def llm_route_prompt(prompt: str) -> dict[str, Any]:
    """Route a user prompt using LLM-assisted intent detection.

    Returns a dict with keys:
        intent, agents, confidence, routing_reason,
        agent_mode, suggested_next_actions, follow_up_questions, used_llm.

    Falls back to keyword-based routing when:
    - The healthy provider is LOCAL_DEV (template-only, no reasoning)
    - The provider call raises an exception
    - The provider returns non-JSON or an unknown intent
    """
    manager = get_provider_manager()
    provider = await manager.get_healthy_provider()
    used_llm = not provider.is_local_dev

    if used_llm:
        try:
            raw = await provider.complete(
                messages=[
                    AIMessage(role="system", content=_ROUTER_SYSTEM_PROMPT),
                    AIMessage(role="user", content=prompt[:500]),
                ],
                temperature=0.1,
                max_tokens=256,
            )
            parsed = _parse_router_json(raw)
            if parsed:
                intent = parsed["intent"]
                agents = parsed.get("agents") or [AGENT_LABELS.get(intent, "QA General Assistant")]
                confidence = float(parsed.get("confidence", 0.7))
                routing_reason = parsed.get("routing_reason", f"Routed to {intent} agent.")
                logger.info(
                    "LLMRouter: intent=%s confidence=%.2f provider=%s",
                    intent, confidence, provider.provider_name,
                )
                return _build_result(intent, agents, confidence, routing_reason, used_llm=True)
        except Exception as exc:
            logger.warning(
                "LLMRouter: provider '%s' failed (%s) — falling back to keyword router",
                provider.provider_name, type(exc).__name__,
            )

    # Keyword fallback
    intent, confidence = detect_intent(prompt)
    agents = [AGENT_LABELS.get(intent, "QA General Assistant")]
    routing_reason = (
        f"Routed to {AGENT_LABELS.get(intent, 'QA Assistant')} "
        "based on keyword analysis."
    )
    return _build_result(intent, agents, confidence, routing_reason, used_llm=False)


def _parse_router_json(raw: str) -> dict[str, Any] | None:
    """Extract and validate a routing JSON object from the LLM response."""
    text = raw.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        end = -1 if lines[-1].strip() in ("```", "```json") else len(lines)
        text = "\n".join(lines[1:end])

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to extract the first {...} block from the response
        match = re.search(r"\{.*?\}", text, re.DOTALL)
        if not match:
            logger.warning("LLMRouter: no JSON found in provider response")
            return None
        try:
            data = json.loads(match.group())
        except json.JSONDecodeError:
            logger.warning("LLMRouter: could not parse extracted JSON block")
            return None

    intent = data.get("intent", "")
    if intent not in _KNOWN_INTENTS:
        logger.warning("LLMRouter: unknown intent '%s' returned by provider", intent)
        return None

    return data


def _build_result(
    intent: str,
    agents: list[str],
    confidence: float,
    routing_reason: str,
    used_llm: bool,
) -> dict[str, Any]:
    mode = _INTENT_TO_MODE.get(intent, "general")
    return {
        "intent": intent,
        "agents": agents,
        "confidence": round(min(max(confidence, 0.0), 1.0), 2),
        "routing_reason": routing_reason,
        "agent_mode": mode,
        "suggested_next_actions": _NEXT_ACTIONS.get(intent, _NEXT_ACTIONS["qa_general"]),
        "follow_up_questions": _FOLLOW_UP_QUESTIONS.get(intent, _FOLLOW_UP_QUESTIONS["qa_general"]),
        "used_llm": used_llm,
    }
