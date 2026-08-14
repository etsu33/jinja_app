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
    expect(result.explanationOnlyFactText).toBeNull();
    expect(result.interpretationText).toBe("相談内容から、今扱いたいテーマを読み取っています。");
    expect(result.actionText).toBe("参拝前に、問いを一つに絞ることを決めておきます。");
    expect(result.fallbackText).toBeNull();
  });

  it("factは優先順位(deity > shrine_history > goriyaku > history_theme)で選ばれる(place_context/labelは候補にしない)", () => {
    const result = buildHeroReasonV4Sections({
      detail: makeDetail({
        fact: { deity: "武神", shrine_history: "由緒あり", place_context: "住所情報", goriyaku: "縁結び", history_theme: "再出発", label: "候補神社" },
      }),
      recommendationReasonV4: null,
      reason: null,
    });

    // deityが最優先で採用される(採用順位そのものはPR5でも変更しない)が、
    // deityはExplanation-onlyのためfactTextではなくexplanationOnlyFactTextへ入る(Finding 9)。
    expect(result.explanationOnlyFactText).toBe("武神");
    expect(result.factText).toBeNull();
  });

  it("deityが選ばれるケース(Explanation-only、factTextには入らない)", () => {
    const result = buildHeroReasonV4Sections({
      detail: makeDetail({
        fact: { deity: "武神", shrine_history: null, place_context: null, goriyaku: null, history_theme: null, label: "武神" },
      }),
      recommendationReasonV4: null,
      reason: null,
    });

    expect(result.explanationOnlyFactText).toBe("武神");
    expect(result.factText).toBeNull();
  });

  it("shrine_historyが選ばれるケース(deityが無い場合、Explanation-only)", () => {
    const result = buildHeroReasonV4Sections({
      detail: makeDetail({
        fact: { deity: null, shrine_history: "由緒あり", place_context: null, goriyaku: null, history_theme: null, label: "由緒あり" },
      }),
      recommendationReasonV4: null,
      reason: null,
    });

    expect(result.explanationOnlyFactText).toBe("由緒あり");
    expect(result.factText).toBeNull();
  });

  it("goriyakuが選ばれるケース(deity/shrine_historyが無い場合、Ranking-related)", () => {
    const result = buildHeroReasonV4Sections({
      detail: makeDetail({
        fact: { deity: null, shrine_history: null, place_context: "住所情報", goriyaku: "縁結び", history_theme: "再出発", label: "住所情報" },
      }),
      recommendationReasonV4: null,
      reason: null,
    });

    expect(result.factText).toBe("縁結び");
    expect(result.factText).not.toBe("住所情報");
    expect(result.explanationOnlyFactText).toBeNull();
  });

  it("history_themeが選ばれるケース(deity/shrine_history/goriyakuが無い場合、Ranking-related)", () => {
    const result = buildHeroReasonV4Sections({
      detail: makeDetail({
        fact: { deity: null, shrine_history: null, place_context: "住所情報", goriyaku: null, history_theme: "再出発", label: "住所情報" },
      }),
      recommendationReasonV4: null,
      reason: null,
    });

    expect(result.factText).toBe("再出発");
    expect(result.explanationOnlyFactText).toBeNull();
  });

  it("place_contextだけではFactを生成しない(住所を神社の特徴として表示しない)", () => {
    const result = buildHeroReasonV4Sections({
      detail: makeDetail({
        fact: {
          deity: null,
          shrine_history: null,
          place_context: "東京都渋谷区代々木神園町1-1",
          goriyaku: null,
          history_theme: null,
          label: "東京都渋谷区代々木神園町1-1",
        },
        interpretation: { text: "" },
        action: { text: "" },
      }),
      recommendationReasonV4: null,
      reason: null,
    });

    expect(result.factText).toBeNull();
  });

  it("labelだけではFactを生成しない", () => {
    const result = buildHeroReasonV4Sections({
      detail: makeDetail({
        fact: {
          deity: null,
          shrine_history: null,
          place_context: null,
          goriyaku: null,
          history_theme: null,
          label: "候補神社",
        },
        interpretation: { text: "" },
        action: { text: "" },
      }),
      recommendationReasonV4: null,
      reason: null,
    });

    expect(result.factText).toBeNull();
  });

  it("BackendのFact本文(deity)が独自fallbackより優先される(interpretationがhasStructuredを成立させる)", () => {
    const result = buildHeroReasonV4Sections({
      detail: makeDetail({
        fact: { deity: "武神", shrine_history: null, place_context: "住所情報", goriyaku: null, history_theme: null, label: "住所情報" },
      }),
      recommendationReasonV4: "recommendation_reason_v4の内容",
      reason: "旧型の理由文",
    });

    expect(result.hasStructured).toBe(true);
    expect(result.explanationOnlyFactText).toBe("武神");
    expect(result.factText).toBeNull();
    expect(result.fallbackText).toBeNull();
  });

  it("deityのみが構造化要素で、interpretation/actionも空の場合はhasStructured=falseとなりlegacy fallbackへ切り替わる(Fallback Contract、Finding 9)", () => {
    const result = buildHeroReasonV4Sections({
      detail: makeDetail({
        fact: { deity: "武神", shrine_history: null, place_context: null, goriyaku: null, history_theme: null, label: "武神" },
        interpretation: { text: "" },
        action: { text: "" },
        reason_text: "reason_textのfallback文言",
      }),
      recommendationReasonV4: "recommendation_reason_v4の内容",
      reason: "旧型の理由文",
    });

    // deity単独では「構造化されたRecommendation理由」として扱わない
    // (=「この神様だから推薦した」という意味一致をConclusionに持たせない)。
    expect(result.hasStructured).toBe(false);
    expect(result.factText).toBeNull();
    expect(result.fallbackText).toBe("reason_textのfallback文言");
    // deity自体は「参考情報」として引き続き利用可能(hasStructuredの有無に関わらず提供される)。
    expect(result.explanationOnlyFactText).toBe("武神");
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
