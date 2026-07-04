import { NextResponse } from "next/server";

/**
 * POST /api/auth/logout
 * Clears the httpOnly auth cookies and redirects to login.
 */
export async function POST() {
  const response = NextResponse.json({ success: true }, { status: 200 });

  // Clear both tokens by setting max-age to 0
  const cookieOpts = {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict" as const,
    path: "/",
    maxAge: 0,
  };

  response.cookies.set("access_token", "", cookieOpts);
  response.cookies.set("refresh_token", "", cookieOpts);

  return response;
}
