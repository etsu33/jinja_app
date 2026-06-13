

import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const BACKEND_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE ||
  process.env.API_BASE_URL ||
  "https://jinja-backend.onrender.com";

function backendVisitsUrl() {
  const base = BACKEND_BASE_URL.replace(/\/+$/, "");
  return `${base}/api/visits/`;
}

export async function GET(request: NextRequest) {
  const headers: HeadersInit = {
    Accept: "application/json",
  };

  const authorization = request.headers.get("authorization");
  const accessToken = request.cookies.get("access_token")?.value;

  if (authorization) {
    headers.Authorization = authorization;
  } else if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  const response = await fetch(backendVisitsUrl(), {
    method: "GET",
    headers,
    cache: "no-store",
  });

  const text = await response.text();
  const responseContentType = response.headers.get("content-type") || "application/json";

  return new NextResponse(text, {
    status: response.status,
    headers: {
      "Content-Type": responseContentType,
    },
  });
}
