// apps/mobile/lib/popularShrines.ts
//
// Search画面「人気の神社」・Ranking画面が共通で利用する、Backend正本API
// (`GET /api/populars/`, `temples.api.views.shrine.PopularShrineListView`)の
// 取得・変換のみを責務とするhelper。
//
// 実際のResponseは`{count, next, previous, results: [...]}`(DRF PageNumberPagination、
// page_size=10固定・`limit`クエリは無視される)であり、各項目は`ShrineListSerializer`の
// フィールド(id, kind, name_jp, address, latitude, longitude, goriyaku_tags, distance,
// distance_text, location, kyusei)のみを持つ。画像・評価値・お気に入り数は含まれないため、
// このhelperではそれらを推測で補わず、実在するフィールドのみをMobile表示用の形へ変換する。
//
// 並び順はBackendの`results`配列順(popular_score降順)をそのまま維持し、Mobile側で
// 再ソート・再計算は行わない。
import { get } from "./http";

export type PopularShrine = {
  id: string;
  name: string;
  address?: string;
};

function toPopularShrines(raw: unknown): PopularShrine[] {
  const items: unknown[] = Array.isArray(raw)
    ? raw
    : Array.isArray((raw as { results?: unknown } | null)?.results)
      ? ((raw as { results: unknown[] }).results)
      : Array.isArray((raw as { items?: unknown } | null)?.items)
        ? ((raw as { items: unknown[] }).items)
        : [];

  const shrines: PopularShrine[] = [];

  for (const item of items) {
    if (!item || typeof item !== "object") continue;
    const record = item as Record<string, unknown>;

    const idRaw = record.id;
    if (idRaw === null || idRaw === undefined || idRaw === "") continue;
    const id = String(idRaw);

    const name = String(record.name_jp ?? record.name ?? "").trim();
    if (!name) continue;

    const address = typeof record.address === "string" && record.address.trim() ? record.address.trim() : undefined;

    shrines.push({ id, name, address });
  }

  return shrines;
}

/**
 * `/populars/`から人気神社一覧を取得する。Backendが既に並び替え済みの順序を
 * そのまま維持し、Mobile側での再ソートは行わない。
 * 失敗時は例外を投げ、呼び出し側でloading/error/emptyを制御できるようにする
 * (`fetchShrineMapPoints`と同じ契約)。空配列は正常な結果として扱う。
 */
export async function fetchPopularShrines(): Promise<PopularShrine[]> {
  const raw = await get<unknown>("/populars/");
  return toPopularShrines(raw);
}

export const __internal = { toPopularShrines };
