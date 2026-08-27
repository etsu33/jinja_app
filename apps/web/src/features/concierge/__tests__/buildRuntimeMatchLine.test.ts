import { describe, expect, it } from "vitest";
import { buildRuntimeMatchLines } from "../buildRuntimeMatchLine";

describe("buildRuntimeMatchLines", () => {
  it("needTags/goriyakuLabelがともに無ければ空配列を返す(placeholderで埋めない)", () => {
    expect(buildRuntimeMatchLines({ needTags: [], goriyakuLabel: null })).toEqual([]);
  });

  it("未知のASCII need tagのみの場合、ラベル化できず空配列を返す", () => {
    expect(buildRuntimeMatchLines({ needTags: ["unknown_internal_key"], goriyakuLabel: null })).toEqual([]);
  });

  it("goriyakuLabelのみの場合、タスク仕様どおりの短文を1件返す", () => {
    const lines = buildRuntimeMatchLines({ needTags: [], goriyakuLabel: "仕事運" });
    expect(lines).toHaveLength(1);
    expect(lines[0]).toBe("今回の相談内容と、この神社に登録されている「仕事運」に関する情報が重なっています。");
  });

  it("needTagsのみの場合、ラベル化済みの短文を1件返す", () => {
    const lines = buildRuntimeMatchLines({ needTags: ["career"], goriyakuLabel: null });
    expect(lines).toHaveLength(1);
    expect(lines[0]).toContain("仕事や転機を見直したい");
    expect(lines[0]).not.toContain("career");
  });

  it("両方存在する場合、1件の文へ統合する(重複ブロックを作らない)", () => {
    const lines = buildRuntimeMatchLines({ needTags: ["career"], goriyakuLabel: "仕事運" });
    expect(lines).toHaveLength(1);
    expect(lines[0]).toContain("仕事や転機を見直したい");
    expect(lines[0]).toContain("仕事運");
  });

  it("goriyakuLabelが空白のみの場合はneedTagsのみとして扱う", () => {
    const lines = buildRuntimeMatchLines({ needTags: ["career"], goriyakuLabel: "   " });
    expect(lines).toHaveLength(1);
    expect(lines[0]).not.toContain("「」");
  });
});
