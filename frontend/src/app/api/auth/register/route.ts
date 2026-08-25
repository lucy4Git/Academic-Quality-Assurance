import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001";

/**
 * POST /api/auth/register
 *
 * Proxies public self-registration to FastAPI POST /api/v1/auth/public-register.
 * No authentication required. Returns registration result (never a token).
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const res = await fetch(`${API_BASE}/api/v1/auth/public-register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await res.json().catch(() => ({ detail: "Registration failed" }));
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    console.error("[auth/register] Unexpected error:", error);
    return NextResponse.json(
      { detail: "An unexpected error occurred." },
      { status: 500 }
    );
  }
}
