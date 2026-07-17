/**
 * Regulatory Framework Engine API client — Phase C
 */

const BASE = "/api/proxy";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface RegulatoryAuthority {
  id: string;
  code: string;
  name: string;
  short_name: string | null;
  authority_type: string;
  jurisdiction: string | null;
  country: string | null;
  description: string | null;
  official_website: string | null;
  is_external: boolean;
  is_internal: boolean;
  is_active: boolean;
  is_test_fixture: boolean;
  status: string;
  source_status: string;
  institution_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface FrameworkVersionBrief {
  id: string;
  framework_id: string;
  version_number: string;
  version_label: string | null;
  status: string;
  source_status: string;
  effective_from: string | null;
  effective_to: string | null;
}

export interface QualityFramework {
  id: string;
  code: string;
  name: string;
  description: string | null;
  framework_type: string;
  scope: string;
  jurisdiction: string | null;
  is_mandatory: boolean;
  is_public: boolean;
  is_active: boolean;
  is_test_fixture: boolean;
  source_status: string;
  authority_id: string;
  institution_id: string | null;
  versions: FrameworkVersionBrief[];
  created_at: string;
  updated_at: string;
}

export interface FrameworkAssessmentRunBrief {
  id: string;
  framework_version_id: string;
  target_entity_type: string;
  target_entity_id: string;
  status: string;
  overall_score: number | null;
  mandatory_compliance_score: number | null;
  risk_level: string | null;
  readiness_status: string | null;
  criteria_total: number | null;
  criteria_met: number | null;
  mandatory_failures: number | null;
  created_at: string;
}

export interface CriterionAssessmentResult {
  id: string;
  criterion_id: string;
  evidence_requirement_id: string | null;
  evidence_found: number;
  evidence_missing: number;
  deterministic_result: boolean | null;
  is_met: boolean;
  is_mandatory: boolean;
  score: number | null;
  severity: string | null;
  citation_reference: string | null;
  explanation: string | null;
  recommendation: string | null;
  finding_id: string | null;
}

export interface FrameworkAssessmentRunRead extends FrameworkAssessmentRunBrief {
  institution_id: string;
  assessment_scope: string | null;
  assessment_period: string | null;
  evidence_coverage_score: number | null;
  quality_score: number | null;
  summary: string | null;
  error_message: string | null;
  criteria_unmet: number | null;
  updated_at: string;
  criterion_results: CriterionAssessmentResult[];
}

// ---------------------------------------------------------------------------
// Regulatory Authorities
// ---------------------------------------------------------------------------

export async function listAuthorities(params?: {
  institution_id?: string;
  include_global?: boolean;
  active_only?: boolean;
}): Promise<RegulatoryAuthority[]> {
  const q = new URLSearchParams();
  if (params?.institution_id) q.set("institution_id", params.institution_id);
  if (params?.include_global !== undefined) q.set("include_global", String(params.include_global));
  if (params?.active_only !== undefined) q.set("active_only", String(params.active_only));
  const res = await fetch(`${BASE}/regulatory-authorities?${q}`);
  if (!res.ok) throw new Error("Failed to load regulatory authorities");
  return res.json();
}

// ---------------------------------------------------------------------------
// Quality Frameworks
// ---------------------------------------------------------------------------

export async function listFrameworks(params?: {
  institution_id?: string;
  include_global?: boolean;
  active_only?: boolean;
}): Promise<QualityFramework[]> {
  const q = new URLSearchParams();
  if (params?.institution_id) q.set("institution_id", params.institution_id);
  if (params?.include_global !== undefined) q.set("include_global", String(params.include_global));
  if (params?.active_only !== undefined) q.set("active_only", String(params.active_only));
  const res = await fetch(`${BASE}/quality-frameworks?${q}`);
  if (!res.ok) throw new Error("Failed to load quality frameworks");
  return res.json();
}

export async function getFramework(id: string): Promise<QualityFramework> {
  const res = await fetch(`${BASE}/quality-frameworks/${id}`);
  if (!res.ok) throw new Error("Failed to load framework");
  return res.json();
}

// ---------------------------------------------------------------------------
// Framework Assessments
// ---------------------------------------------------------------------------

export async function listAssessments(
  institution_id: string,
  params?: { framework_version_id?: string; target_entity_id?: string }
): Promise<FrameworkAssessmentRunBrief[]> {
  const q = new URLSearchParams({ institution_id });
  if (params?.framework_version_id) q.set("framework_version_id", params.framework_version_id);
  if (params?.target_entity_id) q.set("target_entity_id", params.target_entity_id);
  const res = await fetch(`${BASE}/framework-assessments?${q}`);
  if (!res.ok) throw new Error("Failed to load assessments");
  return res.json();
}

export async function runAssessment(
  institution_id: string,
  payload: {
    framework_version_id: string;
    target_entity_type: string;
    target_entity_id: string;
    assessment_scope?: string;
    assessment_period?: string;
  }
): Promise<FrameworkAssessmentRunRead> {
  const res = await fetch(`${BASE}/framework-assessments?institution_id=${institution_id}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to run assessment");
  return res.json();
}

export async function getAssessment(
  run_id: string,
  institution_id: string
): Promise<FrameworkAssessmentRunRead> {
  const res = await fetch(
    `${BASE}/framework-assessments/${run_id}?institution_id=${institution_id}`
  );
  if (!res.ok) throw new Error("Failed to load assessment");
  return res.json();
}
