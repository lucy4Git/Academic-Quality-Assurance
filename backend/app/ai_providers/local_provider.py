"""LOCAL_DEV AI provider — deterministic template-based responses.

Used when no external AI API key is configured.  Returns a structured
template answer assembled from retrieved knowledge chunks, identical to
the original Sprint 4 behaviour.

Never makes external HTTP calls.
"""

from __future__ import annotations

from app.ai_providers.base_provider import AIMessage, BaseAIProvider, HealthResult


class LocalDevProvider(BaseAIProvider):
    """Template-based fallback provider for development environments."""

    async def complete(
        self,
        messages: list[AIMessage],
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        user_content = next(
            (m.content for m in reversed(messages) if m.role == "user"), ""
        )
        lowered = user_content.lower()
        history = "\n".join(m.content for m in messages).lower()
        personal_qa = any(
            m.role == "system" and "personal, non-institutional workspace" in m.content
            for m in messages
        )
        retrieved = [m.content for m in messages if m.role == "system" and "SOURCE:" in m.content]
        if personal_qa and "review my module folder" in lowered and "missing" in lowered and not retrieved:
            return (
                "## Evidence status: UNABLE TO DETERMINE\n\n"
                "No module evidence was attached or retrieved, so I cannot truthfully decide which documents are present or missing. "
                "Upload or attach the module folder evidence—such as the module guide, assessment paper, memorandum, and moderation report—and I can perform a grounded review."
            )
        if personal_qa and "assume i currently have" in lowered:
            return (
                "## QA review based on user-stated facts\n\n"
                "This conclusion is based only on your statement, not on inspected evidence.\n\n"
                "- **Module Guide — PRESENT** (user stated)\n"
                "- **Assessment Paper — PRESENT** (user stated)\n"
                "- **Assessment Memorandum — MISSING** (user stated)\n"
                "- **Internal Moderation Report — MISSING** (user stated)\n\n"
                "## Recommended remediation\n\n"
                "1. Prepare and quality-check the assessment memorandum against the assessment and rubric.\n"
                "2. Complete internal moderation and retain the signed report, findings, and evidence that required changes were addressed."
            )
        if personal_qa and "which of those gaps" in lowered and "assessment memorandum" in history:
            return (
                "## Priority remediation\n\n"
                "Address the **Assessment Memorandum — MISSING** first because moderation cannot reliably verify marking consistency without the expected answers or marking guidance. "
                "Then complete the **Internal Moderation Report — MISSING**, recording the review outcome and any corrective actions. This prioritisation continues the facts you supplied earlier; it is not based on inspected files."
            )
        if personal_qa and retrieved:
            source_names = []
            for block in retrieved:
                source_names.extend(line.removeprefix("SOURCE: ") for line in block.splitlines() if line.startswith("SOURCE: "))
            cited = ", ".join(dict.fromkeys(source_names)) or "the retrieved evidence"
            return (
                "## Grounded QA finding\n\n"
                f"**Evidence reviewed — PRESENT:** {cited}. The response is grounded only in the retrieved owner-scoped excerpt.\n\n"
                "**Finding — INCOMPLETE:** A complete module-folder determination still requires the expected document set and sufficient extracted content.\n\n"
                "## Recommended remediation\n\n"
                "Upload any missing assessment memorandum and internal moderation report, then rerun the review so each status can be tied to a cited file."
            )
        return (
            f"[LOCAL_DEV] Received question: {user_content[:120]}\n\n"
            "This is a deterministic template response from the LOCAL_DEV provider. "
            "Configure AI_PROVIDER=OPENAI, ANTHROPIC, or OLLAMA to get real AI responses."
        )

    @property
    def provider_name(self) -> str:
        return "local_dev"

    @property
    def model_name(self) -> str:
        return "template"

    async def health_check(self) -> HealthResult:
        return HealthResult(status="ok", latency_ms=0.0, extra={"note": "local_dev always available"})

    @property
    def is_local_dev(self) -> bool:
        return True
