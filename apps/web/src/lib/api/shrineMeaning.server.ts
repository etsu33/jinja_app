import "server-only";

import { cookies, headers } from "next/headers";

import type { ShrineMeaningPayloadV2 } from "@/lib/shrineMeaning/payloadV2";
import { isShrineMeaningPayloadV2 } from "@/lib/api/shrineMeaning";
import { getDjangoOrigin } from "@/lib/server/backend";
import { clientIdentityHeaders, clientIdentitySigningEnabled, isBackendUrl } from "@/lib/server/clientIdentity";
import { resolveServerBaseUrl } from "@/lib/server/resolveServerBaseUrl";

/**
 * Server-side reader for ShrineMeaningPayloadV2.
 *
 * 方針:
 * - Premium / Free 判定は Backend（resolve_plan_context → shape_shrine_meaning_payload_for_plan）を正本とする
 * - 取得失敗時は null を返し、詳細画面では既存 fallback を維持する
 *
 * 経路（FU-2-P2, docs/audit/fu2-shrine-meaning-ssr-boundary-2026-10-27.md §6）:
 * - auth context（Authorization ヘッダ / access_token / refresh_token cookie）が 1 つでもある request:
 *   従来どおり Next.js BFF を経由し、現在の request Cookie を BFF へ引き継ぐ（JWT・refresh・Premium は BFF の責務のまま）
 * - auth context が無い request（anonymous）: server-only の Backend origin（getDjangoOrigin）を直接呼ぶ。
 *   Cookie / Authorization は付けない（Django は anonymous としか判定できず、anonymous と free は同一 shaping）。
 *   このページ request の client identity を WS-04 の HMAC で署名する。以前は BFF 経由のため、Backend には
 *   Vercel function の egress が identity として届いていた（FU-1 P2）。
 */

const AUTH_COOKIE_NAMES = ["access_token", "refresh_token"] as const;
const SIGNED_METHOD = "GET";

/** auth context を持つか。判定できないときは true（BFF 経由 = 従来の経路）に倒す。 */
async function hasAuthContext(): Promise<boolean> {
  try {
    const requestHeaders = await headers();
    if (requestHeaders.get("authorization")) return true;
    const cookieStore = await cookies();
    return AUTH_COOKIE_NAMES.some((name) => cookieStore.has(name));
  } catch {
    return true;
  }
}

// 署名できる環境（Vercel 上・secret 設定済み・宛先が設定済みの Backend origin）でだけ headers() を読む。
// ブラウザが送った X-KM-* は読まない・転送しない（署名は clientIdentityHeaders が Vercel の x-forwarded-for から作る）。
async function pageIdentityHeaders(upstream: string): Promise<Record<string, string>> {
  if (!clientIdentitySigningEnabled() || !isBackendUrl(upstream)) return {};
  try {
    return clientIdentityHeaders({ headers: await headers() }, SIGNED_METHOD, upstream);
  } catch {
    // 署名なしで続行し、Backend は edge の peer identity を使う（WS-04 fail-safe）。
    return {};
  }
}

async function fetchViaBff(path: string): Promise<Response> {
  const base = await resolveServerBaseUrl();

  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();

  return fetch(`${base}${path}`, {
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...(cookieHeader ? { Cookie: cookieHeader } : {}),
    },
  });
}

async function fetchAnonymousDirect(path: string): Promise<Response> {
  const upstream = `${getDjangoOrigin()}${path}`;

  return fetch(upstream, {
    method: SIGNED_METHOD,
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...(await pageIdentityHeaders(upstream)),
    },
  });
}

export async function fetchShrineMeaningPayloadV2Server(
  shrineId: number,
): Promise<ShrineMeaningPayloadV2 | null> {
  if (!Number.isFinite(shrineId) || shrineId <= 0) {
    return null;
  }

  try {
    const path = `/api/shrines/${encodeURIComponent(String(shrineId))}/meaning/`;

    const res = (await hasAuthContext()) ? await fetchViaBff(path) : await fetchAnonymousDirect(path);

    if (!res.ok) {
      return null;
    }

    const data = (await res.json()) as unknown;

    return isShrineMeaningPayloadV2(data) ? data : null;
  } catch {
    return null;
  }
}
