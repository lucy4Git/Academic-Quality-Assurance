import { apiClient } from "@/lib/api-client";
import type { Programme, ProgrammeCreate, ProgrammeUpdate } from "@/types";

export async function listProgrammes(departmentId?: string): Promise<Programme[]> {
  const params = departmentId ? { department_id: departmentId } : undefined;
  const { data } = await apiClient.get<Programme[]>("/programmes", { params });
  return data;
}

export async function getProgramme(id: string): Promise<Programme> {
  const { data } = await apiClient.get<Programme>(`/programmes/${id}`);
  return data;
}

export async function createProgramme(payload: ProgrammeCreate): Promise<Programme> {
  const { data } = await apiClient.post<Programme>("/programmes", payload);
  return data;
}

export async function updateProgramme(
  id: string,
  payload: ProgrammeUpdate
): Promise<Programme> {
  const { data } = await apiClient.patch<Programme>(`/programmes/${id}`, payload);
  return data;
}

export async function deleteProgramme(id: string): Promise<void> {
  await apiClient.delete(`/programmes/${id}`);
}
