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

describe("buildDeepRecommendationReason: no stable relationship-proof exists yet (PR-D review correction)", () => {
  it("returns null when deepReasonValid is false (no consultation signal, no reason fact)", () => {
    const ctx = baseContext();
    expect(ctx.validity.deepReasonValid).toBe(false);
    expect(buildDeepRecommendationReason(ctx)).toBeNull();
  });

  it("returns null when consultation evidence is insufficient even though a signal entry exists (empty evidence array)", () => {
    const ctx = baseContext({
      consultation: { situationSignals: [{ type: "depleted", evidence: [] }] },
      recommendationEvidence: {
        primaryReasonFact: { type: "need_tag", label: "転機", evidence: ["need_tag:転機"] },
        secondaryReasonFacts: [],
      },
    });
    expect(buildDeepRecommendationReason(ctx)).toBeNull();
  });

  it("returns null when recommendation evidence is insufficient (primaryReasonFact null) even with consultation signals present", () => {
    const ctx = baseContext({
      consultation: {
        situationSignals: [{ type: "depleted", evidence: [{ text: "疲れている" }] }],
      },
    });
    expect(ctx.validity.consultationContextValid).toBe(true);
    expect(buildDeepRecommendationReason(ctx)).toBeNull();
  });

  it("returns null even when a consultation signal (with evidence) and a valid, unrelated primary reason fact both exist and deepReasonValid is true -- presence of both is not proof of a relationship", () => {
    const ctx = baseContext({
      consultation: {
        situationSignals: [{ type: "depleted", evidence: [{ text: "疲れている" }] }],
      },
      recommendationEvidence: {
        primaryReasonFact: { type: "need_tag", label: "転機", evidence: ["need_tag:転機"] },
        secondaryReasonFacts: [],
      },
    });
    expect(ctx.validity.deepReasonValid).toBe(true);
    expect(buildDeepRecommendationReason(ctx)).toBeNull();
  });

  it("returns null for a distance/popularity-derived fallback reason fact paired with a desired_outcome signal (an unrelated pair by construction, since no shared vocabulary exists)", () => {
    const ctx = baseContext({
      consultation: {
        desiredOutcomeSignals: [{ type: "decide", evidence: [{ text: "決めたい" }] }],
      },
      recommendationEvidence: {
        primaryReasonFact: { type: "fallback", label: "近い候補", evidence: [] },
        secondaryReasonFacts: [],
      },
    });
    expect(buildDeepRecommendationReason(ctx)).toBeNull();
  });

  it("returns null with multiple consultation signals across all three families and both a primary and secondary reason fact present", () => {
    const ctx = baseContext({
      consultation: {
        situationSignals: [{ type: "stalled", evidence: [{ text: "動けない" }] }],
        desiredOutcomeSignals: [{ type: "clarify", evidence: [{ text: "整理したい" }] }],
        explicitConstraintSignals: [{ type: "time", evidence: [{ text: "余裕がない" }] }],
      },
      recommendationEvidence: {
        primaryReasonFact: { type: "history_theme", label: "静穏な由緒", evidence: ["history_theme", "matched_need_tags"] },
        secondaryReasonFacts: [{ type: "visit_style", label: "静か", evidence: ["quiet"] }],
      },
    });
    expect(buildDeepRecommendationReason(ctx)).toBeNull();
  });

  it("never returns an empty object -- always exactly null", () => {
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
  });

  it("does not mutate the input context", () => {
    const ctx = baseContext({
      consultation: {
        situationSignals: [{ type: "depleted", evidence: [{ text: "疲れている" }] }],
      },
      recommendationEvidence: {
        primaryReasonFact: { type: "need_tag", label: "転機", evidence: [] },
        secondaryReasonFacts: [],
      },
    });
    const snapshot = JSON.parse(JSON.stringify(ctx));
    buildDeepRecommendationReason(ctx);
    expect(ctx).toEqual(snapshot);
  });
});
