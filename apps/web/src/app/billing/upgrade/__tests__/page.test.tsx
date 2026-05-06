import { render, screen } from "@testing-library/react";
import BillingUpgradePage from "../page";

describe("BillingUpgradePage", () => {
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

    expect(
      screen.getByText("プレミアム機能は現在順次準備中です。利用可能になり次第、この画面から案内します。"),
    ).toBeInTheDocument();

    expect(screen.getByRole("link", { name: "無料でコンシェルジュを使う" })).toHaveAttribute("href", "/concierge");

    expect(screen.getByRole("link", { name: "プラン状況を確認する" })).toHaveAttribute("href", "/billing");
  });
});
