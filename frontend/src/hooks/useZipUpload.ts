"use client";

import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface ClassifiedFile {
  filename: string;
  category: string | null;
  confidence: number;
  size_bytes: number;
  path_in_zip: string;
}

export interface ZipManifest {
  total_files: number;
  classified: ClassifiedFile[];
  unclassified: ClassifiedFile[];
  missing_required: string[];
}

export interface ConfirmMappingPayload {
  module_id: string;
  files: Array<{ path_in_zip: string; category: string }>;
}

export function useZipUpload() {
  return useMutation<ZipManifest, Error, File>({
    mutationFn: async (file) => {
      const form = new FormData();
      form.append("file", file);
      const { data } = await apiClient.post<ZipManifest>("/files/upload-zip", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data;
    },
  });
}

export function useConfirmZipMapping() {
  return useMutation<{ accepted: number }, Error, ConfirmMappingPayload>({
    mutationFn: async (payload) => {
      const { data } = await apiClient.post<{ accepted: number }>(
        "/files/upload-zip/confirm",
        payload
      );
      return data;
    },
  });
}
