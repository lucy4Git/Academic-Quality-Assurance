"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface InstitutionWorkspace {
  institution_code: string;
  institution_name: string;
  institution_type: string;
  faculties: number;
  departments: number;
  programmes: number;
  modules: number;
  total_audits: number;
  completed_audits: number;
  evidence_files: number;
  knowledge_chunks: number;
  active_users: number;
  pending_reviews: number;
}

export interface ModuleWorkspace {
  module_id: string;
  module_code: string;
  module_name: string;
  programme_name: string | null;
  lecturer_name: string | null;
  total_audits: number;
  completed_audits: number;
  evidence_files: number;
  latest_audit_status: string | null;
  latest_audit_agent: string | null;
  latest_audit_date: string | null;
}

export interface TimelineEvent {
  id: string;
  event_type: string;
  title: string;
  description: string;
  actor: string | null;
  entity_type: string | null;
  entity_id: string | null;
  occurred_at: string;
}

export interface MultiAgentContribution {
  agent: string;
  mode: string;
  answer: string;
  confidence: number;
  sources: string[];
}

export interface MultiAgentResponse {
  prompt: string;
  agents_used: string[];
  contributions: MultiAgentContribution[];
  final_answer: string;
  overall_confidence: number;
  suggested_next_actions: string[];
  follow_up_questions: string[];
  is_multi_agent: boolean;
  provider: string;
  model: string;
}

export function useInstitutionWorkspace(institutionCode: string | null) {
  return useQuery<InstitutionWorkspace>({
    queryKey: ["institution-workspace", institutionCode],
    queryFn: async () => {
      const { data } = await apiClient.get<InstitutionWorkspace>(
        `/workspace/institution/${institutionCode}`
      );
      return data;
    },
    enabled: !!institutionCode,
  });
}

export function useModuleWorkspace(moduleId: string | null) {
  return useQuery<ModuleWorkspace>({
    queryKey: ["module-workspace", moduleId],
    queryFn: async () => {
      const { data } = await apiClient.get<ModuleWorkspace>(
        `/workspace/module/${moduleId}`
      );
      return data;
    },
    enabled: !!moduleId,
  });
}

export function useTimeline(limit = 30) {
  return useQuery<TimelineEvent[]>({
    queryKey: ["timeline", limit],
    queryFn: async () => {
      const { data } = await apiClient.get<TimelineEvent[]>(
        `/workspace/timeline?limit=${limit}`
      );
      return data;
    },
    refetchInterval: 60_000,
  });
}

export function useUnreadCount() {
  return useQuery<{ unread: number }>({
    queryKey: ["notifications-unread-count"],
    queryFn: async () => {
      const { data } = await apiClient.get<{ unread: number }>(
        "/notifications/unread-count"
      );
      return data;
    },
    refetchInterval: 30_000,
    staleTime: 10_000,
  });
}

export function useMultiAgent() {
  return useMutation<
    MultiAgentResponse,
    Error,
    { prompt: string; institution_code?: string | null; context_limit?: number; session_id?: string | null }
  >({
    mutationFn: async (payload) => {
      const { data } = await apiClient.post<MultiAgentResponse>(
        "/ai-assistant/multi-agent",
        payload
      );
      return data;
    },
  });
}
