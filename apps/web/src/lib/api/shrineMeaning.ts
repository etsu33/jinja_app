

import type { ShrineMeaningPayloadV2 } from "@/lib/shrineMeaning/payloadV2";

/**
 * Fetch ShrineMeaningPayloadV2 for shrine detail.
 *
 * 方針:
 * - 成功時は ShrineMeaningPayloadV2 を返す
 * - 失敗時は null を返す
 * - detail page 側では null の場合に buildShrineExplanation fallback を使う
 */
export async function fetchShrineMeaningPayloadV2(shrineId: number): Promise<ShrineMeaningPayloadV2 | null> {
  if (!Number.isFinite(shrineId) || shrineId <= 0) {
    return null;
  }

  try {
    const res = await fetch(`/api/shrines/${encodeURIComponent(String(shrineId))}/meaning/`, {
      cache: "no-store",
    });

    if (!res.ok) {
      return null;
    }

    const data = (await res.json()) as unknown;

    if (!isShrineMeaningPayloadV2(data)) {
      return null;
    }

    return data;
  } catch {
    return null;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function isShrineMeaningPayloadV2(value: unknown): value is ShrineMeaningPayloadV2 {
  if (!isRecord(value)) return false;
  if (value.version !== "v2") return false;
  if (!isRecord(value.source)) return false;
  if (!isRecord(value.generated)) return false;
  if (!isRecord(value.display)) return false;

  const source = value.source;
  const generated = value.generated;
  const display = value.display;

  if (typeof source.shrineId !== "number") return false;
  if (typeof source.nameJp !== "string") return false;

  if (typeof generated.heroMeaningCopy !== "string") return false;
  if (typeof generated.consultationSummary !== "string") return false;
  if (typeof generated.shrineMeaning !== "string") return false;
  if (typeof generated.actionMeaning !== "string") return false;

  if (!Array.isArray(display.blocks)) return false;

  return true;
}
