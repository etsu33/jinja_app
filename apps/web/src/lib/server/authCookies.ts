// apps/web/src/lib/server/authCookies.ts
//
// 認証系 Cookie の書き込み契約を一箇所に固定する。
//
// これ以前は /api/auth/login だけが `secure` を条件付きで立て、token refresh
// 経路（lib/server/bffFetch.ts、api/concierge/chat/route.ts）は `secure` を
// 省略していた。結果として「ログイン時は Secure、最初の refresh で Secure が
// 落ちる」という属性降格が起きていた（docs/audit/beta-core-flow-e2e-audit.md
// E2E-002）。Cookie を書く経路は必ずこのモジュールを経由させる。
//
// 属性値そのもの（HttpOnly / SameSite / Path / Max-Age）は既存の契約を
// そのまま踏襲しており、本モジュールの導入で変更していない。
import "server-only";

import type { NextRequest, NextResponse } from "next/server";

export const ACCESS_TOKEN_COOKIE_NAME = "access_token";
export const REFRESH_TOKEN_COOKIE_NAME = "refresh_token";
export const ANONYMOUS_CONCIERGE_COOKIE_NAME = "concierge_anon_id";

export const ACCESS_TOKEN_COOKIE_MAX_AGE_SECONDS = 60 * 60;
export const REFRESH_TOKEN_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 7;
export const ANONYMOUS_CONCIERGE_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 90;

/**
 * この request に対して `Secure` 属性を立てるべきか。
 *
 * 判定は /api/auth/login が持っていた `isSecureCookie` をそのまま移設したもの
 * で、挙動は変えていない（production 以外は false / x-forwarded-proto を優先）。
 */
export function isSecureRequest(req: NextRequest): boolean {
  if (process.env.NODE_ENV !== "production") return false;

  const xfProto = req.headers.get("x-forwarded-proto");
  const proto = (xfProto ? xfProto.split(",")[0].trim() : req.nextUrl.protocol.replace(":", "")).toLowerCase();

  return proto === "https";
}

export type AuthCookieWriteOptions = {
  /** 通常は isSecureRequest(req) の結果を渡す。 */
  secure: boolean;
};

export function setAccessTokenCookie(
  res: NextResponse,
  value: string,
  { secure }: AuthCookieWriteOptions,
): void {
  res.cookies.set(ACCESS_TOKEN_COOKIE_NAME, value, {
    httpOnly: true,
    secure,
    sameSite: "lax",
    path: "/",
    maxAge: ACCESS_TOKEN_COOKIE_MAX_AGE_SECONDS,
  });
}

export function setRefreshTokenCookie(
  res: NextResponse,
  value: string,
  { secure }: AuthCookieWriteOptions,
): void {
  res.cookies.set(REFRESH_TOKEN_COOKIE_NAME, value, {
    httpOnly: true,
    secure,
    sameSite: "lax",
    path: "/",
    maxAge: REFRESH_TOKEN_COOKIE_MAX_AGE_SECONDS,
  });
}

/**
 * 匿名 Concierge の identity cookie（Web origin 側のコピー）。
 *
 * SameSite:
 *   この cookie は BFF が **Web origin** に対して発行するもので、読み戻すのも
 *   同一オリジンの /api/concierge/** だけである（Backend が Backend origin へ
 *   発行する同名 cookie は別の cookie jar にあり、`SameSite=None` のまま
 *   backend/temples/services/anonymous_id.py の契約に従う。Mobile は BFF を
 *   経由せず Backend を直接叩くため、この変更の影響を受けない）。
 *   したがって Web origin 側は他の認証 cookie と同じ `Lax` で足りる。
 *   もし将来 Web を cross-site へ埋め込む要件が出たら、ここを `none` に戻し、
 *   `secure` を無条件 true にする必要がある（`None` は `Secure` を要求する）。
 *
 * Secure:
 *   以前は無条件 true だったため、http のローカル開発ではブラウザがこの cookie
 *   を破棄し、匿名スレッドの継続が壊れていた（E2E-020）。
 */
export function setAnonymousConciergeCookie(
  res: NextResponse,
  value: string,
  { secure }: AuthCookieWriteOptions,
): void {
  res.cookies.set(ANONYMOUS_CONCIERGE_COOKIE_NAME, value, {
    httpOnly: true,
    secure,
    sameSite: "lax",
    path: "/",
    maxAge: ANONYMOUS_CONCIERGE_COOKIE_MAX_AGE_SECONDS,
  });
}
