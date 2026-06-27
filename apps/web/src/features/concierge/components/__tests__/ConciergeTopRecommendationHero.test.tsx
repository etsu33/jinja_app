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


  it("renders before-visit action suggestions and tracks legacy and canonical events", async () => {
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

    expect(screen.getByTestId("hero-action-suggestions")).toBeInTheDocument();
    expect(screen.getByText("次の小さな一歩")).toBeInTheDocument();
    expect(screen.getByText("今週やることを1つ選ぶ")).toBeInTheDocument();
    expect(screen.getByText("迷っていることから、まず1つだけ選んで動きます。")).toBeInTheDocument();
    expect(screen.queryByText("参拝後")).not.toBeInTheDocument();
    expect(screen.queryByText("記録")).not.toBeInTheDocument();

    await waitFor(() => {
      expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith(
        "action_suggestion_view",
        expect.objectContaining({
          source: "concierge_result",
          threadId: "thread-1",
          resultSetId: "result-set-1",
          shrineId: 17,
          recommendationRank: 1,
          position: "hero_primary",
          historyTheme: "勝負",
          actionSuggestionId: "challenge_choose_this_week",
          actionCategory: "prepare",
          actionTheme: "勝負",
          actionPosition: 1,
        }),
      );
    });

    fireEvent.click(screen.getByRole("button", { name: "試してみる" }));
    expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith(
      "action_suggestion_click",
      expect.objectContaining({
        actionSuggestionId: "challenge_choose_this_week",
        actionCategory: "prepare",
        actionTheme: "勝負",
        actionPosition: 1,
      }),
    );
    expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith(
      "action_started",
      expect.objectContaining({
        actionSuggestionId: "challenge_choose_this_week",
        actionCategory: "prepare",
        actionTheme: "勝負",
        actionPosition: 1,
        legacyEventName: "action_suggestion_click",
      }),
    );

    fireEvent.click(screen.getByRole("button", { name: "完了" }));
    expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith(
      "action_done",
      expect.objectContaining({
        actionSuggestionId: "challenge_choose_this_week",
        actionCategory: "prepare",
        actionTheme: "勝負",
        actionPosition: 1,
      }),
    );
    expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith(
      "action_completed",
      expect.objectContaining({
        actionSuggestionId: "challenge_choose_this_week",
        actionCategory: "prepare",
        actionTheme: "勝負",
        actionPosition: 1,
        legacyEventName: "action_done",
      }),
    );
  });
  it("renders v4 preview actions and tracks preview and click events", async () => {
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
    expect(screen.getByText("次に取りやすい行動")).toBeInTheDocument();
    expect(screen.getByText("まず詳細を見て、行く理由を確認する")).toBeInTheDocument();
    expect(screen.getByText("候補として保存して、あとで見返す")).toBeInTheDocument();
    expect(screen.getByText("この神社に行くとしたら、何を整理する時間にしたいですか？")).toBeInTheDocument();

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

    fireEvent.click(screen.getByRole("button", { name: "この行動で進める" }));
    expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith(
      "primary_action_click",
      expect.objectContaining({
        actionSuggestionVersion: "v4",
        actionRole: "primary",
        actionType: "detail_open",
        actionLabel: "まず詳細を見て、行く理由を確認する",
        promptType: "before_visit",
        actionSource: "fallback",
        sourceKeys: "meaning_translation",
      }),
    );

    fireEvent.click(screen.getByRole("button", { name: "この候補を使う" }));
    expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith(
      "secondary_action_click",
      expect.objectContaining({
        actionSuggestionVersion: "v4",
        actionRole: "secondary",
        actionType: "save",
        actionLabel: "候補として保存して、あとで見返す",
        promptType: "before_visit",
        actionSource: "fallback",
        sourceKeys: "meaning_translation",
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
