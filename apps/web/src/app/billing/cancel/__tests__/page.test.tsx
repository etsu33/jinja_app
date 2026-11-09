import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import BillingCancelPage from "../page";

describe("BillingCancelPage", () => {
  it("cancel文言とbilling upgradeへの復帰導線を表示する", () => {
    render(<BillingCancelPage />);

    expect(screen.getByRole("heading", { name: "パスの購入を中断しました" })).toBeInTheDocument();
    expect(screen.getByText("決済は完了していません。必要になったタイミングで、もう一度購入できます。")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "パスの購入へ戻る" })).toHaveAttribute("href", "/billing/upgrade");
    expect(screen.getByRole("link", { name: "コンシェルジュへ戻る" })).toHaveAttribute("href", "/concierge");
  });
});
