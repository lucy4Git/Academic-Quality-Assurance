import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { extractionApi, type CandidateReviewPayload } from "@/lib/api/extraction";

export function useExtractionStatistics(institutionId?: string) {
  return useQuery({
    queryKey: ["extraction-statistics", institutionId],
    queryFn: () => extractionApi.getStatistics(institutionId),
    enabled: !!institutionId,
  });
}

export function useExtractionRuns(params?: { institution_id?: string; document_id?: string; status?: string }) {
  return useQuery({
    queryKey: ["extraction-runs", params],
    queryFn: () => extractionApi.getRuns(params),
    enabled: !!(params?.institution_id || params?.document_id),
    refetchInterval: 5000,
  });
}

export function useExtractionCandidates(params?: { institution_id?: string; run_id?: string; document_id?: string; mapping_status?: string }) {
  return useQuery({
    queryKey: ["extraction-candidates", params],
    queryFn: () => extractionApi.getCandidates(params),
    enabled: !!(params?.institution_id || params?.run_id || params?.document_id),
  });
}

export function useReviewQueue(institutionId?: string) {
  return useQuery({
    queryKey: ["extraction-review-queue", institutionId],
    queryFn: () => extractionApi.getReviewQueue(institutionId),
    enabled: !!institutionId,
  });
}

export function useTriggerExtraction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (documentId: string) => extractionApi.triggerRun(documentId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["extraction-runs"] });
      qc.invalidateQueries({ queryKey: ["extraction-statistics"] });
    },
  });
}

export function useApproveCandidate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ candidateId, payload }: { candidateId: string; payload: CandidateReviewPayload }) =>
      extractionApi.approveCandidate(candidateId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["extraction-candidates"] });
      qc.invalidateQueries({ queryKey: ["extraction-review-queue"] });
      qc.invalidateQueries({ queryKey: ["extraction-statistics"] });
    },
  });
}

export function useRejectCandidate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ candidateId, payload }: { candidateId: string; payload: CandidateReviewPayload }) =>
      extractionApi.rejectCandidate(candidateId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["extraction-candidates"] });
      qc.invalidateQueries({ queryKey: ["extraction-review-queue"] });
      qc.invalidateQueries({ queryKey: ["extraction-statistics"] });
    },
  });
}
