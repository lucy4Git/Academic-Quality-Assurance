import { apiClient } from "@/lib/api-client";
import type { Institution, InstitutionCreate, InstitutionStats, InstitutionUpdate } from "@/types";

export async function listInstitutions(includeArchived = false): Promise<Institution[]> {
  const params = includeArchived ? "?include_archived=true" : "";
  const { data } = await apiClient.get<Institution[]>(`/institutions${params}`);
  return data;
}

export async function getInstitution(id: string): Promise<Institution> {
  const { data } = await apiClient.get<Institution>(`/institutions/${id}`);
  return data;
}

export async function createInstitution(
  payload: InstitutionCreate
): Promise<Institution> {
  const { data } = await apiClient.post<Institution>("/institutions", payload);
  return data;
}

export async function updateInstitution(
  id: string,
  payload: InstitutionUpdate
): Promise<Institution> {
  const { data } = await apiClient.patch<Institution>(
    `/institutions/${id}`,
    payload
  );
  return data;
}

export async function deleteInstitution(id: string): Promise<void> {
  await apiClient.delete(`/institutions/${id}`);
}

export async function getInstitutionStats(id: string): Promise<InstitutionStats> {
  const { data } = await apiClient.get<InstitutionStats>(`/institutions/${id}/stats`);
  return data;
}
