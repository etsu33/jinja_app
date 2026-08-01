// apps/web/src/app/api/shrines/[id]/data/route.ts
import { NextRequest, NextResponse } from "next/server";
import { djFetch } from "@/lib/server/backend";

type Ctx = { params: Promise<{ id: string }> };
export const dynamic = "force-dynamic";

// 通常Detail API（ShrineViewSet.retrieve、AllowAny）へのBFF境界。
// /api/public/shrines/[id]/route.tsと同じ中継パターン（djFetch経由）に揃える。
const DJANGO_SHRINE_DATA_BASE = "/api/shrines";

export async function GET(req: NextRequest, ctx: Ctx) {
  const { id } = await ctx.params;
  if (!id) return NextResponse.json({ error: "missing_id" }, { status: 400 });

  const upstreamPath = `${DJANGO_SHRINE_DATA_BASE}/${encodeURIComponent(id)}/data/`;
  const upstream = await djFetch(req, upstreamPath, {
    method: "GET",
    forwardAuth: false,
  });

  const contentType = upstream.headers.get("content-type") ?? "";
  const bodyText = await upstream.text();

  if (!upstream.ok) {
    return NextResponse.json(
      {
        error: "upstream_failed",
        status: upstream.status,
        upstream: upstream.url,
        body: bodyText.slice(0, 1000),
      },
      { status: 502 },
    );
  }

  // JSONじゃないなら、そのまま返す（事故防止）
  if (!contentType.includes("application/json")) {
    return new NextResponse(bodyText, {
      status: upstream.status,
      headers: { "Content-Type": contentType || "text/plain" },
    });
  }

  let raw: unknown;
  try {
    raw = JSON.parse(bodyText);
  } catch {
    return NextResponse.json(
      { error: "invalid_json", upstream: upstream.url, body: bodyText.slice(0, 400) },
      { status: 502 },
    );
  }

  return NextResponse.json(raw, { status: upstream.status });
}
