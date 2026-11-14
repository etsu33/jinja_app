import type { NextRequest } from "next/server";

import { bffFetchWithAuthFromReq } from "@/lib/server/bffFetch";

export const dynamic = "force-dynamic";
export const revalidate = 0;

type Ctx = {
  params: Promise<{ id: string }>;
};

// 英語の神社詳細に出す特徴語（Backend: GET /api/shrines/{id}/feature-words-en/、ログインなしで読める）。
export async function GET(req: NextRequest, ctx: Ctx) {
  const { id } = await ctx.params;

  return bffFetchWithAuthFromReq(req, `/api/shrines/${encodeURIComponent(id)}/feature-words-en/`, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
  });
}
