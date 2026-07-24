// apps/mobile/lib/shrineMap.ts
import { get } from "./http";

export type ShrineMapPoint = {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  address?: string;
  imageUrl?: string;
};

function toFiniteNumber(value: unknown): number | null {
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  if (typeof value === "string" && value.trim().length > 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function isValidLatitude(value: number): boolean {
  return value >= -90 && value <= 90;
}

function isValidLongitude(value: number): boolean {
  return value >= -180 && value <= 180;
}

/**
 * APIレスポンスの生データを安全にShrineMapPointへ変換する。
 * id・nameが欠けている、または座標が数値として有効でない項目は除外する。
 */
export function toShrineMapPoints(raw: unknown): ShrineMapPoint[] {
  const items: unknown[] = Array.isArray(raw)
    ? raw
    : Array.isArray((raw as any)?.results)
      ? (raw as any).results
      : Array.isArray((raw as any)?.items)
        ? (raw as any).items
        : [];

  const points: ShrineMapPoint[] = [];

  for (const item of items) {
    if (!item || typeof item !== "object") continue;
    const record = item as Record<string, unknown>;

    const idRaw = record.id;
    if (idRaw === null || idRaw === undefined || idRaw === "") continue;
    const id = String(idRaw);

    const name = String(record.name_jp ?? record.name ?? "").trim();
    if (!name) continue;

    const location = (record.location ?? null) as { lat?: unknown; lng?: unknown } | null;
    const latitude = toFiniteNumber(record.latitude ?? location?.lat);
    const longitude = toFiniteNumber(record.longitude ?? location?.lng);
    if (latitude === null || longitude === null) continue;
    if (!isValidLatitude(latitude) || !isValidLongitude(longitude)) continue;

    const address = typeof record.address === "string" && record.address.trim() ? record.address.trim() : undefined;
    const imageUrl =
      typeof record.imageUrl === "string"
        ? record.imageUrl
        : typeof record.image_url === "string"
          ? record.image_url
          : typeof record.photo_url === "string"
            ? record.photo_url
            : undefined;

    points.push({ id, name, latitude, longitude, address, imageUrl });
  }

  return points;
}

export type FetchShrineMapPointsParams = {
  query?: string;
  limit?: number;
};

/**
 * Search画面が利用している神社一覧APIから、地図表示用の安全な座標データだけを取得する。
 * 失敗時は例外を投げず、呼び出し側でLoading/Errorを制御できるようにErrorを再送出する。
 */
export async function fetchShrineMapPoints(params: FetchShrineMapPointsParams = {}): Promise<ShrineMapPoint[]> {
  const qs = new URLSearchParams();
  if (params.query && params.query.trim()) qs.set("q", params.query.trim());
  if (params.limit) qs.set("limit", String(params.limit));

  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  const raw = await get<unknown>(`/shrines/${suffix}`);
  return toShrineMapPoints(raw);
}
