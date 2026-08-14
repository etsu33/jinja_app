import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const analyticsMocks = vi.hoisted(() => ({
  trackSearchEvent: vi.fn(),
}));

vi.mock("@/lib/analytics/searchEvents", () => ({
  trackSearchEvent: analyticsMocks.trackSearchEvent,
}));

import ConciergeTopRecommendationHero from "../ConciergeTopRecommendationHero";

describe("ConciergeTopRecommendationHero", () => {
  beforeEach(() => {
    analyticsMocks.trackSearchEvent.mockClear();
  });
  it("uses detail as the primary CTA without requiring secondary actions", () => {
    render(
      <ConciergeTopRecommendationHero
        name="検証神社"
        href="/shrines/17?ctx=concierge"
        conclusionLines={["今回の相談の中心にある「金運」のテーマと重なるため、この神社が候補に入っています。"]}
        routeLabel="詳しく見る"
      />,
    );

    expect(screen.queryByRole("button", { name: "まずはここに行く" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "経路案内" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "詳しく見る" })).toHaveAttribute("href", "/shrines/17?ctx=concierge");

    expect(screen.getByText("相談内容・ご利益との一致")).toBeInTheDocument();
    expect(screen.getByText("今回の相談の中心にある「金運」のテーマと重なるため、この神社が候補に入っています。")).toBeInTheDocument();
    expect(screen.queryByText("今の状況から動き出すなら、この候補が自然に見えます。")).not.toBeInTheDocument();
    expect(screen.queryByText("この候補を基準にすると判断しやすくなります。")).not.toBeInTheDocument();

    expect(screen.queryByTestId("hero-secondary-actions")).not.toBeInTheDocument();
  });

  it("Conclusion内の複数lineは渡された順序のまま1つのblockに表示される（Hero Reason Consolidation）", () => {
    render(
      <ConciergeTopRecommendationHero
        name="検証神社"
        conclusionLines={["相談の理解を示す文。", "神社の事実・選定理由を示す文。"]}
      />,
    );

    // 1つのConclusion blockのみが存在する（旧primaryReason/secondaryReasonの2枚には分かれない）。
    expect(screen.getAllByTestId("recommendation-conclusion")).toHaveLength(1);

    const conclusion = screen.getByTestId("recommendation-conclusion");
    const first = screen.getByText("相談の理解を示す文。");
    const second = screen.getByText("神社の事実・選定理由を示す文。");
    expect(conclusion).toContainElement(first);
    expect(conclusion).toContainElement(second);
    expect(first.compareDocumentPosition(second) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("actionReasonとactionSuggestionV4Previewが両方あっても1つのNext Action blockに統合される（重複カードなし）", () => {
    render(
      <ConciergeTopRecommendationHero
        name="検証神社"
        actionReason="参拝前に、問いを一つに絞ることを決めておきます。"
        actionSuggestionV4Preview={{
          primaryAction: {
            label: "参拝ルートを確認する",
            description: "",
            actionType: "route_open",
            confidence: 0.7,
          },
          secondaryAction: {
            label: "保存する",
            description: "",
            actionType: "save",
            confidence: 0.5,
          },
          reflectionPrompt: {
            question: "参拝後、何が変わったか一言で残しますか？",
            promptType: "after_visit",
            sourceSeed: "seed",
          },
          actionSource: { source: "action_context", reason: "ranked_history_theme" },
          preview: true,
          version: "v4",
          sourceKeys: ["ranked_history_theme"],
        }}
      />,
    );

    // 1つのNext Action blockのみが存在する（旧actionReason/次の一歩カードの2枚には分かれない）。
    expect(screen.getAllByTestId("recommendation-next-action")).toHaveLength(1);

    const nextAction = screen.getByTestId("recommendation-next-action");
    expect(nextAction).toHaveTextContent("参拝前に、問いを一つに絞ることを決めておきます。");
    expect(nextAction).toHaveTextContent("参拝ルートを確認する");

    // action.sourceそのものはUIに表示しない(既存契約を維持)。
    expect(screen.queryByText("ranked_history_theme")).not.toBeInTheDocument();
    expect(screen.queryByText("action_context")).not.toBeInTheDocument();
  });

  it("conclusionLines/actionReason/actionSuggestionが無い場合はConclusion/Next Actionどちらも表示しない", () => {
    render(<ConciergeTopRecommendationHero name="検証神社" />);

    expect(screen.queryByTestId("recommendation-conclusion")).not.toBeInTheDocument();
    expect(screen.queryByTestId("recommendation-next-action")).not.toBeInTheDocument();
  });


  it("renders v4 preview as a one-line summary and tracks preview views", async () => {
    render(
      <ConciergeTopRecommendationHero
        name="検証神社"
        href="/shrines/17?ctx=concierge"
        actionSuggestionV4Preview={{
          primaryAction: {
            label: "まず詳細を見て、行く理由を確認する",
            description: "候補神社の詳細を見て判断材料を増やします。",
            actionType: "detail_open",
            confidence: 0.82,
          },
          secondaryAction: {
            label: "候補として保存して、あとで見返す",
            description: "後から相談内容と一緒に見返せます。",
            actionType: "save",
            confidence: 0.74,
          },
          reflectionPrompt: {
            question: "この神社に行くとしたら、何を整理する時間にしたいですか？",
            promptType: "before_visit",
            sourceSeed: "fallback",
          },
          actionSource: {
            source: "fallback",
            reason: "入力が不足しているため、詳細確認と保存を安全な初期提案にした",
          },
          preview: true,
          version: "v4",
          sourceKeys: ["meaning_translation"],
        }}
        analyticsSource="concierge_result"
        threadId="thread-1"
        resultSetId="result-set-1"
        shrineId={17}
        recommendationRank={1}
        historyTheme="勝負"
        routeLabel="詳しく見る"
      />,
    );

    expect(screen.getByTestId("recommendation-next-action")).toBeInTheDocument();
    expect(screen.getByText("参拝前にできること")).toBeInTheDocument();
    expect(screen.getByText("まず詳細を見て、行く理由を確認する")).toBeInTheDocument();
    expect(screen.queryByText("候補として保存して、あとで見返す")).not.toBeInTheDocument();
    expect(screen.queryByText("後から相談内容と一緒に見返せます。")).not.toBeInTheDocument();
    expect(screen.queryByText("この神社に行くとしたら、何を整理する時間にしたいですか？")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "この行動で進める" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "この神社を見る" })).not.toBeInTheDocument();

    await waitFor(() => {
      expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith(
        "action_suggestion_preview_view",
        expect.objectContaining({
          source: "concierge_result",
          threadId: "thread-1",
          resultSetId: "result-set-1",
          shrineId: 17,
          recommendationRank: 1,
          position: "hero_primary",
          historyTheme: "勝負",
          actionSuggestionVersion: "v4",
          primaryActionType: "detail_open",
          secondaryActionType: "save",
          actionPromptType: "before_visit",
          actionSource: "fallback",
          sourceKeys: "meaning_translation",
          summaryLine: "まず詳細を見て、行く理由を確認する",
        }),
      );
    });

    expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith(
      "action_suggestion_reflection_preview_view",
      expect.objectContaining({
        actionPromptType: "before_visit",
        reflectionPromptSourceSeed: "fallback",
      }),
    );
    expect(analyticsMocks.trackSearchEvent).not.toHaveBeenCalledWith(
      "reflection_prompt_view",
      expect.anything(),
    );
  });
  it("calls the detail click handler and renders secondary action slot", () => {
    const onDetailClick = vi.fn();

    render(
      <ConciergeTopRecommendationHero
        name="検証神社"
        href="/shrines/17?ctx=concierge"
        routeLabel="神社の詳細を見る"
        onDetailClick={onDetailClick}
        secondaryActionSlot={<button type="button">あとで見る</button>}
      />,
    );

    expect(screen.getByTestId("hero-secondary-actions")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "あとで見る" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("link", { name: "神社の詳細を見る" }));
    expect(onDetailClick).toHaveBeenCalledTimes(1);
  });

  describe("Design Token参照 (Semantic Token契約、CSS文字列全体の比較はしない)", () => {
    it("CTAリンクがaction-primary系Tokenを参照する", () => {
      render(
        <ConciergeTopRecommendationHero
          name="検証神社"
          href="/shrines/17?ctx=concierge"
          routeLabel="詳しく見る"
        />,
      );

      const cta = screen.getByRole("link", { name: "詳しく見る" });
      expect(cta.className).toContain("rounded-[var(--kt-radius-card)]");
      expect(cta.className).toContain("bg-[var(--kt-color-action-primary)]");
      expect(cta.className).toContain("text-[var(--kt-color-action-primary-text)]");
      expect(cta.className).toContain("hover:bg-[var(--kt-color-action-primary-hover)]");
    });

    it("originSummary / address / topReasonLabelがtext-secondary / text-mutedを参照する", () => {
      render(
        <ConciergeTopRecommendationHero
          name="検証神社"
          href="/shrines/17?ctx=concierge"
          originSummary="由緒の要約"
          address="東京都千代田区1-1-1"
          topReasonLabel="選ばれた理由"
          conclusionLines={["相談とご利益の一致"]}
          routeLabel="詳しく見る"
        />,
      );

      expect(screen.getByText("由緒の要約").className).toContain("text-[var(--kt-color-text-secondary)]");
      expect(screen.getByText("東京都千代田区1-1-1").className).toContain("text-[var(--kt-color-text-muted)]");
      expect(screen.getByText("選ばれた理由").className).toContain("text-[var(--kt-color-text-muted)]");
    });
  });
});
