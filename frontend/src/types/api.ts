// Generic API types

export interface ApiError {
  detail: string | ValidationError[];
  status?: number;
}

export interface ValidationError {
  type: string;
  loc: (string | number)[];
  msg: string;
  input?: unknown;
  ctx?: Record<string, unknown>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface HealthResponse {
  status: "ok";
  app: string;
  environment: string;
}
