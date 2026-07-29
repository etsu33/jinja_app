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
        catchCopy="今の相談に合う候補です。"
        primaryReason="今回の相談の中心にある「金運」のテーマと重なるため、この神社が候補に入っています。"
        routeLabel="詳しく見る"
      />,
    );

    expect(screen.queryByRole("button", { name: "まずはここに行く" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "経路案内" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "詳しく見る" })).toHaveAttribute("href", "/shrines/17?ctx=concierge");

    expect(screen.getByText("相談内容・ご利益との一致")).toBeInTheDocument();
    expect(screen.getByText("今回の相談の中心にある「金運」のテーマと重なるため、この神社が候補に入っています。")).toBeInTheDocument();
    expect(screen.queryByText("今の相談に合う候補です。")).not.toBeInTheDocument();
    expect(screen.queryByText("今の状況から動き出すなら、この候補が自然に見えます。")).not.toBeInTheDocument();
    expect(screen.queryByText("この候補を基準にすると判断しやすくなります。")).not.toBeInTheDocument();

    expect(screen.queryByTestId("hero-secondary-actions")).not.toBeInTheDocument();
  });

  it("主理由の後に通常の推薦理由を表示する", () => {
    render(
      <ConciergeTopRecommendationHero
        name="検証神社"
        catchCopy="入口コピー"
        primaryReason="相談とご利益の一致です。"
        secondaryReason="静かに過ごせることが通常の推薦理由です。"
      />,
    );

    const match = screen.getByTestId("recommendation-match-reason");
    const reason = screen.getByTestId("recommendation-standard-reason");
    expect(match.compareDocumentPosition(reason) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("fact/interpretation/actionをこの順序で表示し、action.sourceは表示しない", () => {
    render(
      <ConciergeTopRecommendationHero
        name="検証神社"
        catchCopy="入口コピー"
        factReason="仕事運に関わる神社です。"
        interpretationReason="相談内容から、今扱いたいテーマを読み取っています。"
        actionReason="参拝前に、問いを一つに絞ることを決めておきます。"
      />,
    );

    const fact = screen.getByTestId("recommendation-reason-v4-fact");
    const interpretation = screen.getByTestId("recommendation-reason-v4-interpretation");
    const action = screen.getByTestId("recommendation-reason-v4-action");

    expect(fact).toHaveTextContent("仕事運に関わる神社です。");
    expect(interpretation).toHaveTextContent("相談内容から、今扱いたいテーマを読み取っています。");
    expect(action).toHaveTextContent("参拝前に、問いを一つに絞ることを決めておきます。");

    expect(fact.compareDocumentPosition(interpretation) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(interpretation.compareDocumentPosition(action) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();

    expect(screen.queryByText("meaning_translation.action_context")).not.toBeInTheDocument();
  });

  it("factReason等が無い場合は各セクションを表示しない", () => {
    render(<ConciergeTopRecommendationHero name="検証神社" catchCopy="入口コピー" />);

    expect(screen.queryByTestId("recommendation-reason-v4-fact")).not.toBeInTheDocument();
    expect(screen.queryByTestId("recommendation-reason-v4-interpretation")).not.toBeInTheDocument();
    expect(screen.queryByTestId("recommendation-reason-v4-action")).not.toBeInTheDocument();
  });


  it("does not render legacy action suggestions on the hero card", () => {
    render(
      <ConciergeTopRecommendationHero
        name="検証神社"
        href="/shrines/17?ctx=concierge"
        catchCopy="今の相談に合う候補です。"
        actionSuggestions={[
          {
            id: "challenge_choose_this_week",
            historyTheme: "勝負",
            title: "今週やることを1つ選ぶ",
            description: "迷っていることから、まず1つだけ選んで動きます。",
            category: "prepare",
            timing: "before_visit",
            difficulty: "easy",
            timeEstimate: "5分",
            measurementKey: "weekly_choice",
          },
        ]}
        analyticsSource="concierge_result"
        threadId="thread-1"
        resultSetId="result-set-1"
        shrineId={17}
        recommendationRank={1}
        historyTheme="勝負"
        routeLabel="詳しく見る"
      />,
    );

    expect(screen.queryByTestId("hero-action-suggestions")).not.toBeInTheDocument();
    expect(screen.queryByText("次の小さな一歩")).not.toBeInTheDocument();
    expect(screen.queryByText("今週やることを1つ選ぶ")).not.toBeInTheDocument();
    expect(screen.queryByText("迷っていることから、まず1つだけ選んで動きます。")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "試してみる" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "完了" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "詳しく見る" })).toHaveAttribute("href", "/shrines/17?ctx=concierge");
    expect(analyticsMocks.trackSearchEvent).not.toHaveBeenCalled();
  });
  it("renders v4 preview as a one-line summary and tracks preview views", async () => {
    render(
      <ConciergeTopRecommendationHero
        name="検証神社"
        href="/shrines/17?ctx=concierge"
        catchCopy="今の相談に合う候補です。"
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

    expect(screen.getByTestId("hero-action-suggestion-v4-preview")).toBeInTheDocument();
    expect(screen.getByText("次の一歩")).toBeInTheDocument();
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
        catchCopy="今の相談に合う候補です。"
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
          catchCopy="今の相談に合う候補です。"
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
          catchCopy="今の相談に合う候補です。"
          originSummary="由緒の要約"
          address="東京都千代田区1-1-1"
          topReasonLabel="選ばれた理由"
          primaryReason="相談とご利益の一致"
          routeLabel="詳しく見る"
        />,
      );

      expect(screen.getByText("由緒の要約").className).toContain("text-[var(--kt-color-text-secondary)]");
      expect(screen.getByText("東京都千代田区1-1-1").className).toContain("text-[var(--kt-color-text-muted)]");
      expect(screen.getByText("選ばれた理由").className).toContain("text-[var(--kt-color-text-muted)]");
    });
  });
});
