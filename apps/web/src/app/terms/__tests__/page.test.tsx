import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import TermsOfServicePage from "../page";

const REQUIRED_SECTIONS = [
  "1. 適用",
  "2. サービス内容",
  "3. アカウント",
  "4. AI・推薦情報の性質",
  "5. Premium",
  "6. 解約・返金",
  "7. ユーザー投稿",
  "8. 禁止事項",
  "9. 知的財産",
  "10. 外部サービス",
  "11. サービスの変更・停止",
  "12. 免責",
  "13. 個人情報",
  "14. 規約の変更",
];

describe("TermsOfServicePage", () => {
  it("主要見出しを表示する", () => {
    render(<TermsOfServicePage />);

    expect(screen.getByRole("heading", { level: 1, name: "利用規約" })).toBeInTheDocument();
    for (const section of REQUIRED_SECTIONS) {
      expect(screen.getByRole("heading", { level: 2, name: section })).toBeInTheDocument();
    }
  });

  it("ご利益・特定の結果を保証すると読める表現を含まない", () => {
    const { container } = render(<TermsOfServicePage />);
    const text = container.textContent ?? "";

    for (const banned of [
      "ご利益を保証",
      "願いが叶います",
      "効果を保証",
      "必ず叶",
      "確実に",
    ]) {
      expect(text).not.toContain(banned);
    }
    expect(text).toContain(
      "参拝によって特定の結果が得られること、願いが叶うこと、その他いかなる効果や利益についても保証しません",
    );
  });

  it("Premiumの課金条件を母艦確定事項どおりに記載する", () => {
    const { container } = render(<TermsOfServicePage />);
    const text = container.textContent ?? "";

    expect(text).toContain("月額780円");
    // 税区分は未確定。780円が税込であると断定しない。
    expect(text).not.toContain("税込");
    expect(text).not.toContain("税抜");
    expect(text).not.toContain("税別");
    expect(text).toContain("契約開始日を基準として毎月自動更新");
    expect(text).toContain("全利用者に共通の締め日はありません");
    expect(text).toContain("解約後も、現在の契約期間が終了するまではPremiumを利用できます");
    expect(text).toContain("次回更新日以降の課金は行われません");
    expect(text).toContain("日割りによる返金は行いません");
  });

  it("事業者の氏名・住所・電話番号を推測して記載しない", () => {
    const { container } = render(<TermsOfServicePage />);
    const text = container.textContent ?? "";

    expect(text).not.toMatch(/\d{2,4}-\d{2,4}-\d{4}/); // 電話番号
    expect(text).not.toMatch(/〒\s*\d{3}-\d{4}/); // 郵便番号
    // 事業者情報ブロックにしか現れない語だけを禁止する。
    // 「神社の所在地」のような本文中の正当な用法は対象外。
    for (const banned of ["運営会社", "運営者名", "代表者", "事業者の所在地", "販売業者"]) {
      expect(text).not.toContain(banned);
    }
  });
});
