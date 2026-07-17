import type { UUID } from "crypto";

export interface ExtractionRun {
  id: string;
  document_id: string;
  institution_id: string;
  status: "pending" | "running" | "completed" | "needs_review" | "failed";
  document_type: string | null;
  classification_confidence: number | null;
  classification_reason: string | null;
  improved_title: string | null;
  title_source: string | null;
  word_count: number | null;
  extraction_quality: "good" | "partial" | "poor" | null;
  candidates_count: number;
  error_message: string | null;
  created_at: string;
}

export interface ExtractionCandidate {
  id: string;
  run_id: string;
  document_id: string;
  institution_id: string;
  entity_type: string;
  extracted_value: string;
  normalized_value: string | null;
  confidence: number;
  source_snippet: string | null;
  extraction_method: string | null;
  proposed_entity_id: string | null;
  proposed_entity_type: string | null;
  proposed_entity_name: string | null;
  match_method: string | null;
  mapping_status: "auto_mapped" | "needs_review" | "approved" | "rejected";
  reviewed_by_id: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  data_status: string;
  is_synthetic: boolean;
  created_at: string;
}

export interface ExtractionStatistics {
  total_runs: number;
  completed_runs: number;
  failed_runs: number;
  needs_review_runs: number;
  total_candidates: number;
  auto_mapped: number;
  needs_review: number;
  approved: number;
  rejected: number;
  institution_id: string | null;
}

export interface CandidateReviewPayload {
  review_notes?: string;
  proposed_entity_id?: string;
  proposed_entity_type?: string;
  proposed_entity_name?: string;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api/proxy/${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? res.statusText);
  }
  return res.json();
}

export const extractionApi = {
  getStatistics: (institutionId?: string) => {
    const params = institutionId ? `?institution_id=${institutionId}` : "";
    return apiFetch<ExtractionStatistics>(`extraction/statistics${params}`);
  },

  getRuns: (params?: { institution_id?: string; document_id?: string; status?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.institution_id) q.set("institution_id", params.institution_id);
    if (params?.document_id) q.set("document_id", params.document_id);
    if (params?.status) q.set("status", params.status);
    if (params?.limit) q.set("limit", String(params.limit));
    const qs = q.toString();
    return apiFetch<ExtractionRun[]>(`extraction/runs${qs ? `?${qs}` : ""}`);
  },

  triggerRun: (documentId: string) =>
    apiFetch<ExtractionRun>(`extraction/run/${documentId}`, { method: "POST", body: "{}" }),

  getRun: (runId: string) => apiFetch<ExtractionRun>(`extraction/runs/${runId}`),

  getCandidates: (params?: { institution_id?: string; run_id?: string; document_id?: string; mapping_status?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.institution_id) q.set("institution_id", params.institution_id);
    if (params?.run_id) q.set("run_id", params.run_id);
    if (params?.document_id) q.set("document_id", params.document_id);
    if (params?.mapping_status) q.set("mapping_status", params.mapping_status);
    if (params?.limit) q.set("limit", String(params.limit));
    const qs = q.toString();
    return apiFetch<ExtractionCandidate[]>(`extraction/candidates${qs ? `?${qs}` : ""}`);
  },

  getReviewQueue: (institutionId?: string) => {
    const params = institutionId ? `?institution_id=${institutionId}` : "";
    return apiFetch<ExtractionCandidate[]>(`extraction/review-queue${params}`);
  },

  approveCandidate: (candidateId: string, payload: CandidateReviewPayload) =>
    apiFetch<ExtractionCandidate>(`extraction/candidates/${candidateId}/approve`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  rejectCandidate: (candidateId: string, payload: CandidateReviewPayload) =>
    apiFetch<ExtractionCandidate>(`extraction/candidates/${candidateId}/reject`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  mapCandidate: (candidateId: string, payload: CandidateReviewPayload) =>
    apiFetch<ExtractionCandidate>(`extraction/candidates/${candidateId}/map`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
