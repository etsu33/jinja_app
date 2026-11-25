// apps/web/src/app/api/shrines/[id]/data/route.ts
import { NextRequest, NextResponse } from "next/server";
import { djFetch } from "@/lib/server/backend";
import { serverLog, getRequestId } from "@/lib/server/logging";

type Ctx = { params: Promise<{ id: string }> };
export const dynamic = "force-dynamic";

// 通常Detail API（ShrineViewSet.retrieve、AllowAny）へのBFF境界。
// Shrine詳細を取得する唯一のBFF経路（djFetch経由で中継する）。
const DJANGO_SHRINE_DATA_BASE = "/api/shrines";

// public error body の契約（docs/audit/beta-core-flow-e2e-audit.md E2E-005）:
//
//   - 「Shrineが無い」と「基盤が落ちている」をHTTP statusで区別できること。
//     404を502へ丸めると、存在しないShrineへのアクセスが監視上は障害として
//     立ち上がり、frontendも両者を判別できない。
//   - 内部情報（backend origin / upstream URL / upstream の生body）を
//     public responseへ載せないこと。upstream.url は DJANGO_ORIGIN を含む
//     完全URLであり、BFF境界がbackend originを隠す目的そのものを破っていた。
//
// 診断に必要な情報はここでは落とさず serverLog 側へ寄せる。
const ERROR_NOT_FOUND = { error: "not_found" } as const;
const ERROR_INVALID_JSON = { error: "invalid_json" } as const;

function upstreamFailureBody(status: number) {
  // upstream の HTTP status（数値）だけを残す。host名でも本文でもないため
  // 内部情報の露出にはあたらず、障害切り分けには効く。
  return { error: "upstream_failed", status } as const;
}

export async function GET(req: NextRequest, ctx: Ctx) {
  const { id } = await ctx.params;
  if (!id) return NextResponse.json({ error: "missing_id" }, { status: 400 });

  const requestId = getRequestId(req);
  const upstreamPath = `${DJANGO_SHRINE_DATA_BASE}/${encodeURIComponent(id)}/data/`;

  let upstream: Response;
  try {
    upstream = await djFetch(req, upstreamPath, {
      method: "GET",
      forwardAuth: false,
    });
  } catch (e) {
    // transport failure（backend到達不能 / DNS / timeout）。
    // 握らずに投げると Next.js の 500 になり、環境によっては URL を含む
    // error message が外へ出る。ここで安全な形へ畳む。
    serverLog("error", "SHRINE_DATA_UPSTREAM_UNREACHABLE", {
      requestId,
      shrineId: id,
      message: e instanceof Error ? e.message : String(e),
    });
    return NextResponse.json(upstreamFailureBody(502), { status: 502 });
  }

  const contentType = upstream.headers.get("content-type") ?? "";
  const bodyText = await upstream.text();

  // Shrineが存在しない = 正常系の一部。502へ丸めない。
  if (upstream.status === 404) {
    serverLog("info", "SHRINE_DATA_NOT_FOUND", { requestId, shrineId: id });
    return NextResponse.json(ERROR_NOT_FOUND, { status: 404 });
  }

  if (!upstream.ok) {
    serverLog("error", "SHRINE_DATA_UPSTREAM_FAILED", {
      requestId,
      shrineId: id,
      upstreamStatus: upstream.status,
      upstreamPath,
      bodyLength: bodyText.length,
    });
    return NextResponse.json(upstreamFailureBody(upstream.status), { status: 502 });
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
    serverLog("error", "SHRINE_DATA_UPSTREAM_INVALID_JSON", {
      requestId,
      shrineId: id,
      upstreamPath,
      bodyLength: bodyText.length,
    });
    return NextResponse.json(ERROR_INVALID_JSON, { status: 502 });
  }

  return NextResponse.json(raw, { status: upstream.status });
}
