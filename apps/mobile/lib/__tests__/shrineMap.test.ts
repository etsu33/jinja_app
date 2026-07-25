import { describe, expect, it } from "vitest";
import {
  computeWebMapViewport,
  findShrineMapPointById,
  hasValidCoordinates,
  isSearchMapSectionAvailable,
  toShrineMapPoints,
} from "../shrineMap";

describe("toShrineMapPoints", () => {
  it("正常な数値座標を通す", () => {
    const points = toShrineMapPoints({
      results: [{ id: 1, name_jp: "明治神宮", address: "東京都渋谷区", latitude: 35.676, longitude: 139.699 }],
    });
    expect(points).toEqual([
      { id: "1", name: "明治神宮", latitude: 35.676, longitude: 139.699, address: "東京都渋谷区", imageUrl: undefined },
    ]);
  });

  it("配列を直接渡してもitemsキーでも受け取れる", () => {
    const arrayInput = toShrineMapPoints([{ id: 2, name_jp: "伏見稲荷大社", latitude: 34.9, longitude: 135.7 }]);
    expect(arrayInput).toHaveLength(1);

    const itemsInput = toShrineMapPoints({ items: [{ id: 3, name_jp: "神田明神", latitude: 35.7, longitude: 139.77 }] });
    expect(itemsInput).toHaveLength(1);
  });

  it("数字文字列の座標を数値へ変換する", () => {
    const points = toShrineMapPoints({
      results: [{ id: "4", name_jp: "住吉神社", latitude: "35.667", longitude: "139.779" }],
    });
    expect(points).toEqual([{ id: "4", name: "住吉神社", latitude: 35.667, longitude: 139.779, address: undefined, imageUrl: undefined }]);
  });

  it("location.lat/lngからも座標を取得できる", () => {
    const points = toShrineMapPoints({
      results: [{ id: 5, name_jp: "location経由", location: { lat: 35.1, lng: 139.1 } }],
    });
    expect(points).toEqual([{ id: "5", name: "location経由", latitude: 35.1, longitude: 139.1, address: undefined, imageUrl: undefined }]);
  });

  it("null座標は除外せず、座標欠損として一覧に残す", () => {
    const points = toShrineMapPoints({ results: [{ id: 6, name_jp: "座標なし", latitude: null, longitude: null }] });
    expect(points).toEqual([{ id: "6", name: "座標なし", latitude: null, longitude: null, address: undefined, imageUrl: undefined }]);
  });

  it("NaNになる座標は座標欠損として一覧に残す", () => {
    const points = toShrineMapPoints({ results: [{ id: 7, name_jp: "不正値", latitude: "abc", longitude: 139.0 }] });
    expect(points).toEqual([{ id: "7", name: "不正値", latitude: null, longitude: null, address: undefined, imageUrl: undefined }]);
  });

  it("Infinityは座標欠損として一覧に残す", () => {
    const points = toShrineMapPoints({ results: [{ id: 8, name_jp: "無限大", latitude: Infinity, longitude: 139.0 }] });
    expect(points).toEqual([{ id: "8", name: "無限大", latitude: null, longitude: null, address: undefined, imageUrl: undefined }]);
  });

  it("範囲外座標は座標欠損として一覧に残す", () => {
    const overLat = toShrineMapPoints({ results: [{ id: 9, name_jp: "緯度範囲外", latitude: 95, longitude: 139.0 }] });
    const overLng = toShrineMapPoints({ results: [{ id: 10, name_jp: "経度範囲外", latitude: 35.0, longitude: 200 }] });
    expect(overLat).toEqual([{ id: "9", name: "緯度範囲外", latitude: null, longitude: null, address: undefined, imageUrl: undefined }]);
    expect(overLng).toEqual([{ id: "10", name: "経度範囲外", latitude: null, longitude: null, address: undefined, imageUrl: undefined }]);
  });

  it("片方だけ有効な座標も欠損として扱う(Markerを安全に省略するため)", () => {
    const points = toShrineMapPoints({ results: [{ id: "14", name_jp: "片方欠損", latitude: 35.0, longitude: null }] });
    expect(points).toEqual([{ id: "14", name: "片方欠損", latitude: null, longitude: null, address: undefined, imageUrl: undefined }]);
  });

  it("有効座標が0件でも、id・nameがある項目は一覧として返す", () => {
    const points = toShrineMapPoints({
      results: [
        { id: 15, name_jp: "座標なしA", latitude: null, longitude: null },
        { id: 16, name_jp: "座標なしB", latitude: "abc", longitude: "def" },
      ],
    });
    expect(points).toHaveLength(2);
    expect(points.every((p) => !hasValidCoordinates(p))).toBe(true);
  });

  it("id欠損を安全に扱う", () => {
    const points = toShrineMapPoints({
      results: [
        { name_jp: "id無し", latitude: 35.0, longitude: 139.0 },
        { id: null, name_jp: "id null", latitude: 35.0, longitude: 139.0 },
        { id: "", name_jp: "id空文字", latitude: 35.0, longitude: 139.0 },
      ],
    });
    expect(points).toEqual([]);
  });

  it("name欠損を安全に扱う", () => {
    const points = toShrineMapPoints({ results: [{ id: 11, latitude: 35.0, longitude: 139.0 }] });
    expect(points).toEqual([]);
  });

  it("不正な入力全体（null・非配列）でも例外を投げない", () => {
    expect(toShrineMapPoints(null)).toEqual([]);
    expect(toShrineMapPoints(undefined)).toEqual([]);
    expect(toShrineMapPoints("not an object")).toEqual([]);
    expect(toShrineMapPoints({})).toEqual([]);
  });

  it("image_url・photo_urlのどちらからも画像URLを拾う", () => {
    const viaImageUrl = toShrineMapPoints({ results: [{ id: 12, name_jp: "画像A", latitude: 1, longitude: 1, image_url: "https://x/a.jpg" }] });
    const viaPhotoUrl = toShrineMapPoints({ results: [{ id: 13, name_jp: "画像B", latitude: 1, longitude: 1, photo_url: "https://x/b.jpg" }] });
    expect(viaImageUrl[0]?.imageUrl).toBe("https://x/a.jpg");
    expect(viaPhotoUrl[0]?.imageUrl).toBe("https://x/b.jpg");
  });
});

describe("hasValidCoordinates", () => {
  it("有効な緯度経度がそろっている場合はtrue", () => {
    expect(hasValidCoordinates({ id: "1", name: "有効", latitude: 35.0, longitude: 139.0 })).toBe(true);
  });

  it("緯度経度がnullの場合はfalse(Marker同期を安全に省略する対象)", () => {
    expect(hasValidCoordinates({ id: "2", name: "座標なし", latitude: null, longitude: null })).toBe(false);
  });

  it("片方だけnullの場合もfalse", () => {
    expect(hasValidCoordinates({ id: "3", name: "片方欠損", latitude: 35.0, longitude: null })).toBe(false);
  });
});

describe("findShrineMapPointById", () => {
  const points = [
    { id: "1", name: "明治神宮", latitude: 35.676, longitude: 139.699 },
    { id: "2", name: "座標なし", latitude: null, longitude: null },
  ];

  it("selectedIdに対応するpointを導出できる", () => {
    expect(findShrineMapPointById(points, "1")).toEqual(points[0]);
  });

  it("座標欠損神社もidが一致すれば導出できる", () => {
    expect(findShrineMapPointById(points, "2")).toEqual(points[1]);
  });

  it("該当idがなければnullを返す", () => {
    expect(findShrineMapPointById(points, "999")).toBeNull();
  });

  it("idがnullならnullを返す", () => {
    expect(findShrineMapPointById(points, null)).toBeNull();
  });
});

describe("isSearchMapSectionAvailable", () => {
  it("Webでstyle URLが未設定の場合はfalse(地図で探すセクションを表示しない)", () => {
    expect(isSearchMapSectionAvailable("web", undefined)).toBe(false);
  });

  it("Webでstyle URLが空文字の場合もfalse", () => {
    expect(isSearchMapSectionAvailable("web", "")).toBe(false);
  });

  it("Webでstyle URLが設定済みの場合はtrue", () => {
    expect(isSearchMapSectionAvailable("web", "https://example.com/style.json")).toBe(true);
  });

  it("iOSはstyle URLの有無に関わらずtrue(Nativeは常時react-native-mapsを表示する)", () => {
    expect(isSearchMapSectionAvailable("ios", undefined)).toBe(true);
    expect(isSearchMapSectionAvailable("ios", "https://example.com/style.json")).toBe(true);
  });

  it("Androidもstyle URLの有無に関わらずtrue", () => {
    expect(isSearchMapSectionAvailable("android", undefined)).toBe(true);
  });
});

describe("computeWebMapViewport", () => {
  it("有効座標が0件ならnullを返す(Web地図を生成しない判定に使う)", () => {
    expect(computeWebMapViewport([])).toBeNull();
  });

  it("1件のときはcenter+zoomを返す(bounds計算はしない)", () => {
    const viewport = computeWebMapViewport([{ latitude: 35.676, longitude: 139.699 }]);
    expect(viewport).toEqual({ kind: "point", center: [139.699, 35.676], zoom: 14 });
  });

  it("center配列は[経度, 緯度]の順序である(緯度経度を逆にしない)", () => {
    const viewport = computeWebMapViewport([{ latitude: 10, longitude: 20 }]);
    expect(viewport?.kind).toBe("point");
    if (viewport?.kind === "point") {
      expect(viewport.center[0]).toBe(20); // longitude
      expect(viewport.center[1]).toBe(10); // latitude
    }
  });

  it("2件以上のときはboundsを返す", () => {
    const viewport = computeWebMapViewport([
      { latitude: 35.0, longitude: 139.0 },
      { latitude: 36.0, longitude: 140.0 },
    ]);
    expect(viewport).toEqual({
      kind: "bounds",
      bounds: [
        [139.0, 35.0],
        [140.0, 36.0],
      ],
      padding: 48,
      maxZoom: 15,
    });
  });

  it("bounds配列も[経度, 緯度]の順序である", () => {
    const viewport = computeWebMapViewport([
      { latitude: 10, longitude: 100 },
      { latitude: 20, longitude: 200 },
    ]);
    expect(viewport?.kind).toBe("bounds");
    if (viewport?.kind === "bounds") {
      expect(viewport.bounds[0]).toEqual([100, 10]); // [minLng, minLat]
      expect(viewport.bounds[1]).toEqual([200, 20]); // [maxLng, maxLat]
    }
  });
});
