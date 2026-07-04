import { apiClient } from "@/lib/api-client";
import type { Module, ModuleCreate, ModuleUpdate } from "@/types";

export interface ListModulesParams {
  programme_id?: string;
  academic_year?: string;
}

export async function listModules(params?: ListModulesParams): Promise<Module[]> {
  const { data } = await apiClient.get<Module[]>("/modules", {
    params: {
      ...(params?.programme_id ? { programme_id: params.programme_id } : {}),
      ...(params?.academic_year ? { academic_year: params.academic_year } : {}),
    },
  });
  return data;
}

export async function getModule(id: string): Promise<Module> {
  const { data } = await apiClient.get<Module>(`/modules/${id}`);
  return data;
}

export async function createModule(payload: ModuleCreate): Promise<Module> {
  const { data } = await apiClient.post<Module>("/modules", payload);
  return data;
}

export async function updateModule(id: string, payload: ModuleUpdate): Promise<Module> {
  const { data } = await apiClient.patch<Module>(`/modules/${id}`, payload);
  return data;
}

export async function deleteModule(id: string): Promise<void> {
  await apiClient.delete(`/modules/${id}`);
}
