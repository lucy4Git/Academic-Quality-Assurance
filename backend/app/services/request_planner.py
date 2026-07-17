"""D2 — Universal Intent and Request Planner.

Accepts a natural-language prompt + resolved context, determines intent and
produces a structured execution plan that tells the orchestration layer what
to do.

Intent families
---------------
The 35 D2-spec intents are grouped into 6 families:

  KNOWLEDGE        — search, explain, policy
  AUDIT            — module/assessment/moderation/attendance/outcome/evidence/accreditation
  FINDINGS         — list, explain, assign, submit, review, approve, reject, escalate
  REGULATORY       — frameworks, versions, criteria, compliance, readiness, accreditation
  REPORTING        — generate reports, evidence packs, executive briefings
  ACTIONS          — file operations, uploads, library
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum

from app.models.enums import UserRole
from app.services.context_engine import ResolvedContext

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Intent registry
# ---------------------------------------------------------------------------


class Intent(str, Enum):
    # Knowledge
    GENERAL_QA_QUESTION = "GENERAL_QA_QUESTION"
    SEARCH_INSTITUTIONAL_KNOWLEDGE = "SEARCH_INSTITUTIONAL_KNOWLEDGE"
    EXPLAIN_POLICY = "EXPLAIN_POLICY"
    GENERAL_ACADEMIC_QUALITY_ASSISTANCE = "GENERAL_ACADEMIC_QUALITY_ASSISTANCE"

    # Audit
    AUDIT_MODULE_FOLDER = "AUDIT_MODULE_FOLDER"
    ASSESS_ASSESSMENT_COMPLIANCE = "ASSESS_ASSESSMENT_COMPLIANCE"
    ASSESS_MODERATION_COMPLIANCE = "ASSESS_MODERATION_COMPLIANCE"
    ASSESS_ATTENDANCE_COMPLIANCE = "ASSESS_ATTENDANCE_COMPLIANCE"
    ASSESS_OUTCOME_ALIGNMENT = "ASSESS_OUTCOME_ALIGNMENT"
    VERIFY_EVIDENCE = "VERIFY_EVIDENCE"
    IDENTIFY_MISSING_EVIDENCE = "IDENTIFY_MISSING_EVIDENCE"
    EXPLAIN_COMPLIANCE_SCORE = "EXPLAIN_COMPLIANCE_SCORE"

    # Findings
    LIST_FINDINGS = "LIST_FINDINGS"
    EXPLAIN_FINDING = "EXPLAIN_FINDING"
    ASSIGN_FINDING = "ASSIGN_FINDING"
    SUBMIT_RESOLUTION = "SUBMIT_RESOLUTION"
    REVIEW_RESOLUTION = "REVIEW_RESOLUTION"
    APPROVE_RESOLUTION = "APPROVE_RESOLUTION"
    REJECT_RESOLUTION = "REJECT_RESOLUTION"
    ESCALATE_FINDING = "ESCALATE_FINDING"
    GENERATE_CORRECTIVE_ACTION_PLAN = "GENERATE_CORRECTIVE_ACTION_PLAN"

    # Regulatory
    IDENTIFY_APPLICABLE_FRAMEWORKS = "IDENTIFY_APPLICABLE_FRAMEWORKS"
    ASSESS_FRAMEWORK_COMPLIANCE = "ASSESS_FRAMEWORK_COMPLIANCE"
    ASSESS_INTEGRATED_READINESS = "ASSESS_INTEGRATED_READINESS"
    COMPARE_FRAMEWORKS = "COMPARE_FRAMEWORKS"
    CHECK_QUALIFICATION_ALIGNMENT = "CHECK_QUALIFICATION_ALIGNMENT"
    CHECK_PROGRAMME_ACCREDITATION = "CHECK_PROGRAMME_ACCREDITATION"
    CHECK_PROFESSIONAL_ACCREDITATION = "CHECK_PROFESSIONAL_ACCREDITATION"

    # Reporting
    GENERATE_REPORT = "GENERATE_REPORT"
    GENERATE_EVIDENCE_PACK = "GENERATE_EVIDENCE_PACK"
    PREPARE_EXECUTIVE_BRIEFING = "PREPARE_EXECUTIVE_BRIEFING"
    PREPARE_QA_MEETING_PACK = "PREPARE_QA_MEETING_PACK"

    # File / Library
    SEARCH_FILES = "SEARCH_FILES"
    OPEN_EVIDENCE = "OPEN_EVIDENCE"
    UPLOAD_AND_ANALYSE = "UPLOAD_AND_ANALYSE"


# ---------------------------------------------------------------------------
# Intent detection patterns
# ---------------------------------------------------------------------------

_INTENT_PATTERNS: list[tuple[Intent, list[str]]] = [
    # ── Findings ──────────────────────────────────────────────────────────
    (Intent.LIST_FINDINGS, [
        r"\b(show|list|view|get|my)\s+(critical\s+|overdue\s+|open\s+|all\s+)?finding(s)?\b",
        r"\bfindings?\s+(for|in|of|on)\b",
        r"\bwhich findings?\b",
        r"\boverdue\s+finding",
    ]),
    (Intent.EXPLAIN_FINDING, [
        r"\bexplain\s+(this\s+)?finding\b",
        r"\bwhat\s+(does|is)\s+(this\s+)?finding\b",
        r"\bfinding\s+detail\b",
        r"\btell me about (the|this) finding\b",
    ]),
    (Intent.ASSIGN_FINDING, [
        r"\bassign\s+(this\s+|the\s+)?finding\b",
        r"\bassign\s+(it|them)\s+to\b",
        r"\bfinding.*assign\b",
    ]),
    (Intent.SUBMIT_RESOLUTION, [
        r"\bsubmit\s+(for\s+)?(review|resolution)\b",
        r"\bsubmit\s+(this\s+|the\s+)?finding\s+(for\s+)?(review|resolution)\b",
        r"\bsubmit\s+(this\s+)?finding\b",
        r"\bmark\s+(as\s+)?resolved\b",
        r"\bstart\s+progress\b",
        r"\bfinding.*for\s+review\b",
    ]),
    (Intent.REVIEW_RESOLUTION, [
        r"\breview\s+(this\s+|the\s+)?resolution\b",
        r"\breview\s+(this\s+|the\s+)?finding\b",
        r"\bcheck\s+(the\s+)?resolution\b",
    ]),
    (Intent.APPROVE_RESOLUTION, [
        r"\bapprove\s+(this\s+|the\s+)?resolution\b",
        r"\bapprove\s+(this\s+|the\s+)?finding\b",
        r"\bmark\s+(as\s+)?closed\b",
        r"\bclose\s+(this\s+|the\s+)?finding\b",
    ]),
    (Intent.REJECT_RESOLUTION, [
        r"\breject\s+(this\s+|the\s+)?resolution\b",
        r"\breject\s+(this\s+|the\s+)?finding\b",
        r"\bsend\s+back\b",
    ]),
    (Intent.ESCALATE_FINDING, [
        r"\bescalate\s+(this\s+|the\s+)?finding\b",
        r"\bescalate\s+(all\s+)?(critical\s+)?finding",
        r"\bmark\s+(as\s+)?escalated\b",
    ]),
    (Intent.GENERATE_CORRECTIVE_ACTION_PLAN, [
        r"\bcorrective\s+action\s+plan\b",
        r"\bremediation\s+plan\b",
        r"\baction\s+plan\b",
        r"\bfix\s+(the\s+)?(finding|gap|non.?compliance)\b",
    ]),

    # ── Audit ─────────────────────────────────────────────────────────────
    (Intent.AUDIT_MODULE_FOLDER, [
        r"\baudit\s+(the\s+|this\s+)?module\b",
        r"\baudit\s+(the\s+|this\s+)?folder\b",
        r"\brun\s+(a\s+)?folder\s+audit\b",
        r"\bcheck\s+(the\s+)?module\s+folder\b",
    ]),
    (Intent.ASSESS_ASSESSMENT_COMPLIANCE, [
        r"\bassessment\s+compliance\b",
        r"\bassessment\s+audit\b",
        r"\bmark(ing)?\s+(plan|sheet|rubric)\s+(compliance|check)\b",
        r"\bcheck\s+(the\s+)?assessment\s+plan\b",
    ]),
    (Intent.ASSESS_MODERATION_COMPLIANCE, [
        r"\bmoderat(ion|e)\s+(compliance|audit|check)\b",
        r"\bcheck\s+(the\s+)?moderat(ion|or)\b",
        r"\binternal\s+moderat(ion|or)\b",
    ]),
    (Intent.ASSESS_ATTENDANCE_COMPLIANCE, [
        r"\battendance\s+(compliance|audit|check)\b",
        r"\bcheck\s+(the\s+)?attendance\b",
        r"\bregister\s+compliance\b",
    ]),
    (Intent.ASSESS_OUTCOME_ALIGNMENT, [
        r"\boutcome\s+alignment\b",
        r"\boutcome\s+audit\b",
        r"\bcheck\s+(the\s+)?learning\s+outcomes?\b",
        r"\bcurriculum\s+alignment\b",
    ]),
    (Intent.VERIFY_EVIDENCE, [
        r"\bverif(y|ication)\s+(of\s+)?evidence\b",
        r"\bevidence\s+verif(y|ication)\b",
        r"\bcheck\s+(if\s+|the\s+)?evidence\s+(is\s+)?(valid|complete)\b",
    ]),
    (Intent.IDENTIFY_MISSING_EVIDENCE, [
        r"\bmissing\s+evidence\b",
        r"\bwhich\s+(documents?|evidence)\s+(is|are)\s+missing\b",
        r"\bevidence\s+gaps?\b",
        r"\bwhat\s+(evidence|documents?)\s+(is|are)\s+(not\s+)?(uploaded|submitted|available)\b",
    ]),
    (Intent.EXPLAIN_COMPLIANCE_SCORE, [
        r"\bexplain\s+(the\s+)?compliance\s+score\b",
        r"\bwhy\s+(is\s+the\s+)?compliance\s+(score|percentage|rate)\b",
        r"\bhow\s+(was|is)\s+(the\s+)?score\s+calculated\b",
    ]),

    # ── Regulatory ────────────────────────────────────────────────────────
    (Intent.IDENTIFY_APPLICABLE_FRAMEWORKS, [
        r"\bwhich\s+framework(s)?\s+(apply|applies)\b",
        r"\bapplicable\s+framework(s)?\b",
        r"\bwhat\s+framework(s)?\s+(apply|applies|are applicable)\b",
        r"\bidentify\s+framework(s)?\b",
    ]),
    (Intent.ASSESS_FRAMEWORK_COMPLIANCE, [
        r"\bframework\s+compliance\b",
        r"\bassess\s+(against\s+)?(the\s+)?(framework|che|ecsa|dhet|saqa)\b",
        r"\bcomply\s+with\s+(the\s+)?framework\b",
        r"\bmandatory\s+criteria\b",
        r"\bcriteria\s+(unmet|not met|missing|unfulfilled)\b",
        r"\bunmet\s+criteria\b",
        r"\bwhich\s+(mandatory\s+)?criteria\b",
    ]),
    (Intent.ASSESS_INTEGRATED_READINESS, [
        r"\bintegrated\s+readiness\b",
        r"\boverall\s+readiness\b",
        r"\bregulatory\s+readiness\b",
        r"\baccreditation\s+readiness\b",
        r"\bprogramme\s+readiness\b",
        r"\breadiness\s+(score|status|check)\b",
    ]),
    (Intent.COMPARE_FRAMEWORKS, [
        r"\bcompar(e|ing)\s+(the\s+)?framework(s)?\b",
        r"\bdifference(s)?\s+between\s+(the\s+)?framework(s)?\b",
        r"\bche\s+(vs|versus)\s+ecsa\b",
        r"\bframework\s+comparison\b",
    ]),
    (Intent.CHECK_QUALIFICATION_ALIGNMENT, [
        r"\bqualification\s+alignment\b",
        r"\bnqf\s+alignment\b",
        r"\bheqsf\s+alignment\b",
        r"\bsaqa\s+registration\b",
    ]),
    (Intent.CHECK_PROGRAMME_ACCREDITATION, [
        r"\bprogramme\s+accreditat(ion|ed)\b",
        r"\bche\s+accreditat(ion|ed)\b",
        r"\binstitutional\s+audit\b",
    ]),
    (Intent.CHECK_PROFESSIONAL_ACCREDITATION, [
        r"\bprofessional\s+accreditat\b",
        r"\becsa\s+accreditat\b",
        r"\bhpcsa\s+accreditat\b",
        r"\bsace\s+accreditat\b",
        r"\bprofessional\s+body\b",
    ]),

    # ── Reporting ─────────────────────────────────────────────────────────
    (Intent.GENERATE_EVIDENCE_PACK, [
        r"\bevidence\s+pack\b",
        r"\bevidence\s+bundle\b",
        r"\bgenerate\s+(the\s+)?evidence\b",
        r"\bassembl(e|y)\s+(an?\s+)?evidence\b",
    ]),
    (Intent.PREPARE_EXECUTIVE_BRIEFING, [
        r"\bexecutive\s+brief(ing)?\b",
        r"\bsenate\s+brief(ing)?\b",
        r"\bmanagement\s+brief(ing)?\b",
    ]),
    (Intent.PREPARE_QA_MEETING_PACK, [
        r"\bqa\s+meeting\s+pack\b",
        r"\bmeeting\s+pack\b",
        r"\bmeeting\s+minutes\b",
        r"\bboard\s+pack\b",
    ]),
    (Intent.GENERATE_REPORT, [
        r"\bgenerate\s+(a\s+)?(report|summary)\b",
        r"\bcreate\s+(a\s+)?(report|summary)\b",
        r"\b(module|programme|faculty|department|institutional)\s+report\b",
        r"\bqa\s+report\b",
    ]),

    # ── Files / Library ───────────────────────────────────────────────────
    (Intent.UPLOAD_AND_ANALYSE, [
        r"\bupload\s+.*(and|then)?\s*(anal(yse|yze)|check|process)\b",
        r"\banalyse\s+(this|the)\s+(file|document|evidence)\b",
        r"\bprocess\s+(this|the)\s+(file|document)\b",
    ]),
    (Intent.SEARCH_FILES, [
        r"\bsearch\s+(for\s+)?(file|document|report|policy)\b",
        r"\bfind\s+(the\s+)?(file|document|report|policy)\b",
        r"\bopen\s+(the\s+)?(file|document|report)\b",
    ]),

    # ── Policy / Knowledge ────────────────────────────────────────────────
    (Intent.EXPLAIN_POLICY, [
        r"\bexplain\s+(the\s+|this\s+)?policy\b",
        r"\bwhat\s+is\s+(the\s+)?policy\b",
        r"\binstitutional\s+policy\b",
        r"\bsupplementary\s+(assessment|exam)\b",
    ]),
    (Intent.SEARCH_INSTITUTIONAL_KNOWLEDGE, [
        r"\bsearch\s+(the\s+)?knowledge\b",
        r"\bknowledge\s+base\b",
        r"\bsearch\s+(for\s+)?information\b",
    ]),
]

# ── Fallback ──────────────────────────────────────────────────────────────
_FALLBACK_INTENT = Intent.GENERAL_ACADEMIC_QUALITY_ASSISTANCE


def detect_intent_d2(prompt: str) -> tuple[Intent, float]:
    """Public alias for D2 intent detection."""
    return _detect_intent(prompt)


def _detect_intent(prompt: str) -> tuple[Intent, float]:
    lower = prompt.lower()
    scores: dict[Intent, int] = {}
    for intent, patterns in _INTENT_PATTERNS:
        hits = sum(1 for p in patterns if re.search(p, lower))
        if hits:
            scores[intent] = scores.get(intent, 0) + hits

    if not scores:
        return (_FALLBACK_INTENT, 0.5)

    best = max(scores, key=lambda k: scores[k])
    total = sum(scores.values())
    conf = min(0.95, 0.5 + (scores[best] / max(total, 1)) * 0.5)
    return (best, round(conf, 2))


# ---------------------------------------------------------------------------
# Service selection
# ---------------------------------------------------------------------------

# Maps each intent to the list of AQAA backend services it needs
_INTENT_SERVICES: dict[Intent, list[str]] = {
    Intent.GENERAL_QA_QUESTION: ["retrieval_service"],
    Intent.SEARCH_INSTITUTIONAL_KNOWLEDGE: ["retrieval_service"],
    Intent.EXPLAIN_POLICY: ["retrieval_service", "policy_engine"],
    Intent.GENERAL_ACADEMIC_QUALITY_ASSISTANCE: ["retrieval_service"],

    Intent.AUDIT_MODULE_FOLDER: ["module_folder_audit_agent"],
    Intent.ASSESS_ASSESSMENT_COMPLIANCE: ["assessment_compliance_agent"],
    Intent.ASSESS_MODERATION_COMPLIANCE: ["moderation_compliance_agent"],
    Intent.ASSESS_ATTENDANCE_COMPLIANCE: ["attendance_compliance_agent"],
    Intent.ASSESS_OUTCOME_ALIGNMENT: ["outcome_alignment_agent"],
    Intent.VERIFY_EVIDENCE: ["evidence_verification_agent"],
    Intent.IDENTIFY_MISSING_EVIDENCE: ["evidence_verification_agent", "retrieval_service"],
    Intent.EXPLAIN_COMPLIANCE_SCORE: ["retrieval_service", "audit_service"],

    Intent.LIST_FINDINGS: ["findings_service"],
    Intent.EXPLAIN_FINDING: ["findings_service"],
    Intent.ASSIGN_FINDING: ["findings_service", "notification_service"],
    Intent.SUBMIT_RESOLUTION: ["findings_service"],
    Intent.REVIEW_RESOLUTION: ["findings_service"],
    Intent.APPROVE_RESOLUTION: ["findings_service", "audit_logging_service"],
    Intent.REJECT_RESOLUTION: ["findings_service", "audit_logging_service"],
    Intent.ESCALATE_FINDING: ["findings_service", "notification_service"],
    Intent.GENERATE_CORRECTIVE_ACTION_PLAN: ["findings_service", "reporting_engine"],

    Intent.IDENTIFY_APPLICABLE_FRAMEWORKS: ["regulatory_framework_engine", "applicability_engine"],
    Intent.ASSESS_FRAMEWORK_COMPLIANCE: ["framework_assessment_engine", "regulatory_framework_engine"],
    Intent.ASSESS_INTEGRATED_READINESS: ["framework_assessment_engine", "applicability_engine", "accreditation_readiness_agent"],
    Intent.COMPARE_FRAMEWORKS: ["cross_framework_engine", "regulatory_framework_engine"],
    Intent.CHECK_QUALIFICATION_ALIGNMENT: ["regulatory_framework_engine"],
    Intent.CHECK_PROGRAMME_ACCREDITATION: ["accreditation_readiness_agent", "regulatory_framework_engine"],
    Intent.CHECK_PROFESSIONAL_ACCREDITATION: ["regulatory_framework_engine", "applicability_engine"],

    Intent.GENERATE_REPORT: ["reporting_engine", "retrieval_service"],
    Intent.GENERATE_EVIDENCE_PACK: ["reporting_engine", "findings_service", "artifact_service"],
    Intent.PREPARE_EXECUTIVE_BRIEFING: ["reporting_engine", "retrieval_service"],
    Intent.PREPARE_QA_MEETING_PACK: ["reporting_engine", "findings_service", "retrieval_service"],

    Intent.SEARCH_FILES: ["retrieval_service"],
    Intent.OPEN_EVIDENCE: ["retrieval_service"],
    Intent.UPLOAD_AND_ANALYSE: ["document_processing_service", "classification_service", "retrieval_service"],
}

# Intents that require confirmation before execution
_REQUIRES_CONFIRMATION: set[Intent] = {
    Intent.ASSIGN_FINDING,
    Intent.APPROVE_RESOLUTION,
    Intent.REJECT_RESOLUTION,
    Intent.ESCALATE_FINDING,
    Intent.GENERATE_EVIDENCE_PACK,
}

# Intents that route to the regulatory orchestration engine
_REGULATORY_INTENTS: set[Intent] = {
    Intent.IDENTIFY_APPLICABLE_FRAMEWORKS,
    Intent.ASSESS_FRAMEWORK_COMPLIANCE,
    Intent.ASSESS_INTEGRATED_READINESS,
    Intent.COMPARE_FRAMEWORKS,
    Intent.CHECK_QUALIFICATION_ALIGNMENT,
    Intent.CHECK_PROGRAMME_ACCREDITATION,
    Intent.CHECK_PROFESSIONAL_ACCREDITATION,
}

# Intents that produce auditable actions
_AUDIT_LOG_REQUIRED: set[Intent] = {
    Intent.ASSIGN_FINDING,
    Intent.SUBMIT_RESOLUTION,
    Intent.APPROVE_RESOLUTION,
    Intent.REJECT_RESOLUTION,
    Intent.ESCALATE_FINDING,
    Intent.AUDIT_MODULE_FOLDER,
    Intent.ASSESS_ASSESSMENT_COMPLIANCE,
    Intent.ASSESS_MODERATION_COMPLIANCE,
    Intent.ASSESS_ATTENDANCE_COMPLIANCE,
    Intent.ASSESS_OUTCOME_ALIGNMENT,
    Intent.VERIFY_EVIDENCE,
}

# Minimum roles needed per intent
_ROLE_REQUIREMENTS: dict[Intent, set[UserRole]] = {
    Intent.APPROVE_RESOLUTION: {UserRole.QUALITY_ASSURANCE_OFFICER, UserRole.FACULTY_DEAN, UserRole.HEAD_OF_DEPARTMENT},
    Intent.REJECT_RESOLUTION: {UserRole.QUALITY_ASSURANCE_OFFICER, UserRole.FACULTY_DEAN, UserRole.HEAD_OF_DEPARTMENT},
    Intent.ASSESS_INTEGRATED_READINESS: {UserRole.QUALITY_ASSURANCE_OFFICER, UserRole.FACULTY_DEAN, UserRole.PROGRAMME_COORDINATOR},
    Intent.GENERATE_EVIDENCE_PACK: {UserRole.QUALITY_ASSURANCE_OFFICER, UserRole.FACULTY_DEAN},
    Intent.PREPARE_EXECUTIVE_BRIEFING: {UserRole.QUALITY_ASSURANCE_OFFICER, UserRole.FACULTY_DEAN, UserRole.HEAD_OF_DEPARTMENT},
    Intent.PREPARE_QA_MEETING_PACK: {UserRole.QUALITY_ASSURANCE_OFFICER, UserRole.FACULTY_DEAN},
}


# ---------------------------------------------------------------------------
# Execution plan
# ---------------------------------------------------------------------------


@dataclass
class ExecutionPlan:
    """Internal plan for one request — never exposed raw to clients."""

    intent: Intent
    confidence: float
    context: ResolvedContext
    services_required: list[str] = field(default_factory=list)
    is_regulatory: bool = False
    requires_confirmation: bool = False
    requires_human_review: bool = False
    audit_log_required: bool = False
    permission_denied: bool = False
    permission_reason: str = ""
    missing_context: list[str] = field(default_factory=list)
    expected_artifact_type: str = ""
    citations_required: bool = False
    generation_mode: str = "DETERMINISTIC_TEMPLATE"

    def to_sse_dict(self) -> dict:
        """Return the public subset safe to send in a 'plan' SSE event."""
        return {
            "intent": self.intent.value,
            "confidence": self.confidence,
            "services_active": len(self.services_required),
            "is_regulatory": self.is_regulatory,
            "requires_confirmation": self.requires_confirmation,
            "requires_human_review": self.requires_human_review,
            "permission_denied": self.permission_denied,
            "permission_reason": self.permission_reason if self.permission_denied else "",
            "expected_artifact": self.expected_artifact_type,
            "context": self.context.to_public_dict(),
        }


# ---------------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------------


def build_execution_plan(
    prompt: str,
    context: ResolvedContext,
) -> ExecutionPlan:
    """Build an execution plan for a user request.

    Parameters
    ----------
    prompt:  Raw natural-language prompt.
    context: Fully resolved context from the context engine.
    """
    intent, confidence = _detect_intent(prompt)

    plan = ExecutionPlan(
        intent=intent,
        confidence=confidence,
        context=context,
        services_required=_INTENT_SERVICES.get(intent, ["retrieval_service"]),
        is_regulatory=intent in _REGULATORY_INTENTS,
        requires_confirmation=intent in _REQUIRES_CONFIRMATION,
        audit_log_required=intent in _AUDIT_LOG_REQUIRED,
        citations_required=intent in _REGULATORY_INTENTS,
        missing_context=list(context.missing_context),
    )

    # ── Permission check ─────────────────────────────────────────────────
    # Lower index = more privileged (SYSTEM_ADMIN=0, STUDENT=6).
    # A role is allowed if its index <= the index of the LEAST privileged
    # required role (i.e. the highest index in required_roles).
    role = context.role
    required_roles = _ROLE_REQUIREMENTS.get(intent)
    if required_roles and role is not None and role not in required_roles:
        _CUMULATIVE = [
            UserRole.SYSTEM_ADMIN,
            UserRole.QUALITY_ASSURANCE_OFFICER,
            UserRole.FACULTY_DEAN,
            UserRole.HEAD_OF_DEPARTMENT,
            UserRole.PROGRAMME_COORDINATOR,
            UserRole.LECTURER,
            UserRole.STUDENT,
        ]
        role_idx = _CUMULATIVE.index(role) if role in _CUMULATIVE else 99
        # Least privileged required role → highest index in the list
        max_required_idx = max(
            (_CUMULATIVE.index(r) for r in required_roles if r in _CUMULATIVE),
            default=0,
        )
        allowed = role_idx <= max_required_idx
        if not allowed:
            plan.permission_denied = True
            plan.permission_reason = (
                f"Your role ({role.value if hasattr(role, 'value') else role}) "
                f"does not have permission to perform this action."
            )

    # ── Human review requirements ─────────────────────────────────────────
    if intent in {Intent.APPROVE_RESOLUTION, Intent.REJECT_RESOLUTION,
                  Intent.COMPARE_FRAMEWORKS, Intent.ASSESS_INTEGRATED_READINESS}:
        plan.requires_human_review = True

    # ── Artifact type ─────────────────────────────────────────────────────
    _ARTIFACT_MAP: dict[Intent, str] = {
        Intent.GENERATE_REPORT: "module_audit_report",
        Intent.GENERATE_EVIDENCE_PACK: "accreditation_evidence_pack",
        Intent.PREPARE_EXECUTIVE_BRIEFING: "executive_briefing",
        Intent.PREPARE_QA_MEETING_PACK: "qa_meeting_pack",
        Intent.GENERATE_CORRECTIVE_ACTION_PLAN: "corrective_action_plan",
        Intent.ASSESS_INTEGRATED_READINESS: "regulatory_readiness_report",
    }
    plan.expected_artifact_type = _ARTIFACT_MAP.get(intent, "")

    # ── Generation mode ───────────────────────────────────────────────────
    if intent in _REGULATORY_INTENTS:
        plan.generation_mode = "HYBRID"
    elif intent in {
        Intent.GENERAL_QA_QUESTION,
        Intent.SEARCH_INSTITUTIONAL_KNOWLEDGE,
        Intent.EXPLAIN_POLICY,
        Intent.GENERAL_ACADEMIC_QUALITY_ASSISTANCE,
    }:
        plan.generation_mode = "LLM"
    else:
        plan.generation_mode = "DETERMINISTIC_TEMPLATE"

    return plan
