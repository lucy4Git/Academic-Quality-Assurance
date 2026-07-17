/**
 * AI Assistant API — streaming and non-streaming helpers.
 *
 * All calls go through the Next.js API proxy at /api/proxy/{path},
 * which reads the httpOnly access_token cookie server-side and forwards
 * it as a Bearer header to FastAPI. Never call FastAPI directly from browser JS.
 */

const PROXY = "/api/proxy";

// ---------------------------------------------------------------------------
// SSE event shapes from POST /ai-assistant/ask-stream
// ---------------------------------------------------------------------------

export interface StreamStartEvent {
  type: "start";
  intent: string;
  agents: string[];
  confidence: number;
  routing_reason: string;
  used_llm: boolean;
}

/** @deprecated Use StreamTokenEvent. Kept for backward compatibility with older SSE consumers. */
export interface StreamChunkEvent {
  type: "chunk";
  content: string;
}

/** Incremental answer text — replaces StreamChunkEvent in the Advanced RAG pipeline. */
export interface StreamTokenEvent {
  type: "token";
  content: string;
}

export interface StreamSourcesEvent {
  type: "sources";
  sources: StreamSource[];
  confidence_score: number;
  suggested_followups: string[];
  suggested_next_actions: string[];
  follow_up_questions: string[];
}

export interface Citation {
  source_id: string;
  title: string;
  entity_type: string;
  snippet: string;
  relevance_score: number;
  source_document: string;
}

/** Advanced RAG citation metadata — emitted after the sources event. */
export interface StreamMetadataEvent {
  type: "metadata";
  citations: Citation[];
  unsupported_claims: string[];
  grounding_status: "grounded" | "partially_grounded" | "no_source_found";
}

export interface StreamDoneEvent {
  type: "done";
  provider: string;
  model: string;
  query_mode: string;
  is_placeholder_mode: boolean;
}

export interface StreamErrorEvent {
  type: "error";
  message: string;
}

/** D1 — Resolved context emitted before any response tokens. */
export interface StreamContextEvent {
  type: "context";
  institution_code: string;
  institution_name: string;
  faculty_name: string;
  department_name: string;
  programme_name: string;
  programme_code: string;
  module_name: string;
  module_code: string;
  module_id: string | null;
  programme_id: string | null;
  academic_year: string;
  semester: string;
  applicable_framework_codes: string[];
  open_finding_count: number;
  confidence: number;
  resolution_source: string;
  requires_clarification: boolean;
  clarification_question: string;
  indicator: Record<string, string>;
}

/** D2 — Execution plan emitted after context resolution. */
export interface StreamPlanEvent {
  type: "plan";
  intent: string;
  confidence: number;
  services_active: number;
  is_regulatory: boolean;
  requires_confirmation: boolean;
  requires_human_review: boolean;
  permission_denied: boolean;
  permission_reason: string;
  expected_artifact: string;
  context: StreamContextEvent;
}

/** D5 — Structured response blocks. */
export interface StructuredBlock {
  type: "applicable_frameworks" | "findings_summary" | "caveat" | "sources" | string;
  frameworks?: string[];
  count?: number;
  findings?: Array<{
    id: string;
    severity: string;
    status: string;
    finding_type: string;
    title: string;
    description: string;
  }>;
  text?: string;
  sources?: unknown[];
}

export interface StreamStructuredEvent {
  type: "structured";
  blocks: StructuredBlock[];
  execution_summary: string;
  requires_human_review: boolean;
  human_review_reason: string;
}

export interface RegulatoryCitationItem {
  framework_code: string;
  framework_name: string;
  version_number: string;
  standard_code: string | null;
  criterion_code: string | null;
  source_url: string | null;
  is_test_fixture: boolean;
}

/** Regulatory orchestration metadata — emitted for regulatory-mode queries. */
export interface StreamRegulatoryEvent {
  type: "regulatory";
  citations: RegulatoryCitationItem[];
  effective_frameworks: string[];
  requires_human_review: boolean;
  generation_mode: "LLM" | "DETERMINISTIC_TEMPLATE" | "HYBRID" | "MANUAL_REVIEW_REQUIRED";
  caveat: string | null;
  suggested_next_actions: string[];
  follow_up_questions: string[];
}

/** Session persistence event — emitted after the stream completes. */
export interface StreamSessionEvent {
  type: "session";
  session_id: string;
}

export type StreamEvent =
  | StreamContextEvent
  | StreamPlanEvent
  | StreamStructuredEvent
  | StreamStartEvent
  | StreamChunkEvent
  | StreamTokenEvent
  | StreamSourcesEvent
  | StreamMetadataEvent
  | StreamDoneEvent
  | StreamErrorEvent
  | StreamRegulatoryEvent
  | StreamSessionEvent;

export interface StreamSource {
  entity_type?: string;
  entity_key?: string;
  title?: string;
  text?: string;
  source_document?: string;
  confidence_score?: number;
  relevance_score?: number;
}

// ---------------------------------------------------------------------------
// Streaming ask
// ---------------------------------------------------------------------------

export interface WorkspaceContextHint {
  institution_id?: string;
  faculty_id?: string;
  department_id?: string;
  programme_id?: string;
  module_id?: string;
  academic_year?: string;
  semester?: string;
}

export interface AskStreamRequest {
  question: string;
  institution_code?: string | null;
  context_limit?: number;
  mode?: string;
  workspace_context?: WorkspaceContextHint | null;
  attached_file_ids?: string[];
}

/**
 * POST /ai-assistant/ask-stream
 *
 * Calls the SSE streaming endpoint and yields parsed StreamEvent objects.
 * Uses fetch + ReadableStream (not EventSource, which doesn't support POST).
 *
 * @param body    Request body
 * @param signal  Optional AbortSignal for cancellation
 */
export async function* askStream(
  body: AskStreamRequest,
  signal?: AbortSignal,
): AsyncGenerator<StreamEvent> {
  const res = await fetch(`${PROXY}/ai-assistant/ask-stream`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question: body.question,
      institution_code: body.institution_code ?? null,
      context_limit: body.context_limit ?? 5,
      mode: body.mode ?? "qa_assistant",
      workspace_context: body.workspace_context ?? null,
      attached_file_ids: body.attached_file_ids ?? [],
    }),
    signal,
  });

  if (!res.ok) {
    throw new Error(`ask-stream: HTTP ${res.status}`);
  }

  if (!res.body) {
    throw new Error("ask-stream: response body is null");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE lines: "data: {...}\n\n"
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? ""; // keep incomplete last line in buffer

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data: ")) continue;
        try {
          const event = JSON.parse(trimmed.slice("data: ".length)) as StreamEvent;
          yield event;
        } catch {
          // malformed line — skip silently
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
