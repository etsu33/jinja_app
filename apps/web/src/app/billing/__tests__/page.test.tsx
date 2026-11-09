import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import BillingPage from "../page";
import type { BillingStatus } from "@/lib/api/billing";

const getBillingStatusMock = vi.fn();

vi.mock("@/lib/api/billing", () => ({
  getBillingStatus: () => getBillingStatusMock(),
}));

function status(overrides: Partial<BillingStatus> = {}): BillingStatus {
  return {
    plan: "free",
    is_active: false,
    provider: "stripe",
    current_period_end: null,
    trial_ends_at: null,
    cancel_at_period_end: false,
    ...overrides,
  };
}

describe("BillingPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("現在のプランを表示する", async () => {
    getBillingStatusMock.mockResolvedValue(status({ plan: "premium", is_active: true }));

    render(<BillingPage />);

    expect(await screen.findByText("Premium（有効）")).toBeInTheDocument();
  });

  it("実装事実と矛盾するstaleな注記を表示しない", async () => {
    getBillingStatusMock.mockResolvedValue(status());

    const { container } = render(<BillingPage />);
    await waitFor(() => expect(screen.getByText("Free")).toBeInTheDocument());

    const text = container.textContent ?? "";
    // 決済連携は PR-2 / PR-2b で実装済み。「この後でOK」は既に事実に反する。
    expect(text).not.toContain("決済連携はこの後でOK");
    expect(text).not.toContain("まずは「状態が見える」ことを優先");
  });

  it("Premium なら日本時間の有効期限と、パスの追加購入の導線を出す", async () => {
    getBillingStatusMock.mockResolvedValue(
      status({ plan: "premium", is_active: true, current_period_end: "2026-11-10T06:30:00Z" }),
    );

    render(<BillingPage />);

    expect(await screen.findByText("有効期限：2026年11月10日 15:30")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "パスを追加で購入する" })).toHaveAttribute("href", "/billing/upgrade");
    expect(screen.queryByRole("link", { name: "プランを管理" })).toBeNull();
  });

  it("Free ならパスの購入の導線を出し、期限は出さない", async () => {
    getBillingStatusMock.mockResolvedValue(status());

    render(<BillingPage />);

    expect(await screen.findByRole("link", { name: "パスを購入する" })).toHaveAttribute("href", "/billing/upgrade");
    expect(screen.queryByText(/有効期限/)).toBeNull();
  });
});
