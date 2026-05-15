import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ConciergeTopRecommendationHero from "../ConciergeTopRecommendationHero";

describe("ConciergeTopRecommendationHero", () => {
  it("uses detail as the primary CTA and keeps save as a secondary action", () => {
    render(
      <ConciergeTopRecommendationHero
        name="検証神社"
        href="/shrines/17?ctx=concierge"
        catchCopy="今の相談に合う候補です。"
        primaryReason="今回の相談の中心にある「金運」のテーマと重なるため、この神社が候補に入っています。"
        routeLabel="詳しく見る"
        secondaryActionSlot={<button type="button">保存する</button>}
        onRouteClick={() => {}}
      />,
    );

    expect(screen.queryByRole("button", { name: "まずはここに行く" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "経路案内" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "詳しく見る" })).toHaveAttribute("href", "/shrines/17?ctx=concierge");

    expect(screen.getByText("今回の相談の中心にある「金運」のテーマと重なるため、この神社が候補に入っています")).toBeInTheDocument();
    expect(screen.queryByText("今の状況から動き出すなら、この候補が自然に見えます。")).not.toBeInTheDocument();
    expect(screen.queryByText("この候補を基準にすると判断しやすくなります。")).not.toBeInTheDocument();

    const secondaryActions = screen.getByTestId("hero-secondary-actions");
    expect(within(secondaryActions).queryByRole("link", { name: "詳しく見る" })).not.toBeInTheDocument();
    expect(within(secondaryActions).getByRole("button", { name: "保存する" })).toBeInTheDocument();
  });
});
