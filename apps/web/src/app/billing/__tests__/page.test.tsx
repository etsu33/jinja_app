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
});
