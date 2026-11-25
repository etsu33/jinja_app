import { describe, expect, it } from "vitest";
import { toNeedTagLabel, toNeedTagLabels } from "../needTagLabelMap";

describe("toNeedTagLabel", () => {
  it("既知のkeyは日本語ラベルへ変換する", () => {
    expect(toNeedTagLabel("career")).toBe("仕事や転機を見直したい");
  });

  it("未知のASCII識別子はnullを返す(内部tag keyを画面へ露出しない)", () => {
    expect(toNeedTagLabel("some_new_internal_key")).toBeNull();
    expect(toNeedTagLabel("WORK")).toBeNull();
  });

  it("既に日本語のタグ文字列(未知)はそのまま返す(ユーザー入力由来の値を握りつぶさない)", () => {
    expect(toNeedTagLabel("厄除け")).toBe("厄除け");
  });
});

describe("toNeedTagLabels", () => {
  it("未知のASCII識別子を除外し、既知のラベルだけを返す", () => {
    expect(toNeedTagLabels(["career", "some_new_internal_key", "money"])).toEqual([
      "仕事や転機を見直したい",
      "金運や巡りを整えたい",
    ]);
  });

  it("全て未知の場合は空配列を返す", () => {
    expect(toNeedTagLabels(["unknown_a", "unknown_b"])).toEqual([]);
  });
});
