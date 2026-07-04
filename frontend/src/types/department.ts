export interface Department {
  id: string;
  faculty_id: string;
  name: string;
  code: string;
  head_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface DepartmentCreate {
  faculty_id: string;
  name: string;
  code: string;
  head_id?: string | null;
}

export interface DepartmentUpdate {
  name?: string;
  code?: string;
  head_id?: string | null;
}
