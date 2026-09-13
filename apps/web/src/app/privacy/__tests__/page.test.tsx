import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import PrivacyPolicyPage from "../page";

const REQUIRED_SECTIONS = [
  "1. 取得する情報",
  "2. 利用目的",
  "3. 相談内容について",
  "4. 位置情報について",
  "5. Cookie / localStorageについて",
  "6. Analyticsについて",
  "7. 決済サービスについて",
  "8. 外部AIサービスについて",
  "9. 外部サービスについて",
  "10. 保存期間",
  "11. 開示・訂正・削除等",
  "12. お問い合わせ",
];

describe("PrivacyPolicyPage", () => {
  it("主要見出しを表示する", () => {
    render(<PrivacyPolicyPage />);

    expect(screen.getByRole("heading", { level: 1, name: "プライバシーポリシー" })).toBeInTheDocument();
    for (const section of REQUIRED_SECTIONS) {
      expect(screen.getByRole("heading", { level: 2, name: section })).toBeInTheDocument();
    }
  });

  it("外部生成AIへ相談内容を送信していない旨を明記する", () => {
    render(<PrivacyPolicyPage />);

    expect(
      screen.getByText(
        "現在、KAMI MUSUBIでは、利用者の相談内容を外部の生成AIサービスへ送信していません。",
      ),
    ).toBeInTheDocument();
  });

  it("将来外部AIを導入する場合はポリシーを更新する旨を明記する", () => {
    const { container } = render(<PrivacyPolicyPage />);
    const text = container.textContent ?? "";

    expect(text).toContain("将来、外部AIサービスを利用する機能を導入する場合");
    expect(text).toContain("本プライバシーポリシーを更新します");
  });

  it("OpenAI等の外部生成AIを現在利用していると誤認させる文言がない", () => {
    const { container } = render(<PrivacyPolicyPage />);
    const text = container.textContent ?? "";

    for (const banned of ["OpenAI", "ChatGPT", "GPT", "Anthropic", "Claude", "Gemini"]) {
      expect(text).not.toContain(banned);
    }
  });

  it("確認できない保存期間・削除方式を断定しない", () => {
    const { container } = render(<PrivacyPolicyPage />);
    const text = container.textContent ?? "";

    // 具体的な保存期間を勝手に決めていないこと
    for (const banned of ["30日", "90日", "1年間", "6か月", "完全に削除します"]) {
      expect(text).not.toContain(banned);
    }
    expect(text).toContain("保存期間の上限や、期間経過による自動削除の仕組みは定めていません");
  });

  it("現行実装で確認できる取得情報と外部サービスを記載する", () => {
    const { container } = render(<PrivacyPolicyPage />);
    const text = container.textContent ?? "";

    for (const fact of [
      "access_token",
      "refresh_token",
      "concierge_anon_id",
      "Stripe",
      "PostHog",
      "Google Maps Platform",
      "OpenStreetMap",
    ]) {
      expect(text).toContain(fact);
    }
    expect(text).toContain("クレジットカード番号などの支払手段そのものは本サービスのサーバーに保存しません");
  });
});
