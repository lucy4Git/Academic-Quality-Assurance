import { apiClient } from "@/lib/api-client";
import type { Department, DepartmentCreate, DepartmentUpdate } from "@/types";

export async function listDepartments(facultyId?: string): Promise<Department[]> {
  const params = facultyId ? { faculty_id: facultyId } : undefined;
  const { data } = await apiClient.get<Department[]>("/departments", { params });
  return data;
}

export async function getDepartment(id: string): Promise<Department> {
  const { data } = await apiClient.get<Department>(`/departments/${id}`);
  return data;
}

export async function createDepartment(payload: DepartmentCreate): Promise<Department> {
  const { data } = await apiClient.post<Department>("/departments", payload);
  return data;
}

export async function updateDepartment(
  id: string,
  payload: DepartmentUpdate
): Promise<Department> {
  const { data } = await apiClient.patch<Department>(`/departments/${id}`, payload);
  return data;
}

export async function deleteDepartment(id: string): Promise<void> {
  await apiClient.delete(`/departments/${id}`);
}
