import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const getMock = vi.fn();
vi.mock("../http", () => ({
  get: (...args: unknown[]) => getMock(...args),
}));

import { __internal, fetchPopularShrines } from "../popularShrines";

const { toPopularShrines } = __internal;

describe("toPopularShrines", () => {
  it("Backendのresults順を維持したまま変換する", () => {
    const shrines = toPopularShrines({
      count: 2,
      next: null,
      previous: null,
      results: [
        { id: 105, kind: "shrine", name_jp: "重複検証神社（別宮）", address: "東京都港区重複3-3-3", latitude: 35.6, longitude: 139.7 },
        { id: 104, kind: "shrine", name_jp: "重複検証神社", address: "東京都中央区重複2-2-2", latitude: 35.68, longitude: 139.76 },
      ],
    });
    expect(shrines).toEqual([
      { id: "105", name: "重複検証神社（別宮）", address: "東京都港区重複3-3-3" },
      { id: "104", name: "重複検証神社", address: "東京都中央区重複2-2-2" },
    ]);
  });

  it("配列を直接渡してもitemsキーでも受け取れる", () => {
    const arrayInput = toPopularShrines([{ id: 1, name_jp: "配列直接" }]);
    expect(arrayInput).toEqual([{ id: "1", name: "配列直接", address: undefined }]);

    const itemsInput = toPopularShrines({ items: [{ id: 2, name_jp: "itemsキー" }] });
    expect(itemsInput).toEqual([{ id: "2", name: "itemsキー", address: undefined }]);
  });

  it("画像・評価値・お気に入り数などAPIに存在しないfieldを推測で補わない", () => {
    const shrines = toPopularShrines({
      results: [{ id: 1, name_jp: "テスト神社", address: "テスト住所", rating: 4.8, favorites: 540, imageUrl: "https://example.com/x.jpg" }],
    });
    expect(shrines).toEqual([{ id: "1", name: "テスト神社", address: "テスト住所" }]);
    expect(shrines[0]).not.toHaveProperty("rating");
    expect(shrines[0]).not.toHaveProperty("favorites");
    expect(shrines[0]).not.toHaveProperty("imageUrl");
  });

  it("空配列を正常な結果として扱う", () => {
    expect(toPopularShrines({ count: 0, next: null, previous: null, results: [] })).toEqual([]);
  });

  it("id欠損を安全に扱う", () => {
    const shrines = toPopularShrines({
      results: [
        { name_jp: "id無し" },
        { id: null, name_jp: "id null" },
        { id: "", name_jp: "id空文字" },
      ],
    });
    expect(shrines).toEqual([]);
  });

  it("name欠損を安全に扱う", () => {
    expect(toPopularShrines({ results: [{ id: 1 }] })).toEqual([]);
  });

  it("addressが文字列でない場合はundefinedにする", () => {
    const shrines = toPopularShrines({ results: [{ id: 1, name_jp: "住所なし", address: null }] });
    expect(shrines).toEqual([{ id: "1", name: "住所なし", address: undefined }]);
  });

  it("不正な入力全体(null・非配列)でも例外を投げない", () => {
    expect(toPopularShrines(null)).toEqual([]);
    expect(toPopularShrines(undefined)).toEqual([]);
    expect(toPopularShrines("not an object")).toEqual([]);
    expect(toPopularShrines({})).toEqual([]);
  });
});

describe("fetchPopularShrines", () => {
  beforeEach(() => {
    getMock.mockReset();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("正しいURL(/populars/)をGETで呼び出す", async () => {
    getMock.mockResolvedValueOnce({ count: 0, next: null, previous: null, results: [] });
    await fetchPopularShrines();
    expect(getMock).toHaveBeenCalledWith("/populars/");
  });

  it("正常Responseを変換して返す", async () => {
    getMock.mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [{ id: 1, name_jp: "明治神宮", address: "東京都渋谷区" }],
    });
    const result = await fetchPopularShrines();
    expect(result).toEqual([{ id: "1", name: "明治神宮", address: "東京都渋谷区" }]);
  });

  it("空配列レスポンスは空配列として返す(errorにしない)", async () => {
    getMock.mockResolvedValueOnce({ count: 0, next: null, previous: null, results: [] });
    await expect(fetchPopularShrines()).resolves.toEqual([]);
  });

  it("非2xx等の取得失敗はhttp helper側の例外をそのまま呼び出し元へ伝える", async () => {
    getMock.mockRejectedValueOnce(new Error("HTTP 500: Internal Server Error"));
    await expect(fetchPopularShrines()).rejects.toThrow("HTTP 500");
  });

  it("不正なResponse(objectだがresults/items/配列のいずれでもない)は空配列として安全に扱う", async () => {
    getMock.mockResolvedValueOnce({ unexpected: "shape" });
    await expect(fetchPopularShrines()).resolves.toEqual([]);
  });
});
