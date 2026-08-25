import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8001";

/**
 * POST /api/auth/verify-email
 * POST /api/auth/verify-email/resend  (via ?action=resend)
 *
 * Proxies email verification requests to FastAPI — no authentication required.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const action = request.nextUrl.searchParams.get("action");
    const endpoint =
      action === "resend"
        ? "/api/v1/auth/resend-verification"
        : "/api/v1/auth/verify-email";

    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await res.json().catch(() => ({ detail: "Verification failed" }));
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    console.error("[auth/verify-email] Unexpected error:", error);
    return NextResponse.json(
      { detail: "An unexpected error occurred." },
      { status: 500 }
    );
  }
}
