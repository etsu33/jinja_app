// apps/web/src/lib/shrine/__tests__/buildShrineDetailReasonV4Sections.test.ts
import { describe, it, expect } from "vitest";
import {
  buildShrineDetailReasonV4Sections,
  normalizeRecommendationReasonV4Detail,
} from "../buildShrineDetailReasonV4Sections";

function makeDetail(overrides: Partial<{ fact: any; interpretation: any; action: any }> = {}) {
  return {
    version: "v4" as const,
    reason_text: "根津神社には、縁結び・厄除けに関する情報があります。",
    fact: {
      label: "候補神社",
      name: "根津神社",
      deity: null,
      shrine_history: null,
      place_context: null,
      history_theme: "再出発",
      goriyaku: "縁結び・厄除け",
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

describe("buildShrineDetailReasonV4Sections", () => {
  it("fact/interpretation/actionが構造化表示として返る", () => {
    const result = buildShrineDetailReasonV4Sections(makeDetail());

    expect(result.hasStructured).toBe(true);
    expect(result.factText).toBe("縁結び・厄除け");
    expect(result.interpretationText).toBe("相談内容から、今扱いたいテーマを読み取っています。");
    expect(result.actionText).toBe("参拝前に、問いを一つに絞ることを決めておきます。");
  });

  it("factは優先順位(deity > shrine_history > goriyaku > history_theme)で選ばれる", () => {
    const result = buildShrineDetailReasonV4Sections(
      makeDetail({
        fact: { deity: "武神", shrine_history: "由緒あり", place_context: "住所情報", goriyaku: "縁結び", history_theme: "再出発" },
      }),
    );

    expect(result.factText).toBe("武神");
  });

  it("deity/shrine_history/goriyakuが無い場合はhistory_themeを使う", () => {
    const result = buildShrineDetailReasonV4Sections(
      makeDetail({
        fact: { deity: null, shrine_history: null, place_context: "住所情報", goriyaku: null, history_theme: "再出発" },
      }),
    );

    expect(result.factText).toBe("再出発");
  });

  it("place_contextだけではFactを生成しない(住所を神社の特徴として表示しない)", () => {
    const result = buildShrineDetailReasonV4Sections(
      makeDetail({
        fact: {
          deity: null,
          shrine_history: null,
          place_context: "東京都渋谷区代々木神園町1-1",
          goriyaku: null,
          history_theme: null,
        },
        interpretation: { text: "" },
        action: { text: "" },
      }),
    );

    expect(result.factText).toBeNull();
    expect(result.hasStructured).toBe(false);
  });

  it("labelだけではFactを生成しない", () => {
    const result = buildShrineDetailReasonV4Sections(
      makeDetail({
        fact: {
          label: "候補神社",
          deity: null,
          shrine_history: null,
          place_context: null,
          goriyaku: null,
          history_theme: null,
        },
        interpretation: { text: "" },
        action: { text: "" },
      }),
    );

    expect(result.factText).toBeNull();
  });

  it("detailがnullの場合はすべてnull/falseを返す", () => {
    const result = buildShrineDetailReasonV4Sections(null);

    expect(result).toEqual({
      factText: null,
      interpretationText: null,
      actionText: null,
      hasStructured: false,
    });
  });
});

describe("normalizeRecommendationReasonV4Detail", () => {
  it("正しいobjectを正規化する", () => {
    const raw = makeDetail();
    const result = normalizeRecommendationReasonV4Detail(raw);
    expect(result?.fact?.goriyaku).toBe("縁結び・厄除け");
    expect(result?.interpretation?.text).toBe("相談内容から、今扱いたいテーマを読み取っています。");
  });

  it("object以外(null/undefined/文字列/配列)はnullを返す(旧Thread互換)", () => {
    expect(normalizeRecommendationReasonV4Detail(null)).toBeNull();
    expect(normalizeRecommendationReasonV4Detail(undefined)).toBeNull();
    expect(normalizeRecommendationReasonV4Detail("not-an-object")).toBeNull();
    expect(normalizeRecommendationReasonV4Detail([])).toBeNull();
  });

  it("fact/interpretation/actionが欠落していてもクラッシュしない(空値で埋める)", () => {
    const result = normalizeRecommendationReasonV4Detail({ reason_text: "本文のみ" });
    expect(result?.reason_text).toBe("本文のみ");
    expect(result?.fact?.deity).toBeNull();
    expect(result?.interpretation?.text).toBeNull();
    expect(result?.action?.text).toBeNull();
  });

  it("空white文字列は空値として扱う", () => {
    const result = normalizeRecommendationReasonV4Detail({
      fact: { deity: "   ", goriyaku: "縁結び" },
    });
    expect(result?.fact?.deity).toBeNull();
    expect(result?.fact?.goriyaku).toBe("縁結び");
  });
});
