import type { NextRequest } from "next/server";

import { bffFetchWithAuthFromReq } from "@/lib/server/bffFetch";

export const dynamic = "force-dynamic";
export const revalidate = 0;

type Ctx = {
  params: Promise<{ id: string }>;
};

// 相談と一致したご利益の名前(任意・繰り返し可)。Backend の ShrineMeaningView と同じ名前。
// ほかの引数は Backend へ渡さない。
const MATCHED_BENEFITS_QUERY_PARAM = "benefits";

function forwardedQuery(req: NextRequest): string {
  const params = new URL(req.url).searchParams;
  if (!params.has(MATCHED_BENEFITS_QUERY_PARAM)) return "";

  const query = new URLSearchParams();
  for (const name of params.getAll(MATCHED_BENEFITS_QUERY_PARAM)) query.append(MATCHED_BENEFITS_QUERY_PARAM, name);
  return `?${query.toString()}`;
}

export async function GET(req: NextRequest, ctx: Ctx) {
  const { id } = await ctx.params;

  return bffFetchWithAuthFromReq(req, `/api/shrines/${encodeURIComponent(id)}/meaning/${forwardedQuery(req)}`, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
  });
}
