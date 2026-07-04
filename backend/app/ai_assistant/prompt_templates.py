"""Response templates and dev-mode notices for the AI QA Assistant.

All templates are plain strings — no external templating engine required.
Variable substitution uses Python str.format() at the call site.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Dev-mode notice (always appended in pilot mode)
# ---------------------------------------------------------------------------

DEV_MODE_NOTICE = (
    "\n\n---\n"
    "**Development mode:** This response was generated using hash-based placeholder "
    "embeddings, not semantic embeddings. Retrieved knowledge chunks may not be "
    "semantically relevant to your question. Results will improve significantly once "
    "real sentence-transformer embeddings are configured in the embedding service."
)

# ---------------------------------------------------------------------------
# Answer templates
# ---------------------------------------------------------------------------

ANSWER_WITH_CONTEXT = (
    "Based on the {institution_code} Institutional Knowledge Package "
    "({ikp_version}, {academic_year}), the following information was found "
    "relevant to your question:\n\n"
    "{context_block}"
)

ANSWER_NO_CONTEXT = (
    "No relevant knowledge chunks were found in the {institution_code} "
    "Institutional Knowledge Package for this query.\n\n"
    "This may be because:\n"
    "- The query topic is not covered in the current IKP version ({ikp_version}).\n"
    "- The Qdrant collection has not been indexed. Ask your System Admin to run "
    "the indexing script.\n"
    "- The question is too specific for the current knowledge base coverage."
)

CONTEXT_CHUNK_TEMPLATE = (
    "**{index}. {entity_key}** ({entity_type})\n"
    "{text_excerpt}\n"
    "_Source: {source_document}_\n"
)

# ---------------------------------------------------------------------------
# Intent-specific preambles
# ---------------------------------------------------------------------------

INTENT_PROGRAMME = (
    "Regarding programmes at {institution_code}:\n\n"
)

INTENT_MODULE = (
    "Regarding modules at {institution_code}:\n\n"
)

INTENT_COMPLIANCE = (
    "Regarding QA compliance at {institution_code}:\n\n"
)

INTENT_AUDIT = (
    "Regarding audit and evidence at {institution_code}:\n\n"
)

INTENT_GENERAL = (
    "Regarding your query about {institution_code}:\n\n"
)

INTENT_PREAMBLES: dict[str, str] = {
    "programme_query": INTENT_PROGRAMME,
    "module_query": INTENT_MODULE,
    "compliance_query": INTENT_COMPLIANCE,
    "audit_query": INTENT_AUDIT,
    "general": INTENT_GENERAL,
}

# ---------------------------------------------------------------------------
# Suggested prompts by role
# ---------------------------------------------------------------------------

SUGGESTED_PROMPTS_STAFF = [
    {"prompt": "What programmes does {institution_code} offer in ICT?",            "category": "Programmes"},
    {"prompt": "List all modules in the {institution_code} knowledge base.",        "category": "Modules"},
    {"prompt": "What are the admission requirements for ICT programmes?",           "category": "Admissions"},
    {"prompt": "What faculties does {institution_code} have?",                      "category": "Structure"},
    {"prompt": "Summarise the NQF levels of programmes at {institution_code}.",     "category": "Programmes"},
    {"prompt": "What departments are in the Faculty of ICT?",                      "category": "Structure"},
]

SUGGESTED_PROMPTS_QA = [
    {"prompt": "What evidence is commonly missing in module folder audits?",        "category": "Compliance"},
    {"prompt": "What corrective actions should I recommend for non-compliant modules?", "category": "Recommendations"},
    {"prompt": "Summarise the QA readiness of {institution_code}.",                "category": "Compliance"},
    {"prompt": "What is the accreditation status for ICT programmes?",             "category": "Accreditation"},
    {"prompt": "Generate an improvement plan for audit compliance.",                "category": "Recommendations"},
    {"prompt": "Which modules are at risk based on current audit data?",            "category": "Risk"},
]

SUGGESTED_PROMPTS_ADMIN = [
    {"prompt": "Compare TUT and UP institutional structures.",                      "category": "Multi-institution"},
    {"prompt": "Show knowledge base coverage for all pilot institutions.",           "category": "Knowledge Base"},
    {"prompt": "Which pilot institution has more indexed knowledge chunks?",        "category": "Knowledge Base"},
    {"prompt": "List programmes at TUT vs UP.",                                    "category": "Multi-institution"},
]

# ---------------------------------------------------------------------------
# Agent mode labels
# ---------------------------------------------------------------------------

AGENT_MODE_LABELS: dict[str, str] = {
    "qa_assistant":            "QA Assistant",
    "policy_assistant":        "Policy Assistant",
    "audit_assistant":         "Audit Assistant",
    "evidence_assistant":      "Evidence Assistant",
    "accreditation_assistant": "Accreditation Assistant",
    "qualification_assistant": "Qualification Assistant",
    "reporting_assistant":     "Reporting Assistant",
}

AGENT_MODES: list[str] = list(AGENT_MODE_LABELS.keys())

# ---------------------------------------------------------------------------
# Mode-specific system prompts
# ---------------------------------------------------------------------------

_MODE_FOCUS: dict[str, str] = {
    "qa_assistant": (
        "You are a general Academic Quality Assurance assistant. "
        "Help QA officers, coordinators, and lecturers with any QA-related queries "
        "about programmes, modules, compliance, and audit evidence."
    ),
    "policy_assistant": (
        "You are a QA policy specialist. Focus on quality assurance policies, "
        "CHE (Council on Higher Education) standards, SAQA requirements, DHET regulations, "
        "and institutional QA frameworks."
    ),
    "audit_assistant": (
        "You are a module folder audit specialist. Focus on audit evidence requirements, "
        "evidence gaps, audit findings, corrective actions, and audit run outcomes."
    ),
    "evidence_assistant": (
        "You are an evidence management specialist. Focus on evidence document categories, "
        "upload requirements, file standards, and what constitutes sufficient evidence "
        "for each module folder component."
    ),
    "accreditation_assistant": (
        "You are an accreditation readiness specialist. Focus on accreditation criteria, "
        "CHE programme evaluations, site visit preparation, and programme review processes."
    ),
    "qualification_assistant": (
        "You are a qualification and programme specialist. Focus on programme structures, "
        "NQF levels, credit values, module allocations, and qualification frameworks."
    ),
    "reporting_assistant": (
        "You are a QA analytics and reporting specialist. Focus on compliance rates, "
        "audit statistics, institutional QA metrics, trends, and improvement planning."
    ),
}


def build_system_prompt(
    institution_code: str,
    mode: str,
    chunks: list[dict],
    ikp_version: str = "v1.x.x",
) -> str:
    """Build a grounded system prompt from retrieved knowledge chunks.

    Args:
        institution_code: The institution code (e.g. "TUT").
        mode: The agent mode key (e.g. "qa_assistant").
        chunks: Retrieved knowledge chunks from Qdrant.
        ikp_version: IKP version string for citation context.

    Returns:
        A complete system prompt ready to pass to the AI provider.
    """
    focus = _MODE_FOCUS.get(mode, _MODE_FOCUS["qa_assistant"])
    mode_label = AGENT_MODE_LABELS.get(mode, "QA Assistant")

    if chunks:
        chunk_parts: list[str] = []
        for i, chunk in enumerate(chunks, start=1):
            title = chunk.get("title") or chunk.get("entity_id") or "—"
            entity_type = chunk.get("entity_type", "unknown")
            text = chunk.get("text", "")[:500]
            source_doc = chunk.get("source_document") or "IKP"
            chunk_parts.append(
                f"{i}. [{entity_type.upper()}] {title}\n{text}\n(Source: {source_doc})"
            )
        knowledge_block = "\n\n".join(chunk_parts)
        no_context_note = ""
    else:
        knowledge_block = "(No knowledge chunks retrieved for this query.)"
        no_context_note = (
            "\nThe knowledge base returned no results for this query. "
            "State clearly that no relevant information was found and suggest "
            "the user check the IKP indexing status or rephrase the question."
        )

    return (
        f"You are AQAA — the Academic Quality Assurance Agent for {institution_code.upper()}.\n"
        f"Current mode: {mode_label}\n\n"
        f"{focus}\n\n"
        "CORE RULES:\n"
        "1. Base all answers strictly on the INSTITUTIONAL KNOWLEDGE provided below.\n"
        "2. Cite specific sources: programme names, module codes, document titles.\n"
        "3. Never invent facts about programmes, modules, or policies not in the knowledge base.\n"
        f"4. If asked about another institution, state you can only answer for {institution_code.upper()}.\n"
        "5. When information is absent, say so clearly and suggest next steps.\n"
        "6. Provide actionable QA recommendations where appropriate.\n"
        "7. Be professional, concise, and specific to academic quality assurance.\n"
        "8. Do not refuse to help with legitimate QA queries.\n\n"
        f"INSTITUTIONAL KNOWLEDGE BASE ({institution_code.upper()}, {ikp_version}):\n"
        f"{knowledge_block}"
        f"{no_context_note}"
    )


# ---------------------------------------------------------------------------
# Audit summary templates
# ---------------------------------------------------------------------------

AUDIT_SUMMARY_TEMPLATE = (
    "**Module:** {module_name}\n"
    "**Compliance:** {compliance_pct}%  |  **Risk Level:** {risk_level}\n"
    "**Status:** {audit_status}\n\n"
    "**Key findings:**\n"
    "{findings_block}\n\n"
    "**Recommendations:**\n"
    "{recommendations_block}"
)
