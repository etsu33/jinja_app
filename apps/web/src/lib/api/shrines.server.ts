// apps/web/src/lib/api/shrines.server.ts
import "server-only";
import type { Shrine } from "./types";

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
// Public API（/api/public/shrines/{id}/）は/navi/[id]専用として維持し、ここでは呼ばない。
export async function getShrineDetailServer(id: number): Promise<Shrine> {
  const base = resolveBackendPublicBaseUrl() ?? (await resolveServerBaseUrl());
  const url = `${base}/api/shrines/${id}/data/`;

  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    const body = await res.text().catch(() => "<failed to read body>");
    throw new Error(`getShrineDetailServer failed: ${res.status} body=${body.slice(0, 300)}`);
  }

  return (await res.json()) as Shrine;
}
