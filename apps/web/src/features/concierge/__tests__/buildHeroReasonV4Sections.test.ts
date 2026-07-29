import { describe, it, expect } from "vitest";
import { buildHeroReasonV4Sections } from "../buildHeroReasonV4Sections";

function makeDetail(overrides: Partial<{ reason_text: string; fact: any; interpretation: any; action: any }> = {}) {
  return {
    version: "v4" as const,
    reason_text: overrides.reason_text ?? "根津神社には、縁結び・厄除けに関する情報があります。",
    fact: {
      label: "候補神社",
      name: null,
      deity: null,
      shrine_history: null,
      place_context: null,
      history_theme: "再出発",
      goriyaku: "縁結び・厄除け",
      visit_style_tags: [],
      evidence: [],
      ...(overrides.fact ?? {}),
    },
    interpretation: {
      theme: "再出発",
      text: "相談内容から、今扱いたいテーマを読み取っています。",
      ...(overrides.interpretation ?? {}),
    },
    action: {
      text: "参拝前に、問いを一つに絞ることを決めておきます。",
      source: "meaning_translation.action_context",
      ...(overrides.action ?? {}),
    },
  };
}

describe("buildHeroReasonV4Sections", () => {
  it("fact/interpretation/actionが構造化表示として返る", () => {
    const result = buildHeroReasonV4Sections({ detail: makeDetail(), recommendationReasonV4: null, reason: null });

    expect(result.hasStructured).toBe(true);
    expect(result.factText).toBe("縁結び・厄除け");
    expect(result.interpretationText).toBe("相談内容から、今扱いたいテーマを読み取っています。");
    expect(result.actionText).toBe("参拝前に、問いを一つに絞ることを決めておきます。");
    expect(result.fallbackText).toBeNull();
  });

  it("factは優先順位(shrine_history > place_context > goriyaku > history_theme > label)で選ばれる", () => {
    const result = buildHeroReasonV4Sections({
      detail: makeDetail({
        fact: { shrine_history: "由緒あり", place_context: "住所情報", goriyaku: "縁結び", history_theme: "再出発", label: "候補神社" },
      }),
      recommendationReasonV4: null,
      reason: null,
    });

    expect(result.factText).toBe("由緒あり");
  });

  it("detailがまったく無い場合はrecommendation_reason_v4へfallbackする", () => {
    const result = buildHeroReasonV4Sections({
      detail: null,
      recommendationReasonV4: "根津神社は仕事運に関わる神社です。",
      reason: "旧型の理由文",
    });

    expect(result.hasStructured).toBe(false);
    expect(result.factText).toBeNull();
    expect(result.interpretationText).toBeNull();
    expect(result.actionText).toBeNull();
    expect(result.fallbackText).toBe("根津神社は仕事運に関わる神社です。");
  });

  it("detailのreason_textが最優先のfallbackになる", () => {
    const result = buildHeroReasonV4Sections({
      detail: makeDetail({
        reason_text: "reason_textの内容",
        fact: { shrine_history: null, place_context: null, goriyaku: null, history_theme: null, label: "" },
        interpretation: { text: "" },
        action: { text: "" },
      }),
      recommendationReasonV4: "recommendation_reason_v4の内容",
      reason: "旧型の理由文",
    });

    expect(result.hasStructured).toBe(false);
    expect(result.fallbackText).toBe("reason_textの内容");
  });

  it("reason_textが無い場合はrecommendation_reason_v4へfallbackする", () => {
    const result = buildHeroReasonV4Sections({
      detail: makeDetail({
        reason_text: "",
        fact: { shrine_history: null, place_context: null, goriyaku: null, history_theme: null, label: "" },
        interpretation: { text: "" },
        action: { text: "" },
      }),
      recommendationReasonV4: "recommendation_reason_v4の内容",
      reason: "旧型の理由文",
    });

    expect(result.fallbackText).toBe("recommendation_reason_v4の内容");
  });

  it("recommendation_reason_v4も無い場合は最終的にreasonへfallbackする", () => {
    const result = buildHeroReasonV4Sections({
      detail: makeDetail({
        reason_text: "",
        fact: { shrine_history: null, place_context: null, goriyaku: null, history_theme: null, label: "" },
        interpretation: { text: "" },
        action: { text: "" },
      }),
      recommendationReasonV4: null,
      reason: "旧型の理由文",
    });

    expect(result.fallbackText).toBe("旧型の理由文");
  });

  it("すべて欠落していてもクラッシュせずnullを返す", () => {
    const result = buildHeroReasonV4Sections({ detail: null, recommendationReasonV4: null, reason: null });

    expect(result.hasStructured).toBe(false);
    expect(result.factText).toBeNull();
    expect(result.interpretationText).toBeNull();
    expect(result.actionText).toBeNull();
    expect(result.fallbackText).toBeNull();
  });

  it("方位・断定表現を含むテキストは表示から除外される", () => {
    const result = buildHeroReasonV4Sections({
      detail: null,
      recommendationReasonV4: "この方位は吉方位なので必ず良い結果になります。",
      reason: null,
    });

    expect(result.fallbackText).toBeNull();
  });

  it("action.sourceはUIモデルに含まれない", () => {
    const result = buildHeroReasonV4Sections({ detail: makeDetail(), recommendationReasonV4: null, reason: null });
    expect(result).not.toHaveProperty("actionSource");
    expect(result).not.toHaveProperty("source");
  });
});
