// apps/web/src/features/concierge/travel/buildTravelChatPayload.ts
//
// 英語の相談ページ（/en/concierge・限定公開）から送る相談の中身を組み立てる。
// - mode は "travel"（旅行・文化体験の推薦モード）、language は "en"。言語とモードは別々に持つ。
// - backend は travel モードのときだけ、相談文から英語の特徴語を取り出して記録する。
//   並び順はまだ need と同じ（travel 専用の点数は後の段）。
// - 出発地点はブラウザの現在地。取れなかったときは lat/lng を送らない。

export type TravelOrigin = { lat: number; lng: number };

export type TravelChatPayload = {
  query: string;
  mode: "travel";
  language: "en";
  lat?: number;
  lng?: number;
};

export function buildTravelChatPayload(query: string, origin: TravelOrigin | null): TravelChatPayload | null {
  const text = query.trim();
  if (!text) return null;

  const payload: TravelChatPayload = { query: text, mode: "travel", language: "en" };
  if (origin && Number.isFinite(origin.lat) && Number.isFinite(origin.lng)) {
    payload.lat = origin.lat;
    payload.lng = origin.lng;
  }
  return payload;
}

// backend の応答から、カードに出す分だけを取り出す（形が違っても落ちないようにする）。
export type TravelRecommendation = {
  key: string;
  name: string;
  href: string | null;
  reason: string | null;
  address: string | null;
  distanceM: number | null;
};

type RawRecommendation = {
  name?: unknown;
  display_name?: unknown;
  shrine_id?: unknown;
  id?: unknown;
  reason?: unknown;
  address?: unknown;
  distance_m?: unknown;
};

function asText(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function asId(value: unknown): number | null {
  const n = typeof value === "string" ? Number(value) : value;
  return typeof n === "number" && Number.isInteger(n) && n > 0 ? n : null;
}

export function pickTravelRecommendations(body: unknown): TravelRecommendation[] {
  const data = (body as { data?: { recommendations?: unknown } } | null)?.data;
  const list = Array.isArray(data?.recommendations) ? (data?.recommendations as RawRecommendation[]) : [];

  return list
    .map((rec, index) => {
      const name = asText(rec?.display_name) ?? asText(rec?.name);
      if (!name) return null;
      const id = asId(rec?.shrine_id) ?? asId(rec?.id);
      const distance = typeof rec?.distance_m === "number" && Number.isFinite(rec.distance_m) ? rec.distance_m : null;
      return {
        key: id ? `shrine-${id}` : `rec-${index}`,
        name,
        href: id ? `/shrines/${id}` : null,
        reason: asText(rec?.reason),
        address: asText(rec?.address),
        distanceM: distance,
      };
    })
    .filter((rec): rec is TravelRecommendation => rec !== null);
}
