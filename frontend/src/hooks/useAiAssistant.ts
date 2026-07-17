"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type {
  AgentMode,
  AskRequest,
  AskResponse,
  AuditSummaryRequest,
  AuditSummaryResponse,
  ChatSessionBrief,
  ChatSessionCreate,
  ChatSessionDetail,
  RecommendationRequest,
  RecommendationsResponse,
  SuggestedPromptsResponse,
} from "@/types/ai-assistant";

export function useAsk() {
  return useMutation<AskResponse, Error, AskRequest>({
    mutationFn: async (payload) => {
      const { data } = await apiClient.post<AskResponse>("/ai-assistant/ask", payload);
      return data;
    },
  });
}

export function useAuditSummary() {
  return useMutation<AuditSummaryResponse, Error, AuditSummaryRequest>({
    mutationFn: async (payload) => {
      const { data } = await apiClient.post<AuditSummaryResponse>(
        "/ai-assistant/audit-summary",
        payload
      );
      return data;
    },
  });
}

export function useRecommendations() {
  return useMutation<RecommendationsResponse, Error, RecommendationRequest>({
    mutationFn: async (payload) => {
      const { data } = await apiClient.post<RecommendationsResponse>(
        "/ai-assistant/recommendations",
        payload
      );
      return data;
    },
  });
}

export function useSuggestedPrompts(institutionCode?: string) {
  return useQuery<SuggestedPromptsResponse>({
    queryKey: ["suggested-prompts", institutionCode],
    queryFn: async () => {
      const params = institutionCode
        ? `?institution_code=${encodeURIComponent(institutionCode)}`
        : "";
      const { data } = await apiClient.get<SuggestedPromptsResponse>(
        `/ai-assistant/suggested-prompts${params}`
      );
      return data;
    },
  });
}

export function useAgentModes() {
  return useQuery<AgentMode[]>({
    queryKey: ["agent-modes"],
    queryFn: async () => {
      const { data } = await apiClient.get<AgentMode[]>("/ai-assistant/modes");
      return data;
    },
    staleTime: Infinity,
  });
}

export function useChatSessions() {
  return useQuery<ChatSessionBrief[]>({
    queryKey: ["chat-sessions"],
    queryFn: async () => {
      const { data } = await apiClient.get<ChatSessionBrief[]>("/ai-assistant/sessions");
      return data;
    },
  });
}

export function useChatSession(sessionId: string | null) {
  return useQuery<ChatSessionDetail>({
    queryKey: ["chat-session", sessionId],
    queryFn: async () => {
      const { data } = await apiClient.get<ChatSessionDetail>(
        `/ai-assistant/sessions/${sessionId}`
      );
      return data;
    },
    enabled: !!sessionId,
  });
}

export function useCreateSession() {
  return useMutation<ChatSessionBrief, Error, ChatSessionCreate>({
    mutationFn: async (payload) => {
      const { data } = await apiClient.post<ChatSessionBrief>(
        "/ai-assistant/sessions",
        payload
      );
      return data;
    },
  });
}

export function useDeleteSession() {
  return useMutation<void, Error, string>({
    mutationFn: async (sessionId) => {
      await apiClient.delete(`/ai-assistant/sessions/${sessionId}`);
    },
  });
}

export function usePinSession() {
  return useMutation<ChatSessionBrief, Error, string>({
    mutationFn: async (sessionId) => {
      const { data } = await apiClient.post<ChatSessionBrief>(
        `/ai-assistant/sessions/${sessionId}/pin`
      );
      return data;
    },
  });
}

export function useRenameSession() {
  return useMutation<ChatSessionBrief, Error, { sessionId: string; title: string }>({
    mutationFn: async ({ sessionId, title }) => {
      const { data } = await apiClient.patch<ChatSessionBrief>(
        `/ai-assistant/sessions/${sessionId}/rename`,
        { title }
      );
      return data;
    },
  });
}

export function useArchiveSession() {
  return useMutation<ChatSessionBrief, Error, string>({
    mutationFn: async (sessionId) => {
      const { data } = await apiClient.post<ChatSessionBrief>(
        `/ai-assistant/sessions/${sessionId}/archive`
      );
      return data;
    },
  });
}

export interface AgentRouterResponse {
  intent: string;
  confidence: number;
  agent_mode: string;
  answer: string;
  sources: string[];
  suggested_next_actions: string[];
  follow_up_questions: string[];
}

export function useAgentRouter() {
  return useMutation<AgentRouterResponse, Error, string>({
    mutationFn: async (prompt) => {
      const { data } = await apiClient.post<AgentRouterResponse>("/ai-assistant/route", {
        prompt,
      });
      return data;
    },
  });
}
