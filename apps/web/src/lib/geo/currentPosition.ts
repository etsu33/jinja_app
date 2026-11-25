// Shared browser-geolocation entry point for mobile-web location features
// (nearby shrines, Compass / direction departure point).
//
// Why this exists (RH3-4b): the per-call-site inline `getCurrentPosition` calls
// diverged. Two of them failed on a real mobile browser in production:
//
//   - Compass `useDevice()` passed NO options -> `timeout` was `Infinity`
//     (hang risk) and `maximumAge` `0` (never accepts a recent fix).
//   - Nearby passed `{ enableHighAccuracy: true, timeout: 8000 }` -> on mobile
//     (esp. iOS Safari indoors) it waits on a GPS fix and frequently `TIMEOUT`s
//     within 8s before a coarse network fix could be returned; `maximumAge` `0`
//     means a just-acquired position is not reused either.
//
// For "neighbourhood shrines" and "departure point" a coarse
// (Wi-Fi / cell) fix is more than enough and is far more reliable and faster on
// mobile than a high-accuracy GPS acquisition. So this helper:
//   - forces `enableHighAccuracy: false`
//   - uses a generous `timeout`
//   - accepts a recent cached fix via `maximumAge`
//   - is SSR-safe and NEVER rejects (callers cannot hang on it)
//   - maps `GeolocationPositionError.code` to a stable reason string

export const MOBILE_WEB_GEO_OPTIONS: PositionOptions = {
  enableHighAccuracy: false,
  timeout: 15000,
  maximumAge: 60000,
};

export type GeoFailureReason = "unsupported" | "denied" | "unavailable" | "timeout";

export type GeoResult =
  | { ok: true; lat: number; lng: number; accuracy: number | null }
  | { ok: false; reason: GeoFailureReason };

function reasonFromCode(code: number | undefined): GeoFailureReason {
  // GeolocationPositionError: 1 PERMISSION_DENIED, 2 POSITION_UNAVAILABLE, 3 TIMEOUT
  if (code === 1) return "denied";
  if (code === 3) return "timeout";
  return "unavailable";
}

/**
 * Request the device's current position. Always resolves — never rejects.
 *
 * @param options overrides for the shared mobile-web options; the default
 *   (`MOBILE_WEB_GEO_OPTIONS`) is what every mobile-web location feature should use.
 */
export function requestCurrentPosition(
  options: PositionOptions = MOBILE_WEB_GEO_OPTIONS,
): Promise<GeoResult> {
  return new Promise<GeoResult>((resolve) => {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      resolve({ ok: false, reason: "unsupported" });
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        resolve({
          ok: true,
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          accuracy: typeof pos.coords.accuracy === "number" ? pos.coords.accuracy : null,
        });
      },
      (err) => {
        resolve({ ok: false, reason: reasonFromCode(err?.code) });
      },
      options,
    );
  });
}
