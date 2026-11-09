import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { isBillingPassType } from "@/lib/billing/passes";
import { bffPostJsonWithAuthFromReq } from "@/lib/server/bffFetch";

export const dynamic = "force-dynamic";
export const revalidate = 0;

async function readPassType(req: NextRequest): Promise<unknown> {
  try {
    const body = (await req.json()) as { pass_type?: unknown } | null;
    return body?.pass_type;
  } catch {
    return undefined;
  }
}

export async function POST(req: NextRequest) {
  // 買い切りの旅行パスの種類（1d / 7d / 14d）。知らない値は backend へ送らずに断る。
  const passType = await readPassType(req);
  if (!isBillingPassType(passType)) {
    return NextResponse.json({ detail: "invalid pass_type" }, { status: 400 });
  }

  const origin = req.nextUrl.origin;
  const upstream = await bffPostJsonWithAuthFromReq(req, "/api/billings/checkout/", {
    pass_type: passType,
    success_url: `${origin}/billing/success`,
    cancel_url: `${origin}/billing/cancel`,
  });

  if (!upstream.ok) {
    const text = await upstream.text().catch(() => "");
    return new NextResponse(text || JSON.stringify({ detail: "checkout failed" }), {
      status: upstream.status,
      headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json" },
    });
  }

  const text = await upstream.text().catch(() => "");
  try {
    const data = JSON.parse(text) as unknown;
    return NextResponse.json(data, { status: 200 });
  } catch {
    return NextResponse.json({ detail: "upstream returned bad json" }, { status: 502 });
  }
}
