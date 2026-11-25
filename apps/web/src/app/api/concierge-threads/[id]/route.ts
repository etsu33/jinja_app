import { NextResponse, type NextRequest } from "next/server";
import { bffFetchWithAuthFromReq } from "@/lib/server/bffFetch";

export const dynamic = "force-dynamic";
export const revalidate = 0;

// Django は /api/concierge-threads/<int:pk>/（BigAutoField）。正の10進整数の正規形だけを通す。
// 復号済みの param をそのまま path に入れると `..` や `/` で upstream の宛先が変わるため、
// それ以外は Django へ送らず、Backend と同じ一律の 404 を返す
// （docs/audit/fu2-p7-concierge-thread-ownership-2026-10-27.md F4）。
const CANONICAL_THREAD_ID = /^[1-9][0-9]{0,18}$/;
const MAX_THREAD_ID = 9223372036854775807n;

function isValidThreadId(id: string): boolean {
  return CANONICAL_THREAD_ID.test(id) && BigInt(id) <= MAX_THREAD_ID;
}

export async function GET(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  if (!isValidThreadId(id)) {
    return NextResponse.json({ detail: "not found" }, { status: 404 });
  }
  const upstreamPath = `/api/concierge-threads/${id}/`;

  const cookieHeader = req.headers.get("cookie") ?? "";
  const hasAuthHeader = Boolean(req.headers.get("authorization"));
  const hasAnonCookie = /(?:^|;\s*)concierge_anon_id=/.test(cookieHeader);
  const hasAccessCookie = /(?:^|;\s*)access_token=/.test(cookieHeader);
  const hasRefreshCookie = /(?:^|;\s*)refresh_token=/.test(cookieHeader);

  console.log("[BFF_THREAD_ROUTE_IN]", {
    id,
    method: req.method,
    hasAuthHeader,
    hasCookieHeader: Boolean(cookieHeader),
    hasAnonCookie,
    hasAccessCookie,
    hasRefreshCookie,
  });

  return bffFetchWithAuthFromReq(req, upstreamPath, {
    method: "GET",
    headers: { Accept: "application/json" },
  });
}
