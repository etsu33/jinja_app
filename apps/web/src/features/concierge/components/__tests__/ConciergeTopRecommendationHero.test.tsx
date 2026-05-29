import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ConciergeTopRecommendationHero from "../ConciergeTopRecommendationHero";

describe("ConciergeTopRecommendationHero", () => {
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
    expect(screen.getByText("今回の入口")).toBeInTheDocument();
    expect(screen.getByText("今の相談に合う候補です。")).toBeInTheDocument();
    expect(
      screen.queryByText("今回の相談の中心にある「金運」のテーマと重なるため、この神社が候補に入っています"),
    ).not.toBeInTheDocument();
    expect(screen.queryByText("今の状況から動き出すなら、この候補が自然に見えます。")).not.toBeInTheDocument();
    expect(screen.queryByText("この候補を基準にすると判断しやすくなります。")).not.toBeInTheDocument();

    expect(screen.queryByTestId("hero-secondary-actions")).not.toBeInTheDocument();
  });
});
