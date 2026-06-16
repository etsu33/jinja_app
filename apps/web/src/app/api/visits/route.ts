import { NextRequest } from "next/server";
import { bffFetchWithAuthFromReq } from "@/lib/server/bffFetch";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: NextRequest) {
  return bffFetchWithAuthFromReq(request, "/api/visits/", {
    method: "GET",
    headers: { Accept: "application/json" },
  });
}
