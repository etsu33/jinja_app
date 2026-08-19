import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { HomeCompassSection } from "../HomeCompassSection";

// docs/audit/compass-analytics-contract-readiness.md §6 (PR-A): Home discovery
// measurement. Mocked at the dispatch-helper boundary, not PostHog itself --
// see the same pattern in
// ConciergeSectionsRenderer.recommendationInstanceId.test.tsx.
const analyticsMocks = vi.hoisted(() => ({
  trackSearchEvent: vi.fn(),
}));

vi.mock("@/lib/analytics/searchEvents", () => ({
  trackSearchEvent: analyticsMocks.trackSearchEvent,
}));

describe("HomeCompassSection", () => {
  beforeEach(() => {
    analyticsMocks.trackSearchEvent.mockClear();
  });

  it("Compassの入口として題名・説明・CTAを表示する", () => {
    render(<HomeCompassSection />);

    expect(screen.getByText("今月から探す")).toBeInTheDocument();
    expect(screen.getByText("今月の流れと方向から、参拝のきっかけを見つけます。")).toBeInTheDocument();
  });

  it("CTAは/compassへ?ref=homeを付与したリンクで、Compass自身の入力収集を重複させない", () => {
    render(<HomeCompassSection />);

    const link = screen.getByRole("link", { name: "参拝コンパスを見る" });
    expect(link).toHaveAttribute("href", "/compass?ref=home");
  });

  it("CTAクリックでhome_compass_entry_clickをsource=homeで送る（Compass Entry/Activationとは別イベント）", () => {
    render(<HomeCompassSection />);

    fireEvent.click(screen.getByRole("link", { name: "参拝コンパスを見る" }));

    expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledTimes(1);
    expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith("home_compass_entry_click", { source: "home" });
  });

  it("既存SUB PATHSカードと同型の視覚トークンを使う（新しい色・radiusを発明しない）", () => {
    const { container } = render(<HomeCompassSection />);
    const card = container.firstElementChild;
    expect(card?.className).toContain("rounded-3xl");
    expect(card?.className).toContain("border-stone-200/25");
  });
});
