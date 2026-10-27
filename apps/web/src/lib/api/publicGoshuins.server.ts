import "server-only";
import { headers } from "next/headers";
import type { PublicGoshuinItem } from "@/components/shrine/detail/PublicGoshuinSection";
import { getDjangoOrigin } from "@/lib/server/backend";
import { clientIdentityHeaders, clientIdentitySigningEnabled, isBackendUrl } from "@/lib/server/clientIdentity";

// SSR の公開御朱印一覧（神社詳細・/shrines/[id]/goshuins）。
//
// FU-2-A2（docs/audit/fu1-ssr-anonymous-identity-design-2026-10-26.md, Option A / P3）:
// 以前は自アプリの BFF（/api/public/goshuins）を HTTP で呼んでいたため、Backend にはこのページ request の
// client identity ではなく Vercel function の egress が届いていた。ここでは server-only の Backend origin
// （getDjangoOrigin: DJANGO_ORIGIN → BACKEND_ORIGIN）を直接呼び、このページ request の identity を WS-04 の
// HMAC で署名する。request の Host / X-Forwarded-Host は宛先の決定に使わない。
//
// 表示結果は BFF 経由のときと同じにする: 同じ upstream（is_public=true&shrine=…）、Backend の並び順のまま
// 先頭 12 件、BFF route と同じ image URL 正規化、そのあと従来どおりの項目 mapping。失敗はすべて [] に倒す。
// BFF route（app/api/public/goshuins/route.ts）はブラウザ等の既存 caller 向けに変更せず残す。

const DISPLAY_LIMIT = 12;
const SIGNED_METHOD = "GET";

/** app/api/public/goshuins/route.ts の normalizeImageUrl と同じ規則（Backend の local / 相対 media URL を origin へ寄せる）。 */
function normalizeImageUrl(url: string | null | undefined, origin: string): string | null {
  const u = (url ?? "").trim();
  if (!u) return null;

  const base = origin.replace(/\/+$/, "");
  if (u.startsWith("http://127.0.0.1:8000/")) return `${base}${u.slice("http://127.0.0.1:8000".length)}`;
  if (u.startsWith("http://localhost:8000/")) return `${base}${u.slice("http://localhost:8000".length)}`;
  if (u.startsWith("/media/")) return `${base}${u}`;
  return u;
}

// 署名できる環境（Vercel 上・secret 設定済み・宛先が設定済みの Backend origin）でだけ headers() を読む。
// ブラウザが送った X-KM-* は読まない・転送しない（署名は clientIdentityHeaders が Vercel の x-forwarded-for から作る）。
async function pageIdentityHeaders(upstream: string): Promise<Record<string, string>> {
  if (!clientIdentitySigningEnabled() || !isBackendUrl(upstream)) return {};
  try {
    return clientIdentityHeaders({ headers: await headers() }, SIGNED_METHOD, upstream);
  } catch {
    // request scope の外など。署名なしで続行し、Backend は edge の peer identity を使う（fail-safe）。
    return {};
  }
}

export async function fetchPublicGoshuinsForShrineServer(shrineId: number): Promise<PublicGoshuinItem[]> {
  const shrine = Number(shrineId);
  // BFF route と同じ: shrine が無い（0 / NaN）なら呼ばない（route は 400 → 従来の SSR は []）。
  if (!shrine || !Number.isFinite(shrine)) return [];

  const origin = getDjangoOrigin();
  const upstream = `${origin}/api/goshuins/?is_public=true&shrine=${encodeURIComponent(String(shrine))}`;

  try {
    const res = await fetch(upstream, {
      method: SIGNED_METHOD,
      cache: "no-store",
      headers: { Accept: "application/json", ...(await pageIdentityHeaders(upstream)) },
    });

    // ログには Backend URL・header・IP・署名を出さない（shrineId と status / 件数だけ）。
    const contentType = res.headers.get("content-type") ?? "";
    if (!res.ok || !contentType.includes("application/json")) {
      console.error("[publicGoshuins.server] upstream not ok", { shrineId: shrine, status: res.status });
      return [];
    }

    const json: any = await res.json();
    const all: any[] = Array.isArray(json) ? json : Array.isArray(json?.results) ? json.results : [];
    const raw = all.slice(0, DISPLAY_LIMIT).map((g) => ({ ...g, image_url: normalizeImageUrl(g?.image_url ?? null, origin) }));

    console.log("[publicGoshuins.server] fetched", { shrineId: shrine, count: raw.length });

    return raw
      .map((g) => ({
        id: Number(g.id),
        title: g.title ?? null,
        created_at: g.created_at ?? null,
        image_url:
          g.image_url ??
          g.imageUrl ??
          g.image?.url ??
          g.images?.[0]?.image_url ??
          g.images?.[0]?.imageUrl ??
          g.images?.[0]?.image ??
          g.images?.[0]?.url ??
          null,
      }))
      .filter((g) => Number.isFinite(g.id));
  } catch (e) {
    console.error("[publicGoshuins.server] fetch failed", {
      shrineId: shrine,
      message: e instanceof Error ? e.message : String(e),
    });
    return [];
  }
}
