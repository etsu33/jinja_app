import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const BACKEND_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE ||
  process.env.API_BASE_URL ||
  "https://jinja-backend.onrender.com";

function backendShrineInteractionsUrl() {
  const base = BACKEND_BASE_URL.replace(/\/+$/, "");
  return `${base}/api/shrine-interactions/`;
}

export async function POST(request: NextRequest) {
  const headers: HeadersInit = {
    Accept: "application/json",
  };

  const contentType = request.headers.get("content-type");
  if (contentType) {
    headers["Content-Type"] = contentType;
  }

  const authorization = request.headers.get("authorization");
  const accessToken = request.cookies.get("access_token")?.value;
  const authSource = authorization ? "header" : accessToken ? "cookie" : "none";

  if (authorization) {
    headers.Authorization = authorization;
  } else if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  const csrfToken = request.headers.get("x-csrftoken") || request.cookies.get("csrftoken")?.value;
  if (csrfToken) {
    headers["X-CSRFToken"] = csrfToken;
  }

  const rawBody = await request.text();
  const response = await fetch(backendShrineInteractionsUrl(), {
    method: "POST",
    headers,
    body: rawBody ? rawBody : undefined,
    cache: "no-store",
  });

  const text = await response.text();
  const responseContentType = response.headers.get("content-type") || "application/json";

  return new NextResponse(text, {
    status: response.status,
    headers: {
      "Content-Type": responseContentType,
      "X-Shrine-Interaction-Proxy": "next-route",
      "X-Shrine-Interaction-Auth-Source": authSource,
    },
  });
}
