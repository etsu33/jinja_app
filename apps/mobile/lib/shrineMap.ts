// apps/mobile/lib/shrineMap.ts
import { get } from "./http";

// latitude/longitudeは片方でも欠けている・不正な場合はnullにする。
// 座標欠損神社も一覧・選択・詳細遷移の対象として残すため、Marker表示可否の判定は
// hasValidCoordinatesで別途行い、このtype自体では除外しない。
export type ShrineMapPoint = {
  id: string;
  name: string;
  latitude: number | null;
  longitude: number | null;
  address?: string;
  imageUrl?: string;
};

// Native/Web両方のShrineSearchMapが共有するProps契約。
// 片方だけ型を変えて挙動が乖離しないよう、両ファイルはこの型をそのまま使う。
export type ShrineSearchMapProps = {
  points: ShrineMapPoint[];
  selectedId: string | null;
  onSelect: (id: string) => void;
};

export function hasValidCoordinates(
  point: ShrineMapPoint,
): point is ShrineMapPoint & { latitude: number; longitude: number } {
  return point.latitude !== null && point.longitude !== null;
}

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
 * id・nameが欠けている項目は除外する。座標が数値として有効でない項目は
 * 除外せず、latitude/longitudeをnullにして一覧・選択の対象として残す
 * (Marker表示のみhasValidCoordinatesで別途絞り込む)。
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
    const latitudeRaw = toFiniteNumber(record.latitude ?? location?.lat);
    const longitudeRaw = toFiniteNumber(record.longitude ?? location?.lng);
    const validPair =
      latitudeRaw !== null && longitudeRaw !== null && isValidLatitude(latitudeRaw) && isValidLongitude(longitudeRaw);
    const latitude = validPair ? latitudeRaw : null;
    const longitude = validPair ? longitudeRaw : null;

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
 * Search画面が利用している神社一覧APIから、地図・一覧表示用のデータを取得する。
 * 座標欠損神社も一覧・選択の対象として含まれる。
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
