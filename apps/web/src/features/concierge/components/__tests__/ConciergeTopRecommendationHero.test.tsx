import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ConciergeTopRecommendationHero from "../ConciergeTopRecommendationHero";

describe("ConciergeTopRecommendationHero", () => {
  it("keeps route as the only primary CTA and renders detail/save as secondary actions", () => {
    render(
      <ConciergeTopRecommendationHero
        name="検証神社"
        href="/shrines/17?ctx=concierge"
        catchCopy="今の相談に合う候補です。"
        primaryReason="今回の相談の中心にある「金運」のテーマと重なるため、この神社が候補に入っています。"
        routeLabel="まずはここに行く"
        secondaryActionSlot={<button type="button">保存する</button>}
        onRouteClick={() => {}}
      />,
    );

    expect(screen.getByRole("button", { name: "まずはここに行く" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "経路案内" })).not.toBeInTheDocument();

    expect(screen.getByText("今回の相談の中心にある「金運」のテーマと重なるため、この神社が候補に入っています")).toBeInTheDocument();
    expect(screen.getByText("だから今はここに行くのが一番迷いが少ないです。")).toBeInTheDocument();

    const secondaryActions = screen.getByTestId("hero-secondary-actions");
    expect(within(secondaryActions).getByRole("link", { name: "詳しく見る" })).toHaveAttribute(
      "href",
      "/shrines/17?ctx=concierge",
    );
    expect(within(secondaryActions).getByRole("button", { name: "保存する" })).toBeInTheDocument();
  });
});
