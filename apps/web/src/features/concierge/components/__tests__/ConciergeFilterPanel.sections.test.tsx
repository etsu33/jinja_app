// Concierge Entry Frontend IA v2 -- Personalize section separation
// (docs/product/concierge-input-architecture.md Frontend IA Implementation
// Addendum, Task 11/16). Level 2 (visit preference) and Level 3-A (personal
// profile) / Level 3-B (explicit constraint) must not render as one
// undifferentiated "条件" pile -- each keeps its own accessible section.
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ConciergeFilterPanel from "../ConciergeFilterPanel";

const baseProps = {
  isOpen: true,
  onClose: vi.fn(),
  onApply: vi.fn(),
  goriyakuTags: [{ id: 1, name: "縁結び" }],
  selectedTagIds: [],
  onToggleTag: vi.fn(),
  tagsLoading: false,
  tagsError: null,
  extraCondition: "",
  onExtraConditionChange: vi.fn(),
  plannedVisitDate: "",
  userOrigin: null,
  onPlannedVisitDateChange: vi.fn(),
  onOriginChange: vi.fn(),
  onUseCurrentLocation: vi.fn(),
};

describe("ConciergeFilterPanel Personalize section separation", () => {
  it("renders the compass guide (no birthday input), Level 2 (今回の参拝の希望), and Level 3-B (ご利益) as distinct accessible sections", () => {
    render(<ConciergeFilterPanel {...baseProps} />);

    // コンシェルジュでは生年月日を使わないため、誕生日の入力の代わりにコンパスへの案内を置く。
    expect(screen.queryByRole("region", { name: "誕生日（任意）" })).not.toBeInTheDocument();
    const personalProfile = screen.getByRole("region", { name: "生年月日からの相性" });
    const visitPreference = screen.getByRole("region", { name: "今回の参拝の希望（任意）" });
    const explicitConstraint = screen.getByRole("region", { name: "ご利益を指定する" });

    expect(personalProfile).toBeInTheDocument();
    expect(visitPreference).toBeInTheDocument();
    expect(explicitConstraint).toBeInTheDocument();

    // Distinct, non-overlapping regions -- the guide must not also live
    // inside the L2 region, and vice versa.
    expect(personalProfile).not.toContainElement(screen.getByText("参拝スタイル"));
    expect(visitPreference).toContainElement(screen.getByText("参拝スタイル"));
    expect(explicitConstraint).toContainElement(screen.getByText("縁結び"));
  });

  it("renders nothing when closed (isOpen=false)", () => {
    const { container } = render(<ConciergeFilterPanel {...baseProps} isOpen={false} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("preserves already-selected values when reopened with the same controlled props", () => {
    const props = { ...baseProps, plannedVisitDate: "2026-09-15", selectedTagIds: [1] };

    const { unmount } = render(<ConciergeFilterPanel {...props} />);
    expect(screen.getByDisplayValue("2026-09-15")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "縁結び" })).toHaveClass("border-[var(--kt-color-action-primary)]");
    unmount();

    // Simulates close (unmount) + reopen (remount) with the same lifted
    // state passed back in -- ConciergeClientFull's filter_close handler
    // only toggles isFilterOpen, it never clears selectedTagIds/
    // plannedVisitDate/extraCondition/visitPreferences, so the parent-held values survive.
    render(<ConciergeFilterPanel {...props} />);
    expect(screen.getByDisplayValue("2026-09-15")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "縁結び" })).toHaveClass("border-[var(--kt-color-action-primary)]");
  });
});
