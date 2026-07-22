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

  it("不正な外部地図URLはリンクにせず代替表示へ縮退する", () => {
    render(<GoogleMapRouteLink href="javascript:alert(1)" label="Googleマップで経路案内" />);
    expect(screen.queryByRole("link", { name: "Googleマップで経路案内" })).not.toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("経路リンクを利用できません");
  });

  it("通常経路分析と操作記録が例外でもリンク操作を維持する", () => {
    vi.spyOn(console, "warn").mockImplementation(() => undefined);
    trackSearchEvent.mockImplementationOnce(() => { throw new Error("search analytics unavailable"); });
    trackShrineInteraction.mockImplementationOnce(() => { throw new Error("interaction unavailable"); });
    render(<GoogleMapRouteLink href={href} label="Googleマップで経路案内" shrineId={123} />);
    const link = screen.getByRole("link", { name: "Googleマップで経路案内" });
    expect(() => fireEvent.click(link)).not.toThrow();
    expect(link).toHaveAttribute("href", href);
    vi.restoreAllMocks();
  });

});
