"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type {
  CalculationRequest,
  CalculationResult,
  QualificationRecordBrief,
  QualificationRecordDetail,
} from "@/types/qualification";

export function useCalculate() {
  return useMutation<CalculationResult, Error, CalculationRequest>({
    mutationFn: async (payload) => {
      const { data } = await apiClient.post<CalculationResult>(
        "/qualification-intelligence/calculate",
        payload
      );
      return data;
    },
  });
}

export function useSaveRecord() {
  const qc = useQueryClient();
  return useMutation<QualificationRecordBrief, Error, CalculationRequest>({
    mutationFn: async (payload) => {
      const { data } = await apiClient.post<QualificationRecordBrief>(
        "/qualification-intelligence/records",
        payload
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["qualification-records"] });
    },
  });
}

export function useQualificationRecords() {
  return useQuery<QualificationRecordBrief[]>({
    queryKey: ["qualification-records"],
    queryFn: async () => {
      const { data } = await apiClient.get<QualificationRecordBrief[]>(
        "/qualification-intelligence/records"
      );
      return data;
    },
  });
}

export function useQualificationRecord(id: string | null) {
  return useQuery<QualificationRecordDetail>({
    queryKey: ["qualification-record", id],
    queryFn: async () => {
      const { data } = await apiClient.get<QualificationRecordDetail>(
        `/qualification-intelligence/records/${id}`
      );
      return data;
    },
    enabled: !!id,
  });
}

export function useDeleteQualificationRecord() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (id) => {
      await apiClient.delete(`/qualification-intelligence/records/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["qualification-records"] });
    },
  });
}
