import { describe, expect, it } from "vitest";

import { buildGoogleMapsDirUrl } from "@/lib/maps/googleMaps";
import { toValidOrigin } from "@/lib/maps/originContract";
import { gmapsDirUrl } from "@/lib/maps";

const TOKYO_STATION = { lat: 35.681236, lng: 139.767125 };
const SHIBUYA = { lat: 35.658034, lng: 139.701636 };

describe("toValidOrigin", () => {
  it("有効な座標はそのまま返す", () => {
    expect(toValidOrigin(SHIBUYA)).toEqual(SHIBUYA);
  });

  it("null / undefined は undefined", () => {
    expect(toValidOrigin(null)).toBeUndefined();
    expect(toValidOrigin(undefined)).toBeUndefined();
  });

  it("number でない値は undefined", () => {
    expect(toValidOrigin({ lat: "35.6" as unknown as number, lng: 139.7 })).toBeUndefined();
    expect(toValidOrigin({ lat: 35.6, lng: null })).toBeUndefined();
    expect(toValidOrigin({ lat: undefined, lng: undefined })).toBeUndefined();
  });

  it("finite でない値は undefined", () => {
    expect(toValidOrigin({ lat: NaN, lng: 139.7 })).toBeUndefined();
    expect(toValidOrigin({ lat: 35.6, lng: Infinity })).toBeUndefined();
    expect(toValidOrigin({ lat: -Infinity, lng: 139.7 })).toBeUndefined();
  });

  it("緯度経度の有効範囲外は undefined", () => {
    expect(toValidOrigin({ lat: 90.1, lng: 139.7 })).toBeUndefined();
    expect(toValidOrigin({ lat: -90.1, lng: 139.7 })).toBeUndefined();
    expect(toValidOrigin({ lat: 35.6, lng: 180.1 })).toBeUndefined();
    expect(toValidOrigin({ lat: 35.6, lng: -180.1 })).toBeUndefined();
  });

  it("境界値（±90 / ±180 / 0,0）は有効", () => {
    expect(toValidOrigin({ lat: 90, lng: 180 })).toEqual({ lat: 90, lng: 180 });
    expect(toValidOrigin({ lat: -90, lng: -180 })).toEqual({ lat: -90, lng: -180 });
    expect(toValidOrigin({ lat: 0, lng: 0 })).toEqual({ lat: 0, lng: 0 });
  });
});

describe("buildGoogleMapsDirUrl - destination（既存仕様の維持）", () => {
  it("lat/lng があれば座標を使う", () => {
    expect(buildGoogleMapsDirUrl({ destination: { lat: 35.1, lng: 139.2, address: "住所", fallbackName: "名前" } })).toBe(
      "https://www.google.com/maps/dir/?api=1&destination=35.1%2C139.2",
    );
  });

  it("lat/lng がなければ address を使う", () => {
    expect(buildGoogleMapsDirUrl({ destination: { address: "東京都千代田区", fallbackName: "名前" } })).toBe(
      "https://www.google.com/maps/dir/?api=1&destination=%E6%9D%B1%E4%BA%AC%E9%83%BD%E5%8D%83%E4%BB%A3%E7%94%B0%E5%8C%BA",
    );
  });

  it("どちらもなければ fallbackName を使う", () => {
    expect(buildGoogleMapsDirUrl({ destination: { fallbackName: "明治神宮" } })).toBe(
      "https://www.google.com/maps/dir/?api=1&destination=%E6%98%8E%E6%B2%BB%E7%A5%9E%E5%AE%AE",
    );
  });

  it("fallbackName もなければ東京駅", () => {
    expect(buildGoogleMapsDirUrl({ destination: {} })).toBe(
      "https://www.google.com/maps/dir/?api=1&destination=%E6%9D%B1%E4%BA%AC%E9%A7%85",
    );
  });
});

describe("buildGoogleMapsDirUrl - origin", () => {
  it("有効な現在地があれば origin を付ける", () => {
    expect(buildGoogleMapsDirUrl({ origin: SHIBUYA, destination: { lat: 35.1, lng: 139.2 } })).toBe(
      "https://www.google.com/maps/dir/?api=1&destination=35.1%2C139.2&origin=35.658034%2C139.701636",
    );
  });

  it("origin 未指定なら URL に origin を入れない", () => {
    const url = buildGoogleMapsDirUrl({ destination: { lat: 35.1, lng: 139.2 } });
    expect(url).not.toContain("origin=");
  });

  it("取得失敗（null）なら origin を入れない", () => {
    const url = buildGoogleMapsDirUrl({ origin: null, destination: { lat: 35.1, lng: 139.2 } });
    expect(url).not.toContain("origin=");
  });

  it("不正な座標なら origin を入れない", () => {
    expect(buildGoogleMapsDirUrl({ origin: { lat: NaN, lng: 139.7 }, destination: { lat: 35.1, lng: 139.2 } })).not.toContain(
      "origin=",
    );
    expect(buildGoogleMapsDirUrl({ origin: { lat: 999, lng: 139.7 }, destination: { lat: 35.1, lng: 139.2 } })).not.toContain(
      "origin=",
    );
  });

  it("呼び出し側が fallback 使用中に origin を渡さなければ URL にも入らない", () => {
    // Map画面の usedFallback 相当。東京駅 fallback は origin にしない。
    const usedFallback = true;
    const url = buildGoogleMapsDirUrl({
      origin: usedFallback ? null : TOKYO_STATION,
      destination: { lat: 35.1, lng: 139.2 },
    });
    expect(url).not.toContain("origin=");
  });
});

describe("gmapsDirUrl - origin は同じ契約を通る", () => {
  it("有効な現在地があれば origin を付ける", () => {
    const url = gmapsDirUrl({ dest: { lat: 35.1, lng: 139.2 }, origin: SHIBUYA });
    expect(url).toContain("origin=35.658034%2C139.701636");
  });

  it("null なら origin を入れない", () => {
    expect(gmapsDirUrl({ dest: { lat: 35.1, lng: 139.2 }, origin: null })).not.toContain("origin=");
  });

  it("不正な座標なら origin を入れない", () => {
    expect(gmapsDirUrl({ dest: { lat: 35.1, lng: 139.2 }, origin: { lat: NaN, lng: NaN } })).not.toContain("origin=");
  });

  it("origin 未指定でも destination / travelmode は従来どおり", () => {
    expect(gmapsDirUrl({ dest: { lat: 35.1, lng: 139.2 }, mode: "walk" })).toBe(
      "https://www.google.com/maps/dir/?api=1&destination=35.1%2C139.2&travelmode=walking",
    );
  });
});
