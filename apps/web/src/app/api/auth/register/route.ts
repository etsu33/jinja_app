// apps/web/src/app/api/auth/register/route.ts
import { NextRequest, NextResponse } from "next/server";

const BACKEND_BASE_URL =
  process.env.DJANGO_API_BASE_URL ||
  process.env.BACKEND_ORIGIN ||
  process.env.BACKEND_BASE_URL ||
  "http://127.0.0.1:8000";

export async function POST(req: NextRequest) {
  try {
    const body = await req.text();

    const upstream = await fetch(`${BACKEND_BASE_URL}/api/users/signup/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body,
      cache: "no-store",
    });

    const text = await upstream.text();

    return new NextResponse(text, {
      status: upstream.status,
      headers: {
        "Content-Type": upstream.headers.get("content-type") || "application/json",
      },
    });
  } catch (e) {
    console.error("[AUTH_REGISTER_PROXY_FAILED]", {
      backendBaseUrl: BACKEND_BASE_URL,
      error: e instanceof Error ? e.message : String(e),
    });

    return NextResponse.json({ detail: "register proxy failed" }, { status: 500 });
  }
}
