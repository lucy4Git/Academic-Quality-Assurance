export interface Faculty {
  id: string;
  institution_id: string;
  name: string;
  code: string;
  campus: string | null;
  dean_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface FacultyCreate {
  institution_id: string;
  name: string;
  code: string;
  campus?: string | null;
  dean_id?: string | null;
}

export interface FacultyUpdate {
  name?: string;
  code?: string;
  campus?: string | null;
  dean_id?: string | null;
}
