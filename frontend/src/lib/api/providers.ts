import { apiClient } from "@/lib/api-client";

export interface ProviderHealthEntry {
  status: "ok" | "error" | "not_configured" | "unavailable" | "not_implemented";
  latency_ms: number;
  error?: string;
  note?: string;
  model_available?: boolean;
  available_models?: string[];
}

export interface ProvidersHealthResponse {
  overall: "healthy" | "degraded";
  providers: Record<string, ProviderHealthEntry>;
}

export interface ProviderStatusResponse {
  active_provider: string;
  active_model: string;
  configured_provider: string;
  fallback_chain: string[];
  temperature: number;
  max_tokens: number;
}

export async function getProvidersHealth(): Promise<ProvidersHealthResponse> {
  const { data } = await apiClient.get<ProvidersHealthResponse>("/providers/health");
  return data;
}

export async function getProviderStatus(): Promise<ProviderStatusResponse> {
  const { data } = await apiClient.get<ProviderStatusResponse>("/providers/status");
  return data;
}
