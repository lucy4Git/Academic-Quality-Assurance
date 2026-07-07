"use client";

import { useQuery } from "@tanstack/react-query";
import {
  getInstitutionCoverage,
  getInstitutionKnowledgeProfile,
  getKnowledgeOverview,
} from "@/lib/api/institutionKnowledge";

export const institutionKnowledgeKeys = {
  all: ["institution-knowledge"] as const,
  overview: () => [...institutionKnowledgeKeys.all, "overview"] as const,
  coverage: (id: string) =>
    [...institutionKnowledgeKeys.all, "coverage", id] as const,
  profile: (id: string) =>
    [...institutionKnowledgeKeys.all, "profile", id] as const,
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
