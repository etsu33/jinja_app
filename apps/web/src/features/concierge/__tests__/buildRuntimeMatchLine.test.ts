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

describe("buildRuntimeMatchLines 表示用の名前", () => {
  it("日本語名(休息)をそのまま文に入れる", () => {
    const lines = buildRuntimeMatchLines({ needTags: ["rest"], goriyakuLabel: "休息", goriyakuMatched: true });
    expect(lines).toEqual(["今回の相談テーマ「静かに休みたい」と、この神社に登録されている「休息」に関する情報が重なっています。"]);
    expect(lines[0]).not.toContain("rest");
  });

  it.each(["rest", "quiet", "goriyaku_tag:501"])("英字・数字・記号だけの名前(%s)は文に入れず、名前を入れない文にする", (label) => {
    expect(buildRuntimeMatchLines({ needTags: [], goriyakuLabel: label, goriyakuMatched: true })).toEqual([
      "今回の相談内容と、この神社に登録されている情報が重なっています。",
    ]);
  });

  it("相談テーマがあり、名前が内部名だけのときも名前を入れない文にする", () => {
    const lines = buildRuntimeMatchLines({ needTags: ["career"], goriyakuLabel: "career", goriyakuMatched: true });
    expect(lines).toEqual(["今回の相談テーマ「仕事や転機を見直したい」と、この神社に登録されている情報が重なっています。"]);
  });

  it("主な根拠が goriyaku_tag で表示名が無い(null)ときも、名前を入れない文で重なりを伝える", () => {
    expect(buildRuntimeMatchLines({ needTags: [], goriyakuLabel: null, goriyakuMatched: true })).toEqual([
      "今回の相談内容と、この神社に登録されている情報が重なっています。",
    ]);
  });

  it("日本語を含む名前(IT守護)はそのまま使う", () => {
    expect(buildRuntimeMatchLines({ needTags: [], goriyakuLabel: "IT守護", goriyakuMatched: true })[0]).toContain("「IT守護」");
  });
});
