import { NextRequest } from "next/server";
import { bffFetchWithAuthFromReq } from "@/lib/server/bffFetch";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  const rawBody = await request.text();

  return bffFetchWithAuthFromReq(request, "/api/compass/recommendations/", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: rawBody ? rawBody : undefined,
  });
}
