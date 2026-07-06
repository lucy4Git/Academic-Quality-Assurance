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

export interface StreamChunkEvent {
  type: "chunk";
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

export type StreamEvent =
  | StreamStartEvent
  | StreamChunkEvent
  | StreamSourcesEvent
  | StreamDoneEvent
  | StreamErrorEvent;

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

export interface AskStreamRequest {
  question: string;
  institution_code?: string | null;
  context_limit?: number;
  mode?: string;
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
