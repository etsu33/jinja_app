import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// docs/product/recommendation-result-information-architecture.md §6, §13, §15 PR2:
// end-to-end coverage of Hero Reason Consolidation through the real renderer, for the
// scenarios that are hardest to get right purely at the buildHeroConclusion.ts unit
// level: Knowledge Explanation-only fact positioning, and a generic_safe Action
// Suggestion merged into the Next Action block.

const analyticsMocks = vi.hoisted(() => ({ trackSearchEvent: vi.fn(), trackCardEvent: vi.fn() }));
vi.mock("@/lib/analytics/searchEvents", () => ({ trackSearchEvent: analyticsMocks.trackSearchEvent }));
vi.mock("@/lib/analytics/cardEvents", () => ({ trackCardEvent: analyticsMocks.trackCardEvent }));
vi.mock("@/lib/auth/AuthProvider", () => ({ useAuth: () => ({ isLoggedIn: false, loading: false }) }));

import ConciergeSectionsRenderer from "../ConciergeSectionsRenderer";
import { buildPayloadFromUnified } from "@/features/concierge/buildPayloadFromUnified";

const baseFilterState: any = {
  isOpen: false,
  birthdate: "",
  element4: null,
  goriyakuTags: [],
  suggestedTags: [],
  selectedTagIds: [],
  tagsLoading: false,
  tagsError: null,
  extraCondition: "",
};

function buildTestPayload(recommendations: any[]) {
  const u: any = { data: { recommendations }, thread: { id: 1 } };
  const payload = buildPayloadFromUnified(u, baseFilterState);
  if (!payload) throw new Error("payload should not be null in this fixture");
  return payload;
}

describe("Hero Reason Consolidation - end-to-end", () => {
  beforeEach(() => {
    analyticsMocks.trackSearchEvent.mockClear();
    analyticsMocks.trackCardEvent.mockClear();
    window.localStorage.clear();
  });

  it("Knowledge Explanation-only(deity由来fact)はPrimaryへ昇格せず、Conclusionには混ざらない(Explanation-only Fact Visual Distinction, PR5, Finding 9)", () => {
    const rec = {
      shrine_id: 1,
      display_name: "武神社",
      reason: "旧型の理由文",
      recommendation_reason_v4_detail: {
        version: "v4",
        reason_text: "武神社は武神が祀られています。",
        fact: {
          label: "武神社",
          name: "武神社",
          deity: "武神", // Explanation-only per docs/product/recommendation-signal-authority.md §8
          shrine_history: null,
          place_context: null,
          history_theme: null,
          goriyaku: null,
          visit_style_tags: [],
          evidence: [],
        },
        interpretation: { theme: "default", text: "相談内容から、今のテーマを読み取っています。" },
        action: { text: "" },
      },
    };
    const payload = buildTestPayload([rec]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={1} isPremiumActive={true} />);

    const conclusion = screen.getByTestId("recommendation-conclusion");
    expect(conclusion).toHaveTextContent("相談内容から、今のテーマを読み取っています。");
    // deity(Explanation-only)はConclusionには一切現れない -- Ranking根拠のように見える形で
    // 提示しない(Signal Authority正本§10 Explanation Contract)。
    expect(conclusion).not.toHaveTextContent("武神");

    // 代わりに「参考情報」ラベル付きの別枠(recommendation-explanation-only-fact)で、
    // Conclusionより弱いトーンで表示される。
    const explanationOnly = screen.getByTestId("recommendation-explanation-only-fact");
    expect(explanationOnly).toHaveTextContent("参考情報");
    expect(explanationOnly).toHaveTextContent("武神");
  });

  it("generic_safe Action(actionSource=fallback)のAction SuggestionもNext Actionへ統合表示される", () => {
    const rec = {
      shrine_id: 1,
      display_name: "検証神社",
      reason: "理由文",
      reason_facts: [{ type: "need_tag", label: "仕事運", score: 1, evidence: [], is_primary: true }],
      action_suggestion_v4_preview: {
        primaryAction: { label: "まず詳細を見て、行く理由を確認する", description: "", actionType: "detail_open", confidence: 0.5 },
        secondaryAction: { label: "保存する", description: "", actionType: "save", confidence: 0.4 },
        reflectionPrompt: { question: "行くとしたら何を確認したいですか？", promptType: "before_visit", sourceSeed: "seed" },
        actionSource: { source: "fallback", reason: "入力不足のため安全な初期提案" },
        preview: true,
        version: "v4",
        sourceKeys: [],
      },
    };
    const payload = buildTestPayload([rec]);

    expect(() => {
      render(<ConciergeSectionsRenderer payload={payload} threadId={1} isPremiumActive={true} />);
    }).not.toThrow();

    const nextAction = screen.getByTestId("recommendation-next-action");
    expect(nextAction).toHaveTextContent("まず詳細を見て、行く理由を確認する");
    // groundingの値そのもの("fallback")はUIへ表示しない(既存契約を維持)。
    expect(screen.queryByText("fallback")).not.toBeInTheDocument();

    // 1つのNext Action blockのみ(重複カードなし)。
    expect(screen.getAllByTestId("recommendation-next-action")).toHaveLength(1);
  });

  it("legacy path(reason_factsのみ)でもConclusionが1 blockへ統合される(non-regression)", () => {
    const rec = {
      shrine_id: 1,
      display_name: "検証神社",
      reason: "旧型の理由文",
      reason_facts: [{ type: "need_tag", label: "縁結び", score: 1, evidence: [], is_primary: true }],
    };
    const payload = buildTestPayload([rec]);
    render(<ConciergeSectionsRenderer payload={payload} threadId={1} isPremiumActive={true} />);

    expect(screen.getAllByTestId("recommendation-conclusion")).toHaveLength(1);
    expect(screen.queryByTestId("recommendation-reason-v4-fact")).not.toBeInTheDocument();
  });
});
