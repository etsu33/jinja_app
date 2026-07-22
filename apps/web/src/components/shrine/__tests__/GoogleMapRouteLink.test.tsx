import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { trackWebDirection, trackSearchEvent, trackShrineInteraction } = vi.hoisted(() => ({
  trackWebDirection: vi.fn(),
  trackSearchEvent: vi.fn(),
  trackShrineInteraction: vi.fn(),
}));
vi.mock("@/lib/analytics/directionEvents", () => ({ trackWebDirection }));
vi.mock("@/lib/analytics/searchEvents", () => ({ trackSearchEvent }));
vi.mock("@/lib/api/shrineInteractions", () => ({ trackShrineInteraction }));

import GoogleMapRouteLink from "../GoogleMapRouteLink";

const href = "https://www.google.com/maps/dir/?api=1&destination=35,139";

describe("GoogleMapRouteLink direction analytics", () => {
  beforeEach(() => vi.clearAllMocks());

  it.each([
    ["Hero", "hero" as const],
    ["その他", "other" as const],
  ])("一致した%s候補の明示クリックで分類値だけを1回送る", (_label, candidatePosition) => {
    const { rerender } = render(
      <GoogleMapRouteLink
        href={href}
        label="Googleマップで経路案内"
        directionRouteContext={{ matched: true, candidatePosition }}
      />,
    );
    expect(trackWebDirection).not.toHaveBeenCalled();
    rerender(
      <GoogleMapRouteLink
        href={href}
        label="Googleマップで経路案内"
        directionRouteContext={{ matched: true, candidatePosition }}
      />,
    );
    expect(trackWebDirection).not.toHaveBeenCalled();

    const link = screen.getByRole("link", { name: "Googleマップで経路案内" });
    fireEvent.focus(link);
    expect(trackWebDirection).not.toHaveBeenCalled();
    fireEvent.click(link);

    expect(trackWebDirection).toHaveBeenCalledTimes(1);
    expect(trackWebDirection).toHaveBeenCalledWith("direction_match_route_clicked", {
      matched: true,
      candidate_position: candidatePosition,
    });
    expect(link).toHaveAttribute("href", href);
    expect(link).toHaveAttribute("target", "_blank");
  });

  it("direction_reference由来のcontextがなければ方位イベントを送らない", () => {
    render(<GoogleMapRouteLink href={href} label="Googleマップで経路案内" />);
    fireEvent.click(screen.getByRole("link", { name: "Googleマップで経路案内" }));
    expect(trackWebDirection).not.toHaveBeenCalled();
  });

  it("既存契約どおり不一致候補では方位経路イベントを送らない", () => {
    render(
      <GoogleMapRouteLink
        href={href}
        label="Googleマップで経路案内"
        directionRouteContext={{ matched: false, candidatePosition: "other" }}
      />,
    );
    fireEvent.click(screen.getByRole("link", { name: "Googleマップで経路案内" }));
    expect(trackWebDirection).not.toHaveBeenCalled();
  });

  it("方位分析が失敗しても既存リンクと既存経路イベントを維持する", () => {
    trackWebDirection.mockImplementationOnce(() => { throw new Error("analytics unavailable"); });
    render(
      <GoogleMapRouteLink
        href={href}
        label="Googleマップで経路案内"
        directionRouteContext={{ matched: true, candidatePosition: "hero" }}
      />,
    );
    const link = screen.getByRole("link", { name: "Googleマップで経路案内" });
    expect(() => fireEvent.click(link)).not.toThrow();
    expect(trackSearchEvent).toHaveBeenCalledWith("route_open", expect.any(Object));
    expect(link).toHaveAttribute("href", href);
  });

});
