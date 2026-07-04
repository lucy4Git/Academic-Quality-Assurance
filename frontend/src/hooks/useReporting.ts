"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type {
  ComplianceSummaryResponse,
  DashboardResponse,
  FacultySummaryResponse,
  ModuleSummaryResponse,
  ProgrammeSummaryResponse,
} from "@/types/reporting";

export function useDashboard() {
  return useQuery<DashboardResponse>({
    queryKey: ["reporting", "dashboard"],
    queryFn: async () => {
      const { data } = await apiClient.get<DashboardResponse>(
        "/reporting/dashboard"
      );
      return data;
    },
  });
}

export function useFacultySummary(facultyId: string | null) {
  return useQuery<FacultySummaryResponse>({
    queryKey: ["reporting", "faculty", facultyId],
    queryFn: async () => {
      const { data } = await apiClient.get<FacultySummaryResponse>(
        `/reporting/faculty-summary?faculty_id=${facultyId}`
      );
      return data;
    },
    enabled: !!facultyId,
  });
}

export function useProgrammeSummary(programmeId: string | null) {
  return useQuery<ProgrammeSummaryResponse>({
    queryKey: ["reporting", "programme", programmeId],
    queryFn: async () => {
      const { data } = await apiClient.get<ProgrammeSummaryResponse>(
        `/reporting/programme-summary?programme_id=${programmeId}`
      );
      return data;
    },
    enabled: !!programmeId,
  });
}

export function useModuleSummary(moduleId: string | null) {
  return useQuery<ModuleSummaryResponse>({
    queryKey: ["reporting", "module", moduleId],
    queryFn: async () => {
      const { data } = await apiClient.get<ModuleSummaryResponse>(
        `/reporting/module-summary?module_id=${moduleId}`
      );
      return data;
    },
    enabled: !!moduleId,
  });
}

export function useComplianceSummary(institutionId?: string | null) {
  return useQuery<ComplianceSummaryResponse>({
    queryKey: ["reporting", "compliance", institutionId],
    queryFn: async () => {
      const params = institutionId
        ? `?institution_id=${institutionId}`
        : "";
      const { data } = await apiClient.get<ComplianceSummaryResponse>(
        `/reporting/compliance-summary${params}`
      );
      return data;
    },
  });
}
