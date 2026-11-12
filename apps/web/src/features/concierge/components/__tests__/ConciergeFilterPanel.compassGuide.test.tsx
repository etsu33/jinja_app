// コンシェルジュでは生年月日を使わない（生年月日との相性はコンパスの役割）。
// 条件のパネルには誕生日の入力・補助傾向・相性から見た候補を置かず、コンパスへの案内を置く。
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

describe("ConciergeFilterPanel コンパスへの案内", () => {
  it("生年月日からの相性はコンパスで見られることを案内し、/compass への入り口を置く", () => {
    render(<ConciergeFilterPanel {...baseProps} />);

    const region = screen.getByRole("region", { name: "生年月日からの相性" });
    expect(region).toContainElement(screen.getByText("生年月日からの相性は、コンパスで見られます。"));
    const link = screen.getByRole("link", { name: "コンパスで相性を見る" });
    expect(link).toHaveAttribute("href", "/compass");
    expect(region).toContainElement(link);
  });

  it("誕生日の入力・補助傾向・相性から見た候補を置かない", () => {
    const { container } = render(<ConciergeFilterPanel {...baseProps} />);
    const text = container.textContent ?? "";

    expect(screen.queryByLabelText("誕生日")).not.toBeInTheDocument();
    expect(container.querySelector('input[type="date"][aria-label="誕生日"]')).toBeNull();
    for (const removed of ["誕生日（任意）", "誕生日から見た補助傾向", "相性から見た候補", "生年月日を保存"]) {
      expect(text).not.toContain(removed);
    }
  });
});
