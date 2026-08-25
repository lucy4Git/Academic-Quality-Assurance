import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8001";

const COOKIE_OPTS = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "strict" as const,
  path: "/",
};

/**
 * POST /api/auth/login
 *
 * Accepts { email, password } JSON from the browser.
 * Forwards as OAuth2 form data to FastAPI /api/v1/auth/token.
 * Stores access_token and refresh_token in httpOnly cookies.
 * Returns { user } to the client (token is NOT returned to JS).
 */
export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as { email: string; password: string };

    // Build form-encoded payload for OAuth2 password flow
    const formData = new URLSearchParams();
    formData.set("username", body.email);
    formData.set("password", body.password);

    const tokenRes = await fetch(`${API_BASE}/api/v1/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData.toString(),
    });

    if (!tokenRes.ok) {
      const err = await tokenRes.json().catch(() => ({ detail: "Login failed" }));
      return NextResponse.json(err, { status: tokenRes.status });
    }

    const tokens = (await tokenRes.json()) as {
      access_token: string;
      refresh_token: string;
    };

    // Fetch user profile using the fresh access token
    const meRes = await fetch(`${API_BASE}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${tokens.access_token}` },
    });

    const user = meRes.ok ? await meRes.json() : null;

    // Set tokens as httpOnly cookies — JS can never read these
    const response = NextResponse.json({ user }, { status: 200 });
    response.cookies.set("access_token", tokens.access_token, {
      ...COOKIE_OPTS,
      maxAge: 60 * 60, // 60 minutes
    });
    response.cookies.set("refresh_token", tokens.refresh_token, {
      ...COOKIE_OPTS,
      maxAge: 60 * 60 * 24 * 7, // 7 days
    });

    return response;
  } catch (error) {
    console.error("[auth/login] Unexpected error:", error);
    return NextResponse.json(
      { detail: "An unexpected error occurred." },
      { status: 500 }
    );
  }
}
