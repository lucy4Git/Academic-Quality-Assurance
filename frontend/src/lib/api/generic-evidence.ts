const PROXY = "/api/proxy";

export interface PersonalWorkspace {
  id: string;
  module_name: string;
  module_code: string | null;
  academic_period: string | null;
}

export interface GenericFile {
  id: string;
  owner_user_id: string;
  workspace_module_id: string | null;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  category: string;
  upload_state: string;
  description: string | null;
  is_library_item: boolean;
  created_at: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${PROXY}${path}`, { credentials: "include", ...init });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail || "The evidence request could not be completed.");
  }
  return response.status === 204 ? undefined as T : response.json() as Promise<T>;
}

export const genericEvidenceApi = {
  listWorkspaces: () => request<PersonalWorkspace[]>("/personal-workspaces"),
  createWorkspace: (body: { module_name: string; module_code?: string }) =>
    request<PersonalWorkspace>("/personal-workspaces", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    }),
  listFiles: (libraryOnly: boolean) => request<GenericFile[]>(`/files?library_only=${libraryOnly}`),
  upload: (body: { file: File; workspaceId: string; category: string; description: string; library: boolean }) => {
    const form = new FormData();
    form.append("file", body.file);
    form.append("workspace_module_id", body.workspaceId);
    form.append("category", body.category);
    form.append("description", body.description);
    form.append("is_library_item", String(body.library));
    return request<GenericFile>("/files/upload", { method: "POST", body: form });
  },
  remove: (id: string) => request<void>(`/files/${id}`, { method: "DELETE" }),
  setLibrary: (id: string, value: boolean) => request<GenericFile>(`/files/${id}`, {
    method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ is_library_item: value }),
  }),
  downloadUrl: (id: string) => `${PROXY}/files/${id}/download`,
};
