import { describe, expect, it } from "vitest";

import type { ConciergeReasonFact } from "@/lib/api/concierge";
import {
  computePremiumMeaningValidity,
  type PremiumMeaningContext,
} from "../premiumMeaningContext";
import { adaptReasonFactsForViewModel } from "../adaptReasonFactsForViewModel";
import { buildRecommendationReasonViewModel } from "../buildRecommendationReasonViewModel";

function fact(type: string, label: string, overrides: Partial<ConciergeReasonFact> = {}): ConciergeReasonFact {
  return { type, label, evidence: [`${type}:${label}`], score: 1, is_primary: true, ...overrides };
}

function baseContext(overrides: Partial<PremiumMeaningContext> = {}): PremiumMeaningContext {
  const consultation: PremiumMeaningContext["consultation"] = {
    primaryNeed: "転機",
    secondaryNeed: null,
    mode: "need",
    interpretedContext: { resolved: true },
  };
  const recommendationEvidence: PremiumMeaningContext["recommendationEvidence"] = {
    primaryReasonFact: { type: "need_tag", label: "転機", evidence: ["need_tag:転機"] },
    secondaryReasonFacts: [],
  };
  const shrineEvidence: PremiumMeaningContext["shrineEvidence"] = {
    shrineId: 17,
    deity: null,
    history: null,
    historyTheme: null,
    originSummary: null,
    placeContext: null,
    culturalStatus: null,
    lineage: null,
    goriyaku: null,
    tradition: null,
    verificationMetadata: null,
    relevantToConsultation: null,
    relevantToVisit: null,
  };
  const personalization: PremiumMeaningContext["personalization"] = {};

  const withoutValidity = {
    shrineId: 17,
    consultation,
    recommendationEvidence,
    shrineEvidence,
    personalization,
  };

  return {
    ...withoutValidity,
    validity: computePremiumMeaningValidity(withoutValidity),
    ...overrides,
  };
}

describe("PremiumMeaningContext: required field contract", () => {
  it("全Required field slotが実体として構築できる(shrineId/consultation/recommendationEvidence/validity)", () => {
    const ctx = baseContext();

    expect(ctx.shrineId).toBe(17);
    expect(ctx.consultation).toHaveProperty("primaryNeed");
    expect(ctx.consultation).toHaveProperty("mode");
    expect(ctx.consultation).toHaveProperty("interpretedContext");
    expect(ctx.recommendationEvidence).toHaveProperty("primaryReasonFact");
    expect(ctx.recommendationEvidence).toHaveProperty("secondaryReasonFacts");
    expect(ctx.shrineEvidence).toHaveProperty("relevantToConsultation");
    expect(ctx.shrineEvidence).toHaveProperty("relevantToVisit");
    expect(ctx.validity).toHaveProperty("consultationContextValid");
    expect(ctx.validity).toHaveProperty("userContextValid");
    expect(ctx.validity).toHaveProperty("recommendationEvidenceValid");
    expect(ctx.validity).toHaveProperty("shrineEvidencePresent");
    expect(ctx.validity).toHaveProperty("shrineEvidenceValid");
    expect(ctx.validity).toHaveProperty("relevantShrineContextValid");
    expect(ctx.validity).toHaveProperty("deepReasonValid");
    expect(ctx.validity).toHaveProperty("personalMeaningValid");
    expect(ctx.validity).toHaveProperty("actionMeaningValid");
  });

  it("primaryReasonFactがnullでもContext自体は構築できる(field slot必須・valueはnullable)", () => {
    const ctx = baseContext();
    ctx.recommendationEvidence.primaryReasonFact = null;

    expect(ctx.recommendationEvidence).toHaveProperty("primaryReasonFact", null);
  });
});

describe("PremiumMeaningContext: nullable Shrine Evidence", () => {
  it("Shrine Evidenceの全fieldがnullでもContextとして構築できる(Coverage不足神社を表現できる)", () => {
    const ctx = baseContext();

    expect(ctx.shrineEvidence.deity).toBeNull();
    expect(ctx.shrineEvidence.history).toBeNull();
    expect(ctx.shrineEvidence.historyTheme).toBeNull();
    expect(ctx.shrineEvidence.originSummary).toBeNull();
    expect(ctx.shrineEvidence.placeContext).toBeNull();
    expect(ctx.shrineEvidence.culturalStatus).toBeNull();
    expect(ctx.shrineEvidence.lineage).toBeNull();
    expect(ctx.shrineEvidence.goriyaku).toBeNull();
    expect(ctx.shrineEvidence.tradition).toBeNull();
    expect(ctx.shrineEvidence.relevantToConsultation).toBeNull();
    expect(ctx.shrineEvidence.relevantToVisit).toBeNull();
    expect(ctx.shrineEvidence).toHaveProperty("shrineId");
  });

  it("shrineIdは必須のまま、他のShrine Evidence fieldだけをnullにできる", () => {
    const ctx = baseContext();
    expect(typeof ctx.shrineEvidence.shrineId).toBe("number");
  });
});

describe("PremiumMeaningContext: secondary reason facts", () => {
  it("secondaryReasonFactsをempty arrayとして表現できる", () => {
    const ctx = baseContext();
    expect(ctx.recommendationEvidence.secondaryReasonFacts).toEqual([]);
  });

  it("secondaryReasonFactsを複数件のfactとして表現できる", () => {
    const ctx = baseContext();
    ctx.recommendationEvidence.secondaryReasonFacts = [
      { type: "distance", label: "1.2km", evidence: ["distance:1.2km"] },
      { type: "popular", label: "人気", evidence: ["popular:人気"] },
    ];

    expect(ctx.recommendationEvidence.secondaryReasonFacts).toHaveLength(2);
    expect(ctx.recommendationEvidence.secondaryReasonFacts[0]).toEqual(
      expect.objectContaining({ type: "distance", label: "1.2km" }),
    );
  });
});

describe("PremiumMeaningContext: Structured Consultation/User Context validity", () => {
  it("primaryNeedだけではconsultationContextValid/userContextValid/personalMeaningValidにならない(interpretedContextがnull)", () => {
    const ctx = baseContext();
    ctx.consultation.interpretedContext = null;
    ctx.shrineEvidence.deity = "祭神A";
    ctx.shrineEvidence.relevantToConsultation = true;

    const validity = computePremiumMeaningValidity(ctx);

    expect(ctx.consultation.primaryNeed).toBe("転機");
    expect(validity.consultationContextValid).toBe(false);
    expect(validity.userContextValid).toBe(false);
    expect(validity.personalMeaningValid).toBe(false);
    expect(validity.deepReasonValid).toBe(false);
  });

  it("Structured User Context VALIDをprimaryNeedとは別条件として表現できる(同じprimaryNeedでもinterpretedContextの有無で結果が変わる)", () => {
    const withInterpretedContext = baseContext();
    withInterpretedContext.consultation.primaryNeed = "仕事";
    withInterpretedContext.consultation.interpretedContext = { someOpaqueSignal: true };

    const withoutInterpretedContext = baseContext();
    withoutInterpretedContext.consultation.primaryNeed = "仕事";
    withoutInterpretedContext.consultation.interpretedContext = null;

    expect(computePremiumMeaningValidity(withInterpretedContext).userContextValid).toBe(true);
    expect(computePremiumMeaningValidity(withoutInterpretedContext).userContextValid).toBe(false);
  });

  it("primaryNeedが無ければinterpretedContextがあってもconsultationContextValidにならない", () => {
    const ctx = baseContext();
    ctx.consultation.primaryNeed = null;
    ctx.consultation.interpretedContext = { someOpaqueSignal: true };

    expect(computePremiumMeaningValidity(ctx).consultationContextValid).toBe(false);
  });
});

describe("PremiumMeaningContext: Shrine Evidence PRESENT vs RELEVANT", () => {
  it("deityが存在するだけではpersonalMeaningValidにならない(relevantToConsultation未設定)", () => {
    const ctx = baseContext();
    ctx.shrineEvidence.deity = "祭神A";
    ctx.shrineEvidence.relevantToConsultation = null;

    const validity = computePremiumMeaningValidity(ctx);

    expect(validity.shrineEvidencePresent).toBe(true);
    expect(validity.shrineEvidenceValid).toBe(false);
    expect(validity.personalMeaningValid).toBe(false);
  });

  it("historyが存在するだけではpersonalMeaningValidにならない(relevantToConsultation未設定)", () => {
    const ctx = baseContext();
    ctx.shrineEvidence.history = "由緒の記述";
    ctx.shrineEvidence.relevantToConsultation = null;

    const validity = computePremiumMeaningValidity(ctx);

    expect(validity.shrineEvidencePresent).toBe(true);
    expect(validity.shrineEvidenceValid).toBe(false);
    expect(validity.personalMeaningValid).toBe(false);
  });

  it("placeContextが存在するだけではpersonalMeaningValidにならない(relevantToConsultation未設定)", () => {
    const ctx = baseContext();
    ctx.shrineEvidence.placeContext = "山間の参道";
    ctx.shrineEvidence.relevantToConsultation = null;

    const validity = computePremiumMeaningValidity(ctx);

    expect(validity.shrineEvidencePresent).toBe(true);
    expect(validity.shrineEvidenceValid).toBe(false);
    expect(validity.personalMeaningValid).toBe(false);
  });

  it("relevantToConsultation=falseの場合も、存在するだけではpersonalMeaningValidにならない", () => {
    const ctx = baseContext();
    ctx.shrineEvidence.deity = "祭神A";
    ctx.shrineEvidence.relevantToConsultation = false;

    expect(computePremiumMeaningValidity(ctx).personalMeaningValid).toBe(false);
  });

  it("goriyaku(タグ)しかない場合はshrineEvidencePresentもfalseになる(LOW specificityは対象外)", () => {
    const ctx = baseContext();
    ctx.shrineEvidence.goriyaku = ["金運"];
    ctx.shrineEvidence.relevantToConsultation = true;

    const validity = computePremiumMeaningValidity(ctx);

    expect(validity.shrineEvidencePresent).toBe(false);
    expect(validity.shrineEvidenceValid).toBe(false);
    expect(validity.personalMeaningValid).toBe(false);
  });

  it("Relevant Shrine Evidence成立時(PRESENT かつ relevantToConsultation=true)のみpersonalMeaningValidになる", () => {
    const ctx = baseContext();
    ctx.shrineEvidence.deity = "祭神A";
    ctx.shrineEvidence.relevantToConsultation = true;

    const validity = computePremiumMeaningValidity(ctx);

    expect(validity.shrineEvidencePresent).toBe(true);
    expect(validity.shrineEvidenceValid).toBe(true);
    expect(validity.personalMeaningValid).toBe(true);
  });
});

describe("PremiumMeaningContext: Action Meaning validity", () => {
  it("actionMeaningValidはshrineEvidenceValidの再利用ではなく、独立したrelevantToVisitに依存する", () => {
    const ctx = baseContext();
    ctx.shrineEvidence.deity = "祭神A";
    ctx.shrineEvidence.relevantToConsultation = true; // personalMeaningValid = true
    ctx.shrineEvidence.relevantToVisit = null; // Action Meaning用のRelevanceは未設定

    const validity = computePremiumMeaningValidity(ctx);

    expect(validity.personalMeaningValid).toBe(true);
    expect(validity.relevantShrineContextValid).toBe(false);
    expect(validity.actionMeaningValid).toBe(false);
  });

  it("personalMeaningValid=true かつ relevantToVisit=trueの場合のみactionMeaningValidになる", () => {
    const ctx = baseContext();
    ctx.shrineEvidence.deity = "祭神A";
    ctx.shrineEvidence.relevantToConsultation = true;
    ctx.shrineEvidence.relevantToVisit = true;

    const validity = computePremiumMeaningValidity(ctx);

    expect(validity.personalMeaningValid).toBe(true);
    expect(validity.relevantShrineContextValid).toBe(true);
    expect(validity.actionMeaningValid).toBe(true);
  });

  it("Personal MeaningがINVALIDならrelevantToVisit=trueでもactionMeaningValidはINVALID(前提条件の連鎖)", () => {
    const ctx = baseContext();
    ctx.shrineEvidence.deity = null;
    ctx.shrineEvidence.history = null;
    ctx.shrineEvidence.placeContext = null;
    ctx.shrineEvidence.relevantToVisit = true;

    const validity = computePremiumMeaningValidity(ctx);

    expect(validity.personalMeaningValid).toBe(false);
    expect(validity.actionMeaningValid).toBe(false);
  });
});

describe("PremiumMeaningContext: full validity state", () => {
  it("Consultation Context/Recommendation Evidence/Relevant Shrine Evidence/Relevant Shrine Contextが全て揃う場合、Deep/Personal/Actionまで全てvalidになる", () => {
    const ctx = baseContext();
    ctx.shrineEvidence.deity = "祭神A";
    ctx.shrineEvidence.relevantToConsultation = true;
    ctx.shrineEvidence.relevantToVisit = true;

    const validity = computePremiumMeaningValidity(ctx);

    expect(validity).toEqual({
      consultationContextValid: true,
      userContextValid: true,
      recommendationEvidenceValid: true,
      shrineEvidencePresent: true,
      shrineEvidenceValid: true,
      relevantShrineContextValid: true,
      deepReasonValid: true,
      personalMeaningValid: true,
      actionMeaningValid: true,
    });
  });

  it("primaryReasonFactが無い場合、recommendationEvidenceValidとdeepReasonValidのみfalseになる(Personal Meaningには影響しない)", () => {
    const ctx = baseContext();
    ctx.recommendationEvidence.primaryReasonFact = null;
    ctx.shrineEvidence.deity = "祭神A";
    ctx.shrineEvidence.relevantToConsultation = true;

    const validity = computePremiumMeaningValidity(ctx);

    expect(validity.recommendationEvidenceValid).toBe(false);
    expect(validity.deepReasonValid).toBe(false);
    expect(validity.personalMeaningValid).toBe(true);
  });
});

describe("PremiumMeaningContext: excluded fields", () => {
  it("Contract groupのkeyにExcluded概念(raw free_text/score/生成済みテキスト/心理推定field等)を含まない", () => {
    const ctx = baseContext();

    const topLevelKeys = Object.keys(ctx);
    const consultationKeys = Object.keys(ctx.consultation);
    const recommendationEvidenceKeys = Object.keys(ctx.recommendationEvidence);
    const shrineEvidenceKeys = Object.keys(ctx.shrineEvidence);
    const personalizationKeys = Object.keys(ctx.personalization);

    const excluded = [
      "freeText",
      "rawFreeText",
      "rawQuery",
      "rawScore",
      "score",
      "breakdown",
      "rankExplanation",
      "rankDebug",
      "shrineMeaning",
      "shrineMeaningText",
      "actionMeaning",
      "actionMeaningText",
      "historyContext",
      "historyContextText",
      "explanationSummary",
      "cultureTranslation",
      "shrineContextTable",
      "tone",
      "ctaCopy",
      "presentationText",
      "stateTone",
      "emotionIntensity",
      "actionIntent",
    ];

    for (const key of excluded) {
      expect(topLevelKeys).not.toContain(key);
      expect(consultationKeys).not.toContain(key);
      expect(recommendationEvidenceKeys).not.toContain(key);
      expect(shrineEvidenceKeys).not.toContain(key);
      expect(personalizationKeys).not.toContain(key);
    }
  });
});

describe("PremiumMeaningContext: existing Basic Reason contract is untouched", () => {
  it("adaptReasonFactsForViewModelは既存の変換仕様のまま動作する", () => {
    expect(adaptReasonFactsForViewModel([fact("goriyaku_tag", "勝運")])).toEqual(
      expect.objectContaining({ primary_axis: "benefit", shrine_benefit: "勝運" }),
    );
  });

  it("buildRecommendationReasonViewModelは既存のBasic Reason出力のまま動作する(shrine_meaning/action_meaningへの影響なし)", () => {
    const vm = buildRecommendationReasonViewModel({
      rec: { id: 999, name: "契約神社" },
      reasonFacts: [fact("history_theme", "再出発")],
      index: 0,
      mode: "need",
      needTags: [],
    });

    expect(vm.detail.shrineMeaning).toContain("再出発");
  });
});
