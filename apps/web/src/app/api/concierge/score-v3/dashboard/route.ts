import type { NextRequest } from "next/server";
import { bffFetchWithAuthFromReq } from "@/lib/server/bffFetch";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(req: NextRequest) {
  return bffFetchWithAuthFromReq(req, "/api/concierge/score-v3/dashboard/", {
    method: "GET",
    headers: { Accept: "application/json" },
  });
}
