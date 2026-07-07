"use client";

import { useQuery } from "@tanstack/react-query";
import {
  getCoverageSummary,
  getFullInstitutionProfile,
  getInstitutionCoverage,
  getInstitutionKnowledgeProfile,
  getKnowledgeOverview,
  getLiveCounts,
} from "@/lib/api/institutionKnowledge";

export const institutionKnowledgeKeys = {
  all: ["institution-knowledge"] as const,
  overview: () => [...institutionKnowledgeKeys.all, "overview"] as const,
  coverage: (id: string) =>
    [...institutionKnowledgeKeys.all, "coverage", id] as const,
  profile: (id: string) =>
    [...institutionKnowledgeKeys.all, "profile", id] as const,
  liveCounts: (id: string) =>
    [...institutionKnowledgeKeys.all, "live-counts", id] as const,
  coverageSummary: (id: string) =>
    [...institutionKnowledgeKeys.all, "coverage-summary", id] as const,
  fullProfile: (id: string) =>
    [...institutionKnowledgeKeys.all, "full-profile", id] as const,
};

export function useKnowledgeOverview(enabled = true) {
  return useQuery({
    queryKey: institutionKnowledgeKeys.overview(),
    queryFn: getKnowledgeOverview,
    enabled,
    staleTime: 2 * 60 * 1000,
  });
}

export function useInstitutionCoverage(id: string | undefined) {
  return useQuery({
    queryKey: institutionKnowledgeKeys.coverage(id ?? ""),
    queryFn: () => getInstitutionCoverage(id as string),
    enabled: !!id,
    staleTime: 2 * 60 * 1000,
  });
}

export function useInstitutionKnowledgeProfile(id: string | undefined) {
  return useQuery({
    queryKey: institutionKnowledgeKeys.profile(id ?? ""),
    queryFn: () => getInstitutionKnowledgeProfile(id as string),
    enabled: !!id,
    staleTime: 2 * 60 * 1000,
  });
}

export function useInstitutionKnowledgeLiveCounts(institutionId?: string) {
  return useQuery({
    queryKey: institutionKnowledgeKeys.liveCounts(institutionId ?? ""),
    queryFn: () => getLiveCounts(institutionId),
    staleTime: 2 * 60 * 1000,
  });
}

export function useCoverageSummary(institutionId?: string) {
  return useQuery({
    queryKey: institutionKnowledgeKeys.coverageSummary(institutionId ?? ""),
    queryFn: () => getCoverageSummary(institutionId),
    staleTime: 2 * 60 * 1000,
  });
}

export function useFullInstitutionProfile(id: string | undefined) {
  return useQuery({
    queryKey: institutionKnowledgeKeys.fullProfile(id ?? ""),
    queryFn: () => getFullInstitutionProfile(id as string),
    enabled: !!id,
    staleTime: 2 * 60 * 1000,
  });
}
