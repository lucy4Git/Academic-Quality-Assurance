"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { acquisitionApi } from "@/lib/api/acquisition";

export function useAcquisitionStatistics(institutionId?: string) {
  return useQuery({
    queryKey: ["acquisition-statistics", institutionId],
    queryFn: () => acquisitionApi.getStatistics(institutionId),
  });
}

export function useAcquisitionSources(institutionId?: string) {
  return useQuery({
    queryKey: ["acquisition-sources", institutionId],
    queryFn: () => acquisitionApi.getSources(institutionId),
  });
}

export function useAcquisitionJobs(institutionId?: string) {
  return useQuery({
    queryKey: ["acquisition-jobs", institutionId],
    queryFn: () => acquisitionApi.getJobs(institutionId),
    refetchInterval: 5000, // poll every 5s while jobs may be running
  });
}

export function useAcquisitionLogs(institutionId?: string, jobId?: string) {
  return useQuery({
    queryKey: ["acquisition-logs", institutionId, jobId],
    queryFn: () => acquisitionApi.getLogs(institutionId, jobId),
  });
}

export function useAcquisitionDownloads(institutionId?: string) {
  return useQuery({
    queryKey: ["acquisition-downloads", institutionId],
    queryFn: () => acquisitionApi.getDownloads(institutionId),
  });
}

export function useStartAcquisitionJob(institutionId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (sourceIds?: string[]) =>
      acquisitionApi.startJob(institutionId, sourceIds),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["acquisition-jobs"] });
      qc.invalidateQueries({ queryKey: ["acquisition-statistics"] });
    },
  });
}

export function useRetryAcquisitionJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => acquisitionApi.retryJob(jobId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["acquisition-jobs"] });
      qc.invalidateQueries({ queryKey: ["acquisition-statistics"] });
    },
  });
}
