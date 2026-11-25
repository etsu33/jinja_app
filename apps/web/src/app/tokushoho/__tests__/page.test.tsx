import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import TokushohoPage from "../page";
import { BILLING_PASSES } from "@/lib/billing/passes";
import { CONTACT_EMAIL, CONTACT_MAILTO_HREF } from "@/lib/contact";
import { SELLER_NAME } from "@/lib/legal/seller";

const REQUIRED_ROWS = [
  "販売事業者",
  "所在地",
  "電話番号",
  "連絡先",
  "販売価格",
  "価格以外の費用",
  "支払い方法",
  "支払いの時期",
  "提供の時期",
  "有効期限",
  "返品・キャンセル",
  "動作環境",
];

function rowText(label: string): string {
  const term = screen.getByText(label, { selector: "dt" });
  const row = term.parentElement as HTMLElement;
  return within(row).getByRole("definition").textContent ?? "";
}

describe("TokushohoPage", () => {
  it("見出しと、決められた項目をすべて表示する", () => {
    render(<TokushohoPage />);

    expect(screen.getByRole("heading", { level: 1, name: "特定商取引法に基づく表記" })).toBeInTheDocument();
    for (const label of REQUIRED_ROWS) {
      expect(screen.getByText(label, { selector: "dt" })).toBeInTheDocument();
    }
  });

  it("販売事業者名は1か所の定数から表示する", () => {
    render(<TokushohoPage />);

    expect(rowText("販売事業者")).toBe(SELLER_NAME);
  });

  it("所在地・電話番号は記載せず、請求があれば開示すると書く", () => {
    const { container } = render(<TokushohoPage />);

    expect(rowText("所在地")).toBe("請求があれば遅滞なく開示します");
    expect(rowText("電話番号")).toBe("請求があれば遅滞なく開示します");
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/\d{2,4}-\d{2,4}-\d{4}/); // 電話番号
    expect(text).not.toMatch(/〒\s*\d{3}-\d{4}/); // 郵便番号
  });

  it("連絡先はフッターのお問い合わせと同じ先", () => {
    render(<TokushohoPage />);

    expect(screen.getByRole("link", { name: CONTACT_EMAIL })).toHaveAttribute("href", CONTACT_MAILTO_HREF);
  });

  it("販売価格は購入の画面と同じ値段で、総額であることを書き、税込みとは書かない", () => {
    render(<TokushohoPage />);
    const price = rowText("販売価格");

    expect(price).toBe("1日パス 2.99米ドル／7日パス 7.99米ドル／14日パス 11.99米ドル（表示価格がお支払いの総額です）");
    for (const pass of BILLING_PASSES) {
      expect(price).toContain(`${pass.label} ${pass.priceLabel.replace("$", "")}米ドル`);
    }
    expect(price).not.toContain("税込");
    expect(price).not.toContain("税抜");
  });

  it("価格以外の費用に、通信料と為替の一文を書く", () => {
    render(<TokushohoPage />);
    const cost = rowText("価格以外の費用");

    expect(cost).toContain("インターネットの通信料はお客様のご負担となります。");
    expect(cost).toContain("カード会社の為替レート・手数料により、円でのご請求額は変わることがあります。");
  });

  it("支払い・提供・有効期限・返品の条件を書く", () => {
    render(<TokushohoPage />);

    expect(rowText("支払い方法")).toBe("クレジットカード");
    expect(rowText("支払いの時期")).toBe("購入の手続きの完了時");
    expect(rowText("提供の時期")).toContain("お支払いの完了後、すぐにご利用いただけます");
    const expiry = rowText("有効期限");
    expect(expiry).toContain("1日パスは24時間、7日パスは7日間、14日パスは14日間");
    expect(expiry).toContain("自動更新はありません");
    expect(expiry).toContain("残りの有効期限にそのパスの日数を足します");
    const refund = rowText("返品・キャンセル");
    expect(refund).toContain("購入後の返品・返金は、原則としてお受けしません");
    expect(refund).toContain("決済が重複した場合、および本サービスの不具合によりパスを利用できなかった場合は、お問い合わせのうえ返金します");
    expect(refund).toContain("そのパスの日数分、有効期限を短くします");
  });

  it("動作環境に、ビルドの対象のブラウザを書く", () => {
    render(<TokushohoPage />);
    const env = rowText("動作環境");

    expect(env).toContain("Chrome／Edge／Firefox 111 以降、Safari 16.4 以降");
  });

  it("375px幅で横スクロールを生む固定幅を持たない", () => {
    const { container } = render(<TokushohoPage />);

    for (const el of Array.from(container.querySelectorAll("*"))) {
      const className = el.getAttribute("class") ?? "";
      expect(className).not.toMatch(/(^|\s)w-\[\d{3,}px\]/);
      expect(className).not.toMatch(/(^|\s)min-w-\[\d{3,}px\]/);
    }
    expect(container.querySelector("article")?.className ?? "").toContain("max-w-2xl");
  });
});
