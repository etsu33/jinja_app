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

describe("buildDeepRecommendationReason: null contract", () => {
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

  it("returns null when primaryReasonFact has an empty label", () => {
    const ctx = baseContext({
      consultation: {
        situationSignals: [{ type: "depleted", evidence: [{ text: "疲れている" }] }],
      },
      recommendationEvidence: {
        primaryReasonFact: { type: "need_tag", label: "", evidence: [] },
        secondaryReasonFacts: [],
      },
    });
    expect(buildDeepRecommendationReason(ctx)).toBeNull();
  });

  it("never returns an empty object -- null or a fully-populated DeepRecommendationReason only", () => {
    const ctx = baseContext();
    const result = buildDeepRecommendationReason(ctx);
    expect(result === null || (result.lines.length > 0 && result.sources.consultation.length > 0 && result.sources.recommendation.length > 0)).toBe(true);
  });
});

describe("buildDeepRecommendationReason: single-signal, single-fact case", () => {
  it("produces exactly 1 line, quoting the evidence verbatim and the fact label, with exactly one source each", () => {
    const ctx = baseContext({
      consultation: {
        situationSignals: [{ type: "depleted", evidence: [{ text: "疲れている" }] }],
      },
      recommendationEvidence: {
        primaryReasonFact: { type: "history_theme", label: "静穏な由緒", evidence: [] },
        secondaryReasonFacts: [],
      },
    });

    const result = buildDeepRecommendationReason(ctx);
    expect(result).not.toBeNull();
    expect(result!.lines.length).toBe(1);
    expect(result!.lines[0]).toContain("疲れている");
    expect(result!.lines[0]).toContain("静穏な由緒");

    expect(result!.sources.consultation).toEqual([
      { category: "situation", type: "depleted", evidence: ["疲れている"] },
    ]);
    expect(result!.sources.recommendation).toEqual([{ role: "primary", text: "静穏な由緒" }]);
  });

  it("selects situation before desired_outcome before explicit_constraint when multiple families have evidence, and only sources the one actually used", () => {
    const ctx = baseContext({
      consultation: {
        situationSignals: [],
        desiredOutcomeSignals: [{ type: "decide", evidence: [{ text: "決めたい" }] }],
        explicitConstraintSignals: [{ type: "money", evidence: [{ text: "お金が足りなくて" }] }],
      },
      recommendationEvidence: {
        primaryReasonFact: { type: "need_tag", label: "転機", evidence: [] },
        secondaryReasonFacts: [],
      },
    });

    const result = buildDeepRecommendationReason(ctx);
    expect(result).not.toBeNull();
    // desired_outcome comes before explicit_constraint in priority order
    expect(result!.sources.consultation[0].category).toBe("desired_outcome");
  });
});

describe("buildDeepRecommendationReason: 2-line cases", () => {
  it("adds a second line from a distinct secondary reason fact, keeping the same consultation source", () => {
    const ctx = baseContext({
      consultation: {
        situationSignals: [{ type: "depleted", evidence: [{ text: "疲れている" }] }],
      },
      recommendationEvidence: {
        primaryReasonFact: { type: "need_tag", label: "転機", evidence: [] },
        secondaryReasonFacts: [{ type: "history_theme", label: "静穏な由緒", evidence: [] }],
      },
    });

    const result = buildDeepRecommendationReason(ctx);
    expect(result).not.toBeNull();
    expect(result!.lines.length).toBe(2);
    expect(result!.lines[1]).toContain("静穏な由緒");
    expect(result!.sources.consultation.length).toBe(1);
    expect(result!.sources.recommendation).toEqual([
      { role: "primary", text: "転機" },
      { role: "secondary", text: "静穏な由緒" },
    ]);
  });

  it("adds a second line from a distinct second consultation signal when no usable secondary fact exists", () => {
    const ctx = baseContext({
      consultation: {
        situationSignals: [{ type: "depleted", evidence: [{ text: "疲れている" }] }],
        desiredOutcomeSignals: [{ type: "decide", evidence: [{ text: "決めたい" }] }],
      },
      recommendationEvidence: {
        primaryReasonFact: { type: "need_tag", label: "転機", evidence: [] },
        secondaryReasonFacts: [],
      },
    });

    const result = buildDeepRecommendationReason(ctx);
    expect(result).not.toBeNull();
    expect(result!.lines.length).toBe(2);
    expect(result!.lines[1]).toContain("決めたい");
    expect(result!.sources.consultation).toEqual([
      { category: "situation", type: "depleted", evidence: ["疲れている"] },
      { category: "desired_outcome", type: "decide", evidence: ["決めたい"] },
    ]);
    expect(result!.sources.recommendation).toEqual([{ role: "primary", text: "転機" }]);
  });

  it("does not fabricate a secondary reason fact source when secondaryReasonFacts only duplicates the primary label", () => {
    const ctx = baseContext({
      consultation: {
        situationSignals: [{ type: "depleted", evidence: [{ text: "疲れている" }] }],
      },
      recommendationEvidence: {
        primaryReasonFact: { type: "need_tag", label: "転機", evidence: [] },
        secondaryReasonFacts: [{ type: "goriyaku_tag", label: "転機", evidence: [] }],
      },
    });

    const result = buildDeepRecommendationReason(ctx);
    expect(result).not.toBeNull();
    expect(result!.lines.length).toBe(1);
    expect(result!.sources.recommendation).toEqual([{ role: "primary", text: "転機" }]);
  });

  it("stays at 1 line when only one signal and one fact exist, with no fabricated second entry", () => {
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
    expect(result!.lines.length).toBe(1);
    expect(result!.sources.consultation.length).toBe(1);
    expect(result!.sources.recommendation.length).toBe(1);
  });
});

describe("buildDeepRecommendationReason: traceability invariant", () => {
  it("always includes at least one consultation source and one recommendation source when non-null", () => {
    const ctx = baseContext({
      consultation: {
        situationSignals: [{ type: "stalled", evidence: [{ text: "動けない" }] }],
      },
      recommendationEvidence: {
        primaryReasonFact: { type: "text_hint", label: "静けさ", evidence: [] },
        secondaryReasonFacts: [],
      },
    });

    const result = buildDeepRecommendationReason(ctx);
    expect(result).not.toBeNull();
    expect(result!.sources.consultation.length).toBeGreaterThanOrEqual(1);
    expect(result!.sources.recommendation.length).toBeGreaterThanOrEqual(1);
  });

  it("every evidence string quoted in lines[0] appears in sources.consultation[0].evidence", () => {
    const ctx = baseContext({
      consultation: {
        explicitConstraintSignals: [{ type: "time", evidence: [{ text: "余裕がない" }] }],
      },
      recommendationEvidence: {
        primaryReasonFact: { type: "visit_style", label: "近場で無理なく", evidence: [] },
        secondaryReasonFacts: [],
      },
    });

    const result = buildDeepRecommendationReason(ctx);
    expect(result).not.toBeNull();
    expect(result!.lines[0]).toContain("余裕がない");
    expect(result!.sources.consultation[0].evidence).toContain("余裕がない");
  });
});

describe("buildDeepRecommendationReason: semantic boundary", () => {
  it("output shape carries no Personal Meaning or Action Meaning fields", () => {
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
    expect(result).not.toBeNull();
    expect(Object.keys(result!)).toEqual(["lines", "sources"]);
  });
});
