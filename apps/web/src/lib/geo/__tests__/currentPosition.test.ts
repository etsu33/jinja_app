import { afterEach, describe, expect, it, vi } from "vitest";

import {
  MOBILE_WEB_GEO_OPTIONS,
  requestCurrentPosition,
  type GeoResult,
} from "../currentPosition";

type GetCurrentPosition = typeof navigator.geolocation.getCurrentPosition;

function stubGeolocation(impl: GetCurrentPosition | null) {
  if (impl === null) {
    // simulate a browser without geolocation
    Object.defineProperty(navigator, "geolocation", {
      configurable: true,
      value: undefined,
    });
    return;
  }
  Object.defineProperty(navigator, "geolocation", {
    configurable: true,
    value: { getCurrentPosition: impl },
  });
}

function coords(lat: number, lng: number, accuracy: number | null = 25) {
  return {
    coords: {
      latitude: lat,
      longitude: lng,
      accuracy,
      altitude: null,
      altitudeAccuracy: null,
      heading: null,
      speed: null,
    },
    timestamp: Date.now(),
  } as GeolocationPosition;
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("requestCurrentPosition", () => {
  it("success: resolves { ok: true } with coordinates + accuracy", async () => {
    stubGeolocation(((success) => success(coords(35.6762, 139.6503, 30))) as GetCurrentPosition);

    const res = await requestCurrentPosition();

    expect(res).toEqual<GeoResult>({ ok: true, lat: 35.6762, lng: 139.6503, accuracy: 30 });
  });

  it("success with non-numeric accuracy: accuracy is null, no throw", async () => {
    stubGeolocation(((success) => success(coords(1, 2, null))) as GetCurrentPosition);

    const res = await requestCurrentPosition();

    expect(res).toEqual<GeoResult>({ ok: true, lat: 1, lng: 2, accuracy: null });
  });

  it("PERMISSION_DENIED (code 1) -> { ok: false, reason: 'denied' }", async () => {
    stubGeolocation(((_s, error) => error?.({ code: 1, message: "denied" } as GeolocationPositionError)) as GetCurrentPosition);

    const res = await requestCurrentPosition();

    expect(res).toEqual<GeoResult>({ ok: false, reason: "denied" });
  });

  it("POSITION_UNAVAILABLE (code 2) -> { ok: false, reason: 'unavailable' }", async () => {
    stubGeolocation(((_s, error) => error?.({ code: 2, message: "unavailable" } as GeolocationPositionError)) as GetCurrentPosition);

    const res = await requestCurrentPosition();

    expect(res).toEqual<GeoResult>({ ok: false, reason: "unavailable" });
  });

  it("TIMEOUT (code 3) -> { ok: false, reason: 'timeout' }", async () => {
    stubGeolocation(((_s, error) => error?.({ code: 3, message: "timeout" } as GeolocationPositionError)) as GetCurrentPosition);

    const res = await requestCurrentPosition();

    expect(res).toEqual<GeoResult>({ ok: false, reason: "timeout" });
  });

  it("unknown error code -> { ok: false, reason: 'unavailable' }", async () => {
    stubGeolocation(((_s, error) => error?.({ code: 99, message: "?" } as unknown as GeolocationPositionError)) as GetCurrentPosition);

    const res = await requestCurrentPosition();

    expect(res).toEqual<GeoResult>({ ok: false, reason: "unavailable" });
  });

  it("no geolocation API -> { ok: false, reason: 'unsupported' } (never rejects)", async () => {
    stubGeolocation(null);

    const res = await requestCurrentPosition();

    expect(res).toEqual<GeoResult>({ ok: false, reason: "unsupported" });
  });

  it("passes the shared mobile-web options by default", async () => {
    const spy = vi.fn(((success) => success(coords(0, 0))) as GetCurrentPosition);
    stubGeolocation(spy);

    await requestCurrentPosition();

    const passedOptions = spy.mock.calls[0][2];
    expect(passedOptions).toEqual(MOBILE_WEB_GEO_OPTIONS);
    expect(MOBILE_WEB_GEO_OPTIONS.enableHighAccuracy).toBe(false);
    expect(MOBILE_WEB_GEO_OPTIONS.timeout).toBeGreaterThanOrEqual(10000);
    expect(MOBILE_WEB_GEO_OPTIONS.maximumAge).toBeGreaterThan(0);
  });

  it("caller-provided options override the default", async () => {
    const spy = vi.fn(((success) => success(coords(0, 0))) as GetCurrentPosition);
    stubGeolocation(spy);

    const custom: PositionOptions = { enableHighAccuracy: true, timeout: 1, maximumAge: 0 };
    await requestCurrentPosition(custom);

    expect(spy.mock.calls[0][2]).toEqual(custom);
  });

  it("retry: a failure then a success resolves ok on the second call", async () => {
    let call = 0;
    stubGeolocation(((success, error) => {
      call += 1;
      if (call === 1) {
        error?.({ code: 3, message: "timeout" } as GeolocationPositionError);
      } else {
        success(coords(10, 20));
      }
    }) as GetCurrentPosition);

    const first = await requestCurrentPosition();
    expect(first).toEqual<GeoResult>({ ok: false, reason: "timeout" });

    const second = await requestCurrentPosition();
    expect(second).toEqual<GeoResult>({ ok: true, lat: 10, lng: 20, accuracy: 25 });
  });
});
