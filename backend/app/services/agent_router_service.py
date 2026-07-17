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
    # ---------------------------------------------------------------------------
    # Phase C — Regulatory intents
    # ---------------------------------------------------------------------------
    ("identify_applicable_frameworks", [
        r"\bwhich framework(s)?\b", r"\bapplicable framework\b", r"\bwhat framework\b",
        r"\bidentify framework\b", r"\bframeworks? appl(y|ies)\b",
    ]),
    ("explain_applicability", [
        r"\bwhy (is|are).*(framework|standard|regulation)\b", r"\bhow does.*(apply|applicable)\b",
        r"\bapplicability\b", r"\bwhy does it apply\b",
    ]),
    ("assess_framework_compliance", [
        r"\bcompl(y|iance) with (the )?framework\b", r"\bframework compliance\b",
        r"\bassess.*(framework|standard)\b", r"\bmeet.*(framework|standard|criterion)\b",
    ]),
    ("assess_integrated_readiness", [
        r"\bintegrated readiness\b", r"\boverall readiness\b", r"\bmulti.?framework\b",
        r"\bcombined compliance\b", r"\bholistic.*(compliance|readiness)\b",
    ]),
    ("explain_regulatory_requirement", [
        r"\bwhat does.*(criterion|standard|requirement|regulation) require\b",
        r"\bexplain.*(criterion|standard|requirement|regulation)\b",
        r"\bwhat is required (by|under)\b",
    ]),
    ("find_missing_regulatory_evidence", [
        r"\bmissing (regulatory )?evidence\b", r"\bgaps?.*(evidence|criterion)\b",
        r"\bwhich (evidence|document)s? (are|is) missing\b", r"\bunmet criterion\b",
    ]),
    ("compare_frameworks", [
        r"\bcompar(e|ing).*(framework|standard)\b", r"\bdifference(s)? between.*(framework|standard)\b",
        r"\bframework (vs|versus|comparison)\b",
    ]),
    ("explain_framework_overlap", [
        r"\boverlap(ping)?.*(framework|standard)\b", r"\bshared (criteria|standards)\b",
        r"\bboth frameworks?\b", r"\bduplication.*(framework|standard)\b",
    ]),
    ("explain_framework_conflict", [
        r"\bconflict(ing)?.*(framework|standard|requirement)\b",
        r"\bincompat(ible|ibility).*(framework|standard)\b",
        r"\bcontradiction.*(framework|standard)\b",
    ]),
    ("generate_regulatory_report", [
        r"\bregulatory report\b", r"\bgenerate.*(framework|regulatory) report\b",
        r"\bframework.*(summary|report)\b",
    ]),
    ("generate_evidence_pack", [
        r"\bevidence pack\b", r"\bevidence bundle\b", r"\bassembl(e|y).*(evidence|pack)\b",
        r"\bprepare.*(accreditation|submission) pack\b",
    ]),
    ("create_corrective_action_plan", [
        r"\bcorrective action\b", r"\bremediation plan\b", r"\baction plan\b",
        r"\bfix.*(finding|gap|non.?compliance)\b", r"\baddress.*(finding|gap)\b",
    ]),
    ("explain_regulatory_finding", [
        r"\bregulatory finding\b", r"\bwhat does.*(finding|non.?compliance) mean\b",
        r"\bexplain.*(finding|gap|non.?compliance)\b",
    ]),
    ("check_framework_version", [
        r"\bframework version\b", r"\bcurrent version.*(framework|standard)\b",
        r"\blatest.*(standard|framework|edition)\b", r"\bversion (of|for).*(framework)\b",
    ]),
    ("check_qualification_alignment", [
        r"\bqualification alignment\b", r"\bnqf alignment\b", r"\bheqsf alignment\b",
        r"\bprogramme.*(nqf|heqsf|saqa)\b", r"\bdegree.*(nqf|level|aligned)\b",
    ]),
    ("check_programme_accreditation", [
        r"\bprogramme accreditat(ion|ed)\b", r"\bche accreditat(ion|ed)\b",
        r"\bdhet.*(programme|accreditat)\b", r"\binstitutional audit\b",
    ]),
    ("check_professional_accreditation", [
        r"\bprofessional accreditat\b", r"\becsa accreditat\b", r"\bhpcsa accreditat\b",
        r"\bsace accreditat\b", r"\bprofessional body\b", r"\bprofessional council\b",
    ]),
    ("check_institutional_audit_readiness", [
        r"\binstitutional audit readiness\b", r"\bche (site visit|audit)\b",
        r"\bdhet.*(audit|inspection|review)\b", r"\binstitutional review readiness\b",
    ]),
    ("check_occupational_qualification_compliance", [
        r"\boccu?pational qual(ification)?\b", r"\bqcto\b", r"\bseta\b",
        r"\bpart qual(ification)?\b", r"\boccupational cert(ificate)?\b",
        r"\bunit standard\b", r"\blearnership\b",
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
    # Phase C — Regulatory intents
    "identify_applicable_frameworks": [
        "Open Framework Management workspace",
        "View applicable frameworks for your programme",
        "Run a framework assessment",
    ],
    "explain_applicability": [
        "View framework applicability rules",
        "Open Regulatory Readiness workspace",
        "Contact your QA Officer for applicability guidance",
    ],
    "assess_framework_compliance": [
        "Trigger a framework compliance assessment",
        "View assessment results for this framework",
        "Upload evidence to improve your compliance score",
    ],
    "assess_integrated_readiness": [
        "View integrated readiness score across all frameworks",
        "Identify mandatory failures blocking readiness",
        "Generate a combined regulatory report",
    ],
    "explain_regulatory_requirement": [
        "View the criterion detail in Framework Management",
        "Upload evidence for this requirement",
        "Ask for a corrective action plan",
    ],
    "find_missing_regulatory_evidence": [
        "View missing evidence gaps in Regulatory Readiness",
        "Upload missing evidence files",
        "Promote gaps to findings for tracking",
    ],
    "compare_frameworks": [
        "View cross-framework mapping in Framework Management",
        "Run assessments for both frameworks",
        "Generate a comparison report",
    ],
    "explain_framework_overlap": [
        "View shared criteria across frameworks",
        "Review cross-framework equivalence mappings",
        "Optimise evidence submission for overlapping criteria",
    ],
    "explain_framework_conflict": [
        "Review conflicting requirements with your QA Officer",
        "Flag the conflict in the findings tracker",
        "Request human review for conflicting criteria",
    ],
    "generate_regulatory_report": [
        "Generate regulatory compliance report",
        "Download assessment results as PDF",
        "Share report with accreditation body",
    ],
    "generate_evidence_pack": [
        "Assemble evidence pack for submission",
        "Review evidence coverage before submission",
        "Upload any missing evidence items",
    ],
    "create_corrective_action_plan": [
        "View open findings for this programme",
        "Generate corrective action plan from findings",
        "Assign findings to responsible parties",
    ],
    "explain_regulatory_finding": [
        "View finding detail in Findings tracker",
        "Request guidance from QA Officer",
        "Assign finding to a responsible party",
    ],
    "check_framework_version": [
        "View active version in Framework Management",
        "Review version lifecycle history",
        "Check if your assessment used the active version",
    ],
    "check_qualification_alignment": [
        "Run Outcome Alignment audit for this programme",
        "View NQF level descriptors in Knowledge Base",
        "Check HEQSF alignment for your qualification",
    ],
    "check_programme_accreditation": [
        "Run Programme Accreditation Readiness assessment",
        "View CHE accreditation criteria",
        "Upload programme self-evaluation report",
    ],
    "check_professional_accreditation": [
        "Run professional body accreditation assessment",
        "View ECSA / HPCSA accreditation criteria",
        "Upload professional accreditation evidence",
    ],
    "check_institutional_audit_readiness": [
        "Open Institutional Audit Readiness workspace",
        "View CHE site visit preparation checklist",
        "Generate institutional audit readiness report",
    ],
    "check_occupational_qualification_compliance": [
        "View QCTO / SETA occupational framework criteria",
        "Upload unit standard evidence",
        "Check learnership compliance status",
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
    # Phase C — Regulatory intents
    "identify_applicable_frameworks": [
        "Which programme or module are you asking about?",
        "Are you looking at institutional or programme-level frameworks?",
    ],
    "explain_applicability": [
        "Which framework or standard would you like me to explain?",
        "Is this for your institution or a specific programme?",
    ],
    "assess_framework_compliance": [
        "Which framework should I assess compliance against?",
        "Which module or programme is in scope?",
    ],
    "assess_integrated_readiness": [
        "Which programme or institution should I assess?",
        "Should I include all active frameworks or specific ones?",
    ],
    "explain_regulatory_requirement": [
        "Which criterion or standard would you like explained?",
        "Are you asking about a mandatory or advisory requirement?",
    ],
    "find_missing_regulatory_evidence": [
        "Which framework or criterion are you checking evidence gaps for?",
        "Should I look at module-level or programme-level evidence?",
    ],
    "compare_frameworks": [
        "Which two frameworks would you like me to compare?",
        "Are you interested in overlapping criteria or conflicting requirements?",
    ],
    "explain_framework_overlap": [
        "Which frameworks should I check for overlap?",
        "Are you looking for shared criteria to reduce submission duplication?",
    ],
    "explain_framework_conflict": [
        "Which frameworks have conflicting requirements you'd like explained?",
        "Would you like me to flag this for human review?",
    ],
    "generate_regulatory_report": [
        "Which framework or programme should the report cover?",
        "What time period should the report include?",
    ],
    "generate_evidence_pack": [
        "Which accreditation body is this evidence pack for?",
        "Should I include all verified evidence or only mandatory items?",
    ],
    "create_corrective_action_plan": [
        "Which findings or gaps should the corrective plan address?",
        "Who should be assigned responsibility for these actions?",
    ],
    "explain_regulatory_finding": [
        "Which finding would you like me to explain?",
        "Are you looking for guidance on how to remediate it?",
    ],
    "check_framework_version": [
        "Which framework's version would you like to check?",
        "Are you checking the version used in a specific assessment?",
    ],
    "check_qualification_alignment": [
        "Which qualification or programme are you checking?",
        "Are you checking NQF level alignment or graduate attribute mapping?",
    ],
    "check_programme_accreditation": [
        "Which programme's accreditation status should I check?",
        "Which accrediting body — CHE, DHET, or another?",
    ],
    "check_professional_accreditation": [
        "Which professional body accreditation are you checking (ECSA, HPCSA, SACE)?",
        "Which programme is under professional accreditation review?",
    ],
    "check_institutional_audit_readiness": [
        "Is this for a CHE institutional audit or DHET inspection?",
        "Which institution or campus should I assess readiness for?",
    ],
    "check_occupational_qualification_compliance": [
        "Which QCTO occupational qualification or SETA unit standard are you checking?",
        "Is this for a learnership or a skills programme?",
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
    # Phase C — Regulatory intents
    "identify_applicable_frameworks": "regulatory",
    "explain_applicability": "regulatory",
    "assess_framework_compliance": "regulatory",
    "assess_integrated_readiness": "regulatory",
    "explain_regulatory_requirement": "regulatory",
    "find_missing_regulatory_evidence": "regulatory",
    "compare_frameworks": "regulatory",
    "explain_framework_overlap": "regulatory",
    "explain_framework_conflict": "regulatory",
    "generate_regulatory_report": "regulatory",
    "generate_evidence_pack": "regulatory",
    "create_corrective_action_plan": "regulatory",
    "explain_regulatory_finding": "regulatory",
    "check_framework_version": "regulatory",
    "check_qualification_alignment": "regulatory",
    "check_programme_accreditation": "regulatory",
    "check_professional_accreditation": "regulatory",
    "check_institutional_audit_readiness": "regulatory",
    "check_occupational_qualification_compliance": "regulatory",
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
        # Phase C — Regulatory intents
        "identify_applicable_frameworks": "Regulatory Framework Identification",
        "explain_applicability": "Framework Applicability Explanation",
        "assess_framework_compliance": "Framework Compliance Assessment",
        "assess_integrated_readiness": "Integrated Regulatory Readiness",
        "explain_regulatory_requirement": "Regulatory Requirement Explanation",
        "find_missing_regulatory_evidence": "Missing Evidence Detection",
        "compare_frameworks": "Framework Comparison",
        "explain_framework_overlap": "Framework Overlap Analysis",
        "explain_framework_conflict": "Framework Conflict Analysis",
        "generate_regulatory_report": "Regulatory Report Generation",
        "generate_evidence_pack": "Evidence Pack Assembly",
        "create_corrective_action_plan": "Corrective Action Planning",
        "explain_regulatory_finding": "Regulatory Finding Explanation",
        "check_framework_version": "Framework Version Check",
        "check_qualification_alignment": "Qualification Alignment Check",
        "check_programme_accreditation": "Programme Accreditation Check",
        "check_professional_accreditation": "Professional Accreditation Check",
        "check_institutional_audit_readiness": "Institutional Audit Readiness",
        "check_occupational_qualification_compliance": "Occupational Qualification Compliance",
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
        # Phase C — Regulatory intents
        "identify_applicable_frameworks": ["Framework Applicability Engine", "Regulatory Authority Registry", "Quality Framework Catalogue"],
        "explain_applicability": ["Framework Applicability Rules", "HEQSF Level Descriptors", "SAQA NQF Framework"],
        "assess_framework_compliance": ["Framework Assessment Engine", "Criterion Assessment Results", "Evidence Mapping Records"],
        "assess_integrated_readiness": ["Integrated Regulatory Readiness Dashboard", "Multi-Framework Assessment Results"],
        "explain_regulatory_requirement": ["Framework Standards and Criteria", "Evidence Requirements Register", "Regulatory Authority Guidelines"],
        "find_missing_regulatory_evidence": ["Evidence Coverage Gap Report", "Criterion Assessment Results", "Evidence Requirements Register"],
        "compare_frameworks": ["Cross-Framework Mapping Registry", "Framework Standards Catalogue", "Human-Verified Equivalence Records"],
        "explain_framework_overlap": ["Cross-Framework Equivalence Mappings", "Shared Criteria Analysis"],
        "explain_framework_conflict": ["Cross-Framework Conflict Records", "QA Officer Escalation Log"],
        "generate_regulatory_report": ["Framework Assessment Run Results", "Compliance Score History", "Regulatory Authority Requirements"],
        "generate_evidence_pack": ["Verified Evidence Mappings", "Evidence Requirements Register", "Accreditation Submission Checklist"],
        "create_corrective_action_plan": ["Regulatory Findings Register", "Gap Promotion Records", "Finding Lifecycle Tracker"],
        "explain_regulatory_finding": ["Regulatory Findings Register", "Criterion Assessment Results", "Framework Standards"],
        "check_framework_version": ["Framework Version Lifecycle Records", "Active Version Registry", "Version Transition History"],
        "check_qualification_alignment": ["HEQSF Qualification Standards", "NQF Level Descriptors", "SAQA Qualification Register"],
        "check_programme_accreditation": ["CHE Programme Accreditation Standards", "DHET Programme Requirements", "Institutional Quality Assurance Framework"],
        "check_professional_accreditation": ["ECSA Engineering Accreditation Criteria", "HPCSA Health Professions Standards", "SACE Teacher Education Requirements"],
        "check_institutional_audit_readiness": ["CHE Institutional Audit Framework", "DHET Inspection Requirements", "Institutional Self-Evaluation Guidelines"],
        "check_occupational_qualification_compliance": ["QCTO Occupational Qualification Framework", "SETA Unit Standards", "Learnership Compliance Register"],
    }
    return source_map.get(intent, ["AQAA Knowledge Base"])
