import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  assignFinding,
  getFinding,
  getFindingHistory,
  listFindings,
  transitionFinding,
  type ListFindingsParams,
} from "@/lib/api/findings";

export function useFindings(params: ListFindingsParams = {}) {
  return useQuery({
    queryKey: ["findings", params],
    queryFn: () => listFindings(params),
  });
}

export function useFinding(id: string | null) {
  return useQuery({
    queryKey: ["finding", id],
    queryFn: () => getFinding(id!),
    enabled: id != null,
  });
}

export function useFindingHistory(id: string | null) {
  return useQuery({
    queryKey: ["finding-history", id],
    queryFn: () => getFindingHistory(id!),
    enabled: id != null,
  });
}

export function useFindingTransition() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, action, note }: { id: string; action: string; note?: string }) =>
      transitionFinding(id, action, note),
    onSuccess: (updated) => {
      qc.invalidateQueries({ queryKey: ["findings"] });
      qc.invalidateQueries({ queryKey: ["finding", updated.id] });
      qc.invalidateQueries({ queryKey: ["finding-history", updated.id] });
    },
  });
}

export function useFindingAssign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      assignee_id,
      due_date,
    }: {
      id: string;
      assignee_id: string;
      due_date?: string;
    }) => assignFinding(id, assignee_id, due_date),
    onSuccess: (updated) => {
      qc.invalidateQueries({ queryKey: ["findings"] });
      qc.invalidateQueries({ queryKey: ["finding", updated.id] });
    },
  });
}
