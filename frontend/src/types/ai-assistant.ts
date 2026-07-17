export interface AskRequest {
  question: string;
  institution_code?: string | null;
  context_limit?: number;
  mode?: string;
  session_id?: string | null;
}

export interface SourceChunk {
  entity_type: string;
  entity_key: string;
  title: string;
  text: string;
  source_document: string;
  confidence_score: number;
  relevance_score: number;
}

export interface AskResponse {
  question: string;
  answer: string;
  sources: SourceChunk[];
  confidence_score: number;
  institution_code: string;
  is_placeholder_mode: boolean;
  suggested_followups: string[];
  query_mode: string;
  provider: string;
  model: string;
  mode: string;
  session_id?: string | null;
}

export interface AuditSummaryRequest {
  audit_run_id?: string | null;
  module_id?: string | null;
  institution_code?: string | null;
}

export interface AuditSummaryResponse {
  module_name: string | null;
  compliance_percentage: number | null;
  risk_level: string | null;
  audit_status: string | null;
  key_findings: string[];
  recommendations: string[];
  is_placeholder_mode: boolean;
}

export interface RecommendationRequest {
  module_id?: string | null;
  institution_code?: string | null;
  audit_status?: string | null;
  missing_evidence_types: string[];
}

export interface RecommendationItem {
  priority: "high" | "medium" | "low";
  category: string;
  action: string;
  rationale: string;
}

export interface RecommendationsResponse {
  recommendations: RecommendationItem[];
  is_placeholder_mode: boolean;
}

export interface SuggestedPrompt {
  prompt: string;
  category: string;
}

export interface SuggestedPromptsResponse {
  prompts: SuggestedPrompt[];
  institution_code: string | null;
}

export interface AgentMode {
  mode: string;
  label: string;
}

export interface ChatSessionCreate {
  mode?: string;
  title?: string | null;
  institution_code?: string | null;
}

export interface ChatSessionBrief {
  id: string;
  mode: string;
  title: string | null;
  provider: string | null;
  model_name: string | null;
  is_active: boolean;
  is_pinned: boolean;
  is_archived: boolean;
  created_at: string;
  message_count: number;
}

export interface ChatMessageBrief {
  id: string;
  role: "user" | "assistant";
  content: string;
  confidence_score: number | null;
  provider: string | null;
  query_mode: string | null;
  intent: string | null;
  created_at: string;
  sources?: Array<Record<string, unknown>> | null;
  attached_file_ids?: string[] | null;
  structured_blocks?: Array<Record<string, unknown>> | null;
  citations?: Array<Record<string, unknown>> | null;
}

export interface ChatSessionDetail {
  id: string;
  mode: string;
  title: string | null;
  provider: string | null;
  model_name: string | null;
  is_active: boolean;
  is_pinned: boolean;
  is_archived: boolean;
  created_at: string;
  messages: ChatMessageBrief[];
}
