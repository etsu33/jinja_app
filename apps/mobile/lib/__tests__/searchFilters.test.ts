import { describe, expect, it } from "vitest";
import { buildSearchFilters, filterShrines, parseSearchFilters } from "../searchFilters";
import type { Shrine } from "../../data/shrines";

const SAMPLE_SHRINES: Shrine[] = [
  { id: "meiji", name: "明治神宮", imageUrl: "", tags: ["縁結び", "厄除け"], prefecture: "東京都" },
  { id: "fushimi", name: "伏見稲荷大社", imageUrl: "", tags: ["商売繁盛", "金運"], prefecture: "京都府" },
  { id: "kanda", name: "神田明神", imageUrl: "", tags: ["商売繁盛", "厄除け", "IT守護"], prefecture: "東京都" },
];

describe("buildSearchFilters", () => {
  it("選択済みの安全な条件からfilters文字列を組み立てる", () => {
    expect(buildSearchFilters(["縁結び"])).toBe("縁結び");
  });

  it("未選択(undefined)や空文字は除外し、対象が0件ならundefinedを返す", () => {
    expect(buildSearchFilters([undefined])).toBeUndefined();
    expect(buildSearchFilters([""])).toBeUndefined();
    expect(buildSearchFilters([undefined, ""])).toBeUndefined();
  });

  it("重複した値は1つにまとめる", () => {
    expect(buildSearchFilters(["縁結び", "縁結び"])).toBe("縁結び");
  });

  it("自由入力・住所・緯度経度・誕生日のような値を渡しても、そのまま素通りする(呼び出し側の責務)", () => {
    // buildSearchFiltersは受け取った値をそのまま整形するだけであり、
    // どの値を渡すかはHome側(呼び出し側)の責務。ここでは値の整形のみを確認する。
    expect(buildSearchFilters(["静かに整えたい"])).toBe("静かに整えたい");
  });
});

describe("parseSearchFilters", () => {
  it("カンマ区切りの正常な値を配列へ解析する", () => {
    expect(parseSearchFilters("縁結び,金運")).toEqual(["縁結び", "金運"]);
  });

  it("未指定(undefined/null)や空文字は未指定として扱う", () => {
    expect(parseSearchFilters(undefined)).toEqual([]);
    expect(parseSearchFilters(null)).toEqual([]);
    expect(parseSearchFilters("")).toEqual([]);
  });

  it("空要素・前後の空白を無視する", () => {
    expect(parseSearchFilters("縁結び,,  金運  ,")).toEqual(["縁結び", "金運"]);
  });

  it("重複値を除去する", () => {
    expect(parseSearchFilters("縁結び,縁結び,金運")).toEqual(["縁結び", "金運"]);
  });

  it("未知の値でもクラッシュせず、そのまま候補として返す(一致判定はfilterShrines側の責務)", () => {
    expect(parseSearchFilters("未知のタグ")).toEqual(["未知のタグ"]);
  });

  it("巨大な入力でもクラッシュせず、件数・値の長さの両方を上限で切り詰める", () => {
    const manyValues = Array.from({ length: 50 }, (_, i) => `tag${i}`).join(",");
    const result = parseSearchFilters(manyValues);
    expect(result.length).toBeLessThanOrEqual(10);

    const hugeValue = "a".repeat(500);
    expect(parseSearchFilters(hugeValue)).toEqual([]);
    expect(parseSearchFilters(`縁結び,${hugeValue}`)).toEqual(["縁結び"]);
  });
});

describe("filterShrines", () => {
  it("paramsなし(query/filtersともに未指定)では全件を返す", () => {
    expect(filterShrines(SAMPLE_SHRINES, {})).toHaveLength(SAMPLE_SHRINES.length);
  });

  it("1つのfilters条件で該当する神社だけを残す", () => {
    const result = filterShrines(SAMPLE_SHRINES, { filters: "縁結び" });
    expect(result.map((s) => s.id)).toEqual(["meiji"]);
  });

  it("複数filters条件はAND(すべてに一致する神社だけを残す)", () => {
    const result = filterShrines(SAMPLE_SHRINES, { filters: "商売繁盛,厄除け" });
    expect(result.map((s) => s.id)).toEqual(["kanda"]);
  });

  it("都道府県名もfiltersの一致対象になる(既存仕様)", () => {
    const result = filterShrines(SAMPLE_SHRINES, { filters: "京都府" });
    expect(result.map((s) => s.id)).toEqual(["fushimi"]);
  });

  it("queryは神社名・タグ・都道府県への部分一致(大文字小文字を無視)", () => {
    expect(filterShrines(SAMPLE_SHRINES, { query: "神宮" }).map((s) => s.id)).toEqual(["meiji"]);
    expect(filterShrines(SAMPLE_SHRINES, { query: "金運" }).map((s) => s.id)).toEqual(["fushimi"]);
  });

  it("一致する神社がない場合は空配列を返す(呼び出し側でempty stateを出す)", () => {
    expect(filterShrines(SAMPLE_SHRINES, { filters: "存在しないタグ" })).toEqual([]);
    expect(filterShrines(SAMPLE_SHRINES, { query: "存在しない神社名" })).toEqual([]);
  });

  it("未知のfilters値は無視した扱いになり、クラッシュせず空配列を返す", () => {
    expect(() => filterShrines(SAMPLE_SHRINES, { filters: "未知の値,未知の値2" })).not.toThrow();
    expect(filterShrines(SAMPLE_SHRINES, { filters: "未知の値,未知の値2" })).toEqual([]);
  });
});
