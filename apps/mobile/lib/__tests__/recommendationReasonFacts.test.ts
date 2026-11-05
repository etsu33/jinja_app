import { describe, expect, it } from "vitest";
import {
  buildReasonFactItems,
  findPrimaryReasonFact,
  normalizeRecommendationReasonFacts,
  resolveActionEventHistoryTheme,
} from "../recommendationReasonFacts";

const fact = (type: string, label: string, isPrimary = true) => ({
  type,
  label,
  evidence: [`${type}_evidence`],
  score: 3.5,
  is_primary: isPrimary,
});

describe("Mobile Recommendation Reason Facts contract", () => {
  it.each([
    ["need_tag Primary", "need_tag", "仕事", "相談との一致"],
    ["history_theme Primary", "history_theme", "再出発", "神社固有の文脈"],
    ["goriyaku Primary", "goriyaku_tag", "厄除け", "ご利益・意味"],
    ["Explicit Constraint", "user_selected_tag", "駅から近い", "明示した条件"],
    ["Personalization", "element", "火", "生年月日との相性"],
    ["visit_style", "visit_style", "静かに参拝", "参拝との相性"],
    ["fallback", "fallback", "条件に近い候補", "参考情報"],
  ])("%sをBackend指定のPrimaryとして保持する", (_case, type, label, displayLabel) => {
    const raw = [fact("need_tag", "先頭だが非Primary", false), fact(type, label)];

    const normalized = normalizeRecommendationReasonFacts(raw);

    expect(normalized).toEqual(raw);
    expect(findPrimaryReasonFact(normalized)).toEqual(fact(type, label));
    expect(buildReasonFactItems(normalized)).toContainEqual(expect.objectContaining({ label: displayLabel, value: label }));
  });

  it("malformed Factとunknown typeを安全に扱う", () => {
    const normalized = normalizeRecommendationReasonFacts([
      null,
      "invalid",
      { type: "", label: "missing type" },
      { type: "need_tag", label: "" },
      { type: "unknown", label: "未知", evidence: [" ok ", 1], score: "bad", is_primary: true },
    ]);

    expect(normalized).toEqual([
      { type: "unknown", label: "未知", evidence: ["ok"], score: 0, is_primary: true },
    ]);
    expect(buildReasonFactItems(normalized)).toEqual([]);
    expect(normalizeRecommendationReasonFacts({ primary_axis: "history_theme" })).toEqual([]);
  });

  it("no-primary Fact[]でPrimaryを推測しない", () => {
    const normalized = normalizeRecommendationReasonFacts([
      fact("history_theme", "勝負", false),
      { type: "need_tag", label: "仕事", evidence: [], score: 99 },
    ]);

    expect(findPrimaryReasonFact(normalized)).toBeNull();
    expect(resolveActionEventHistoryTheme({
      facts: normalized,
      actionSourceKeys: ["ranked_history_theme", "action_catalog"],
    })).toBe("");
  });

  it("ActionEventにはgrounded history Primaryだけを記録する", () => {
    expect(resolveActionEventHistoryTheme({
      facts: [fact("history_theme", "縁")],
      actionSourceKeys: ["ranked_history_theme", "action_catalog"],
    })).toBe("縁");

    for (const primary of [
      fact("need_tag", "仕事"),
      fact("goriyaku_tag", "厄除け"),
      fact("user_selected_tag", "駅から近い"),
      fact("element", "火"),
      fact("visit_style", "静かに参拝"),
      fact("fallback", "条件に近い候補"),
    ]) {
      expect(resolveActionEventHistoryTheme({
        facts: [primary],
        actionSourceKeys: ["ranked_history_theme", "action_catalog"],
      })).toBe("");
    }

    expect(resolveActionEventHistoryTheme({
      facts: [fact("history_theme", "縁")],
      actionSourceKeys: ["recommendation_reason_v4", "culture_translation"],
    })).toBe("");
  });
});

describe("buildReasonFactItems: 表示名と値が同じ根拠をまとめる", () => {
  // Backend の実データの形（_attach_breakdown の返り値）。同じ相談テーマに goriyaku_tag と text_hint が両方付く。
  const goriyakuMoney = {
    type: "goriyaku_tag",
    label: "money",
    label_ja: "金運",
    evidence: ["goriyaku_tag_ids"],
    score: 2,
    is_primary: false,
  };
  const textHintMoney = {
    type: "text_hint",
    label: "money",
    label_ja: "金運",
    evidence: ["text_score:6"],
    score: 6,
    is_primary: true,
  };

  it("表示名＋labelが同じ根拠は1行にまとめ、keyが重複しない", () => {
    const items = buildReasonFactItems(normalizeRecommendationReasonFacts([goriyakuMoney, textHintMoney]));

    expect(items).toEqual([{ key: "ご利益・意味-money", label: "ご利益・意味", value: "金運" }]);
    expect(new Set(items.map((item) => item.key)).size).toBe(items.length);
  });

  it("is_primary: true の根拠を残す（後ろにあっても、行の位置は最初の位置のまま）", () => {
    const facts = normalizeRecommendationReasonFacts([
      { ...goriyakuMoney, label_ja: "金運（タグ）" },
      { type: "need_tag", label: "love", label_ja: "恋愛", evidence: [], score: 2, is_primary: false },
      { ...textHintMoney, label_ja: "金運（説明文）" },
    ]);

    expect(buildReasonFactItems(facts)).toEqual([
      { key: "ご利益・意味-money", label: "ご利益・意味", value: "金運（説明文）" },
      { key: "相談との一致-love", label: "相談との一致", value: "恋愛" },
    ]);
  });

  it("日本語名ではなくlabelで比べる（label_jaの表記揺れがあってもまとまる）", () => {
    const facts = normalizeRecommendationReasonFacts([
      { ...goriyakuMoney, label_ja: "金運" },
      { ...textHintMoney, label_ja: "金 運" },
    ]);

    expect(buildReasonFactItems(facts)).toHaveLength(1);
  });

  it("labelが違えば、日本語名が同じでもまとめない", () => {
    const facts = normalizeRecommendationReasonFacts([
      { ...goriyakuMoney, label: "money", label_ja: "金運" },
      { ...goriyakuMoney, label: "money_alt", label_ja: "金運", is_primary: true },
    ]);

    expect(buildReasonFactItems(facts).map((item) => item.key)).toEqual([
      "ご利益・意味-money",
      "ご利益・意味-money_alt",
    ]);
  });

  it("まとめてから3件に絞るので、同じ根拠が枠を食わない", () => {
    const facts = normalizeRecommendationReasonFacts([
      goriyakuMoney,
      textHintMoney,
      { type: "need_tag", label: "love", label_ja: "恋愛", evidence: [], score: 2 },
      { type: "user_selected_tag", label: "縁結び", evidence: [], score: 3 },
    ]);

    expect(buildReasonFactItems(facts).slice(0, 3).map((item) => item.value)).toEqual(["金運", "恋愛", "縁結び"]);
  });

  it("label_jaが無いときはlabelを表示する", () => {
    const facts = normalizeRecommendationReasonFacts([
      { type: "history_theme", label: "再出発", evidence: [], score: 4, is_primary: true },
      { ...goriyakuMoney, label_ja: "   " },
    ]);

    expect(buildReasonFactItems(facts).map((item) => item.value)).toEqual(["再出発", "money"]);
  });

  it("値が表示名とまったく同じになるときは値を出さない（nullにする）", () => {
    const facts = normalizeRecommendationReasonFacts([
      { type: "element", label: "element", label_ja: "生年月日との相性", evidence: [], score: 1 },
    ]);

    expect(buildReasonFactItems(facts)).toEqual([
      { key: "生年月日との相性-element", label: "生年月日との相性", value: null },
    ]);
  });

  it("値と表示名が違う語なら、意味が近くても値を出す（visit_style）", () => {
    const facts = normalizeRecommendationReasonFacts([
      { type: "visit_style", label: "visit_style", label_ja: "参拝スタイル", evidence: [], score: 1 },
    ]);

    expect(buildReasonFactItems(facts)).toEqual([
      { key: "参拝との相性-visit_style", label: "参拝との相性", value: "参拝スタイル" },
    ]);
  });

  it("生データはまとめない: 正規化結果とPrimaryの判定はBackendの返り値どおり", () => {
    const normalized = normalizeRecommendationReasonFacts([goriyakuMoney, textHintMoney]);

    expect(normalized).toHaveLength(2);
    expect(normalized.map((fact) => fact.label_ja)).toEqual(["金運", "金運"]);
    expect(findPrimaryReasonFact(normalized)?.type).toBe("text_hint");
  });
});
