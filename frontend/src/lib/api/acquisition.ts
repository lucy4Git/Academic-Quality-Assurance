import { apiClient, extractErrorMessage } from "@/lib/api-client";

export interface AcquisitionSource {
  id: string;
  institution_id: string;
  source_url: string;
  source_name: string;
  source_type: string;
  description: string | null;
  data_status: string;
  data_confidence: number | null;
  is_active: boolean;
  is_demo: boolean;
  robots_allowed: boolean | null;
  created_at: string;
}

export interface AcquisitionJob {
  id: string;
  institution_id: string;
  status: string;
  documents_downloaded: number;
  errors_count: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface AcquisitionLog {
  id: string;
  job_id: string;
  source_url: string;
  success: boolean;
  status_code: number | null;
  file_type: string | null;
  error_message: string | null;
  robots_blocked: boolean;
  created_at: string;
}

export interface DownloadedDocument {
  id: string;
  institution_id: string;
  source_url: string;
  title: string;
  file_type: string;
  document_type: string;
  data_status: string;
  checksum: string | null;
  is_duplicate: boolean;
  created_at: string;
  // Wave 3 extraction fields
  extraction_status?: string;
  meaningful_title?: string | null;
  title_source?: string | null;
}

export interface AcquisitionStatistics {
  institution_id: string | null;
  total_sources: number;
  active_sources: number;
  total_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  total_documents: number;
  total_errors: number;
  last_job_at: string | null;
}

function instParam(institutionId?: string): Record<string, string> {
  return institutionId ? { institution_id: institutionId } : {};
}

export const acquisitionApi = {
  getSources: async (institutionId?: string): Promise<AcquisitionSource[]> => {
    const res = await apiClient.get<AcquisitionSource[]>("/acquisition/sources", {
      params: instParam(institutionId),
    });
    return res.data;
  },
  getJobs: async (institutionId?: string): Promise<AcquisitionJob[]> => {
    const res = await apiClient.get<AcquisitionJob[]>("/acquisition/jobs", {
      params: instParam(institutionId),
    });
    return res.data;
  },
  getLogs: async (
    institutionId?: string,
    jobId?: string,
  ): Promise<AcquisitionLog[]> => {
    const params: Record<string, string> = { ...instParam(institutionId) };
    if (jobId) params.job_id = jobId;
    const res = await apiClient.get<AcquisitionLog[]>("/acquisition/logs", { params });
    return res.data;
  },
  getDownloads: async (institutionId?: string): Promise<DownloadedDocument[]> => {
    const res = await apiClient.get<DownloadedDocument[]>("/acquisition/downloads", {
      params: instParam(institutionId),
    });
    return res.data;
  },
  getStatistics: async (
    institutionId?: string,
  ): Promise<AcquisitionStatistics> => {
    const res = await apiClient.get<AcquisitionStatistics>(
      "/acquisition/statistics",
      { params: instParam(institutionId) },
    );
    return res.data;
  },
  startJob: async (
    institutionId: string,
    sourceIds?: string[],
  ): Promise<AcquisitionJob> => {
    try {
      const res = await apiClient.post<AcquisitionJob>("/acquisition/jobs/start", {
        institution_id: institutionId,
        source_ids: sourceIds ?? null,
      });
      return res.data;
    } catch (err) {
      throw new Error(extractErrorMessage(err));
    }
  },
  retryJob: async (jobId: string): Promise<AcquisitionJob> => {
    const res = await apiClient.post<AcquisitionJob>(`/acquisition/retry/${jobId}`);
    return res.data;
  },
};
