import { NextRequest, NextResponse } from "next/server";
import type { UserRole } from "@/types";
import { canAccess } from "@/lib/rbac";

// Routes that bypass authentication entirely
const PUBLIC_PATHS = [
  "/login",
  "/register",
  "/verify-email",
  "/pending-review",
  "/activate",
  "/forbidden",
  "/api/auth",
  "/api/proxy/auth/activate",
  "/",
];

function isPublicPath(pathname: string) {
  return PUBLIC_PATHS.some((p) => pathname.startsWith(p));
}

function isInternalPath(pathname: string) {
  return (
    pathname.startsWith("/_next/") ||
    pathname.startsWith("/favicon") ||
    pathname.includes(".")
  );
}

/**
 * Decode the role from a JWT without verifying the signature.
 * Signature verification is handled by FastAPI on every API call.
 * We only need the role claim here to enforce frontend routing rules.
 */
function decodeRole(token: string): UserRole | null {
  try {
    const payload = token.split(".")[1];
    if (!payload) return null;
    // base64url → base64 → JSON
    const padded = payload.replace(/-/g, "+").replace(/_/g, "/");
    const json = atob(padded);
    const claims = JSON.parse(json) as { role?: UserRole };
    return claims.role ?? null;
  } catch {
    return null;
  }
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (isInternalPath(pathname) || isPublicPath(pathname)) {
    return NextResponse.next();
  }

  const accessToken = request.cookies.get("access_token")?.value;

  // No token → redirect to login, preserving the destination
  if (!accessToken) {
    const url = new URL("/login", request.url);
    url.searchParams.set("redirect", pathname);
    return NextResponse.redirect(url);
  }

  // Authenticated user on /login → route based on role
  if (pathname === "/login") {
    const role = decodeRole(accessToken);
    const destination = role === "generic_user" ? "/workspace" : "/dashboard";
    return NextResponse.redirect(new URL(destination, request.url));
  }

  // Decode the role claim from the JWT (no signature check — that's FastAPI's job)
  const role = decodeRole(accessToken);

  // Malformed token (no role claim) → treat as unauthenticated
  if (!role) {
    const url = new URL("/login", request.url);
    url.searchParams.set("redirect", pathname);
    return NextResponse.redirect(url);
  }

  // Role-based access check
  if (!canAccess(pathname, role)) {
    return NextResponse.redirect(new URL("/forbidden", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
