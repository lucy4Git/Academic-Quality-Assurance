import type { UserRole } from "./enums";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  institution_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface TokenPayload {
  sub: string;
  role: UserRole;
  institution_id: string | null;
  type: "access" | "refresh";
  iat: number;
  exp: number;
  jti?: string;
}
