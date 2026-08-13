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
    expect(buildReasonFactItems(normalized)).toContainEqual({ label: displayLabel, value: label });
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
