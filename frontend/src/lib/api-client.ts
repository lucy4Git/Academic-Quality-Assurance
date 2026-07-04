"use client";

import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import type { ApiError } from "@/types";

/**
 * Axios client — routes every request through the Next.js /api/proxy/* handler.
 *
 * WHY THE PROXY:
 * JWTs live in httpOnly cookies and are invisible to browser JS. The proxy
 * reads the `access_token` cookie server-side and forwards it as a
 * `Authorization: Bearer …` header to FastAPI. Calling FastAPI directly from
 * the browser would always 401 because no token is present in the request.
 *
 * Route mapping:
 *   apiClient.get("/auth/me")        → GET  /api/proxy/auth/me
 *   apiClient.get("/institutions")   → GET  /api/proxy/institutions
 *   proxy handler                   → GET  http://localhost:8000/api/v1/auth/me
 */
export const apiClient = axios.create({
  baseURL: "/api/proxy",
  headers: {
    "Content-Type": "application/json",
  },
  // No withCredentials needed for same-origin proxy calls; the proxy
  // reads the cookie from the incoming request, not the client.
});

// ── Response interceptor: handle 401 by attempting token refresh ──────────
let isRefreshing = false;
let pendingQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

function drainQueue(error: unknown, token?: string) {
  pendingQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  });
  pendingQueue = [];
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status === 401 && !original._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          pendingQueue.push({ resolve, reject });
        }).then(() => apiClient(original));
      }

      original._retry = true;
      isRefreshing = true;

      try {
        await fetch("/api/auth/refresh", { method: "POST" });
        drainQueue(null);
        return apiClient(original);
      } catch (refreshError) {
        drainQueue(refreshError);
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

/** Extract a human-readable message from an Axios error */
export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as ApiError | undefined;
    if (typeof data?.detail === "string") {
      return data.detail;
    }
    if (Array.isArray(data?.detail) && data.detail.length > 0) {
      return data.detail.map((e) => e.msg).join("; ");
    }
    if (error.message) return error.message;
  }
  if (error instanceof Error) return error.message;
  return "An unexpected error occurred.";
}
