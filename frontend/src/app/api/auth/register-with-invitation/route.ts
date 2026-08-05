import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/**
 * POST /api/auth/register-with-invitation
 *
 * Proxies invitation-based registration to FastAPI POST /api/v1/invitations/register.
 * No authentication required. Role and institution come from the invitation — never
 * from this request body.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const res = await fetch(`${API_BASE}/api/v1/invitations/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await res.json().catch(() => ({ detail: "Registration failed" }));
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    console.error("[auth/register-with-invitation] Unexpected error:", error);
    return NextResponse.json(
      { detail: "An unexpected error occurred." },
      { status: 500 }
    );
  }
}
