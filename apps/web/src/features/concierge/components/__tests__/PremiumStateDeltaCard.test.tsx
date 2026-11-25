import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const analyticsMocks = vi.hoisted(() => ({ trackRetentionEvent: vi.fn() }));
vi.mock("@/lib/analytics/retentionEvents", () => ({ trackRetentionEvent: analyticsMocks.trackRetentionEvent }));

import PremiumStateDeltaCard from "../PremiumStateDeltaCard";
import type { StateDelta } from "@/lib/concierge/stateComparison";

const baseDelta: StateDelta = {
  changedNeedTags: ["mental"],
  continuedNeedTags: ["career"],
  summary: "前回より行動に意識が向いています。",
  combinationChange: null,
  transitionNarrative: null,
  actionReflection: null,
  daysSincePrevious: 3,
  within7DaysSincePrevious: true,
} as unknown as StateDelta;

describe("PremiumStateDeltaCard — CTA-B (Continuity) presentation", () => {
  beforeEach(() => {
    analyticsMocks.trackRetentionEvent.mockClear();
  });

  it("non-premium: renders the Continuity prompt + link with unchanged copy / route / event", () => {
    render(<PremiumStateDeltaCard stateDelta={baseDelta} isPremium={false} />);

    expect(screen.getByText("前回との違いをPremiumで確認できます。")).toBeInTheDocument();
    expect(screen.getByText("気持ちの変化や、続いているテーマをあとから振り返れます。")).toBeInTheDocument();

    const link = screen.getByRole("link", { name: "前回との違いを見る" });
    expect(link.getAttribute("href")).toBe(
      "/billing/upgrade?source=state_delta_card&funnelStep=comparison_preview",
    );

    fireEvent.click(link);
    expect(analyticsMocks.trackRetentionEvent).toHaveBeenCalledWith("premium_history_comparison_click", {
      source: "state_delta_card",
      funnelStep: "comparison_preview",
    });
  });

  it("non-premium: CTA-B is a restrained neutral surface, not a second Premium amber box", () => {
    const { container } = render(<PremiumStateDeltaCard stateDelta={baseDelta} isPremium={false} />);

    const section = container.querySelector("section")!;
    // no amber literals, no filled Premium accent button -> does not compete with CTA-A (the seam)
    expect(section.className).not.toMatch(/amber-\d/);
    expect(section.className).not.toContain("bg-[var(--kt-color-premium-surface)]");
    expect(section.className).toContain("bg-[var(--kt-color-surface-default)]");

    const link = screen.getByRole("link", { name: "前回との違いを見る" });
    expect(link.className).not.toContain("bg-[var(--kt-color-premium-accent)]");
  });

  it("premium: still renders the full comparison content (unchanged behavior)", () => {
    render(<PremiumStateDeltaCard stateDelta={baseDelta} isPremium />);

    expect(screen.getByText("前回との違い")).toBeInTheDocument();
    expect(screen.getByText("前回より行動に意識が向いています。")).toBeInTheDocument();
    expect(analyticsMocks.trackRetentionEvent).toHaveBeenCalledWith(
      "premium_history_comparison_view",
      expect.objectContaining({ source: "state_delta_card" }),
    );
  });
});
