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

    expect(screen.getByText("今回の入口")).toBeInTheDocument();
    expect(screen.getByText("今の相談に合う候補です。")).toBeInTheDocument();
    expect(
      screen.queryByText("今回の相談の中心にある「金運」のテーマと重なるため、この神社が候補に入っています"),
    ).not.toBeInTheDocument();
    expect(screen.queryByText("今の状況から動き出すなら、この候補が自然に見えます。")).not.toBeInTheDocument();
    expect(screen.queryByText("この候補を基準にすると判断しやすくなります。")).not.toBeInTheDocument();

    expect(screen.queryByTestId("hero-secondary-actions")).not.toBeInTheDocument();
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
          promptType: "before_visit",
          actionSource: "fallback",
          sourceKeys: "meaning_translation",
          summaryLine: "まず詳細を見て、行く理由を確認する",
        }),
      );
    });

    expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith(
      "reflection_prompt_view",
      expect.objectContaining({
        promptType: "before_visit",
        reflectionPromptSourceSeed: "fallback",
      }),
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
});
