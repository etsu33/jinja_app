// apps/web/src/lib/server/bffFetch.ts
import "server-only";

import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { getDjangoOrigin } from "@/lib/server/backend";
import { isSecureRequest, setAccessTokenCookie } from "@/lib/server/authCookies";



type Init = RequestInit;

export type BffFetchOptions = {
  retryOn401?: boolean; // default true
  setAccessCookie?: boolean; // default true
};

function apiBase() {
  return getDjangoOrigin().replace(/\/$/, "");
}

function getUpstreamSetCookies(upstream: Response): string[] {
  const headersAny = upstream.headers as Headers & {
    getSetCookie?: () => string[];
  };

  if (typeof headersAny.getSetCookie === "function") {
    return headersAny.getSetCookie().filter(Boolean);
  }

  const single = upstream.headers.get("set-cookie");
  return single ? [single] : [];
}

/**
 * 進行中の token refresh を「その refresh token 単位で」束ねる。
 *
 * ここが module scope の単一 Promise だったとき、1 つの server instance が
 * 複数ユーザーのリクエストを並行処理する環境（本番の Next.js route handler が
 * まさにそれ）では、後から入ったユーザーが先行ユーザーの access token を
 * そのまま受け取り、Set-Cookie まで書かれていた
 * （docs/audit/beta-core-flow-e2e-audit.md E2E-001）。
 *
 * key は refresh token の文字列そのものを使う。
 * - 異なるユーザーが同じ refresh JWT を持つことはない（jti / user_id を含む）
 *   ため、この key は認証 identity の境界そのものになる。
 * - digest ではなく完全一致の文字列を key にすることで、ハッシュ衝突による
 *   identity 混線が原理的に起こり得ない。
 *
 * entry は成功・失敗・reject のいずれでも settle 時点で必ず取り除く。
 * したがって「あるユーザーの refresh 失敗」が Map に残って他のユーザーへ
 * 観測されることはなく、同一 identity の次のリクエストは再試行できる。
 */
const refreshInFlightByToken = new Map<string, Promise<string | null>>();

async function refreshAccessViaBackendMutex(refresh: string): Promise<string | null> {
  const inFlight = refreshInFlightByToken.get(refresh);
  if (inFlight) return inFlight;

  const pending: Promise<string | null> = refreshAccessViaBackend(refresh).finally(() => {
    // 自分が登録した entry だけを消す（同じ token で後続の refresh が
    // 既に登録し直している可能性があるため）。
    if (refreshInFlightByToken.get(refresh) === pending) {
      refreshInFlightByToken.delete(refresh);
    }
  });

  refreshInFlightByToken.set(refresh, pending);

  return pending;
}

/** テスト用。進行中の refresh を持ち越さずにケースを独立させるため。 */
export function __resetRefreshInFlightForTest(): void {
  refreshInFlightByToken.clear();
}

async function refreshAccessViaBackend(refresh: string): Promise<string | null> {
  const r = await fetch(`${apiBase()}/api/auth/jwt/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ refresh }),
    cache: "no-store",
  });
  if (!r.ok) return null;

  const data = (await r.json().catch(() => null)) as any;
  return typeof data?.access === "string" ? data.access : null;
}

function readJwtExp(token: string): number | null {
  try {
    const parts = token.split(".");
    if (parts.length < 2) return null;

    const payload = parts[1];
    const b64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const pad = "=".repeat((4 - (b64.length % 4)) % 4);
    const b64p = b64 + pad;

    const bin = typeof atob === "function" ? atob(b64p) : null;
    if (bin == null) return null;

    const bytes = Uint8Array.from(bin, (c) => c.charCodeAt(0));
    const json = new TextDecoder().decode(bytes);

    const obj = JSON.parse(json) as any;
    return typeof obj?.exp === "number" ? obj.exp : null;
  } catch {
    return null;
  }
}

/**
 * 互換レイヤ:
 * 既存の route.ts が import してる bffFetchWithAuthFromReq を復活させる。
 * 中身は djFetch に委譲。
 */


export async function bffFetchWithAuthFromReq(
  req: NextRequest,
  upstreamPath: string,
  init: Init = {},
  opts: BffFetchOptions = {},
): Promise<NextResponse> {
  const { retryOn401 = true, setAccessCookie = true } = opts;

  const headerAuth = req.headers.get("authorization") ?? null;
  const access = req.cookies.get("access_token")?.value ?? null;
  const refresh = req.cookies.get("refresh_token")?.value ?? null;

  let preRefreshedAccess: string | null = null;

  const nowSec = Math.floor(Date.now() / 1000);
  const exp = access ? readJwtExp(access) : null;
  const skewSec = 20;

  const shouldPreRefresh =
    retryOn401 && refresh && !headerAuth && (!access || (exp != null && exp <= nowSec + skewSec));

  if (shouldPreRefresh) {
    preRefreshedAccess = await refreshAccessViaBackendMutex(refresh);
  }

  const buildAuth = (override?: string | null) => {
    if (headerAuth) return headerAuth;
    if (override) return `Bearer ${override}`;
    if (preRefreshedAccess) return `Bearer ${preRefreshedAccess}`;
    if (access) return `Bearer ${access}`;
    return null;
  };

  const doFetch = (overrideAccess?: string | null) => {
    const auth = buildAuth(overrideAccess);
    const cookieHeader = req.headers.get("cookie") ?? "";

    const hasAnonCookie = /(?:^|;\s*)concierge_anon_id=/.test(cookieHeader);
    const hasAccessCookie = /(?:^|;\s*)access_token=/.test(cookieHeader);
    const hasRefreshCookie = /(?:^|;\s*)refresh_token=/.test(cookieHeader);

    console.log("[BFF_THREAD_UPSTREAM_REQUEST]", {
      upstreamPath,
      method: init.method ?? "GET",
      hasAuthorization: Boolean(auth),
      authSource: headerAuth
        ? "incoming_header"
        : overrideAccess
          ? "override_access"
          : preRefreshedAccess
            ? "pre_refreshed_access"
            : access
              ? "access_cookie"
              : null,
      hasCookieHeader: Boolean(cookieHeader),
      hasAnonCookie,
      hasAccessCookie,
      hasRefreshCookie,
    });

    return fetch(`${apiBase()}${upstreamPath}`, {
      ...init,
      cache: "no-store",
      headers: {
        ...(init.headers ?? {}),
        ...(auth ? { Authorization: auth } : {}),
        ...(cookieHeader ? { Cookie: cookieHeader } : {}),
      },
    });
  };

  let upstream = await doFetch(preRefreshedAccess);

  let newAccess: string | null = null;
  // 401 だけが「この access token はもう受け付けられない」を意味する。
  // 403 は認証済み principal に対する認可判断（例: 非管理者が IsAdminUser の
  // view を叩いた）であり、refresh しても結果は変わらない。retry すると
  // backend 往復が増え、不要な token 再発行まで起きる
  // （docs/audit/beta-core-flow-e2e-audit.md E2E-023）。
  if (upstream.status === 401 && retryOn401 && refresh) {
    newAccess = await refreshAccessViaBackendMutex(refresh);
    if (newAccess) upstream = await doFetch(newAccess);
  }

  const text = upstream.status === 204 ? "" : await upstream.text().catch(() => "");
  const contentType = upstream.headers.get("content-type");

  console.log("[BFF_UPSTREAM]", {
    upstreamPath,
    status: upstream.status,
    contentType,
    hasSetCookie: Boolean(upstream.headers.get("set-cookie")),
    isJson: contentType?.includes("application/json") ?? false,
    responseLength: text.length,
  });


  const res =
    upstream.status === 204
      ? new NextResponse(null, { status: 204 })
      : new NextResponse(text, {
          status: upstream.status,
          headers: {
            "Content-Type": contentType ?? "application/json",
          },
        });

  const upstreamSetCookies = getUpstreamSetCookies(upstream);
  for (const value of upstreamSetCookies) {
    res.headers.append("set-cookie", value);
  }

  const tokenToSet = newAccess ?? preRefreshedAccess;
  if (tokenToSet && setAccessCookie) {
    // 属性は /api/auth/login と同じ契約（Secure を含む）を共有する。
    setAccessTokenCookie(res, tokenToSet, { secure: isSecureRequest(req) });
  }

  return res;
}

export async function bffPostJsonWithAuthFromReq(
  req: NextRequest,
  upstreamPath: string,
  payload: unknown,
  opts: BffFetchOptions = {},
): Promise<NextResponse> {
  return bffFetchWithAuthFromReq(
    req,
    upstreamPath,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload ?? {}),
    },
    opts,
  );
}
