"""Rule-based QA improvement recommendation engine.

Produces structured improvement recommendations based on:
- Audit compliance status (from DB)
- Missing evidence types (from audit findings)
- QA risk level (compliant / at_risk / non_compliant)

These are deterministic rules — no LLM required.  When a real AI layer is
added, these rules serve as a fallback and validation check.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Rule library
# ---------------------------------------------------------------------------

_RULES: list[dict[str, Any]] = [
    # Missing evidence rules
    {
        "trigger": "missing_assessment_brief",
        "priority": "high",
        "category": "Evidence",
        "action": "Upload the signed assessment brief to the module folder evidence section.",
        "rationale": "Assessment briefs are mandatory for CHE compliance and must be present before assessments commence.",
    },
    {
        "trigger": "missing_moderation_record",
        "priority": "high",
        "category": "Moderation",
        "action": "Upload the internal moderation record signed by the moderator.",
        "rationale": "Moderation records are required to demonstrate that assessments have been quality-checked before learner submission.",
    },
    {
        "trigger": "missing_attendance_register",
        "priority": "medium",
        "category": "Attendance",
        "action": "Upload the attendance register for all contact sessions.",
        "rationale": "Attendance registers are evidence of contact time and are required for CHE and DHET compliance.",
    },
    {
        "trigger": "missing_learner_sample",
        "priority": "high",
        "category": "Evidence",
        "action": "Upload a representative sample of marked learner scripts (at least 10% or minimum 5).",
        "rationale": "Marked learner evidence is required to verify that assessments were conducted and marked according to the rubric.",
    },
    {
        "trigger": "missing_course_outline",
        "priority": "high",
        "category": "Curriculum",
        "action": "Upload the approved course outline / module descriptor for this academic year.",
        "rationale": "Course outlines are the primary reference for learning outcomes and must be current and approved.",
    },
    # Compliance level rules
    {
        "trigger": "non_compliant",
        "priority": "high",
        "category": "Compliance",
        "action": "Escalate to the Programme Coordinator and Head of Department immediately. Schedule a corrective action plan within 5 business days.",
        "rationale": "Non-compliant modules (< 70% compliance) are flagged for urgent attention before the next accreditation cycle.",
    },
    {
        "trigger": "at_risk",
        "priority": "medium",
        "category": "Compliance",
        "action": "Schedule a module folder review session with the lecturer within 10 business days.",
        "rationale": "At-risk modules (70–89% compliance) require targeted evidence uploads to reach the 90% compliant threshold.",
    },
    {
        "trigger": "no_recent_audit",
        "priority": "medium",
        "category": "Audit",
        "action": "Trigger a module folder audit for this module. No audit has been run recently.",
        "rationale": "Modules should be audited at least once per semester to maintain continuous quality assurance.",
    },
    # Outcome alignment rules
    {
        "trigger": "outcome_misalignment",
        "priority": "medium",
        "category": "Curriculum",
        "action": "Review the learning outcomes against the assessment briefs and moderation records to ensure alignment.",
        "rationale": "Outcome misalignment is a common finding in accreditation visits and indicates a curriculum review is needed.",
    },
    # General improvement
    {
        "trigger": "general_improvement",
        "priority": "low",
        "category": "Process",
        "action": "Schedule a departmental QA awareness session to review evidence upload requirements.",
        "rationale": "Proactive awareness reduces the number of missing documents found at audit time.",
    },
]

# Map compliance status strings to triggers
_STATUS_TRIGGERS: dict[str, list[str]] = {
    "non_compliant": ["non_compliant"],
    "at_risk": ["at_risk"],
    "compliant": ["general_improvement"],
    None: ["no_recent_audit", "general_improvement"],
}


def get_recommendations(
    audit_status: str | None = None,
    missing_evidence_types: list[str] | None = None,
    include_general: bool = True,
) -> list[dict[str, Any]]:
    """Return a prioritised list of QA recommendations.

    Args:
        audit_status: "compliant", "at_risk", "non_compliant", or None.
        missing_evidence_types: List of missing document categories
            (e.g. ["assessment_brief", "moderation_record"]).
        include_general: Always include one general improvement item.

    Returns:
        List of recommendation dicts with keys: priority, category, action, rationale.
    """
    triggers: set[str] = set()

    # Compliance status triggers
    status_key: str | None = audit_status
    for status in _STATUS_TRIGGERS:
        if status is not None and audit_status == status:
            triggers.update(_STATUS_TRIGGERS[status])
    if audit_status is None:
        triggers.update(_STATUS_TRIGGERS[None])  # type: ignore[arg-type]

    # Missing evidence triggers
    for ev_type in (missing_evidence_types or []):
        clean = ev_type.lower().replace(" ", "_").replace("-", "_")
        trigger_key = f"missing_{clean}"
        triggers.add(trigger_key)

    if include_general and "general_improvement" not in triggers:
        triggers.add("general_improvement")

    # Match triggers to rules
    matched: list[dict[str, Any]] = []
    seen_actions: set[str] = set()
    for rule in _RULES:
        if rule["trigger"] in triggers and rule["action"] not in seen_actions:
            matched.append(
                {
                    "priority": rule["priority"],
                    "category": rule["category"],
                    "action": rule["action"],
                    "rationale": rule["rationale"],
                }
            )
            seen_actions.add(rule["action"])

    # Sort: high → medium → low
    order = {"high": 0, "medium": 1, "low": 2}
    matched.sort(key=lambda r: order.get(r["priority"], 3))
    return matched
