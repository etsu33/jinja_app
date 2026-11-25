// apps/web/src/lib/api/shrines.server.ts
import "server-only";
import { headers } from "next/headers";
import type { Shrine } from "./types";

import {
  clientIdentityHeaders,
  clientIdentitySigningEnabled,
  isBackendUrl,
} from "@/lib/server/clientIdentity";
import { resolveServerBaseUrl } from "@/lib/server/resolveServerBaseUrl";

function normalizeBaseUrl(value: string): string {
  return value.replace(/\/$/, "");
}

function resolveBackendPublicBaseUrl(): string | null {
  const raw =
    process.env.DJANGO_API_BASE_URL ||
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    null;

  return raw ? normalizeBaseUrl(raw) : null;
}

// 通常Detail API（/api/shrines/{id}/data/、ShrineViewSet.retrieve）を使用する。
// AllowAnyのためanonymous SSR fetchのまま（認証headerは付けない）。
// Shrine詳細のupstreamはこの通常Detail APIに一本化されている。
//
// WS-04: Django を直接呼ぶときだけ、このページ request の client identity を BFF と同じ HMAC 方式で署名する。
// 自アプリの BFF（resolveServerBaseUrl）を経由する fallback では付けない。BFF 側は自分が受けた request から
// identity を決めるため、ここで付けても使われず、署名を Backend 以外へ送ることにもなる。
// headers() は署名できる環境（Vercel 上・secret 設定済み・Backend 直行）でだけ読む。
async function shrineDetailIdentityHeaders(url: string): Promise<Record<string, string>> {
  if (!clientIdentitySigningEnabled() || !isBackendUrl(url)) return {};
  return clientIdentityHeaders({ headers: await headers() }, "GET", url);
}

export async function getShrineDetailServer(id: number): Promise<Shrine> {
  const base = resolveBackendPublicBaseUrl() ?? (await resolveServerBaseUrl());
  const url = `${base}/api/shrines/${id}/data/`;

  const identity = await shrineDetailIdentityHeaders(url);
  const res = await fetch(
    url,
    Object.keys(identity).length > 0 ? { cache: "no-store", headers: identity } : { cache: "no-store" },
  );
  if (!res.ok) {
    const body = await res.text().catch(() => "<failed to read body>");
    throw new Error(`getShrineDetailServer failed: ${res.status} body=${body.slice(0, 300)}`);
  }

  return (await res.json()) as Shrine;
}
