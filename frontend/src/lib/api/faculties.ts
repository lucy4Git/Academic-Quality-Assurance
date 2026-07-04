import { apiClient } from "@/lib/api-client";
import type { Faculty, FacultyCreate, FacultyUpdate } from "@/types";

export async function listFaculties(
  institutionId?: string
): Promise<Faculty[]> {
  const params = institutionId ? { institution_id: institutionId } : undefined;
  const { data } = await apiClient.get<Faculty[]>("/faculties", { params });
  return data;
}

export async function getFaculty(id: string): Promise<Faculty> {
  const { data } = await apiClient.get<Faculty>(`/faculties/${id}`);
  return data;
}

export async function createFaculty(
  payload: FacultyCreate
): Promise<Faculty> {
  const { data } = await apiClient.post<Faculty>("/faculties", payload);
  return data;
}

export async function updateFaculty(
  id: string,
  payload: FacultyUpdate
): Promise<Faculty> {
  const { data } = await apiClient.patch<Faculty>(
    `/faculties/${id}`,
    payload
  );
  return data;
}

export async function deleteFaculty(id: string): Promise<void> {
  await apiClient.delete(`/faculties/${id}`);
}
