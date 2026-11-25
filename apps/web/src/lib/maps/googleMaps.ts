// apps/web/src/lib/maps/googleMaps.ts

import { resolveDestination, type DestinationInput } from "./destinationContract";
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
 * destination: `resolveDestination()` の契約に従う（`destinationContract.ts` 参照）。
 *   有効座標 → trim後に空でないaddress → trim後に空でないfallbackName の順。
 *   候補が1つも無ければ `null` を返し、東京駅などへはフォールバックしない。
 *   呼び出し側は `null` のとき経路案内CTAを出さないこと。
 * origin: `toValidOrigin()` を通過した場合のみ付与する（`originContract.ts` 参照）。
 *   現在地が取れていない・fallback 座標しかない場合は origin を付けず、
 *   従来どおり destination だけで Google Maps を開く。
 */
export function buildGoogleMapsDirUrl(params: {
  origin?: { lat?: number | null; lng?: number | null } | null;
  destination: DestinationInput;
}): string | null {
  const destination = resolveDestination(params.destination);
  if (!destination) return null;

  let url = `https://www.google.com/maps/dir/?api=1&destination=${enc(destination.value)}`;

  const origin = toValidOrigin(params.origin);
  if (origin) url += `&origin=${enc(`${origin.lat},${origin.lng}`)}`;

  return url;
}
