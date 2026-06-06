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


  it("renders action suggestions and tracks view, click, and done events", async () => {
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
            timing: "today",
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
  });
});
