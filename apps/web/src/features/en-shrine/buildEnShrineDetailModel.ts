// 英語の神社詳細（/en/shrines/{id}）に出す中身を組み立てる。
//
// 枠の順（インバウンド向け神社選定・情報設計ルール v1.1 の5章）:
//   1 写真 / 2 神社名・所在地 / 3 訪れる価値の一言 / 4 歴史・文化 / 5 景観・季節・体験 /
//   6 参拝の情報・距離・ルート / 7 参拝作法・ご利益
// 今出すのは 2 → 4 → 5 → 6 だけ。1（写真）・3（出典のある英語の一言）・7（英語のデータ）は
// データが無いので出さない。推測や AI の文で埋めない。推薦理由・ご縁・ご利益の文も作らない。
import { gmapsDirUrl } from "@/lib/maps";

export type EnFeatureWordSlot = "history_culture" | "scenery_experience";

export type EnFeatureWord = {
  wordId: string;
  labelEn: string;
  slot: EnFeatureWordSlot;
  sourceUrl: string;
  checkedOn: string | null;
};

export type EnShrineBasics = {
  id: number;
  nameJa: string;
  nameRomaji: string | null;
  address: string | null;
  lat: number | null;
  lng: number | null;
};

export type EnShrineSection =
  | { kind: "name_location"; nameJa: string; nameRomaji: string | null; address: string | null }
  | { kind: "history_culture"; words: EnFeatureWord[] }
  | { kind: "scenery_experience"; words: EnFeatureWord[] }
  | { kind: "no_feature_words" }
  | { kind: "visit"; distanceText: string | null; routeUrl: string | null };

function asText(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function asNumber(value: unknown): number | null {
  const n = typeof value === "string" && value.trim() ? Number(value) : value;
  return typeof n === "number" && Number.isFinite(n) ? n : null;
}

/** 神社データ（/api/shrines/{id}/data/）から、英語の詳細に使う項目だけを取り出す。 */
export function pickEnShrineBasics(raw: unknown, id: number): EnShrineBasics | null {
  if (!raw || typeof raw !== "object") return null;
  const r = raw as Record<string, unknown>;
  const nameJa = asText(r.name_jp) ?? asText(r.name);
  if (!nameJa) return null;
  return {
    id,
    nameJa,
    nameRomaji: asText(r.name_romaji),
    address: asText(r.address),
    lat: asNumber(r.latitude ?? r.lat),
    lng: asNumber(r.longitude ?? r.lng),
  };
}

/** 特徴語（/api/shrines/{id}/feature-words-en/）を取り出す。形の違う項目は捨てる。 */
export function pickEnFeatureWords(raw: unknown): EnFeatureWord[] {
  const items = (raw as { items?: unknown } | null)?.items;
  if (!Array.isArray(items)) return [];
  return items.flatMap((item) => {
    if (!item || typeof item !== "object") return [];
    const r = item as Record<string, unknown>;
    const wordId = asText(r.word_id);
    const labelEn = asText(r.label_en);
    const sourceUrl = asText(r.source_url);
    const slot = r.slot === "history_culture" || r.slot === "scenery_experience" ? r.slot : null;
    if (!wordId || !labelEn || !sourceUrl || !slot || !/^https?:\/\//.test(sourceUrl)) return [];
    return [{ wordId, labelEn, slot, sourceUrl, checkedOn: asText(r.checked_on) }];
  });
}

/** 2点間の距離（メートル）。 */
export function distanceMeters(a: { lat: number; lng: number }, b: { lat: number; lng: number }): number {
  const R = 6371000;
  const toRad = (d: number) => (d * Math.PI) / 180;
  const dLat = toRad(b.lat - a.lat);
  const dLng = toRad(b.lng - a.lng);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

/** 英語の距離の表示（例: "850 m away" / "3.2 km away"）。 */
export function formatDistanceEn(meters: number): string {
  if (meters < 1000) return `${Math.round(meters)} m away`;
  return `${(meters / 1000).toFixed(1)} km away`;
}

export function buildEnShrineSections(args: {
  shrine: EnShrineBasics;
  featureWords: EnFeatureWord[];
  origin?: { lat: number; lng: number } | null;
}): EnShrineSection[] {
  const { shrine, featureWords, origin } = args;
  const history = featureWords.filter((w) => w.slot === "history_culture");
  const scenery = featureWords.filter((w) => w.slot === "scenery_experience");
  const hasLocation = shrine.lat !== null && shrine.lng !== null;
  const dest = hasLocation ? { lat: shrine.lat as number, lng: shrine.lng as number } : null;

  const sections: EnShrineSection[] = [
    { kind: "name_location", nameJa: shrine.nameJa, nameRomaji: shrine.nameRomaji, address: shrine.address },
  ];
  if (history.length) sections.push({ kind: "history_culture", words: history });
  if (scenery.length) sections.push({ kind: "scenery_experience", words: scenery });
  if (!history.length && !scenery.length) sections.push({ kind: "no_feature_words" });

  const distanceText = dest && origin ? formatDistanceEn(distanceMeters(origin, dest)) : null;
  // 出発地点は URL に入れない（Google マップ側で現在地から案内する）。
  const routeUrl = dest ? gmapsDirUrl({ dest }) : null;
  if (distanceText || routeUrl) sections.push({ kind: "visit", distanceText, routeUrl });
  return sections;
}
