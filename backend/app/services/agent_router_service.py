"""Intelligent Agent Router — intent detection and agent dispatch.

Given a free-text user prompt, detect the intended domain and route to
the appropriate AQAA agent mode.  Returns a structured response including
the detected intent, confidence, answer, sources, and suggested next actions.

Routing table
-------------
assessment   → Assessment Compliance agent
moderation   → Moderation Compliance agent
attendance   → Attendance Compliance agent
evidence     → Evidence Verification agent
outcome      → Outcome Alignment agent
accreditation→ Accreditation Readiness agent
programme    → Programme Review agent
qualification→ Qualification Intelligence
knowledge    → Knowledge Search / IKP
reporting    → Reporting & Analytics
workflow     → Workflow & Approvals
qa_general   → General QA Assistant (default)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Intent detection
# ---------------------------------------------------------------------------

_INTENT_PATTERNS: list[tuple[str, list[str]]] = [
    ("assessment", [
        r"\bassessment\b", r"\bmark(s|ing)?\b", r"\brubric\b", r"\bgrade[sd]?\b",
        r"\bexam(ination)?\b", r"\btest paper\b", r"\bquestion paper\b",
    ]),
    ("moderation", [
        r"\bmoderat(e|ion|or)\b", r"\bsecond marker\b", r"\bdouble.?mark",
        r"\binternal moderator\b", r"\bexternal moderator\b",
    ]),
    ("attendance", [
        r"\battendance\b", r"\bregister\b", r"\bsign.?in\b", r"\bpresence\b",
        r"\babsent(ee)?\b",
    ]),
    ("evidence", [
        r"\bevidence\b", r"\bportfolio\b", r"\bartefact\b", r"\bartifact\b",
        r"\bdocument(ation)?\b", r"\bverif(y|ication)\b",
    ]),
    ("outcome", [
        r"\boutcome(s)?\b", r"\bgraduate attribute\b", r"\blearning outcome\b",
        r"\bprogramme spec\b", r"\bcurriculum\b", r"\balignment\b",
    ]),
    ("accreditation", [
        r"\baccreditat(e|ion)\b", r"\bsaqa\b", r"\bheqsf\b", r"\bcbe\b",
        r"\becsa\b", r"\bhpcsa\b", r"\bnqf level\b", r"\bpanel\b",
    ]),
    ("programme", [
        r"\bprogramme review\b", r"\bprogram(me)? quality\b", r"\bself.?evaluation\b",
        r"\bperiodic review\b",
    ]),
    ("qualification", [
        r"\bgpa\b", r"\bcgpa\b", r"\bgrade point\b", r"\bqualification\b",
        r"\bdegree classification\b", r"\bnqf advisory\b",
    ]),
    ("knowledge", [
        r"\bpolic(y|ies)\b", r"\bregulat(ion|ions)\b", r"\bstatute\b",
        r"\bknowledge base\b", r"\bsearch\b", r"\bfind document\b",
    ]),
    ("reporting", [
        r"\breport(s|ing)?\b", r"\banalytics\b", r"\bdashboard\b",
        r"\bstatistic(s)?\b", r"\bsummar(y|ise)\b", r"\btrend(s)?\b",
    ]),
    ("workflow", [
        r"\bapproval\b", r"\bworkflow\b", r"\bsubmission\b", r"\bdeadline\b",
        r"\bnotification\b", r"\bstatus\b",
    ]),
]


def detect_intent(prompt: str) -> tuple[str, float]:
    """Return (intent_label, confidence) for the given prompt.

    Confidence is a simple ratio of matched patterns; falls back to
    'qa_general' with confidence 0.5 if no pattern matches.
    """
    lower = prompt.lower()
    scores: dict[str, int] = {}
    for intent, patterns in _INTENT_PATTERNS:
        hits = sum(1 for p in patterns if re.search(p, lower))
        if hits:
            scores[intent] = hits

    if not scores:
        return ("qa_general", 0.5)

    best_intent = max(scores, key=lambda k: scores[k])
    total_hits = sum(scores.values())
    best_hits = scores[best_intent]
    confidence = min(0.95, 0.5 + (best_hits / max(total_hits, 1)) * 0.5)
    return (best_intent, round(confidence, 2))


# ---------------------------------------------------------------------------
# Suggested next actions per intent
# ---------------------------------------------------------------------------

_NEXT_ACTIONS: dict[str, list[str]] = {
    "assessment": [
        "View Assessment Compliance audit for a module",
        "Upload assessment plan or marks sheet",
        "Trigger new Assessment Compliance audit",
    ],
    "moderation": [
        "Run Moderation Compliance audit",
        "Review moderation checklist",
        "Upload moderation report",
    ],
    "attendance": [
        "Run Attendance Compliance audit",
        "Upload attendance register",
        "View attendance compliance history",
    ],
    "evidence": [
        "Run Evidence Verification audit",
        "Upload evidence files",
        "View evidence audit findings",
    ],
    "outcome": [
        "Run Outcome Alignment audit",
        "Review programme specifications",
        "Upload curriculum map",
    ],
    "accreditation": [
        "Run Accreditation Readiness audit",
        "View accreditation readiness report",
        "Upload accreditation evidence bundle",
    ],
    "programme": [
        "Trigger Programme Review audit",
        "View programme review history",
        "Upload programme self-evaluation report",
    ],
    "qualification": [
        "Open Qualification Intelligence calculator",
        "Calculate GPA/CGPA for a student",
        "View saved qualification records",
    ],
    "knowledge": [
        "Search the Knowledge Base",
        "Browse Institutional Knowledge Portal",
        "Upload a policy document",
    ],
    "reporting": [
        "Open Reports & Analytics dashboard",
        "Generate compliance summary report",
        "View audit trend charts",
    ],
    "workflow": [
        "View pending approvals",
        "Check submission deadlines",
        "Review workflow notifications",
    ],
    "qa_general": [
        "Browse the QA Dashboard",
        "Select an audit agent",
        "Contact your QA Officer",
    ],
}

_FOLLOW_UP_QUESTIONS: dict[str, list[str]] = {
    "assessment": [
        "Which module would you like to audit?",
        "Do you want to see the assessment compliance checklist?",
    ],
    "moderation": [
        "Which module's moderation records should I check?",
        "Would you like to see the moderation compliance requirements?",
    ],
    "attendance": [
        "Which module's attendance should I analyse?",
        "What is the minimum attendance threshold you expect?",
    ],
    "evidence": [
        "Which module's evidence folder should I verify?",
        "Are you looking for missing evidence or compliance gaps?",
    ],
    "outcome": [
        "Which programme's outcome alignment should I check?",
        "Would you like a full curriculum map analysis?",
    ],
    "accreditation": [
        "Which programme is under accreditation review?",
        "Which accrediting body are you preparing for (ECSA, HPCSA, CHE)?",
    ],
    "programme": [
        "Which programme should I review?",
        "Is this a scheduled periodic review or an ad-hoc evaluation?",
    ],
    "qualification": [
        "Which student's GPA would you like to calculate?",
        "Are you calculating for a full programme (CGPA) or a single semester?",
    ],
    "knowledge": [
        "What policy or regulation are you searching for?",
        "Should I search institution-wide or within a specific faculty?",
    ],
    "reporting": [
        "Which time period should the report cover?",
        "Do you want a summary across all agents or a specific audit type?",
    ],
    "workflow": [
        "Which submission or approval are you tracking?",
        "Would you like to see all open workflow items for your role?",
    ],
    "qa_general": [
        "What aspect of quality assurance can I help you with?",
        "Are you looking for compliance gaps, evidence, or a specific audit?",
    ],
}


# ---------------------------------------------------------------------------
# Route response
# ---------------------------------------------------------------------------


@dataclass
class AgentRouterResponse:
    """Structured response from the agent router."""

    intent: str
    confidence: float
    agent_mode: str
    answer: str
    sources: list[str] = field(default_factory=list)
    suggested_next_actions: list[str] = field(default_factory=list)
    follow_up_questions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "agent_mode": self.agent_mode,
            "answer": self.answer,
            "sources": self.sources,
            "suggested_next_actions": self.suggested_next_actions,
            "follow_up_questions": self.follow_up_questions,
        }


_INTENT_TO_MODE: dict[str, str] = {
    "assessment": "assessment",
    "moderation": "moderation",
    "attendance": "attendance",
    "evidence": "evidence",
    "outcome": "outcome_alignment",
    "accreditation": "accreditation_readiness",
    "programme": "programme_review",
    "qualification": "qualification",
    "knowledge": "knowledge_search",
    "reporting": "reporting",
    "workflow": "workflow",
    "qa_general": "general",
}


def route_prompt(prompt: str) -> AgentRouterResponse:
    """Detect intent and return a structured routing response.

    This is a synchronous function suitable for use inside FastAPI endpoints
    or background tasks.  The actual LLM call happens inside the existing
    ai_assistant route; this layer only resolves the destination mode.
    """
    intent, confidence = detect_intent(prompt)
    mode = _INTENT_TO_MODE.get(intent, "general")

    answer = _build_answer(intent, prompt, confidence)
    sources = _build_sources(intent)

    logger.info("AgentRouter: prompt=%r intent=%s confidence=%.2f mode=%s", prompt[:80], intent, confidence, mode)

    return AgentRouterResponse(
        intent=intent,
        confidence=confidence,
        agent_mode=mode,
        answer=answer,
        sources=sources,
        suggested_next_actions=_NEXT_ACTIONS.get(intent, _NEXT_ACTIONS["qa_general"]),
        follow_up_questions=_FOLLOW_UP_QUESTIONS.get(intent, _FOLLOW_UP_QUESTIONS["qa_general"]),
    )


def _build_answer(intent: str, prompt: str, confidence: float) -> str:
    intent_labels = {
        "assessment": "Assessment Compliance",
        "moderation": "Moderation Compliance",
        "attendance": "Attendance Compliance",
        "evidence": "Evidence Verification",
        "outcome": "Outcome Alignment",
        "accreditation": "Accreditation Readiness",
        "programme": "Programme Review",
        "qualification": "Qualification Intelligence",
        "knowledge": "Knowledge Search",
        "reporting": "Reporting & Analytics",
        "workflow": "Workflow Management",
        "qa_general": "General QA Assistant",
    }
    label = intent_labels.get(intent, "QA Assistant")
    if confidence >= 0.75:
        routing_note = f"I've routed your query to the **{label}** agent."
    else:
        routing_note = (
            f"I've routed your query to the **{label}** agent "
            f"(confidence: {int(confidence * 100)}% — you may want to select a different agent if this doesn't match your intent)."
        )
    return (
        f"{routing_note}\n\n"
        f"Your query: *\"{prompt[:200]}\"*\n\n"
        f"The {label} agent can help you analyse compliance gaps, review audit findings, "
        f"and generate actionable recommendations for your institution."
    )


def _build_sources(intent: str) -> list[str]:
    source_map = {
        "assessment": ["SAQA Assessment Policy", "CHE Good Practices Guide", "Institutional Assessment Policy"],
        "moderation": ["Internal Moderation Policy", "External Moderation Framework", "CHE Moderation Guidelines"],
        "attendance": ["Student Attendance Policy", "DHET Attendance Requirements"],
        "evidence": ["Evidence Framework", "Module Folder Requirements Checklist"],
        "outcome": ["HEQSF Qualification Standards", "Programme Specification Template"],
        "accreditation": ["HEQSF Level Descriptors", "Professional Body Requirements", "CHE Accreditation Standards"],
        "programme": ["Periodic Programme Review Policy", "CHE Self-Evaluation Framework"],
        "qualification": ["HEQSF NQF Level Descriptors", "SAQA Qualification Standards", "SA GPA Calculator Guidance"],
        "knowledge": ["Institutional Knowledge Portal", "Policy Document Repository"],
        "reporting": ["AQAA Analytics Module", "Compliance Reporting Framework"],
        "workflow": ["Institutional Workflow Policy", "Approval Process Manual"],
    }
    return source_map.get(intent, ["AQAA Knowledge Base"])
