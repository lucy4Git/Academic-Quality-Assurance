import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8001";

/**
 * Transparent proxy for all /api/proxy/* requests.
 * Reads the access_token httpOnly cookie and forwards it as a Bearer header
 * to the FastAPI backend, then streams the response back to the client.
 *
 * Usage from the client: fetch('/api/proxy/institutions') rather than
 * hitting FastAPI directly, so the JWT never touches JavaScript.
 */
async function handler(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  const { path } = await context.params;
  const accessToken = request.cookies.get("access_token")?.value;
  const upstreamPath = path.join("/");
  const searchParams = request.nextUrl.searchParams.toString();
  const url = `${API_BASE}/api/v1/${upstreamPath}${searchParams ? `?${searchParams}` : ""}`;

  const headers: Record<string, string> = {
    "Content-Type": request.headers.get("content-type") ?? "application/json",
  };

  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  let body: string | undefined;
  if (!["GET", "HEAD"].includes(request.method)) {
    body = await request.text();
  }

  try {
    const upstream = await fetch(url, {
      method: request.method,
      headers,
      body,
    });

    const contentType = upstream.headers.get("content-type") ?? "application/json";
    const isEventStream = contentType.toLowerCase().includes("text/event-stream");
    const responseBody = isEventStream ? upstream.body : await upstream.text();
    return new NextResponse(responseBody, {
      status: upstream.status,
      headers: {
        "Content-Type": contentType,
        ...(isEventStream
          ? { "Cache-Control": "no-cache", "X-Accel-Buffering": "no" }
          : {}),
      },
    });
  } catch (error) {
    console.error("[proxy] Upstream request failed:", error);
    return NextResponse.json(
      { detail: "Gateway error: unable to reach the backend API." },
      { status: 502 }
    );
  }
}

export const GET = handler;
export const POST = handler;
export const PUT = handler;
export const PATCH = handler;
export const DELETE = handler;
