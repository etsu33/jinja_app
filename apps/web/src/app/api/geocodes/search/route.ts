import type { NextRequest } from "next/server";
import { bffFetchWithAuthFromReq } from "@/lib/server/bffFetch";
export const dynamic = "force-dynamic";
export async function GET(req: NextRequest) {
  return bffFetchWithAuthFromReq(req, `/api/geocodes/search/${req.nextUrl.search}`, { method: "GET", headers: { Accept: "application/json" } });
}
