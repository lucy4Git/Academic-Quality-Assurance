import { apiClient } from "@/lib/api-client";

export interface ProvenanceBreakdown {
  public_verified: number;
  needs_review: number;
  synthetic_demo: number;
  customer_data: number;
}

export interface InstitutionCoverage {
  institution_id: string;
  institution_code: string;
  institution_name: string;
  counts: Record<string, number>;
  provenance: ProvenanceBreakdown;
  ready_for_rag: boolean;
  generated_at: string;
}

export interface KnowledgeOverview {
  institutions: number;
  campuses: number;
  faculties: number;
  schools: number;
  departments: number;
  programmes: number;
  qualifications: number;
  modules: number;
  learning_outcomes: number;
  graduate_attributes: number;
  policies: number;
  institution_documents: number;
  accreditation_bodies: number;
  accreditations: number;
  contacts: number;
  provenance: ProvenanceBreakdown;
}

export interface CampusRead {
  id: string;
  name: string;
  city: string | null;
  province: string | null;
  is_main_campus: boolean;
  is_active: boolean;
  data_status: string;
  is_synthetic: boolean;
  source_url: string | null;
}

export interface ContactRead {
  id: string;
  name: string | null;
  role: string | null;
  email: string | null;
  phone: string | null;
  department: string | null;
  contact_type: string | null;
  is_public: boolean;
  data_status: string;
  is_synthetic: boolean;
}

export interface AccreditationRead {
  id: string;
  body_id: string;
  programme_id: string | null;
  status: string;
  accredited_date: string | null;
  expiry_date: string | null;
  notes: string | null;
  data_status: string;
  is_synthetic: boolean;
}

export interface InstitutionProfile {
  id: string;
  name: string;
  code: string;
  country: string | null;
  province: string | null;
  website: string | null;
  logo_url: string | null;
  data_status: string | null;
  is_demo: boolean;
  campuses: CampusRead[];
  faculties: { id: string; name: string; code: string }[];
  contacts: ContactRead[];
  accreditations: AccreditationRead[];
}

export interface LiveCountsResponse {
  institution_id: string | null;
  campuses: number;
  faculties: number;
  schools: number;
  departments: number;
  programmes: number;
  qualifications: number;
  modules: number;
  learning_outcomes: number;
  graduate_attributes: number;
  policies: number;
  policy_versions: number;
  institution_documents: number;
  accreditation_bodies: number;
  accreditations: number;
  contacts: number;
}

export interface CoverageSummaryResponse {
  institution_id: string | null;
  total_entities: number;
  public_verified_pct: number;
  needs_review_pct: number;
  synthetic_demo_pct: number;
  customer_data_pct: number;
  rag_readiness: "ready" | "partial" | "not_ready";
  crawler_readiness: "ready" | "partial" | "not_ready";
  missing_data_warnings: string[];
}

export interface FullInstitutionProfile {
  id: string;
  name: string;
  code: string;
  country: string | null;
  province: string | null;
  website: string | null;
  logo_url: string | null;
  data_status: string | null;
  is_demo: boolean;
  campuses: CampusRead[];
  faculties: { id: string; name: string; code: string; department_count: number }[];
  policies: {
    id: string;
    title: string;
    policy_type: string | null;
    description: string | null;
    is_active: boolean;
    data_status: string;
    is_synthetic: boolean;
    source_url: string | null;
  }[];
  documents: {
    id: string;
    title: string;
    document_type: string | null;
    description: string | null;
    document_url: string | null;
    publication_year: number | null;
    data_status: string;
    is_synthetic: boolean;
    source_url: string | null;
  }[];
  accreditations: AccreditationRead[];
  contacts: ContactRead[];
  coverage: Record<string, number>;
}

export async function getKnowledgeOverview(): Promise<KnowledgeOverview> {
  const { data } = await apiClient.get<KnowledgeOverview>(
    "/institution-knowledge/overview"
  );
  return data;
}

export async function getInstitutionCoverage(
  institutionId: string
): Promise<InstitutionCoverage> {
  const { data } = await apiClient.get<InstitutionCoverage>(
    `/institution-knowledge/institutions/${institutionId}/coverage`
  );
  return data;
}

export async function getInstitutionKnowledgeProfile(
  institutionId: string
): Promise<InstitutionProfile> {
  const { data } = await apiClient.get<InstitutionProfile>(
    `/institution-knowledge/institutions/${institutionId}/profile`
  );
  return data;
}

export async function getLiveCounts(
  institutionId?: string
): Promise<LiveCountsResponse> {
  const params = institutionId ? `?institution_id=${institutionId}` : "";
  const { data } = await apiClient.get<LiveCountsResponse>(
    `/institution-knowledge/live-counts${params}`
  );
  return data;
}

export async function getCoverageSummary(
  institutionId?: string
): Promise<CoverageSummaryResponse> {
  const params = institutionId ? `?institution_id=${institutionId}` : "";
  const { data } = await apiClient.get<CoverageSummaryResponse>(
    `/institution-knowledge/coverage-summary${params}`
  );
  return data;
}

export async function getFullInstitutionProfile(
  institutionId: string
): Promise<FullInstitutionProfile> {
  const { data } = await apiClient.get<FullInstitutionProfile>(
    `/institution-knowledge/institutions/${institutionId}/full-profile`
  );
  return data;
}
