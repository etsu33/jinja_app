import { NextRequest, NextResponse } from "next/server";
import { djFetch } from "@/lib/server/backend";

// POST /api/deep-dive/ask/ -> Django POST /api/deep-dive/ask/ (AllowAny, no auth to forward).
//
// Thin proxy: upstream's HTTP status is passed through unchanged (400/404/200/500),
// so the Frontend can distinguish input error / shrine not found / normal product
// state (readiness="not_ready" is still HTTP 200) from an actual system failure.
// No response body reinterpretation happens here.

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  const payload = await req.text();
  const contentType = req.headers.get("content-type") ?? "application/json";

  let upstream: Response;
  try {
    upstream = await djFetch(req, "/api/deep-dive/ask/", {
      method: "POST",
      forwardAuth: false,
      headers: { "content-type": contentType },
      body: payload,
    });
  } catch {
    return NextResponse.json({ detail: "upstream unreachable" }, { status: 502 });
  }

  const body = await upstream.text();
  const ct = upstream.headers.get("content-type") || "application/json";

  return new NextResponse(body, {
    status: upstream.status,
    headers: { "content-type": ct },
  });
}
