import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import TermsOfServicePage from "../page";

const REQUIRED_SECTIONS = [
  "1. 適用",
  "2. サービス内容",
  "3. アカウント",
  "4. AI・推薦情報の性質",
  "5. Premium（旅行パス）",
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

  it("Premiumを買い切りの旅行パス（自動更新なし）として記載する", () => {
    const { container } = render(<TermsOfServicePage />);
    const text = container.textContent ?? "";

    expect(text).toContain("1日パス：2.99米ドル（購入した時点から24時間）");
    expect(text).toContain("7日パス：7.99米ドル（購入した時点から7日間）");
    expect(text).toContain("14日パス：11.99米ドル（購入した時点から14日間）");
    expect(text).toContain("自動更新はありません");
    expect(text).toContain("残りの有効期限にそのパスの日数を足します");
    expect(text).toContain("クレジットカードによるお支払いのみ");
    expect(text).toContain("返金したパスの日数分、有効期限を短くします");
    expect(text).toContain("購入後の返品・返金は、原則としてお受けしません");
    expect(text).toContain(
      "決済が重複した場合、および本サービスの不具合によりパスを利用できなかった場合は、お問い合わせのうえ返金します",
    );
    expect(text).toContain("日割りによる返金は行いません");
    // 税区分は未確定。税込であると断定しない。
    expect(text).not.toContain("税込");
    expect(text).not.toContain("税抜");
    expect(text).not.toContain("税別");
    // 月額の自動更新の文言は残さない。
    for (const banned of ["月額", "780円", "毎月自動更新", "Customer Portal", "次回更新日"]) {
      expect(text).not.toContain(banned);
    }
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
