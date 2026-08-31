import { describe, expect, it } from "vitest";

import { buildDeepRecommendationReason } from "../buildDeepRecommendationReason";
import { computePremiumMeaningValidity, type PremiumMeaningContext } from "../premiumMeaningContext";

type BaseContextOverrides = {
  consultation?: Partial<PremiumMeaningContext["consultation"]>;
  recommendationEvidence?: Partial<PremiumMeaningContext["recommendationEvidence"]>;
  shrineEvidence?: Partial<PremiumMeaningContext["shrineEvidence"]>;
};

function baseContext(overrides: BaseContextOverrides = {}): PremiumMeaningContext {
  const consultation: PremiumMeaningContext["consultation"] = {
    primaryNeed: "転機",
    secondaryNeed: null,
    mode: "need",
    situationSignals: [],
    desiredOutcomeSignals: [],
    explicitConstraintSignals: [],
  };
  const recommendationEvidence: PremiumMeaningContext["recommendationEvidence"] = {
    primaryReasonFact: null,
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
    consultation: { ...consultation, ...overrides.consultation },
    recommendationEvidence: { ...recommendationEvidence, ...overrides.recommendationEvidence },
    shrineEvidence: { ...shrineEvidence, ...overrides.shrineEvidence },
    personalization,
  };

  return {
    ...withoutValidity,
    validity: computePremiumMeaningValidity(withoutValidity),
  };
}

describe("buildDeepRecommendationReason: fail-safe (no stable relationship-proof exists yet)", () => {
  it("no context content -> null", () => {
    const ctx = baseContext();
    expect(ctx.validity.deepReasonValid).toBe(false);
    expect(buildDeepRecommendationReason(ctx)).toBeNull();
  });

  it("valid consultation + valid recommendation fact -> null (co-presence is not proof of a relationship)", () => {
    const ctx = baseContext({
      consultation: {
        situationSignals: [{ type: "depleted", evidence: [{ text: "疲れている" }] }],
      },
      recommendationEvidence: {
        primaryReasonFact: { type: "need_tag", label: "転機", evidence: ["need_tag:転機"] },
        secondaryReasonFacts: [],
      },
    });
    expect(ctx.validity.consultationContextValid).toBe(true);
    expect(ctx.validity.recommendationEvidenceValid).toBe(true);
    expect(buildDeepRecommendationReason(ctx)).toBeNull();
  });

  it("situation signal + history_theme fact -> null", () => {
    const ctx = baseContext({
      consultation: {
        situationSignals: [{ type: "stalled", evidence: [{ text: "動けない" }] }],
      },
      recommendationEvidence: {
        primaryReasonFact: { type: "history_theme", label: "静穏な由緒", evidence: ["history_theme", "matched_need_tags"] },
        secondaryReasonFacts: [],
      },
    });
    expect(buildDeepRecommendationReason(ctx)).toBeNull();
  });

  it("desired_outcome signal + need_tag fact -> null", () => {
    const ctx = baseContext({
      consultation: {
        desiredOutcomeSignals: [{ type: "decide", evidence: [{ text: "決めたい" }] }],
      },
      recommendationEvidence: {
        primaryReasonFact: { type: "need_tag", label: "転機", evidence: ["need_tag:転機"] },
        secondaryReasonFacts: [],
      },
    });
    expect(buildDeepRecommendationReason(ctx)).toBeNull();
  });

  it("explicit_constraint signal + visit_style fact -> null", () => {
    const ctx = baseContext({
      consultation: {
        explicitConstraintSignals: [{ type: "time", evidence: [{ text: "余裕がない" }] }],
      },
      recommendationEvidence: {
        primaryReasonFact: { type: "visit_style", label: "静か", evidence: ["quiet"] },
        secondaryReasonFacts: [],
      },
    });
    expect(buildDeepRecommendationReason(ctx)).toBeNull();
  });

  it("multiple signals across all three families + multiple reason facts (primary and secondary) -> null", () => {
    const ctx = baseContext({
      consultation: {
        situationSignals: [{ type: "depleted", evidence: [{ text: "疲れている" }] }],
        desiredOutcomeSignals: [{ type: "clarify", evidence: [{ text: "整理したい" }] }],
        explicitConstraintSignals: [{ type: "money", evidence: [{ text: "お金が足りなくて" }] }],
      },
      recommendationEvidence: {
        primaryReasonFact: { type: "history_theme", label: "静穏な由緒", evidence: ["history_theme", "matched_need_tags"] },
        secondaryReasonFacts: [{ type: "visit_style", label: "静か", evidence: ["quiet"] }],
      },
    });
    expect(buildDeepRecommendationReason(ctx)).toBeNull();
  });

  it("deepReasonValid true -> still null without relationship proof", () => {
    const ctx = baseContext({
      consultation: {
        situationSignals: [{ type: "undecided", evidence: [{ text: "迷っている" }] }],
      },
      recommendationEvidence: {
        primaryReasonFact: { type: "element", label: "生年月日との相性", evidence: ["score_element:2"] },
        secondaryReasonFacts: [],
      },
    });
    expect(ctx.validity.deepReasonValid).toBe(true);
    expect(buildDeepRecommendationReason(ctx)).toBeNull();
  });

  it("output never fabricates Personal Meaning / Action Meaning -- null carries no such content", () => {
    const ctx = baseContext({
      consultation: {
        situationSignals: [{ type: "depleted", evidence: [{ text: "疲れている" }] }],
      },
      recommendationEvidence: {
        primaryReasonFact: { type: "need_tag", label: "転機", evidence: [] },
        secondaryReasonFacts: [],
      },
    });
    const result = buildDeepRecommendationReason(ctx);
    expect(result).toBeNull();
    // No object is ever returned -- so no personalMeaning/actionMeaning-shaped
    // fields can be smuggled onto the result.
    expect(result === null).toBe(true);
  });
});
