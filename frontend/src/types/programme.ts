import type { ProgrammeLevel } from "./enums";

export type { ProgrammeLevel };

export const PROGRAMME_LEVEL_LABELS: Record<ProgrammeLevel, string> = {
  undergraduate: "Undergraduate",
  postgraduate: "Postgraduate",
  doctoral: "Doctoral",
};

export type ProgrammeStatus =
  | "active"
  | "inactive"
  | "pending_accreditation"
  | "suspended";

export const PROGRAMME_STATUS_LABELS: Record<ProgrammeStatus, string> = {
  active: "Active",
  inactive: "Inactive",
  pending_accreditation: "Pending Accreditation",
  suspended: "Suspended",
};

export interface Programme {
  id: string;
  department_id: string;
  name: string;
  code: string;
  level: ProgrammeLevel;
  coordinator_id: string | null;
  // Extended QA fields
  qualification_type: string | null;
  nqf_level: number | null;
  duration_years: number | null;
  total_credits: number | null;
  status: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProgrammeCreate {
  department_id: string;
  name: string;
  code: string;
  level: ProgrammeLevel;
  coordinator_id?: string | null;
  qualification_type?: string | null;
  nqf_level?: number | null;
  duration_years?: number | null;
  total_credits?: number | null;
  status?: ProgrammeStatus | null;
}

export interface ProgrammeUpdate {
  name?: string;
  code?: string;
  level?: ProgrammeLevel;
  coordinator_id?: string | null;
  qualification_type?: string | null;
  nqf_level?: number | null;
  duration_years?: number | null;
  total_credits?: number | null;
  status?: ProgrammeStatus | null;
}
