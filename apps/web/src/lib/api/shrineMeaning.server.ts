import "server-only";

import type { ShrineMeaningPayloadV2 } from "@/lib/shrineMeaning/payloadV2";
import { isShrineMeaningPayloadV2 } from "@/lib/api/shrineMeaning";
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

/**
 * Server-side reader for ShrineMeaningPayloadV2.
 *
 * 方針:
 * - Server Component から呼ぶため absolute URL を使う
 * - 取得失敗時は null を返し、詳細画面では既存 fallback を維持する
 */
export async function fetchShrineMeaningPayloadV2Server(
  shrineId: number,
): Promise<ShrineMeaningPayloadV2 | null> {
  if (!Number.isFinite(shrineId) || shrineId <= 0) {
    return null;
  }

  try {
    const base = resolveBackendPublicBaseUrl() ?? (await resolveServerBaseUrl());
    const url = `${base}/api/shrines/${encodeURIComponent(String(shrineId))}/meaning/`;

    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) {
      return null;
    }

    const data = (await res.json()) as unknown;
    return isShrineMeaningPayloadV2(data) ? data : null;
  } catch {
    return null;
  }
}
