import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import BillingSuccessPage from "../page";

const refreshMock = vi.fn();
const trackBillingEventMock = vi.fn();
let searchParams = new URLSearchParams();
let billingState = {
  loading: false,
  error: null as string | null,
  status: {
    plan: "free",
    is_active: false,
  },
  refresh: refreshMock,
};

vi.mock("next/navigation", () => ({
  useSearchParams: () => searchParams,
}));

vi.mock("@/features/billing/hooks/useBilling", () => ({
  useBilling: () => billingState,
}));

vi.mock("@/lib/analytics/billing", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/analytics/billing")>()),
  trackBillingEvent: (...args: unknown[]) => trackBillingEventMock(...args),
}));

describe("BillingSuccessPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.sessionStorage.clear();
    searchParams = new URLSearchParams("session_id=cs_test_123");
    billingState = {
      loading: false,
      error: null,
      status: {
        plan: "free",
        is_active: false,
      },
      refresh: refreshMock,
    };
  });

  it("session_idなしなら再checkout導線を表示する", () => {
    searchParams = new URLSearchParams();

    render(<BillingSuccessPage />);

    expect(screen.getByRole("heading", { name: "決済セッションを確認できません" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "プレミアム登録へ戻る" })).toHaveAttribute("href", "/billing/upgrade");
  });

  it("premium activeなら有効化済み表示をする", () => {
    billingState = {
      loading: false,
      error: null,
      status: {
        plan: "premium",
        is_active: true,
      },
      refresh: refreshMock,
    };

    render(<BillingSuccessPage />);

    expect(screen.getByRole("heading", { name: "プレミアムが有効になりました" })).toBeInTheDocument();
    expect(screen.getByText("現在のプランに反映されています。")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "プラン状況を見る" })).toHaveAttribute("href", "/billing");
  });

  it("premium未反映なら反映待ち表示をする", () => {
    render(<BillingSuccessPage />);

    expect(screen.getByRole("heading", { name: "決済結果を確認しています" })).toBeInTheDocument();
    expect(screen.getByText("決済完了後の反映待ちです。少し時間をおいてからプラン状況を再確認してください。")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "もう一度登録を開始する" })).toHaveAttribute("href", "/billing/upgrade");
  });

  it("upgrade entry contextをanalytics payloadのsource / funnelStep / cardIdへ戻す", () => {
    window.sessionStorage.setItem(
      "upgrade:entry-context",
      JSON.stringify({
        entryPoint: "state_delta_card",
        entryStep: "comparison_preview",
        entryCardId: "personal_meaning",
        session_id: "raw_session_id",
        sessionId: "rawSessionId",
      }),
    );

    render(<BillingSuccessPage />);

    expect(trackBillingEventMock).toHaveBeenCalledWith("checkout_success", {
      checkoutSessionId: "cs_test_123",
      source: "state_delta_card",
      funnelStep: "comparison_preview",
      cardId: "personal_meaning",
      historyTheme: null,
    });
  });
});
