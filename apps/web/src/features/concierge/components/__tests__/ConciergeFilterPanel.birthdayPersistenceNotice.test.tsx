// 誕生日はログイン中のみ profile へ永続化される（useSharedBirthdayPersistence）。
// 入力時点でそれが分かるよう、ログイン中だけ保存説明を出す。
// Guest には出さない — 保存されないのに「保存します」と読ませないため。
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ConciergeFilterPanel from "../ConciergeFilterPanel";

const NOTICE = "ログイン中は、生年月日を保存してコンシェルジュとコンパスで共通利用します。";

const baseProps = {
  isOpen: true,
  onClose: vi.fn(),
  onApply: vi.fn(),
  birthdate: "",
  onBirthdateChange: vi.fn(),
  element4: null,
  goriyakuTags: [{ id: 1, name: "縁結び" }],
  suggestedTags: [],
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

describe("ConciergeFilterPanel 誕生日の保存説明", () => {
  it("ログイン中は保存説明を表示する", () => {
    render(<ConciergeFilterPanel {...baseProps} isLoggedIn />);

    expect(screen.getByText(NOTICE)).toBeInTheDocument();
    // 誕生日セクションの中に置く（別の場所に浮かせない）
    expect(screen.getByRole("region", { name: "誕生日（任意）" })).toContainElement(
      screen.getByText(NOTICE),
    );
  });

  it("Guestには保存説明を表示しない", () => {
    render(<ConciergeFilterPanel {...baseProps} isLoggedIn={false} />);

    expect(screen.queryByText(NOTICE)).not.toBeInTheDocument();
  });

  it("isLoggedIn未指定でも保存説明を表示しない（既定は保存しない側）", () => {
    const { container } = render(<ConciergeFilterPanel {...baseProps} />);

    expect(screen.queryByText(NOTICE)).not.toBeInTheDocument();
    // 「保存」と読ませる文言自体を置かない
    expect(container.textContent ?? "").not.toContain("保存します");
  });

  it("「誕生日（任意）」の見出しと任意である説明を維持する", () => {
    render(<ConciergeFilterPanel {...baseProps} isLoggedIn />);

    expect(screen.getByRole("region", { name: "誕生日（任意）" })).toBeInTheDocument();
    expect(screen.getByText("誕生日（任意）")).toBeInTheDocument();
    expect(screen.getByText("相性候補を見るための任意の補助情報です")).toBeInTheDocument();
    // 必須化しない
    expect(screen.getByLabelText("誕生日")).not.toBeRequired();
  });

  it("onBirthdateChangeの契約を壊さない（ログイン状態に依らず発火する）", () => {
    for (const isLoggedIn of [true, false]) {
      const onBirthdateChange = vi.fn();
      const { unmount } = render(
        <ConciergeFilterPanel
          {...baseProps}
          isLoggedIn={isLoggedIn}
          onBirthdateChange={onBirthdateChange}
        />,
      );

      fireEvent.change(screen.getByLabelText("誕生日"), { target: { value: "1990-05-20" } });

      expect(onBirthdateChange).toHaveBeenCalledTimes(1);
      expect(onBirthdateChange).toHaveBeenCalledWith("1990-05-20");
      unmount();
    }
  });
});
