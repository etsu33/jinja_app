// apps/web/src/lib/maps/destinationContract.ts
//
// Google Maps 経路案内URLへ `destination`（目的地）を渡すときの共通契約。
//
// 契約:
//   1. lat/lng が両方とも有効座標なら座標を使う
//   2. 座標が無効なら trim 後に空でない address を使う
//   3. address もなければ trim 後に空でない fallbackName を使う
//   4. どれも無いなら destination を「捏造しない」— 呼び出し側へ不在を返す
//
// 東京駅（35.681236, 139.767125 / "東京駅"）は Nearby 検索が現在地を取れない
// ときに使う検索用 fallback であり、経路案内の目的地ではない。ここで暗黙の
// destination として使ってはならない（ユーザーが意図していない場所への経路を
// 提示してしまうため）。Nearby 検索側の東京駅 fallback は本契約の対象外で、
// 変更しない。
//
// 座標の有効条件は origin 側（originContract.ts の toValidOrigin）と同一の
// 判定を destination 用に定義したもの。origin contract は本PRのスコープ外の
// ため参照せず、ここで独立に定義している（両者を1つのprimitiveへ寄せる
// 統合は別PRの候補）。

export type GeoDestination = { lat: number; lng: number };

/**
 * destination として Google Maps に渡してよい座標だけを返す。
 *
 * 有効条件（すべて満たすこと）:
 * - lat/lng が両方 number（片方だけは無効）
 * - Number.isFinite（NaN / ±Infinity を除外）
 * - lat が -90..90
 * - lng が -180..180
 *
 * 日本国内かどうかの bounds 判定は行わない（WGS84 の値域のみを見る）。
 */
export function toValidDestinationCoords(
  candidate: { lat?: number | null; lng?: number | null } | null | undefined,
): GeoDestination | undefined {
  if (!candidate) return undefined;

  const { lat, lng } = candidate;
  if (typeof lat !== "number" || typeof lng !== "number") return undefined;
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return undefined;
  if (lat < -90 || lat > 90) return undefined;
  if (lng < -180 || lng > 180) return undefined;

  return { lat, lng };
}

export type DestinationInput = {
  lat?: number | null;
  lng?: number | null;
  address?: string | null;
  /** 座標も住所も無いときに使う表示名（神社名など）。 */
  fallbackName?: string | null;
};

export type ResolvedDestination = {
  /** どの候補が採用されたか。呼び出し側のログ/分岐用。 */
  kind: "coords" | "address" | "name";
  /** Google Maps の `destination=` に入れる生の値（URLエンコード前）。 */
  value: string;
};

function trimmedOrNull(value: string | null | undefined): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

/**
 * destination 候補を契約どおりの優先順位で解決する。
 * 候補が1つも無ければ `null`（= 経路案内を提示できない）を返す。
 * 東京駅などの既定値へは決してフォールバックしない。
 */
export function resolveDestination(dest: DestinationInput | null | undefined): ResolvedDestination | null {
  if (!dest) return null;

  const coords = toValidDestinationCoords(dest);
  if (coords) return { kind: "coords", value: `${coords.lat},${coords.lng}` };

  const address = trimmedOrNull(dest.address);
  if (address) return { kind: "address", value: address };

  const name = trimmedOrNull(dest.fallbackName);
  if (name) return { kind: "name", value: name };

  return null;
}
