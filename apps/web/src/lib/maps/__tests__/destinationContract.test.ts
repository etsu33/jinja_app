import { describe, expect, it } from "vitest";

import { buildGoogleMapsDirUrl } from "@/lib/maps/googleMaps";
import { resolveDestination, toValidDestinationCoords } from "@/lib/maps/destinationContract";

// Nearby検索用の東京駅fallback座標。destinationとして暗黙に使われてはならない。
const TOKYO_STATION = { lat: 35.681236, lng: 139.767125 };

describe("toValidDestinationCoords", () => {
  it("valid lat/lng はそのまま返す", () => {
    expect(toValidDestinationCoords({ lat: 35.1, lng: 139.2 })).toEqual({ lat: 35.1, lng: 139.2 });
  });

  it("境界値（±90 / ±180 / 0,0）は有効", () => {
    expect(toValidDestinationCoords({ lat: 90, lng: 180 })).toEqual({ lat: 90, lng: 180 });
    expect(toValidDestinationCoords({ lat: -90, lng: -180 })).toEqual({ lat: -90, lng: -180 });
    expect(toValidDestinationCoords({ lat: 0, lng: 0 })).toEqual({ lat: 0, lng: 0 });
  });

  it("NaN は無効", () => {
    expect(toValidDestinationCoords({ lat: NaN, lng: 139.2 })).toBeUndefined();
    expect(toValidDestinationCoords({ lat: 35.1, lng: NaN })).toBeUndefined();
  });

  it("Infinity は無効", () => {
    expect(toValidDestinationCoords({ lat: Infinity, lng: 139.2 })).toBeUndefined();
    expect(toValidDestinationCoords({ lat: 35.1, lng: -Infinity })).toBeUndefined();
  });

  it("latitude range外は無効", () => {
    expect(toValidDestinationCoords({ lat: 90.1, lng: 139.2 })).toBeUndefined();
    expect(toValidDestinationCoords({ lat: -90.1, lng: 139.2 })).toBeUndefined();
  });

  it("longitude range外は無効", () => {
    expect(toValidDestinationCoords({ lat: 35.1, lng: 180.1 })).toBeUndefined();
    expect(toValidDestinationCoords({ lat: 35.1, lng: -180.1 })).toBeUndefined();
  });

  it("latのみ / lngのみは無効", () => {
    expect(toValidDestinationCoords({ lat: 35.1 })).toBeUndefined();
    expect(toValidDestinationCoords({ lng: 139.2 })).toBeUndefined();
    expect(toValidDestinationCoords({ lat: 35.1, lng: null })).toBeUndefined();
    expect(toValidDestinationCoords({ lat: null, lng: 139.2 })).toBeUndefined();
  });

  it("numberでない値 / null / undefined は無効", () => {
    expect(toValidDestinationCoords({ lat: "35.1" as unknown as number, lng: 139.2 })).toBeUndefined();
    expect(toValidDestinationCoords(null)).toBeUndefined();
    expect(toValidDestinationCoords(undefined)).toBeUndefined();
  });

  it("日本国内boundsは判定しない（WGS84値域のみ）", () => {
    expect(toValidDestinationCoords({ lat: 48.85, lng: 2.35 })).toEqual({ lat: 48.85, lng: 2.35 });
  });
});

describe("resolveDestination - 優先順位", () => {
  it("valid lat/lng があれば座標を最優先する", () => {
    expect(resolveDestination({ lat: 35.1, lng: 139.2, address: "住所", fallbackName: "名前" })).toEqual({
      kind: "coords",
      value: "35.1,139.2",
    });
  });

  it("invalid coordinates + address なら address へ落ちる", () => {
    expect(resolveDestination({ lat: NaN, lng: 139.2, address: "東京都千代田区", fallbackName: "名前" })).toEqual({
      kind: "address",
      value: "東京都千代田区",
    });
  });

  it("invalid coordinates + no address + name なら name へ落ちる", () => {
    expect(resolveDestination({ lat: 999, lng: 139.2, fallbackName: "明治神宮" })).toEqual({
      kind: "name",
      value: "明治神宮",
    });
  });

  it("空白のみの address / fallbackName は候補として扱わない", () => {
    expect(resolveDestination({ address: "   ", fallbackName: "明治神宮" })).toEqual({
      kind: "name",
      value: "明治神宮",
    });
    expect(resolveDestination({ address: "   ", fallbackName: "  " })).toBeNull();
    expect(resolveDestination({ address: "", fallbackName: "" })).toBeNull();
  });

  it("採用値はtrim済みで返す", () => {
    expect(resolveDestination({ address: "  東京都千代田区  " })).toEqual({
      kind: "address",
      value: "東京都千代田区",
    });
  });

  it("全欠落ならnullを返す", () => {
    expect(resolveDestination({})).toBeNull();
    expect(resolveDestination(null)).toBeNull();
    expect(resolveDestination(undefined)).toBeNull();
    expect(resolveDestination({ lat: NaN, lng: NaN, address: null, fallbackName: null })).toBeNull();
  });
});

describe("buildGoogleMapsDirUrl - destination", () => {
  it("valid lat/lng で座標URLを返す", () => {
    expect(buildGoogleMapsDirUrl({ destination: { lat: 35.1, lng: 139.2 } })).toBe(
      "https://www.google.com/maps/dir/?api=1&destination=35.1%2C139.2",
    );
  });

  it("invalid coordinates + address で address URLを返す", () => {
    expect(buildGoogleMapsDirUrl({ destination: { lat: NaN, lng: NaN, address: "東京都千代田区" } })).toBe(
      "https://www.google.com/maps/dir/?api=1&destination=%E6%9D%B1%E4%BA%AC%E9%83%BD%E5%8D%83%E4%BB%A3%E7%94%B0%E5%8C%BA",
    );
  });

  it("invalid coordinates + no address + name で name URLを返す", () => {
    expect(buildGoogleMapsDirUrl({ destination: { lat: 200, lng: 0, fallbackName: "明治神宮" } })).toBe(
      "https://www.google.com/maps/dir/?api=1&destination=%E6%98%8E%E6%B2%BB%E7%A5%9E%E5%AE%AE",
    );
  });

  it("片方だけの座標は座標として使わず次の候補へ落ちる", () => {
    expect(buildGoogleMapsDirUrl({ destination: { lat: 35.1, address: "東京都千代田区" } })).toContain(
      "destination=%E6%9D%B1%E4%BA%AC%E9%83%BD%E5%8D%83%E4%BB%A3%E7%94%B0%E5%8C%BA",
    );
    expect(buildGoogleMapsDirUrl({ destination: { lng: 139.2, address: "東京都千代田区" } })).toContain(
      "destination=%E6%9D%B1%E4%BA%AC%E9%83%BD%E5%8D%83%E4%BB%A3%E7%94%B0%E5%8C%BA",
    );
  });

  it("destination候補が全て無ければnullを返す", () => {
    expect(buildGoogleMapsDirUrl({ destination: {} })).toBeNull();
    expect(buildGoogleMapsDirUrl({ destination: { lat: NaN, lng: NaN } })).toBeNull();
    expect(buildGoogleMapsDirUrl({ destination: { address: "  ", fallbackName: "  " } })).toBeNull();
  });

  it("東京駅が暗黙のdestinationにならない", () => {
    expect(buildGoogleMapsDirUrl({ destination: {} })).toBeNull();

    // 座標が無効でも住所も名前も無ければ、東京駅の名称・座標のいずれも使わない。
    const url = buildGoogleMapsDirUrl({ destination: { lat: NaN, lng: NaN, address: "", fallbackName: "" } });
    expect(url).toBeNull();

    // originに東京駅fallbackが入ったとしてもdestinationへは流れ込まない。
    const withOrigin = buildGoogleMapsDirUrl({ origin: TOKYO_STATION, destination: {} });
    expect(withOrigin).toBeNull();
  });

  it("origin契約は従来どおり維持する（destination変更の巻き添えにしない）", () => {
    expect(buildGoogleMapsDirUrl({ origin: { lat: 35.658034, lng: 139.701636 }, destination: { lat: 35.1, lng: 139.2 } })).toBe(
      "https://www.google.com/maps/dir/?api=1&destination=35.1%2C139.2&origin=35.658034%2C139.701636",
    );
    expect(buildGoogleMapsDirUrl({ origin: null, destination: { lat: 35.1, lng: 139.2 } })).not.toContain("origin=");
    expect(
      buildGoogleMapsDirUrl({ origin: { lat: NaN, lng: 139.7 }, destination: { lat: 35.1, lng: 139.2 } }),
    ).not.toContain("origin=");
  });
});
