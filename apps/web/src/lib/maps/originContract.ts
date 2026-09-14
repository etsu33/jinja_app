// apps/web/src/lib/maps/originContract.ts
//
// Google Maps 経路案内URLへ `origin`（出発地）を渡すときの共通契約。
//
// 実装関数は画面ごとに分かれている（Map画面: buildGoogleMapsDirUrl /
// `/navi/[id]`・`/shrines/[id]`: gmapsDirUrl）が、
// 「どんな座標なら origin として Google Maps に渡してよいか」という挙動契約は
// ここに一本化する。
//
// 契約:
//   - 実際に取得できた現在地のみを origin にする
//   - 取得失敗（拒否 / timeout / 非対応 / その他）のときは origin を付けない
//   - 検索用の fallback 座標（例: 東京駅）は origin にしない
//
// 注意: fallback 座標かどうかはこの関数では判定できない。
// 東京駅の座標そのものを弾いてしまうと、実際に東京駅にいるユーザーの現在地まで
// 捨てることになるため、「fallback を使用中か」の判定は呼び出し側の状態
// （例: Map画面の `usedFallback`）が責務を持つ。
// この関数は座標そのものの妥当性（number / finite / 緯度経度の有効範囲）だけを見る。

export type GeoOrigin = { lat: number; lng: number };

export function toValidOrigin(
  candidate: { lat?: number | null; lng?: number | null } | null | undefined,
): GeoOrigin | undefined {
  if (!candidate) return undefined;

  const { lat, lng } = candidate;
  if (typeof lat !== "number" || typeof lng !== "number") return undefined;
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return undefined;
  if (lat < -90 || lat > 90) return undefined;
  if (lng < -180 || lng > 180) return undefined;

  return { lat, lng };
}
