import { NextRequest } from "next/server";
import { bffFetchWithAuthFromReq } from "@/lib/server/bffFetch";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  const headers: HeadersInit = {
    Accept: "application/json",
  };

  const contentType = request.headers.get("content-type");
  if (contentType) {
    headers["Content-Type"] = contentType;
  }

  const csrfToken = request.headers.get("x-csrftoken") || request.cookies.get("csrftoken")?.value;
  if (csrfToken) {
    headers["X-CSRFToken"] = csrfToken;
  }

  const rawBody = await request.text();
  return bffFetchWithAuthFromReq(request, "/api/shrine-interactions/", {
    method: "POST",
    headers,
    body: rawBody ? rawBody : undefined,
  });
}
