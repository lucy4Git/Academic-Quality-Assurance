export interface Institution {
  id: string;
  name: string;
  code: string;
  country: string | null;
  address: string | null;
  logo_url: string | null;
  is_active: boolean;
  institution_type: "pilot" | "demo" | "production";
  created_at: string;
  updated_at: string;
}

export interface InstitutionCreate {
  name: string;
  code: string;
  country?: string | null;
  address?: string | null;
  logo_url?: string | null;
  institution_type?: string;
}

export interface InstitutionStats {
  faculties: number;
  departments: number;
  programmes: number;
  modules: number;
  users: number;
  files: number;
}

export interface InstitutionUpdate {
  name?: string;
  code?: string;
  country?: string | null;
  address?: string | null;
  logo_url?: string | null;
  is_active?: boolean;
  institution_type?: string;
}
