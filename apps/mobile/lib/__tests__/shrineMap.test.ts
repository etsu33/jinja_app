import { describe, expect, it } from "vitest";
import { toShrineMapPoints } from "../shrineMap";

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

  it("null座標を除外する", () => {
    const points = toShrineMapPoints({ results: [{ id: 6, name_jp: "座標なし", latitude: null, longitude: null }] });
    expect(points).toEqual([]);
  });

  it("NaNを除外する", () => {
    const points = toShrineMapPoints({ results: [{ id: 7, name_jp: "不正値", latitude: "abc", longitude: 139.0 }] });
    expect(points).toEqual([]);
  });

  it("Infinityを除外する", () => {
    const points = toShrineMapPoints({ results: [{ id: 8, name_jp: "無限大", latitude: Infinity, longitude: 139.0 }] });
    expect(points).toEqual([]);
  });

  it("範囲外座標を除外する", () => {
    const overLat = toShrineMapPoints({ results: [{ id: 9, name_jp: "緯度範囲外", latitude: 95, longitude: 139.0 }] });
    const overLng = toShrineMapPoints({ results: [{ id: 10, name_jp: "経度範囲外", latitude: 35.0, longitude: 200 }] });
    expect(overLat).toEqual([]);
    expect(overLng).toEqual([]);
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
