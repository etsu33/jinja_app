// apps/web/src/lib/maps/googleMaps.ts

import { toValidOrigin } from "./originContract";

function enc(v: string) {
  return encodeURIComponent(v);
}

export function buildGoogleMapsSearchUrl(name: string, address?: string) {
  const q = address ? `${name} ${address}` : name;
  return `https://www.google.com/maps/search/?api=1&query=${enc(q)}`;
}

/**
 * Google Maps の経路案内URLを生成する。
 *
 * destination: 既存仕様を維持する（lat/lng → address → fallbackName）。
 * origin: `toValidOrigin()` を通過した場合のみ付与する（`originContract.ts` 参照）。
 *   現在地が取れていない・fallback 座標しかない場合は origin を付けず、
 *   従来どおり destination だけで Google Maps を開く。
 */
export function buildGoogleMapsDirUrl(params: {
  origin?: { lat?: number | null; lng?: number | null } | null;
  destination: { lat?: number; lng?: number; address?: string; fallbackName?: string };
}) {
  const dest = params.destination;

  const destinationParam =
    typeof dest.lat === "number" && typeof dest.lng === "number"
      ? `${dest.lat},${dest.lng}`
      : dest.address
        ? dest.address
        : (dest.fallbackName ?? "東京駅");

  let url = `https://www.google.com/maps/dir/?api=1&destination=${enc(destinationParam)}`;

  const origin = toValidOrigin(params.origin);
  if (origin) url += `&origin=${enc(`${origin.lat},${origin.lng}`)}`;

  return url;
}
