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

// 主な根拠(is_primary)が意味の一致を表す種類のとき(推薦の根拠になる)。
const AUTHORITY_FACTS = [{ type: "need_tag", label: "love", evidence: [], score: 1, is_primary: true }];
// 主な根拠が意味の一致でないとき(生年月日の相性など)。
const NON_AUTHORITY_FACTS = [{ type: "element", label: "element", evidence: [], score: 1, is_primary: true }];

describe("buildShrineDetailReasonV4Sections", () => {
  it("fact/interpretation/actionが構造化表示として返る", () => {
    const result = buildShrineDetailReasonV4Sections(makeDetail(), AUTHORITY_FACTS);

    expect(result.hasStructured).toBe(true);
    expect(result.factText).toBe("縁結び・厄除け");
    expect(result.aboutShrineFactText).toBeNull();
    expect(result.interpretationText).toBe("相談内容から、今扱いたいテーマを読み取っています。");
    expect(result.actionText).toBe("参拝前に、問いを一つに絞ることを決めておきます。");
  });

  it("factは優先順位(deity > shrine_history > goriyaku > history_theme)で選ばれる", () => {
    const result = buildShrineDetailReasonV4Sections(
      makeDetail({
        fact: { deity: "武神", shrine_history: "由緒あり", place_context: "住所情報", goriyaku: "縁結び", history_theme: "再出発" },
      }),
    );

    expect(result.factText).toBeNull();
  });

  // App-wide Evidence & Dark UI Regression Audit Bug-1: deity/shrine_historyはExplanation-only
  // Knowledge Fact(Signal Authority正本§8、Rank/Eligibilityに一切寄与しない)。主な根拠が意味の
  // 一致でも、factText(選ばれた背景)へは混ぜず、aboutShrineFactText(この神社について)へ分離する。
  it("deityが勝ちfactの場合、主な根拠が意味の一致でもfactTextではなくaboutShrineFactTextへ分離される", () => {
    const result = buildShrineDetailReasonV4Sections(
      makeDetail({
        fact: { deity: "武神", shrine_history: null, place_context: null, goriyaku: "縁結び", history_theme: "再出発" },
        interpretation: { text: "" },
        action: { text: "" },
      }),
      AUTHORITY_FACTS,
    );

    expect(result.factText).toBeNull();
    expect(result.aboutShrineFactText).toBe("武神");
    expect(result.aboutShrineFactSource).toBe("deity");
    // Explanation-onlyのみでは「構造化されたRecommendation理由」として数えない
    // (hasStructuredはfactText/interpretationText/actionTextのみで判定する)。
    expect(result.hasStructured).toBe(false);
  });

  it("shrine_historyが勝ちfactの場合も同様にaboutShrineFactTextへ分離される", () => {
    const result = buildShrineDetailReasonV4Sections(
      makeDetail({
        fact: { deity: null, shrine_history: "由緒あり", place_context: null, goriyaku: "縁結び", history_theme: "再出発" },
      }),
      AUTHORITY_FACTS,
    );

    expect(result.factText).toBeNull();
    expect(result.aboutShrineFactText).toBe("由緒あり");
  });

  it("deity/shrine_historyが無く主な根拠が意味の一致のとき、goriyakuはfactText(選ばれた背景)", () => {
    const result = buildShrineDetailReasonV4Sections(
      makeDetail({
        fact: { deity: null, shrine_history: null, place_context: null, goriyaku: "縁結び", history_theme: "再出発" },
      }),
      AUTHORITY_FACTS,
    );

    expect(result.factText).toBe("縁結び");
    expect(result.aboutShrineFactText).toBeNull();
  });

  it("deity/shrine_history/goriyakuが無い場合はhistory_themeを使う(主な根拠が意味の一致ならfactText)", () => {
    const result = buildShrineDetailReasonV4Sections(
      makeDetail({
        fact: { deity: null, shrine_history: null, place_context: "住所情報", goriyaku: null, history_theme: "再出発" },
      }),
      AUTHORITY_FACTS,
    );

    expect(result.factText).toBe("再出発");
    expect(result.aboutShrineFactText).toBeNull();
  });

  it.each(["history_theme", "need_tag", "text_hint", "goriyaku_tag"])(
    "主な根拠が %s のとき、goriyakuはfactText(選ばれた背景)",
    (type) => {
      const result = buildShrineDetailReasonV4Sections(
        makeDetail({ fact: { deity: null, shrine_history: null, goriyaku: "縁結び" } }),
        [{ type, label: "x", evidence: [], score: 1, is_primary: true }],
      );
      expect(result.factText).toBe("縁結び");
      expect(result.aboutShrineFactText).toBeNull();
    },
  );

  it.each(["element", "visit_style", "fallback", "user_selected_tag"])(
    "主な根拠が %s のとき、goriyakuは根拠ではないためaboutShrineFactText(この神社について)",
    (type) => {
      const result = buildShrineDetailReasonV4Sections(
        makeDetail({ fact: { deity: null, shrine_history: null, goriyaku: "縁結び" } }),
        [{ type, label: "x", evidence: [], score: 1, is_primary: true }],
      );
      expect(result.factText).toBeNull();
      expect(result.aboutShrineFactText).toBe("縁結び");
      expect(result.aboutShrineFactSource).toBe("goriyaku");
    },
  );

  it("主な根拠が意味の一致でないとき、history_themeもaboutShrineFactText", () => {
    const result = buildShrineDetailReasonV4Sections(
      makeDetail({ fact: { deity: null, shrine_history: null, goriyaku: null, history_theme: "再出発" } }),
      NON_AUTHORITY_FACTS,
    );
    expect(result.factText).toBeNull();
    expect(result.aboutShrineFactText).toBe("再出発");
    expect(result.aboutShrineFactSource).toBe("history_theme");
  });

  it.each([
    ["reason_factsが無い", undefined],
    ["reason_factsが空", []],
    ["is_primaryが無い", [{ type: "need_tag", label: "love", evidence: [], score: 1 }]],
  ])("%sときは根拠が分からないため、goriyakuもaboutShrineFactText", (_case, reasonFacts) => {
    const result = buildShrineDetailReasonV4Sections(
      makeDetail({ fact: { deity: null, shrine_history: null, goriyaku: "縁結び" } }),
      reasonFacts,
    );
    expect(result.factText).toBeNull();
    expect(result.aboutShrineFactText).toBe("縁結び");
  });

  describe("確認済みの御祭神・由緒のデータ(deities / histories)との重なり", () => {
    const deityFact = { deity: "八幡大神", shrine_history: null, goriyaku: "勝運", history_theme: null };
    const historyFact = { deity: null, shrine_history: "古くからの由緒", goriyaku: "勝運", history_theme: null };

    it("選ばれた事実が御祭神で、確認済みの御祭神データがあるとき、「この神社について」に出さない", () => {
      const result = buildShrineDetailReasonV4Sections(makeDetail({ fact: deityFact }), AUTHORITY_FACTS, {
        hasDeities: true,
        hasHistories: false,
      });
      expect(result.factText).toBeNull();
      expect(result.aboutShrineFactText).toBeNull();
      expect(result.aboutShrineFactSource).toBeNull();
    });

    it("選ばれた事実が由緒で、確認済みの由緒データがあるとき、「この神社について」に出さない", () => {
      const result = buildShrineDetailReasonV4Sections(makeDetail({ fact: historyFact }), AUTHORITY_FACTS, {
        hasDeities: false,
        hasHistories: true,
      });
      expect(result.aboutShrineFactText).toBeNull();
    });

    it("確認済みのデータが無いとき、古い項目から来た御祭神を「この神社について」に出す", () => {
      const result = buildShrineDetailReasonV4Sections(makeDetail({ fact: deityFact }), AUTHORITY_FACTS, {
        hasDeities: false,
        hasHistories: false,
      });
      expect(result.aboutShrineFactText).toBe("八幡大神");
      expect(result.aboutShrineFactSource).toBe("deity");
    });

    it("御祭神と由緒は別々に見分ける(確認済みの由緒だけがあっても、御祭神は出す)", () => {
      const deityResult = buildShrineDetailReasonV4Sections(makeDetail({ fact: deityFact }), AUTHORITY_FACTS, {
        hasDeities: false,
        hasHistories: true,
      });
      expect(deityResult.aboutShrineFactText).toBe("八幡大神");

      const historyResult = buildShrineDetailReasonV4Sections(makeDetail({ fact: historyFact }), AUTHORITY_FACTS, {
        hasDeities: true,
        hasHistories: false,
      });
      expect(historyResult.aboutShrineFactText).toBe("古くからの由緒");
    });

    it("御祭神を外しても、次の事実(ご利益)へ選び直さない", () => {
      const result = buildShrineDetailReasonV4Sections(makeDetail({ fact: deityFact }), AUTHORITY_FACTS, {
        hasDeities: true,
        hasHistories: true,
      });
      expect(result.factText).toBeNull();
      expect(result.aboutShrineFactText).toBeNull();
    });

    it("根拠にならないご利益は、確認済みのデータがあっても「この神社について」に出す", () => {
      const result = buildShrineDetailReasonV4Sections(
        makeDetail({ fact: { deity: null, shrine_history: null, goriyaku: "縁結び", history_theme: null } }),
        NON_AUTHORITY_FACTS,
        { hasDeities: true, hasHistories: true },
      );
      expect(result.aboutShrineFactText).toBe("縁結び");
      expect(result.aboutShrineFactSource).toBe("goriyaku");
    });

    it("根拠にならない歴史のテーマは、確認済みのデータがあっても「この神社について」に出す", () => {
      const result = buildShrineDetailReasonV4Sections(
        makeDetail({ fact: { deity: null, shrine_history: null, goriyaku: null, history_theme: "再出発" } }),
        NON_AUTHORITY_FACTS,
        { hasDeities: true, hasHistories: true },
      );
      expect(result.aboutShrineFactText).toBe("再出発");
    });

    it("根拠になるご利益は、確認済みのデータがあっても「選ばれた背景」(factText)のまま", () => {
      const result = buildShrineDetailReasonV4Sections(
        makeDetail({ fact: { deity: null, shrine_history: null, goriyaku: "縁結び", history_theme: null } }),
        AUTHORITY_FACTS,
        { hasDeities: true, hasHistories: true },
      );
      expect(result.factText).toBe("縁結び");
      expect(result.aboutShrineFactText).toBeNull();
    });
  });

  it("出し分けは reason_text(補助情報の文の有無)では判定しない", () => {
    const withNote = makeDetail({ fact: { deity: null, shrine_history: null, goriyaku: "縁結び" } });
    withNote.reason_text = "縁結び。この情報は神社を説明する補助情報であり、今回の順位根拠ではありません。";
    expect(buildShrineDetailReasonV4Sections(withNote, AUTHORITY_FACTS).factText).toBe("縁結び");
    expect(buildShrineDetailReasonV4Sections(makeDetail(), NON_AUTHORITY_FACTS).factText).toBeNull();
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
      aboutShrineFactText: null,
      aboutShrineFactSource: null,
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
