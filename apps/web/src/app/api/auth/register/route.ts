// apps/web/src/app/api/auth/register/route.ts
import { NextRequest, NextResponse } from "next/server";
import { serverLog, getRequestId } from "@/lib/server/logging";

export const dynamic = "force-dynamic";
export const revalidate = 0;

/**
 * Backend オリジンの環境変数名は歴史的に複数系統が併存している
 * （docs/audit/backend-origin-env-migration-design.md）。
 *
 * この route だけが `DJANGO_ORIGIN` を参照しておらず、他の BFF（`djFetch()` 経由。
 * 解決順は `DJANGO_ORIGIN` → `BACKEND_ORIGIN`）が疎通できている環境でも
 * signup だけが既定値 `http://127.0.0.1:8000` へ向いて fetch に失敗し得た。
 * どの名称が設定されていても解決できるよう、他 BFF と同じ `DJANGO_ORIGIN` を
 * 先頭に置き、この route が従来見ていた名称も後方互換として残す。
 */
const BACKEND_ORIGIN_ENV_NAMES = [
  "DJANGO_ORIGIN",
  "BACKEND_ORIGIN",
  "DJANGO_API_BASE_URL",
  "BACKEND_BASE_URL",
] as const;

const DEFAULT_BACKEND_ORIGIN = "http://127.0.0.1:8000";

/** Signup の upstream パス。Backend の `users/api/urls.py` と 1:1 で対応する。 */
const SIGNUP_UPSTREAM_PATH = "/api/users/signup/";

function resolveBackendOrigin(): { origin: string; source: string } {
  for (const name of BACKEND_ORIGIN_ENV_NAMES) {
    const value = process.env[name]?.trim();
    if (value) {
      return { origin: value.replace(/\/+$/, ""), source: name };
    }
  }
  return { origin: DEFAULT_BACKEND_ORIGIN, source: "default" };
}

export async function POST(req: NextRequest) {
  const requestId = getRequestId(req);
  const { origin, source } = resolveBackendOrigin();
  const upstreamUrl = `${origin}${SIGNUP_UPSTREAM_PATH}`;

  let body: string;
  try {
    body = await req.text();
  } catch (e) {
    serverLog("warn", "AUTH_REGISTER_BAD_REQUEST_BODY", {
      requestId,
      error: e instanceof Error ? e.message : String(e),
    });
    return NextResponse.json({ detail: "invalid request body" }, { status: 400 });
  }

  let upstream: Response;
  try {
    upstream = await fetch(upstreamUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body,
      cache: "no-store",
    });
  } catch (e) {
    // Backend へ到達できないケース。validation error（Backend が返す 4xx）とは
    // 明確に区別し、Frontend が generic な通信エラーとして扱えるようにする。
    serverLog("error", "AUTH_REGISTER_UPSTREAM_UNREACHABLE", {
      requestId,
      backendOriginSource: source,
      error: e instanceof Error ? e.message : String(e),
    });

    return NextResponse.json(
      { detail: "バックエンドに接続できません", code: "backend_unreachable" },
      { status: 502 },
    );
  }

  const text = await upstream.text();

  if (!upstream.ok) {
    serverLog("warn", "AUTH_REGISTER_UPSTREAM_NOT_OK", {
      requestId,
      status: upstream.status,
      backendOriginSource: source,
      bodyLength: text.length,
    });
  }

  // Backend を validation の正本とするため、status / body はそのまま透過する。
  return new NextResponse(text, {
    status: upstream.status,
    headers: {
      "Content-Type": upstream.headers.get("content-type") || "application/json",
    },
  });
}
