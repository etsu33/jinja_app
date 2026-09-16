/**
 * Audit-only evidence for docs/audit/recommendation-public-output-boundary-audit.md.
 *
 * These tests do NOT assert desired behaviour. They pin the CURRENT behaviour so
 * the findings in that document are reproducible, and they are expected to be
 * rewritten by the fix PRs the document proposes.
 *
 * Covered findings:
 *   REC-001  the internal ranking score delta (`gap_from_top`, derived from
 *            `_score_total`) is rendered to the user as a bare number, and the
 *            same number also appears inside `comparison_summary`.
 *   REC-002  `normalizeRecommendations()` spreads the backend object, so every
 *            internal field (`_score_total`, `_primary_reason_label`,
 *            `_explanation_payload`, `breakdown.score_*`) survives into the
 *            client-side ViewModel. There is no public DTO at this layer.
 *   REC-006  the "name missing" fallback differs between the two normalizers.
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { normalizeRecommendations } from "@/lib/api/concierge/normalize";
import { RecommendationMetaSection } from "@/components/shrine/detail/RecommendationMetaSection";

/**
 * Shape of one recommendation as the backend actually emits it.
 * Underscore-prefixed keys are set in
 * backend/temples/services/concierge_chat_ranking.py and are never stripped
 * before the public /api/concierge/chat/ response.
 */
const BACKEND_RECOMMENDATION = {
  shrine_id: 49,
  name: "明治神宮",
  display_name: "明治神宮",
  reason: "気持ちを整えたい時に選びやすい神社です。",
  _score_total: 4.318,
  _primary_reason_source: "need_tag",
  _primary_reason_label: "mental",
  _reason_facts: [{ type: "need_tag", label: "mental", evidence: ["score_element:2"], score: 3 }],
  _explanation_payload: { original_reason: "…", primary_reason: { label: "mental" } },
  breakdown: {
    score_element: 2,
    score_need: 3,
    score_popular: 0.4,
    score_total: 4.318,
    weights: { element: 0.6, need: 0.3, popular: 0.1 },
    matched_need_tags: ["mental"],
  },
  rank_comparison: {
    version: 1,
    rank: 2,
    is_top: false,
    gap_from_top: 0.27,
    comparison_summary: "1位と共通する悩み軸は「不安・心」です。1位との差は 0.27 です。",
  },
};

describe("REC-002: the client ViewModel has no public field allowlist", () => {
  it("normalizeRecommendations passes internal backend fields straight through", () => {
    const [normalized] = normalizeRecommendations([BACKEND_RECOMMENDATION]) as any[];

    // Internal ranking authority reaches the browser unchanged.
    expect(normalized._score_total).toBe(4.318);
    expect(normalized._primary_reason_label).toBe("mental");
    expect(normalized._primary_reason_source).toBe("need_tag");
    expect(normalized._explanation_payload).toBeDefined();
    expect(normalized._reason_facts).toBeDefined();

    // Per-axis score components reach the browser unchanged.
    expect(normalized.breakdown.score_total).toBe(4.318);
    expect(normalized.breakdown.score_element).toBe(2);
    expect(normalized.breakdown.weights).toEqual({ element: 0.6, need: 0.3, popular: 0.1 });

    // Internal reason-fact evidence strings survive too.
    expect(normalized._reason_facts[0].evidence).toContain("score_element:2");
  });

  it("REC-006: the missing-name fallback here is 「（名称不明）」 (parenthesised)", () => {
    const [normalized] = normalizeRecommendations([{ shrine_id: 1 }]) as any[];
    // buildPayloadFromUnified.normalizeRecommendation() uses 「名称不明」 without
    // parentheses for the same condition — the two normalizers disagree.
    expect(normalized.name).toBe("（名称不明）");
  });
});

describe("REC-001: the internal ranking score delta is user-visible", () => {
  it("renders the raw score gap as a bare number, with no unit or product meaning", () => {
    render(
      <RecommendationMetaSection
        recommendationMeta={{
          rankTitle: "1位との違い",
          rankBody: BACKEND_RECOMMENDATION.rank_comparison.comparison_summary,
          rankComparison: {
            is_top: false,
            gap_from_top: BACKEND_RECOMMENDATION.rank_comparison.gap_from_top,
          },
        }}
      />,
    );

    // The bare number line, rendered from gap_from_top (= top._score_total - rec._score_total).
    expect(screen.getByText("1位との差: 0.27")).toBeInTheDocument();
  });

  it("shows the same score twice: inside the sentence and again as its own line", () => {
    const { container } = render(
      <RecommendationMetaSection
        recommendationMeta={{
          rankTitle: "1位との違い",
          rankBody: BACKEND_RECOMMENDATION.rank_comparison.comparison_summary,
          rankComparison: {
            is_top: false,
            gap_from_top: BACKEND_RECOMMENDATION.rank_comparison.gap_from_top,
          },
        }}
      />,
    );

    const occurrences = (container.textContent ?? "").match(/0\.27/g) ?? [];
    expect(occurrences).toHaveLength(2);
  });

  it("is rendered with no access-level gate: the section itself never checks the tier", () => {
    // RecommendationMetaSection takes only `recommendationMeta`; accessLevel is
    // used by ShrineDetailArticle for analytics only, not to gate this JSX.
    render(
      <RecommendationMetaSection
        recommendationMeta={{
          rankTitle: "1位との違い",
          rankBody: "1位との差は 0.27 です。",
          rankComparison: { is_top: false, gap_from_top: 0.27 },
        }}
      />,
    );

    expect(screen.getByTestId("shrine-detail-recommendation-meta")).toBeInTheDocument();
  });
});
