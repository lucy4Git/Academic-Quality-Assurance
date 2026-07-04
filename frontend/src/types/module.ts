export interface Module {
  id: string;
  programme_id: string;
  name: string;
  code: string;
  credits: number;
  semester: string;
  academic_year: string;
  lecturer_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ModuleBrief {
  id: string;
  programme_id: string;
  name: string;
  code: string;
  academic_year: string;
}

export interface ModuleCreate {
  programme_id: string;
  name: string;
  code: string;
  credits: number;
  semester: string;
  academic_year: string;
  lecturer_id?: string | null;
}

export interface ModuleUpdate {
  name?: string;
  code?: string;
  credits?: number;
  semester?: string;
  academic_year?: string;
  lecturer_id?: string | null;
}

/** Common semester options for the form selector */
export const SEMESTER_OPTIONS = [
  "Semester 1",
  "Semester 2",
  "Year Module",
  "Summer",
  "Block 1",
  "Block 2",
] as const;
