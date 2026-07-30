import { NextRequest, NextResponse } from "next/server";

const upstreamBase = (
  process.env.INCIDENTS_API_URL ||
  process.env.NEXT_PUBLIC_INCIDENTS_API_URL ||
  "http://localhost:8001"
).replace(/\/$/, "");

export async function GET(
  _request: NextRequest,
  context: { params: Promise<{ id: string }> },
) {
  try {
    const { id } = await context.params;
    const response = await fetch(`${upstreamBase}/api/incidents/${id}`, {
      cache: "no-store",
    });
    const text = await response.text();
    return new NextResponse(text, {
      status: response.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return NextResponse.json(
      { message: "Incident service is temporarily unavailable. Please try again." },
      { status: 502 },
    );
  }
}
