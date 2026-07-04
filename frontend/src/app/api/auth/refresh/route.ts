import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/**
 * POST /api/auth/refresh
 * Reads the refresh_token httpOnly cookie, exchanges it for a new token pair,
 * and sets updated cookies. Called by the Axios 401 interceptor.
 */
export async function POST(request: NextRequest) {
  const refreshToken = request.cookies.get("refresh_token")?.value;

  if (!refreshToken) {
    return NextResponse.json({ detail: "No refresh token." }, { status: 401 });
  }

  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Token refresh failed." }));
      // Clear cookies on refresh failure
      const response = NextResponse.json(err, { status: res.status });
      response.cookies.set("access_token", "", { maxAge: 0, path: "/" });
      response.cookies.set("refresh_token", "", { maxAge: 0, path: "/" });
      return response;
    }

    const tokens = (await res.json()) as {
      access_token: string;
      refresh_token: string;
    };

    const cookieOpts = {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "strict" as const,
      path: "/",
    };

    const response = NextResponse.json({ success: true }, { status: 200 });
    response.cookies.set("access_token", tokens.access_token, {
      ...cookieOpts,
      maxAge: 60 * 60,
    });
    response.cookies.set("refresh_token", tokens.refresh_token, {
      ...cookieOpts,
      maxAge: 60 * 60 * 24 * 7,
    });

    return response;
  } catch (error) {
    console.error("[auth/refresh] Unexpected error:", error);
    return NextResponse.json({ detail: "Refresh failed." }, { status: 500 });
  }
}
