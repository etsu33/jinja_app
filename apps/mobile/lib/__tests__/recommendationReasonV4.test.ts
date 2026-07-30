import { describe, expect, it } from "vitest";
import {
  buildReasonV4Sections,
  normalizeRecommendationReasonV4Detail,
  serializeReasonV4Detail,
  type RecommendationReasonV4Detail,
} from "../recommendationReasonV4";

function makeDetail(
  overrides: Partial<{
    reason_text: string;
    fact: Partial<RecommendationReasonV4Detail["fact"]>;
    interpretation: Partial<RecommendationReasonV4Detail["interpretation"]>;
    action: Partial<RecommendationReasonV4Detail["action"]>;
  }> = {},
): RecommendationReasonV4Detail {
  return {
    version: "v4",
    reason_text: overrides.reason_text ?? "根津神社は仕事運に関わる神社です。",
    fact: {
      label: "根津神社",
      name: "根津神社",
      deity: null,
      shrine_history: null,
      place_context: null,
      history_theme: "再出発",
      goriyaku: "仕事運",
      visit_style_tags: [],
      evidence: ["history_theme:再出発"],
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

describe("normalizeRecommendationReasonV4Detail", () => {
  it("正しいobjectを欠損なく正規化する", () => {
    const raw = makeDetail();
    const result = normalizeRecommendationReasonV4Detail(raw);
    expect(result).toEqual(raw);
  });

  it("object以外(null/undefined/文字列/配列)はnullを返す", () => {
    expect(normalizeRecommendationReasonV4Detail(null)).toBeNull();
    expect(normalizeRecommendationReasonV4Detail(undefined)).toBeNull();
    expect(normalizeRecommendationReasonV4Detail("not-an-object")).toBeNull();
    expect(normalizeRecommendationReasonV4Detail([])).toBeNull();
  });

  it("空objectでもクラッシュせず空値で埋めたobjectを返す", () => {
    const result = normalizeRecommendationReasonV4Detail({});
    expect(result).toEqual({
      version: "v4",
      reason_text: "",
      fact: {
        label: "",
        name: null,
        deity: null,
        shrine_history: null,
        place_context: null,
        history_theme: null,
        goriyaku: null,
        visit_style_tags: [],
        evidence: [],
      },
      interpretation: { theme: "", text: "" },
      action: { text: "", source: "" },
    });
  });

  it("fact/interpretation/actionが欠落していてもクラッシュしない", () => {
    const result = normalizeRecommendationReasonV4Detail({ reason_text: "本文のみ" });
    expect(result?.reason_text).toBe("本文のみ");
    expect(result?.fact.label).toBe("");
    expect(result?.interpretation.text).toBe("");
    expect(result?.action.text).toBe("");
  });

  it("空白のみの文字列は空文字として扱う", () => {
    const result = normalizeRecommendationReasonV4Detail({
      reason_text: "   ",
      fact: { label: "  ", history_theme: "   " },
    });
    expect(result?.reason_text).toBe("");
    expect(result?.fact.label).toBe("");
    expect(result?.fact.history_theme).toBeNull();
  });

  it("visit_style_tags/evidenceが配列以外の場合は空配列にする", () => {
    const result = normalizeRecommendationReasonV4Detail({
      fact: { visit_style_tags: "not-an-array", evidence: null },
    });
    expect(result?.fact.visit_style_tags).toEqual([]);
    expect(result?.fact.evidence).toEqual([]);
  });
});

describe("buildReasonV4Sections", () => {
  it("fact/interpretation/actionすべて存在する場合は構造化表示になる", () => {
    const result = buildReasonV4Sections({ detail: makeDetail(), fallbackReason: null });
    expect(result.hasStructured).toBe(true);
    expect(result.factText).toBe("仕事運");
    expect(result.interpretationText).toBe("相談内容から、今扱いたいテーマを読み取っています。");
    expect(result.actionText).toBe("参拝前に、問いを一つに絞ることを決めておきます。");
    expect(result.fallbackText).toBeNull();
  });

  it("factのみ存在する場合もhasStructured=trueになる", () => {
    const result = buildReasonV4Sections({
      detail: makeDetail({ interpretation: { text: "" }, action: { text: "" } }),
      fallbackReason: null,
    });
    expect(result.hasStructured).toBe(true);
    expect(result.factText).toBe("仕事運");
    expect(result.interpretationText).toBeNull();
    expect(result.actionText).toBeNull();
  });

  it("interpretationのみ存在する場合もhasStructured=trueになる", () => {
    const result = buildReasonV4Sections({
      detail: makeDetail({
        fact: { shrine_history: null, place_context: null, goriyaku: null, history_theme: null, label: "" },
        action: { text: "" },
      }),
      fallbackReason: null,
    });
    expect(result.hasStructured).toBe(true);
    expect(result.factText).toBeNull();
    expect(result.interpretationText).toBe("相談内容から、今扱いたいテーマを読み取っています。");
    expect(result.actionText).toBeNull();
  });

  it("actionのみ存在する場合もhasStructured=trueになる", () => {
    const result = buildReasonV4Sections({
      detail: makeDetail({
        fact: { shrine_history: null, place_context: null, goriyaku: null, history_theme: null, label: "" },
        interpretation: { text: "" },
      }),
      fallbackReason: null,
    });
    expect(result.hasStructured).toBe(true);
    expect(result.factText).toBeNull();
    expect(result.interpretationText).toBeNull();
    expect(result.actionText).toBe("参拝前に、問いを一つに絞ることを決めておきます。");
  });

  it("fact優先順位はdeity > shrine_history > goriyaku > history_theme(place_context/labelは候補にしない)", () => {
    const result = buildReasonV4Sections({
      detail: makeDetail({
        fact: { deity: "武神", shrine_history: "由緒あり", place_context: "住所情報", goriyaku: "縁結び", history_theme: "再出発", label: "候補神社" },
      }),
      fallbackReason: null,
    });
    expect(result.factText).toBe("武神");
  });

  it("deity/shrine_historyが無い場合はgoriyakuを優先し、place_contextは使わない", () => {
    const result = buildReasonV4Sections({
      detail: makeDetail({
        fact: { deity: null, shrine_history: null, place_context: "住所情報", goriyaku: "縁結び", history_theme: "再出発", label: "住所情報" },
      }),
      fallbackReason: null,
    });
    expect(result.factText).toBe("縁結び");
    expect(result.factText).not.toBe("住所情報");
  });

  it("place_contextのみの場合はfactTextをnullにする(住所を神社の特徴として表示しない)", () => {
    const result = buildReasonV4Sections({
      detail: makeDetail({
        fact: {
          deity: null,
          shrine_history: null,
          place_context: "東京都渋谷区代々木神園町1-1",
          goriyaku: null,
          history_theme: null,
          label: "東京都渋谷区代々木神園町1-1",
        },
      }),
      fallbackReason: null,
    });
    expect(result.factText).toBeNull();
  });

  it("空objectのdetail(全field空)はhasStructured=falseになりreason_textへfallbackする", () => {
    const result = buildReasonV4Sections({
      detail: normalizeRecommendationReasonV4Detail({}),
      fallbackReason: "旧型の理由文",
    });
    expect(result.hasStructured).toBe(false);
    expect(result.fallbackText).toBe("旧型の理由文");
  });

  it("構造化fieldがすべて空でもreason_textがあればreason_textへfallbackする", () => {
    const result = buildReasonV4Sections({
      detail: makeDetail({
        fact: { shrine_history: null, place_context: null, goriyaku: null, history_theme: null, label: "" },
        interpretation: { text: "" },
        action: { text: "" },
        reason_text: "reason_textの内容",
      }),
      fallbackReason: "recommendation_reason_v4等の解決済み理由",
    });
    expect(result.hasStructured).toBe(false);
    expect(result.fallbackText).toBe("reason_textの内容");
  });

  it("reason_textが無い場合はfallbackReason(recommendation_reason_v4/reasonFacts/reason解決済み)を使う", () => {
    const result = buildReasonV4Sections({
      detail: makeDetail({
        fact: { shrine_history: null, place_context: null, goriyaku: null, history_theme: null, label: "" },
        interpretation: { text: "" },
        action: { text: "" },
        reason_text: "",
      }),
      fallbackReason: "recommendation_reason_v4等の解決済み理由",
    });
    expect(result.fallbackText).toBe("recommendation_reason_v4等の解決済み理由");
  });

  it("detailがnullでもfallbackReasonへ安全にfallbackする(reasonFacts/reason解決済み想定)", () => {
    const result = buildReasonV4Sections({ detail: null, fallbackReason: "相談内容と神社情報をもとに選ばれた神社です。" });
    expect(result.hasStructured).toBe(false);
    expect(result.fallbackText).toBe("相談内容と神社情報をもとに選ばれた神社です。");
  });

  it("detail・fallbackReasonとも欠落してもクラッシュせずnullを返す", () => {
    const result = buildReasonV4Sections({ detail: null, fallbackReason: null });
    expect(result.hasStructured).toBe(false);
    expect(result.factText).toBeNull();
    expect(result.interpretationText).toBeNull();
    expect(result.actionText).toBeNull();
    expect(result.fallbackText).toBeNull();
  });

  it("action.sourceは戻り値に含まれない", () => {
    const result = buildReasonV4Sections({ detail: makeDetail(), fallbackReason: null });
    expect(result).not.toHaveProperty("actionSource");
    expect(result).not.toHaveProperty("source");
    expect(Object.keys(result)).toEqual(["factText", "interpretationText", "actionText", "hasStructured", "fallbackText"]);
  });

  it("構造化表示が可能な場合、fallbackTextと重複しない(fallbackTextはnull)", () => {
    const result = buildReasonV4Sections({
      detail: makeDetail({ reason_text: "reason_textの内容" }),
      fallbackReason: "旧型の理由文",
    });
    expect(result.hasStructured).toBe(true);
    expect(result.fallbackText).toBeNull();
  });

  it("方位・断定表現を含むテキストは表示から除外される", () => {
    const result = buildReasonV4Sections({
      detail: null,
      fallbackReason: "この方位は吉方位なので必ず良い結果になります。",
    });
    expect(result.fallbackText).toBeNull();
  });
});

describe("serializeReasonV4Detail", () => {
  it("detailが存在する場合はJSON文字列化する", () => {
    const detail = makeDetail();
    expect(serializeReasonV4Detail(detail)).toBe(JSON.stringify(detail));
  });

  it("detailがnullの場合は空文字を返す(不要なJSON文字列を生成しない)", () => {
    expect(serializeReasonV4Detail(null)).toBe("");
  });

  it("detailがundefinedの場合は空文字を返す", () => {
    expect(serializeReasonV4Detail(undefined)).toBe("");
  });
});
