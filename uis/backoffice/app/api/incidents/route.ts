import { NextRequest, NextResponse } from "next/server";

const upstreamBase = (
  process.env.INCIDENTS_API_URL ||
  process.env.NEXT_PUBLIC_INCIDENTS_API_URL ||
  "http://localhost:8001"
).replace(/\/$/, "");

async function proxy(request: NextRequest, upstreamPath: string): Promise<NextResponse> {
  try {
    const url = new URL(upstreamPath, `${upstreamBase}/`);
    request.nextUrl.searchParams.forEach((value, key) => {
      url.searchParams.set(key, value);
    });

    const init: RequestInit = {
      method: request.method,
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
    };

    if (request.method !== "GET" && request.method !== "HEAD") {
      init.body = await request.text();
    }

    const response = await fetch(url, init);
    const text = await response.text();
    return new NextResponse(text, {
      status: response.status,
      headers: { "Content-Type": response.headers.get("Content-Type") || "application/json" },
    });
  } catch {
    return NextResponse.json(
      { message: "Incident service is temporarily unavailable. Please try again." },
      { status: 502 },
    );
  }
}

export async function GET(request: NextRequest) {
  return proxy(request, "/api/incidents");
}

export async function POST(request: NextRequest) {
  return proxy(request, "/api/incidents");
}
