import { render, screen } from "@testing-library/react";
import { fireEvent, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import BillingUpgradePage from "../page";

const pushMock = vi.fn();
const startBillingCheckoutMock = vi.fn();
const assignMock = vi.fn();
const trackBillingEventMock = vi.fn();

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

let searchParamsState = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
  useSearchParams: () => searchParamsState,
}));

vi.mock("@/lib/api/billing", () => ({
  startBillingCheckout: (passType: string) => startBillingCheckoutMock(passType),
}));

vi.mock("@/lib/auth/AuthProvider", () => ({
  useAuth: () => authState,
}));

vi.mock("@/lib/analytics/billing", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/analytics/billing")>()),
  trackBillingEvent: (...args: unknown[]) => trackBillingEventMock(...args),
}));

describe("BillingUpgradePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.sessionStorage.clear();
    searchParamsState = new URLSearchParams();
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

  it("Heroに製品名とコンセプトを表示する", () => {
    render(<BillingUpgradePage />);

    expect(screen.getByRole("heading", { name: "KAMI MUSUBI Premium" })).toBeInTheDocument();
    expect(screen.getByText("一度の答えではなく、変化を重ねていくために。")).toBeInTheDocument();
  });

  it("現在利用できるPremium価値3本を表示する", () => {
    render(<BillingUpgradePage />);

    expect(screen.getByText("何度でも相談できる")).toBeInTheDocument();
    expect(screen.getByText("なぜ今、この神社なのかを深く知る")).toBeInTheDocument();
    expect(screen.getByText("前回からの自分の変化を振り返る")).toBeInTheDocument();
  });

  it("1日・7日・14日の旅行パスを米ドルの値段で表示する", () => {
    render(<BillingUpgradePage />);

    expect(screen.getByRole("button", { name: /1日パス/ })).toHaveTextContent("$2.99");
    expect(screen.getByRole("button", { name: /7日パス/ })).toHaveTextContent("$7.99");
    expect(screen.getByRole("button", { name: /14日パス/ })).toHaveTextContent("$11.99");
  });

  it("自動更新が無いことを書き、月額・解約の案内を出さない", () => {
    const { container } = render(<BillingUpgradePage />);
    const text = container.textContent ?? "";

    expect(text).toContain("自動更新はありません");
    expect(text).toContain("お支払いはクレジットカードのみです");
    for (const banned of ["780円", "/ 月", "解約", "Stripeの管理画面", "β Early User価格"]) {
      expect(text).not.toContain(banned);
    }
    expect(screen.getByRole("link", { name: "プラン状況を確認する" })).toHaveAttribute("href", "/billing");
  });

  it("利用規約とプライバシーポリシーへ到達できる", () => {
    render(<BillingUpgradePage />);

    expect(screen.getByRole("link", { name: "利用規約" })).toHaveAttribute("href", "/terms");
    expect(screen.getByRole("link", { name: "プライバシーポリシー" })).toHaveAttribute(
      "href",
      "/privacy",
    );
    expect(screen.getByRole("link", { name: "特定商取引法に基づく表記" })).toHaveAttribute("href", "/tokushoho");
  });

  it("LegalリンクはCTAより視覚的に弱い", () => {
    render(<BillingUpgradePage />);

    const cta = screen.getByRole("button", { name: /7日パス/ });
    const legal = screen.getByRole("link", { name: "利用規約" });

    // CTAは面を持つ塗りボタン（Worldview の強調面）、Legalは下線テキストのみ
    expect(cta.className).toContain("bg-[var(--kt-color-surface-emphasis)]");
    expect(legal.className).not.toContain("bg-");
    expect(legal.className).toContain("underline");
    // 文字サイズもCTA(text-sm)より小さいこと
    expect(legal.closest("p")?.className ?? "").toContain("text-[11px]");
  });

  it("将来予定コピーとRecommendation精度の誤認表現を含まない", () => {
    const { container } = render(<BillingUpgradePage />);
    const text = container.textContent ?? "";

    for (const banned of [
      "今後の拡張機能",
      "使いやすくしていく予定",
      "予定です",
      "もっと自分に合う神社提案",
      "より自分に合った提案",
      "精度",
    ]) {
      expect(text).not.toContain(banned);
    }
  });

  it("未ログイン時はログインへ送る", () => {
    authState = {
      loading: false,
      isLoggedIn: false,
      user: null,
    };

    render(<BillingUpgradePage />);

    fireEvent.click(screen.getByRole("button", { name: /7日パス/ }));

    expect(pushMock).toHaveBeenCalledWith("/auth/login?returnTo=%2Fbilling%2Fupgrade");
    expect(startBillingCheckoutMock).not.toHaveBeenCalled();
  });

  it("ログイン済みならcheckout URLへ遷移する", async () => {
    startBillingCheckoutMock.mockResolvedValue({
      session_id: "cs_test_123",
      checkout_url: "https://checkout.stripe.com/c/pay/cs_test_123",
    });

    render(<BillingUpgradePage />);

    fireEvent.click(screen.getByRole("button", { name: /7日パス/ }));

    await waitFor(() => {
      expect(assignMock).toHaveBeenCalledWith("https://checkout.stripe.com/c/pay/cs_test_123");
    });
    expect(startBillingCheckoutMock).toHaveBeenCalledWith("7d");
  });

  it.each([
    [/1日パス/, "1d"],
    [/14日パス/, "14d"],
  ])("選んだパス（%s）の種類で購入を始める", async (name, passType) => {
    startBillingCheckoutMock.mockResolvedValue({
      session_id: "cs_test_pass",
      checkout_url: "https://checkout.stripe.com/c/pay/cs_test_pass",
    });

    render(<BillingUpgradePage />);
    fireEvent.click(screen.getByRole("button", { name }));

    await waitFor(() => {
      expect(startBillingCheckoutMock).toHaveBeenCalledWith(passType);
    });
  });

  it("upgrade entry contextにcardIdを保存し、analytics payloadにもcardIdを含める", async () => {
    startBillingCheckoutMock.mockResolvedValue({
      session_id: "cs_test_123",
      checkout_url: "https://checkout.stripe.com/c/pay/cs_test_123",
    });

    render(<BillingUpgradePage />);

    fireEvent.click(screen.getByRole("button", { name: /7日パス/ }));

    await waitFor(() => {
      expect(assignMock).toHaveBeenCalledWith("https://checkout.stripe.com/c/pay/cs_test_123");
    });

    expect(window.sessionStorage.getItem("billing:funnel-attribution")).toBeNull();
    expect(JSON.parse(window.sessionStorage.getItem("upgrade:entry-context") ?? "{}")).toEqual({
      entryPoint: null,
      entryStep: null,
      entryCardId: null,
      entryHistoryTheme: null,
    });
    expect(trackBillingEventMock).toHaveBeenCalledWith("upgrade_click", {
      passType: "7d",
      source: null,
      funnelStep: null,
      cardId: null,
      historyTheme: null,
    });
    expect(trackBillingEventMock).toHaveBeenCalledWith("checkout_started", {
      checkoutSessionId: "cs_test_123",
      passType: "7d",
      source: null,
      funnelStep: null,
      cardId: null,
      historyTheme: null,
    });
  });

  it("attribution queryをsessionStorageとanalyticsへ引き渡す", async () => {
    searchParamsState = new URLSearchParams(
      "source=shrine_detail&funnelStep=comparison_preview&cardId=card_1&historyTheme=work",
    );
    startBillingCheckoutMock.mockResolvedValue({
      session_id: "cs_test_456",
      checkout_url: "https://checkout.stripe.com/c/pay/cs_test_456",
    });

    render(<BillingUpgradePage />);

    fireEvent.click(screen.getByRole("button", { name: /7日パス/ }));

    await waitFor(() => {
      expect(assignMock).toHaveBeenCalledWith("https://checkout.stripe.com/c/pay/cs_test_456");
    });

    expect(JSON.parse(window.sessionStorage.getItem("upgrade:entry-context") ?? "{}")).toEqual({
      entryPoint: "shrine_detail",
      entryStep: "comparison_preview",
      entryCardId: "card_1",
      entryHistoryTheme: "work",
    });
    expect(trackBillingEventMock).toHaveBeenCalledWith("upgrade_click", {
      passType: "7d",
      source: "shrine_detail",
      funnelStep: "comparison_preview",
      cardId: "card_1",
      historyTheme: "work",
    });
    expect(trackBillingEventMock).toHaveBeenCalledWith("checkout_started", {
      checkoutSessionId: "cs_test_456",
      passType: "7d",
      source: "shrine_detail",
      funnelStep: "comparison_preview",
      cardId: "card_1",
      historyTheme: "work",
    });
  });

  it("未ログイン時はattribution query付きでログインへ送る", () => {
    searchParamsState = new URLSearchParams("source=shrine_detail&cardId=card_1");
    authState = { loading: false, isLoggedIn: false, user: null };

    render(<BillingUpgradePage />);

    fireEvent.click(screen.getByRole("button", { name: /7日パス/ }));

    const [href] = pushMock.mock.calls[0] as [string];
    expect(decodeURIComponent(href)).toBe(
      "/auth/login?returnTo=/billing/upgrade?source=shrine_detail&cardId=card_1",
    );
    expect(startBillingCheckoutMock).not.toHaveBeenCalled();
  });

  it("checkout失敗時はエラーを表示し遷移しない", async () => {
    startBillingCheckoutMock.mockRejectedValue(new Error("billing checkout 503"));

    render(<BillingUpgradePage />);

    fireEvent.click(screen.getByRole("button", { name: /7日パス/ }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("決済画面を開始できませんでした。時間をおいて再度お試しください。");
    expect(alert.textContent).not.toContain("503");
    expect(assignMock).not.toHaveBeenCalled();
  });
});
