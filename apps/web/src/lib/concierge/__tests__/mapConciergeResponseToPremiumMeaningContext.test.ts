import { describe, expect, it } from "vitest";

import type { ConciergeRecommendation } from "@/lib/api/concierge";
import { mapConciergeResponseToPremiumMeaningContext } from "../mapConciergeResponseToPremiumMeaningContext";

function rec(overrides: Partial<ConciergeRecommendation> = {}): ConciergeRecommendation {
  return {
    id: 17,
    shrine_id: 17,
    name: "契約神社",
    ...overrides,
  };
}

describe("mapConciergeResponseToPremiumMeaningContext: primary reason_fact mapping", () => {
  it("is_primary=trueのfactをprimaryReasonFactへmappingする", () => {
    const ctx = mapConciergeResponseToPremiumMeaningContext({
      rec: rec({
        reason_facts: [
          { type: "need_tag", label: "転機", evidence: ["need_tag:転機"], score: 1, is_primary: true },
        ],
      }),
    });

    expect(ctx?.recommendationEvidence.primaryReasonFact).toEqual({
      type: "need_tag",
      label: "転機",
      evidence: ["need_tag:転機"],
    });
  });

  it("is_primaryが無いfact配列ではprimaryReasonFactがnullになる", () => {
    const ctx = mapConciergeResponseToPremiumMeaningContext({
      rec: rec({
        reason_facts: [{ type: "distance", label: "1.2km", evidence: [], score: 1 }],
      }),
    });

    expect(ctx?.recommendationEvidence.primaryReasonFact).toBeNull();
  });
});

describe("mapConciergeResponseToPremiumMeaningContext: secondary reason_facts", () => {
  it("secondary reason_factsが全件保持される(切り捨てない)", () => {
    const ctx = mapConciergeResponseToPremiumMeaningContext({
      rec: rec({
        reason_facts: [
          { type: "need_tag", label: "転機", evidence: ["a"], score: 3, is_primary: true },
          { type: "distance", label: "1.2km", evidence: ["b"], score: 2 },
          { type: "popular", label: "人気", evidence: ["c"], score: 1 },
          { type: "goriyaku_tag", label: "勝運", evidence: ["d"], score: 1 },
        ],
      }),
    });

    expect(ctx?.recommendationEvidence.secondaryReasonFacts).toHaveLength(3);
    expect(ctx?.recommendationEvidence.secondaryReasonFacts).toEqual([
      { type: "distance", label: "1.2km", evidence: ["b"] },
      { type: "popular", label: "人気", evidence: ["c"] },
      { type: "goriyaku_tag", label: "勝運", evidence: ["d"] },
    ]);
  });

  it("reason_factsが空/未定義ならsecondaryReasonFactsは空配列になる(throwしない)", () => {
    const ctxEmpty = mapConciergeResponseToPremiumMeaningContext({ rec: rec({ reason_facts: [] }) });
    const ctxUndefined = mapConciergeResponseToPremiumMeaningContext({ rec: rec({ reason_facts: undefined }) });

    expect(ctxEmpty?.recommendationEvidence.secondaryReasonFacts).toEqual([]);
    expect(ctxUndefined?.recommendationEvidence.secondaryReasonFacts).toEqual([]);
  });
});

describe("mapConciergeResponseToPremiumMeaningContext: shrine evidence mapping", () => {
  it("recommendation_reason_v4_detail.factからdeity/history/placeContext/historyThemeをmappingする", () => {
    const ctx = mapConciergeResponseToPremiumMeaningContext({
      rec: rec({
        recommendation_reason_v4_detail: {
          version: "v4",
          reason_text: "",
          fact: {
            label: "",
            name: null,
            deity: "祭神A",
            shrine_history: "由緒の記述",
            place_context: "山間の参道",
            history_theme: "再出発",
            goriyaku: "勝運",
            visit_style_tags: [],
            evidence: [],
          },
          interpretation: { theme: "", text: "" },
          action: { text: "", source: "" },
        },
      }),
    });

    expect(ctx?.shrineEvidence.deity).toBe("祭神A");
    expect(ctx?.shrineEvidence.history).toBe("由緒の記述");
    expect(ctx?.shrineEvidence.placeContext).toBe("山間の参道");
    expect(ctx?.shrineEvidence.historyTheme).toBe("再出発");
    expect(ctx?.shrineEvidence.goriyaku).toEqual(["勝運"]);
  });

  it("trust_metadataからoriginSummary/culturalStatus/lineageをmappingする", () => {
    const ctx = mapConciergeResponseToPremiumMeaningContext({
      rec: rec({
        trust_metadata: {
          rank_class: "A",
          cultural_status: ["国宝"],
          lineage: "式内社",
          origin_summary: "創建に関する記述",
        },
      }),
    });

    expect(ctx?.shrineEvidence.originSummary).toBe("創建に関する記述");
    expect(ctx?.shrineEvidence.culturalStatus).toEqual(["国宝"]);
    expect(ctx?.shrineEvidence.lineage).toBe("式内社");
  });

  it("Shrine Knowledgeが存在しない(recommendation_reason_v4_detail/trust_metadataが無い)場合、対応するfieldはnullになる", () => {
    const ctx = mapConciergeResponseToPremiumMeaningContext({ rec: rec() });

    expect(ctx?.shrineEvidence.deity).toBeNull();
    expect(ctx?.shrineEvidence.history).toBeNull();
    expect(ctx?.shrineEvidence.placeContext).toBeNull();
    expect(ctx?.shrineEvidence.historyTheme).toBeNull();
    expect(ctx?.shrineEvidence.goriyaku).toBeNull();
    expect(ctx?.shrineEvidence.originSummary).toBeNull();
    expect(ctx?.shrineEvidence.culturalStatus).toBeNull();
    expect(ctx?.shrineEvidence.lineage).toBeNull();
    expect(ctx?.shrineEvidence.tradition).toBeNull();
    expect(ctx?.shrineEvidence.verificationMetadata).toBeNull();
  });
});

describe("mapConciergeResponseToPremiumMeaningContext: fixed null fields", () => {
  it("relevantToConsultationは常にnullになる(Evidence存在から推定しない)", () => {
    const ctx = mapConciergeResponseToPremiumMeaningContext({
      rec: rec({
        recommendation_reason_v4_detail: {
          version: "v4",
          reason_text: "",
          fact: {
            label: "",
            name: null,
            deity: "祭神A",
            shrine_history: null,
            place_context: null,
            history_theme: null,
            goriyaku: null,
            visit_style_tags: [],
            evidence: [],
          },
          interpretation: { theme: "", text: "" },
          action: { text: "", source: "" },
        },
      }),
    });

    expect(ctx?.shrineEvidence.deity).toBe("祭神A");
    expect(ctx?.shrineEvidence.relevantToConsultation).toBeNull();
  });

  it("relevantToVisitは常にnullになる", () => {
    const ctx = mapConciergeResponseToPremiumMeaningContext({ rec: rec() });

    expect(ctx?.shrineEvidence.relevantToVisit).toBeNull();
  });

  it("fixed null fieldsの結果、Evidenceが揃っていてもpersonalMeaningValid/actionMeaningValidはfalseのままになる", () => {
    const ctx = mapConciergeResponseToPremiumMeaningContext({
      rec: rec({
        recommendation_reason_v4_detail: {
          version: "v4",
          reason_text: "",
          fact: {
            label: "",
            name: null,
            deity: "祭神A",
            shrine_history: null,
            place_context: null,
            history_theme: null,
            goriyaku: null,
            visit_style_tags: [],
            evidence: [],
          },
          interpretation: { theme: "", text: "" },
          action: { text: "", source: "" },
        },
      }),
      need: { tags: ["転機"] },
      mode: "need",
    });

    expect(ctx?.validity.shrineEvidencePresent).toBe(true);
    expect(ctx?.validity.personalMeaningValid).toBe(false);
    expect(ctx?.validity.actionMeaningValid).toBe(false);
  });
});

describe("mapConciergeResponseToPremiumMeaningContext: empty/missing API data does not throw", () => {
  it("recが未定義でもthrowせずnullを返す", () => {
    expect(() => mapConciergeResponseToPremiumMeaningContext({})).not.toThrow();
    expect(mapConciergeResponseToPremiumMeaningContext({})).toBeNull();
  });

  it("recがnullでもthrowせずnullを返す", () => {
    expect(() => mapConciergeResponseToPremiumMeaningContext({ rec: null })).not.toThrow();
    expect(mapConciergeResponseToPremiumMeaningContext({ rec: null })).toBeNull();
  });

  it("shrine_id/idが両方無いrecではthrowせずnullを返す", () => {
    const ctx = mapConciergeResponseToPremiumMeaningContext({
      rec: { name: "id不明神社" } as ConciergeRecommendation,
    });

    expect(ctx).toBeNull();
  });

  it("needが未定義/emptyでもthrowしない", () => {
    expect(() => mapConciergeResponseToPremiumMeaningContext({ rec: rec(), need: undefined })).not.toThrow();
    expect(() => mapConciergeResponseToPremiumMeaningContext({ rec: rec(), need: {} })).not.toThrow();

    const ctx = mapConciergeResponseToPremiumMeaningContext({ rec: rec(), need: {} });
    expect(ctx?.consultation.primaryNeed).toBeNull();
  });

  it("空のrec({}相当、shrine_id/idのみ)でもフィールドがnull/空で埋まりthrowしない", () => {
    expect(() => mapConciergeResponseToPremiumMeaningContext({ rec: { id: 1 } as ConciergeRecommendation })).not.toThrow();

    const ctx = mapConciergeResponseToPremiumMeaningContext({ rec: { id: 1 } as ConciergeRecommendation });
    expect(ctx?.shrineId).toBe(1);
    expect(ctx?.recommendationEvidence.primaryReasonFact).toBeNull();
    expect(ctx?.recommendationEvidence.secondaryReasonFacts).toEqual([]);
  });
});

describe("mapConciergeResponseToPremiumMeaningContext: _need / mode mapping", () => {
  it("need.tagsの先頭2件をprimaryNeed/secondaryNeedへmappingする", () => {
    const ctx = mapConciergeResponseToPremiumMeaningContext({
      rec: rec(),
      need: { tags: ["転機", "仕事", "健康"] },
      mode: "need",
    });

    expect(ctx?.consultation.primaryNeed).toBe("転機");
    expect(ctx?.consultation.secondaryNeed).toBe("仕事");
    expect(ctx?.consultation.mode).toBe("need");
  });
});

describe("mapConciergeResponseToPremiumMeaningContext: consultation_meaning mapping (PR-C)", () => {
  it("snake_case APIのconsultation_meaningをcamelCaseの3配列へmappingする", () => {
    const ctx = mapConciergeResponseToPremiumMeaningContext({
      rec: rec(),
      consultationMeaning: {
        situation_signals: [{ type: "depleted", evidence: [{ text: "疲れている" }] }],
        desired_outcome_signals: [{ type: "clarify", evidence: [{ text: "整理したい" }] }],
        explicit_constraint_signals: [],
      },
    });

    expect(ctx?.consultation.situationSignals).toEqual([{ type: "depleted", evidence: [{ text: "疲れている" }] }]);
    expect(ctx?.consultation.desiredOutcomeSignals).toEqual([{ type: "clarify", evidence: [{ text: "整理したい" }] }]);
    expect(ctx?.consultation.explicitConstraintSignals).toEqual([]);
  });

  it("consultation_meaningが未定義の場合、3配列は空配列になる(throwしない)", () => {
    const ctx = mapConciergeResponseToPremiumMeaningContext({ rec: rec() });

    expect(ctx?.consultation.situationSignals).toEqual([]);
    expect(ctx?.consultation.desiredOutcomeSignals).toEqual([]);
    expect(ctx?.consultation.explicitConstraintSignals).toEqual([]);
  });

  it("consultation_meaningがnullでもthrowせず空配列になる", () => {
    expect(() =>
      mapConciergeResponseToPremiumMeaningContext({ rec: rec(), consultationMeaning: null }),
    ).not.toThrow();

    const ctx = mapConciergeResponseToPremiumMeaningContext({ rec: rec(), consultationMeaning: null });
    expect(ctx?.consultation.situationSignals).toEqual([]);
  });

  it("mappingされたsituationSignalsがuserContextValid/personalMeaningValidを成立させる(need_tag非依存)", () => {
    const ctx = mapConciergeResponseToPremiumMeaningContext({
      rec: rec({
        recommendation_reason_v4_detail: {
          version: "v4",
          reason_text: "",
          fact: {
            label: "",
            name: null,
            deity: "祭神A",
            shrine_history: null,
            place_context: null,
            history_theme: null,
            goriyaku: null,
            visit_style_tags: [],
            evidence: [],
          },
          interpretation: { theme: "", text: "" },
          action: { text: "", source: "" },
        },
      }),
      consultationMeaning: {
        situation_signals: [{ type: "depleted", evidence: [{ text: "疲れている" }] }],
        desired_outcome_signals: [],
        explicit_constraint_signals: [],
      },
    });

    expect(ctx?.validity.userContextValid).toBe(true);
    // relevantToConsultationは常にnull(fixed null field)のため、
    // shrineEvidenceValid/personalMeaningValid自体はまだfalseのまま
    expect(ctx?.shrineEvidence.relevantToConsultation).toBeNull();
    expect(ctx?.validity.personalMeaningValid).toBe(false);
  });

  it("primaryNeedのみ(consultation_meaningなし)ではuserContextValidが成立しない(need_tagはRecommendation Signalのみ)", () => {
    const ctx = mapConciergeResponseToPremiumMeaningContext({
      rec: rec(),
      need: { tags: ["転機"] },
      mode: "need",
    });

    expect(ctx?.consultation.primaryNeed).toBe("転機");
    expect(ctx?.validity.consultationContextValid).toBe(false);
    expect(ctx?.validity.userContextValid).toBe(false);
  });
});

describe("mapConciergeResponseToPremiumMeaningContext: existing Basic Reason contract is untouched", () => {
  it("このmodule追加はbuildRecommendationReasonViewModel等の既存importに影響しない", async () => {
    const { buildRecommendationReasonViewModel } = await import("../buildRecommendationReasonViewModel");
    const vm = buildRecommendationReasonViewModel({
      rec: { id: 999, name: "契約神社" },
      reasonFacts: [{ type: "history_theme", label: "再出発", evidence: [], score: 1, is_primary: true }],
      index: 0,
      mode: "need",
      needTags: [],
    });

    expect(vm.detail.shrineMeaning).toContain("再出発");
  });
});
