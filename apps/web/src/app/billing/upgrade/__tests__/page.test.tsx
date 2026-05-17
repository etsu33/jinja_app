import { render, screen } from "@testing-library/react";
import { fireEvent, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import BillingUpgradePage from "../page";

const pushMock = vi.fn();
const startBillingCheckoutMock = vi.fn();
const assignMock = vi.fn();

type MockAuthState = {
  loading: boolean;
  isLoggedIn: boolean;
  user: { id: number } | null;
};

let authState: MockAuthState = {
  loading: false,
  isLoggedIn: true,
  user: { id: 1 },
};

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/lib/api/billing", () => ({
  startBillingCheckout: () => startBillingCheckoutMock(),
}));

vi.mock("@/lib/auth/AuthProvider", () => ({
  useAuth: () => authState,
}));

describe("BillingUpgradePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authState = {
      loading: false,
      isLoggedIn: true,
      user: { id: 1 },
    };
    Object.defineProperty(window, "location", {
      value: { assign: assignMock },
      writable: true,
    });
  });

  it("価値訴求と導線を表示する", () => {
    render(<BillingUpgradePage />);

    expect(
      screen.getByRole("heading", {
        name: "もっと自分に合う神社提案を受け取りたい方へ",
      }),
    ).toBeInTheDocument();

    expect(screen.getByText("無料プランとの違い")).toBeInTheDocument();
    expect(screen.getByText("無料")).toBeInTheDocument();
    expect(screen.getByText("プレミアム")).toBeInTheDocument();

    expect(screen.getByRole("button", { name: "プレミアムにする" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "プラン状況を確認する" })).toHaveAttribute("href", "/billing");
  });

  it("未ログイン時はログインへ送る", () => {
    authState = {
      loading: false,
      isLoggedIn: false,
      user: null,
    };

    render(<BillingUpgradePage />);

    fireEvent.click(screen.getByRole("button", { name: "プレミアムにする" }));

    expect(pushMock).toHaveBeenCalledWith("/auth/login?returnTo=%2Fbilling%2Fupgrade");
    expect(startBillingCheckoutMock).not.toHaveBeenCalled();
  });

  it("ログイン済みならcheckout URLへ遷移する", async () => {
    startBillingCheckoutMock.mockResolvedValue({
      session_id: "cs_test_123",
      checkout_url: "https://checkout.stripe.com/c/pay/cs_test_123",
    });

    render(<BillingUpgradePage />);

    fireEvent.click(screen.getByRole("button", { name: "プレミアムにする" }));

    await waitFor(() => {
      expect(assignMock).toHaveBeenCalledWith("https://checkout.stripe.com/c/pay/cs_test_123");
    });
  });
});
