import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { bffPostJsonWithAuthFromReq } from "@/lib/server/bffFetch";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function POST(req: NextRequest) {
  const origin = req.nextUrl.origin;
  const upstream = await bffPostJsonWithAuthFromReq(req, "/api/billings/checkout/", {
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
